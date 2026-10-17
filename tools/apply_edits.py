# Apply text edit specs to textures.
# spec file tr/edits/<name>.json : {"key": "NNNNN/idx" or "NNNNN/name.bflim", "edits": [ {...}, ... ]}
# edit: box [x,y,w,h] (top-down px), bg: "clear" | "inpaint" | "#RRGGBB" | "keep",
#       text (\n allowed), fill "#RRGGBB", outline "#RRGGBB"|null, ow int, shadow "#RRGGBB"|null, sd [dx,dy],
#       font heavy|xbold|bold|reg, size (px, optional: auto-fit), align center|left|right, skew float, vcenter bool
# usage: python tools/apply_edits.py [names...]   -> writes tr/img/<file>.png and view/prev/<name>.png
import os, sys, json, glob
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
import cv2
from PIL import Image
from texpatch import load_tex
from koimg import styled, paste

B = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')


def hexc(s):
    s = s.lstrip('#')
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


def run(spec):
    img, fmt = load_tex(os.path.join(B, 'dec'), spec['key'])
    img = img.copy()
    H, W = img.shape[:2]
    # 1) backgrounds
    for e in spec['edits']:
        x, y, w, h = [int(v) for v in e['box']]
        x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
        bg = e.get('bg', 'clear')
        if bg == 'clear':
            img[y0:y1, x0:x1] = 0
        elif bg == 'inpaint':
            mask = np.zeros((H, W), np.uint8)
            mask[y0:y1, x0:x1] = 255
            rgb = cv2.inpaint(np.ascontiguousarray(img[:, :, :3]), mask, 5, cv2.INPAINT_TELEA)
            a = cv2.inpaint(np.ascontiguousarray(img[:, :, 3]), mask, 5, cv2.INPAINT_TELEA)
            img[:, :, :3] = rgb
            img[:, :, 3] = a
        elif bg.startswith('#'):
            c = hexc(bg)
            img[y0:y1, x0:x1, :3] = c
            img[y0:y1, x0:x1, 3] = 255
    # 2) text
    for e in spec['edits']:
        t = e.get('text', '')
        if not t:
            continue
        x, y, w, h = [int(v) for v in e['box']]
        size = int(e.get('size', max(8, int(h * 0.9 / max(1, t.count('\n') + 1)))))
        ow = int(e.get('ow', 0))
        sd = tuple(e.get('sd', (0, 0)))
        s = styled(t, size, e.get('font', 'heavy'), hexc(e.get('fill', '#FFFFFF')),
                   hexc(e['outline']) if e.get('outline') else None, ow,
                   hexc(e['shadow']) if e.get('shadow') else None, sd,
                   skew=float(e.get('skew', 0)), maxw=w, maxh=h)
        sh, sw = s.shape[:2]
        al = e.get('align', 'center')
        px = x + (w - sw) // 2 if al == 'center' else (x if al == 'left' else x + w - sw)
        py = y + (h - sh) // 2
        paste(img, s, px, py)
    return img


def preview(img, path, scale=3):
    H, W = img.shape[:2]
    bg = np.zeros((H, W, 4), np.uint8)
    bg[..., :3] = (90, 90, 120)
    bg[..., 3] = 255
    a = img[..., 3:4].astype(np.float32) / 255
    comp = (img[..., :3] * a + bg[..., :3] * (1 - a)).astype(np.uint8)
    im = Image.fromarray(comp)
    if max(W, H) * scale > 2048:
        scale = max(1, 2048 // max(W, H))
    im.resize((W * scale, H * scale), Image.NEAREST).save(path)


if __name__ == '__main__':
    os.makedirs(os.path.join(B, 'view', 'prev'), exist_ok=True)
    names = sys.argv[1:] or [os.path.basename(p)[:-5] for p in glob.glob(os.path.join(B, 'tr', 'edits', '*.json'))]
    for nm in names:
        spec = json.load(open(os.path.join(B, 'tr', 'edits', nm + '.json'), encoding='utf-8'))
        img = run(spec)
        fn = spec['key'].replace('/', '_') + '.png'
        Image.fromarray(img, 'RGBA').save(os.path.join(B, 'tr', 'img', fn))
        preview(img, os.path.join(B, 'view', 'prev', nm + '.png'))
        print('ok', nm)
