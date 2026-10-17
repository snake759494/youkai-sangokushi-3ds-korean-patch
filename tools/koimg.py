# Korean text rendering helpers for texture localization
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

import os
FD = os.environ.get('YK_GAME', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')) + '/'
FONTS = {'heavy': FD + 'NanumSquareNeo-eHv.ttf', 'xbold': FD + 'NanumSquareNeo-dEb.ttf',
         'bold': FD + 'NanumSquareNeo-cBd.ttf', 'reg': FD + 'NanumSquareNeo-bRg.ttf'}


def text_mask(text, size, font='heavy', skew=0.0, spacing=0):
    f = ImageFont.truetype(FONTS[font], size)
    d = ImageDraw.Draw(Image.new('L', (4, 4)))
    lines = text.split('\n')
    bbs = [d.textbbox((0, 0), l, font=f) for l in lines]
    asc, desc = f.getmetrics()
    lh = asc + desc + spacing
    W = max(b[2] for b in bbs) + 8 + int(abs(skew) * lh * len(lines))
    H = lh * len(lines) + 8
    im = Image.new('L', (W, H), 0)
    dd = ImageDraw.Draw(im)
    for k, l in enumerate(lines):
        bw = bbs[k][2] - bbs[k][0]
        dd.text(((W - bw) // 2 - bbs[k][0], 4 + k * lh), l, font=f, fill=255)
    if skew:
        im = im.transform(im.size, Image.AFFINE, (1, skew, -skew * H / 2, 0, 1, 0), Image.BICUBIC)
    a = np.array(im)
    ys, xs = np.nonzero(a > 8)
    if len(ys) == 0:
        return a[:1, :1]
    return a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def fit(mask, maxw, maxh):
    h, w = mask.shape
    sx = min(1.0, maxw / w)
    sy = min(1.0, maxh / h)
    s = min(sy, 1.0)
    nw = max(1, int(w * min(sx, s)))
    nh = max(1, int(h * s))
    return np.array(Image.fromarray(mask).resize((nw, nh), Image.LANCZOS))


def dilate(mask, r):
    if r <= 0:
        return mask
    return np.array(Image.fromarray(mask).filter(ImageFilter.MaxFilter(2 * r + 1)))


def compose(canvas, layers, x, y):
    """canvas: float RGBA (h,w,4) 0..1 ; layers: list of (mask uint8, (r,g,b), dx, dy) drawn in order"""
    H, W = canvas.shape[:2]
    for m, col, dx, dy in layers:
        h, w = m.shape
        x0 = x + dx
        y0 = y + dy
        sx0 = max(0, -x0)
        sy0 = max(0, -y0)
        x1 = min(W, x0 + w)
        y1 = min(H, y0 + h)
        if x1 <= max(0, x0) or y1 <= max(0, y0):
            continue
        a = m[sy0:sy0 + (y1 - max(0, y0)), sx0:sx0 + (x1 - max(0, x0))].astype(np.float32) / 255
        reg = canvas[max(0, y0):y1, max(0, x0):x1]
        c = np.array(col, np.float32) / 255
        oa = reg[..., 3:4]
        na = a[..., None] + oa * (1 - a[..., None])
        rgb = (c * a[..., None] + reg[..., :3] * oa * (1 - a[..., None])) / np.maximum(na, 1e-6)
        reg[..., :3] = rgb
        reg[..., 3:4] = na
    return canvas


def styled(text, size, font, fill, outline=None, ow=0, shadow=None, sd=(0, 0), skew=0.0, maxw=9999, maxh=9999, spacing=0):
    """returns (rgba float image, w, h) tight"""
    m = text_mask(text, size, font, skew, spacing)
    pad = ow + max(abs(sd[0]), abs(sd[1])) + 1
    m = fit(m, maxw - 2 * pad, maxh - 2 * pad)
    h, w = m.shape
    big = np.zeros((h + 2 * pad, w + 2 * pad), np.uint8)
    big[pad:pad + h, pad:pad + w] = m
    o = dilate(big, ow) if outline else None
    can = np.zeros(big.shape + (4,), np.float32)
    layers = []
    if shadow is not None:
        layers.append((o if o is not None else big, shadow, sd[0], sd[1]))
    if o is not None:
        layers.append((o, outline, 0, 0))
    layers.append((big, fill, 0, 0))
    compose(can, layers, 0, 0)
    return can


def paste(dst, src, x, y):
    """alpha-over float RGBA src onto uint8 RGBA dst at x,y"""
    H, W = dst.shape[:2]
    h, w = src.shape[:2]
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0:
        return dst
    s = src[y0 - y:y1 - y, x0 - x:x1 - x]
    d = dst[y0:y1, x0:x1].astype(np.float32) / 255
    a = s[..., 3:4]
    na = a + d[..., 3:4] * (1 - a)
    rgb = (s[..., :3] * a + d[..., :3] * d[..., 3:4] * (1 - a)) / np.maximum(na, 1e-6)
    dst[y0:y1, x0:x1, :3] = np.clip(rgb * 255, 0, 255).astype(np.uint8)
    dst[y0:y1, x0:x1, 3:4] = np.clip(na * 255, 0, 255).astype(np.uint8)
    return dst
