# Korean title logo for 17986/Title.bflim (keeps original cloud / tiles, replaces lettering)
import sys, os, numpy as np, cv2
sys.path.insert(0, os.path.dirname(__file__))
from PIL import Image, ImageDraw
from texpatch import load_tex
from koimg import text_mask, fit, dilate, compose

B = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')


def layered(text, size, box, layers, font='heavy', skew=0.0, sx=1.0, stretch=False, close=0):
    """layers: list of (radius, rgb) outermost first; radius 0 = fill"""
    x, y, w, h = box
    pad = max(r for r, c in layers) + 1
    m = text_mask(text, size, font, skew)
    if sx != 1.0:
        m = np.array(Image.fromarray(m).resize((int(m.shape[1] * sx), m.shape[0]), Image.LANCZOS))
    m = np.array(Image.fromarray(m).resize((w - 2 * pad, h - 2 * pad), Image.LANCZOS)) if stretch else fit(m, w - 2 * pad, h - 2 * pad)
    mh, mw = m.shape
    big = np.zeros((mh + 2 * pad, mw + 2 * pad), np.uint8)
    big[pad:pad + mh, pad:pad + mw] = m
    can = np.zeros(big.shape + (4,), np.float32)
    if close:
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * close + 1, 2 * close + 1))
        closed = cv2.morphologyEx(dilate(big, 2), cv2.MORPH_CLOSE, k)
    else:
        closed = big
    outer = max(r for r, c in layers)
    compose(can, [(dilate(closed if r >= outer - 2 and close else big, r), c, 0, 0) for r, c in layers], 0, 0)
    ox = x + (w - big.shape[1]) // 2
    oy = y + (h - big.shape[0]) // 2
    return can, ox, oy, (ox + pad, oy + pad, mw, mh)


def over(dst, can, ox, oy):
    H, W = dst.shape[:2]
    h, w = can.shape[:2]
    x0, y0, x1, y1 = max(0, ox), max(0, oy), min(W, ox + w), min(H, oy + h)
    s = can[y0 - oy:y1 - oy, x0 - ox:x1 - ox]
    d = dst[y0:y1, x0:x1].astype(np.float32) / 255
    a = s[..., 3:4]
    na = a + d[..., 3:4] * (1 - a)
    rgb = (s[..., :3] * a + d[..., :3] * d[..., 3:4] * (1 - a)) / np.maximum(na, 1e-6)
    dst[y0:y1, x0:x1, :3] = (rgb * 255).clip(0, 255)
    dst[y0:y1, x0:x1, 3:4] = (na * 255).clip(0, 255)


def eye(dst, cx, cy, r):
    im = Image.fromarray(dst, 'RGBA')
    d = ImageDraw.Draw(im)
    d.ellipse((cx - r - 1, cy - r - 1, cx + r + 1, cy + r + 1), fill=(0, 0, 0, 255))
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 255, 255, 255))
    pr = max(2, r // 2)
    d.ellipse((cx - pr + 1, cy - pr, cx + pr + 1, cy + pr), fill=(0, 0, 0, 255))
    dst[:] = np.array(im)


def build():
    img, fmt = load_tex(os.path.join(B, 'dec'), '17986/Title.bflim')
    img = img.copy()
    r, g, b, a = [img[..., i].astype(int) for i in range(4)]
    letter = ((r > 150) & (b < 110) & (a > 100)) | ((r < 90) & (g < 90) & (b < 90) & (a > 100))
    region = np.zeros(letter.shape, bool)
    region[8:172, 60:330] = True
    m = dilate((letter & region).astype(np.uint8) * 255, 3)
    m[172:, :] = 0
    rgb = cv2.inpaint(np.ascontiguousarray(img[..., :3]), m, 4, cv2.INPAINT_TELEA)
    al = cv2.inpaint(np.ascontiguousarray(img[..., 3]), m, 4, cv2.INPAINT_TELEA)
    img[..., :3] = rgb
    img[..., 3] = al
    band = m[150:173, 120:240] > 0
    img[150:173, 120:240, 3][band] = 0
    # tiles: clear the kana inside the 5 yellow hexes
    tiles = [(137, 174, 20, 23), (166, 174, 20, 23), (194, 174, 21, 23), (223, 174, 21, 23), (252, 174, 20, 23)]
    for (x, y, w, h) in tiles:
        sub = img[y:y + h, x:x + w]
        dark = (sub[..., 0] < 120) & (sub[..., 3] > 100)
        inner = np.zeros_like(dark)
        inner[3:-3, 3:-3] = True
        sub[dark & inner, :3] = (248, 224, 0)
    WHITE, BLACK, YEL, RED = (255, 255, 255), (12, 12, 12), (250, 222, 0), (230, 16, 22)
    # 요괴 (yellow, black outline, white rim)
    can, ox, oy, _ = layered('요괴', 44, (60, 24, 120, 78), [(7, WHITE), (5, BLACK), (0, YEL)], skew=-0.12, stretch=True)
    over(img, can, ox, oy)
    # 삼국지 (red, yellow inline, thick black, white rim)
    can, ox, oy, gb = layered('삼국지', 72, (74, 76, 262, 100), [(9, WHITE), (7, BLACK), (3, YEL), (0, RED)], stretch=True, close=4)
    over(img, can, ox, oy)
    # tiles text
    for (x, y, w, h), t in zip(tiles, ['★', '삼', '국', '지', '★']):
        c2, ox2, oy2, _ = layered(t, 15, (x + 1, y + 2, w - 2, h - 3), [(0, BLACK)], font='heavy')
        over(img, c2, ox2, oy2)
    # googly eyes like the original logo
    eye(img, 150, 52, 6)
    gx, gy, gw, gh = gb
    eye(img, gx + gw - 12, gy + gh - 22, 7)
    return img


if __name__ == '__main__':
    img = build()
    Image.fromarray(img, 'RGBA').save(os.path.join(B, 'tr', 'img', '17986_Title.bflim.png'))
    bg = Image.new('RGBA', (512, 256), (200, 120, 40, 255))
    bg.alpha_composite(Image.fromarray(img, 'RGBA'))
    bg.crop((30, 0, 370, 210)).resize((1020, 630), Image.NEAREST).save(os.path.join(B, 'view', 'logo_new.png'))
