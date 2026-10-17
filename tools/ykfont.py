# Yo-kai Sangokushi font builder: GT1G (LINKDATA #0) A4 sheets + code table in code.bin rodata
import struct, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(__file__))
from tex import untile4, tile4

TEXT_BASE = 0x100000
DESC = 0x61bf74          # 6 descriptors x 0x18
TABLE = 0x615350         # merged code table (3 x 0x216c bytes available)
TABLE_MAX = 3 * 0x216c // 4
CAP = 2628               # 14px sheet capacity (73x36)
SIZES = [(16, 64, 1024, 1024), (14, 73, 1024, 512), (12, 85, 1024, 512)]


def u32(code, va):
    return struct.unpack_from('<I', code, va - TEXT_BASE)[0]


def packed(ch):
    return int.from_bytes(ch.encode('utf-8'), 'big')


def unpack_code(v):
    return v.to_bytes(4, 'big').lstrip(b'\0').decode('utf-8')


def orig_codes(code):
    n = u32(code, DESC + 0x14) & 0xffff
    ct = u32(code, DESC)
    return [unpack_code(u32(code, ct + i * 4)) for i in range(n)]


def ksx1001():
    s = []
    for hi in range(0xb0, 0xc9):
        for lo in range(0xa1, 0xff):
            try:
                s.append(bytes([hi, lo]).decode('euc-kr'))
            except UnicodeDecodeError:
                pass
    return s


def gt1g_sheets(b):
    size, toff, num = struct.unpack_from('<III', b, 8)
    offs = [toff + struct.unpack_from('<I', b, toff + 4 * i)[0] for i in range(num)]
    return offs


def charset(code, used_hangul=()):
    orig = orig_codes(code)
    kanji = lambda c: 0x4e00 <= ord(c) <= 0x9fff or c == '々'
    kana = lambda c: 0x3041 <= ord(c) <= 0x30ff
    keep = [c for c in orig if not kanji(c)]  # symbols + all kana (kana glyphs carry Korean for the keyboard)
    from kanamap import KANA_MAP
    need = list(dict.fromkeys(list(used_hangul) + [c for c in KANA_MAP.values()]))
    room = CAP - len(keep) - len(need)
    if room < 0:
        raise SystemExit('too many glyphs %d' % (len(keep) + len(need)))
    rest = [c for c in ksx1001() if c not in set(need)][:room]
    out = keep + need + rest
    return sorted(set(out), key=packed), orig


def render_hangul(font, ch, cell, box):
    y0, y1 = box
    im = Image.new('L', (cell * 4, cell * 4), 0)
    d = ImageDraw.Draw(im)
    d.text((cell, cell), ch, font=font, fill=255)
    a = np.array(im)
    rows = np.flatnonzero(a.max(1) > 0)
    cols = np.flatnonzero(a.max(0) > 0)
    out = np.zeros((cell, cell), np.uint8)
    if not len(rows):
        return out
    g = a[rows[0]:rows[-1] + 1, cols[0]:cols[-1] + 1]
    return g


def build(gt1g, code, ttf, used_hangul=(), sizes_px=(15, 13, 11), gain=1.35):
    chars, orig = charset(code, used_hangul)
    idx_old = {c: i for i, c in enumerate(orig)}
    b = bytearray(gt1g)
    offs = gt1g_sheets(b)
    for si, (cell, cols, w, h) in enumerate(SIZES):
        o = offs[si] + 8
        nbytes = w * h // 2
        img = untile4(bytes(b[o:o + nbytes]), w, h)[::-1]  # flip to top-down
        new = np.zeros_like(img)
        font = ImageFont.truetype(ttf, sizes_px[si])
        ref = ImageDraw.Draw(Image.new('L', (8, 8))).textbbox((0, 0), '한', font=font)
        for k, c in enumerate(chars):
            x = (k % cols) * cell
            y = (k // cols) * cell
            from kanamap import KANA_MAP
            if c in KANA_MAP:
                c_draw = KANA_MAP[c]
            else:
                c_draw = None
            if c in idx_old and c_draw is None:
                j = idx_old[c]
                ox = (j % cols) * cell
                oy = (j // cols) * cell
                new[y:y + cell, x:x + cell] = img[oy:oy + cell, ox:ox + cell]
                continue
            g = Image.new('L', (cell, cell), 0)
            d = ImageDraw.Draw(g)
            ch_ = c_draw or c
            bb = d.textbbox((0, 0), ch_, font=font)
            gw = bb[2] - bb[0]
            gh = ref[3] - ref[1]
            ox = (cell - gw) // 2 - bb[0]
            oy = (cell - gh) // 2 - ref[1]
            d.text((ox, oy), ch_, font=font, fill=255)
            a = np.array(g).astype(np.float32) * gain
            new[y:y + cell, x:x + cell] = np.clip(a, 0, 255).astype(np.uint8)
        # quantize to 4 bits (tile4 expects 0..255 values)
        q = (np.round(new / 17.0) * 17).astype(np.uint8)
        b[o:o + nbytes] = tile4(q[::-1].copy())
    # code patch
    c2 = bytearray(code)
    assert len(chars) <= TABLE_MAX
    for i, ch in enumerate(chars):
        struct.pack_into('<I', c2, TABLE - TEXT_BASE + i * 4, packed(ch))
    for i in range(len(chars), TABLE_MAX):
        struct.pack_into('<I', c2, TABLE - TEXT_BASE + i * 4, 0xffffffff)
    for di in range(3):
        a = DESC + di * 0x18 - TEXT_BASE
        struct.pack_into('<I', c2, a, TABLE)
        struct.pack_into('<H', c2, a + 0x14, len(chars))
    return bytes(b), bytes(c2), chars


def preview(gt1g, si, out, n=0, count=200):
    cell, cols, w, h = SIZES[si]
    offs = gt1g_sheets(gt1g)
    o = offs[si] + 8
    img = untile4(bytes(gt1g[o:o + w * h // 2]), w, h)[::-1]
    rows = (count + 19) // 20
    canvas = np.zeros((rows * (cell + 2), 20 * (cell + 2)), np.uint8) + 40
    for k in range(count):
        j = n + k
        x = (j % cols) * cell
        y = (j // cols) * cell
        cx = (k % 20) * (cell + 2) + 1
        cy = (k // 20) * (cell + 2) + 1
        canvas[cy:cy + cell, cx:cx + cell] = img[y:y + cell, x:x + cell]
    Image.fromarray(canvas).resize((canvas.shape[1] * 4, canvas.shape[0] * 4), Image.NEAREST).save(out)
