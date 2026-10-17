# 3DS texture decode/encode (PICA tiled), GT1G and BFLIM containers
import struct
import numpy as np

# morton index -> (x,y) inside 8x8 tile
_MX = np.zeros(64, np.int32)
_MY = np.zeros(64, np.int32)
for i in range(64):
    x = y = 0
    for b in range(3):
        x |= ((i >> (2 * b)) & 1) << b
        y |= ((i >> (2 * b + 1)) & 1) << b
    _MX[i] = x
    _MY[i] = y


def _pix_index(w, h):
    """for linear pixel stream order -> (y,x) arrays"""
    tiles_x = w // 8
    n = w * h
    i = np.arange(n)
    t = i // 64
    m = i % 64
    ty = t // tiles_x
    tx = t % tiles_x
    return ty * 8 + _MY[m], tx * 8 + _MX[m]


def untile(px, w, h):
    """px: (w*h, C) in stream order -> (h,w,C)"""
    ys, xs = _pix_index(w, h)
    out = np.zeros((h, w) + px.shape[1:], px.dtype)
    out[ys, xs] = px
    return out


def tile(img):
    h, w = img.shape[:2]
    ys, xs = _pix_index(w, h)
    return img[ys, xs]


def _x4(v):
    return (v * 17).astype(np.uint8)


def _x5(v):
    return ((v << 3) | (v >> 2)).astype(np.uint8)


def _x6(v):
    return ((v << 2) | (v >> 4)).astype(np.uint8)


ETC_MOD = np.array([[2, 8, -2, -8], [5, 17, -5, -17], [9, 29, -9, -29], [13, 42, -13, -42],
                    [18, 60, -18, -60], [24, 80, -24, -80], [33, 106, -33, -106], [47, 183, -47, -183]], np.int32)


def etc1_blocks(blk):
    """blk: (N,) uint64 (little-endian as stored on 3DS) -> (N,4,4,3)"""
    N = len(blk)
    v = blk.astype(np.uint64)
    hi = (v >> np.uint64(32)).astype(np.int64)
    lo = (v & np.uint64(0xffffffff)).astype(np.int64)
    diff = (hi >> 1) & 1
    flip = hi & 1
    t1 = (hi >> 5) & 7
    t2 = (hi >> 2) & 7
    # individual
    r1i = ((hi >> 28) & 15) * 17
    g1i = ((hi >> 20) & 15) * 17
    b1i = ((hi >> 12) & 15) * 17
    r2i = ((hi >> 24) & 15) * 17
    g2i = ((hi >> 16) & 15) * 17
    b2i = ((hi >> 8) & 15) * 17
    # differential
    def sx3(x):
        return np.where(x >= 4, x - 8, x)
    R = (hi >> 27) & 31
    G = (hi >> 19) & 31
    Bc = (hi >> 11) & 31
    dR = sx3((hi >> 24) & 7)
    dG = sx3((hi >> 16) & 7)
    dB = sx3((hi >> 8) & 7)
    e5 = lambda x: (x << 3) | (x >> 2)
    R2 = (R + dR) & 31
    G2 = (G + dG) & 31
    B2 = (Bc + dB) & 31
    r1 = np.where(diff == 1, e5(R), r1i)
    g1 = np.where(diff == 1, e5(G), g1i)
    b1 = np.where(diff == 1, e5(Bc), b1i)
    r2 = np.where(diff == 1, e5(R2), r2i)
    g2 = np.where(diff == 1, e5(G2), g2i)
    b2 = np.where(diff == 1, e5(B2), b2i)
    out = np.zeros((N, 4, 4, 3), np.uint8)
    for x in range(4):
        for y in range(4):
            k = x * 4 + y
            msb = (lo >> (k + 16)) & 1
            lsb = (lo >> k) & 1
            idx = (msb << 1) | lsb
            sub2 = np.where(flip == 1, y >= 2, x >= 2)
            tb = np.where(sub2, t2, t1)
            m = ETC_MOD[tb, idx]
            rr = np.where(sub2, r2, r1) + m
            gg = np.where(sub2, g2, g1) + m
            bb = np.where(sub2, b2, b1) + m
            out[:, y, x, 0] = np.clip(rr, 0, 255)
            out[:, y, x, 1] = np.clip(gg, 0, 255)
            out[:, y, x, 2] = np.clip(bb, 0, 255)
    return out


def decode_etc(data, w, h, alpha):
    bs = 16 if alpha else 8
    nb = (w // 4) * (h // 4)
    raw = np.frombuffer(data[:nb * bs], np.uint8).reshape(nb, bs)
    if alpha:
        a = raw[:, :8]
        col = raw[:, 8:]
    else:
        col = raw
    blk = col.copy().view('<u8').reshape(nb)
    rgb = etc1_blocks(blk)
    if alpha:
        av = np.zeros((nb, 4, 4), np.uint8)
        a64 = a.copy().view('<u8').reshape(nb)
        for x in range(4):
            for y in range(4):
                k = x * 4 + y
                av[:, y, x] = ((a64 >> np.uint64(k * 4)) & np.uint64(15)).astype(np.uint8) * 17
    else:
        av = np.full((nb, 4, 4), 255, np.uint8)
    rgba = np.concatenate([rgb, av[..., None]], 3)  # (nb,4,4,4)
    # block order: 8x8 tiles, each 2x2 blocks in Z order
    img = np.zeros((h, w, 4), np.uint8)
    tiles_x = w // 8
    b = np.arange(nb)
    t = b // 4
    s = b % 4
    ty = t // tiles_x
    tx = t % tiles_x
    by = ty * 8 + (s // 2) * 4
    bx = tx * 8 + (s % 2) * 4
    for yy in range(4):
        for xx in range(4):
            img[by + yy, bx + xx] = rgba[:, yy, xx]
    return img


# format name -> (bits per pixel)
BPP = {'rgba8': 32, 'rgb8': 24, 'rgba5551': 16, 'rgb565': 16, 'rgba4': 16, 'la8': 16, 'hilo8': 16,
       'l8': 8, 'a8': 8, 'la4': 8, 'l4': 4, 'a4': 4, 'etc1': 4, 'etc1a4': 8}


def decode(fmt, data, w, h):
    if fmt in ('etc1', 'etc1a4'):
        return decode_etc(data, w, h, fmt == 'etc1a4')
    n = w * h
    a = np.frombuffer(data, np.uint8)
    if fmt == 'rgba8':
        p = a[:n * 4].reshape(n, 4)[:, ::-1]
    elif fmt == 'rgb8':
        p = a[:n * 3].reshape(n, 3)[:, ::-1]
        p = np.concatenate([p, np.full((n, 1), 255, np.uint8)], 1)
    elif fmt in ('rgba5551', 'rgb565', 'rgba4', 'la8', 'hilo8'):
        v = a[:n * 2].copy().view('<u2').astype(np.int32)
        if fmt == 'rgba4':
            p = np.stack([_x4(v >> 12 & 15), _x4(v >> 8 & 15), _x4(v >> 4 & 15), _x4(v & 15)], 1)
        elif fmt == 'rgb565':
            p = np.stack([_x5(v >> 11 & 31), _x6(v >> 5 & 63), _x5(v & 31), np.full(n, 255, np.uint8)], 1)
        elif fmt == 'rgba5551':
            p = np.stack([_x5(v >> 11 & 31), _x5(v >> 6 & 31), _x5(v >> 1 & 31), ((v & 1) * 255).astype(np.uint8)], 1)
        else:  # la8: byte0=A byte1=L
            L = (v >> 8).astype(np.uint8)
            A = (v & 255).astype(np.uint8)
            p = np.stack([L, L, L, A], 1)
    elif fmt in ('l8', 'a8'):
        v = a[:n]
        p = np.stack([v, v, v, np.full(n, 255, np.uint8)], 1) if fmt == 'l8' else np.stack([np.full(n, 255, np.uint8)] * 3 + [v], 1)
    elif fmt == 'la4':
        v = a[:n]
        L = _x4(v >> 4)
        A = _x4(v & 15)
        p = np.stack([L, L, L, A], 1)
    elif fmt in ('l4', 'a4'):
        v = a[:n // 2]
        px = np.empty(n, np.uint8)
        px[0::2] = v & 15
        px[1::2] = v >> 4
        px = _x4(px)
        p = np.stack([px, px, px, np.full(n, 255, np.uint8)], 1) if fmt == 'l4' else np.stack([np.full(n, 255, np.uint8)] * 3 + [px], 1)
    else:
        raise ValueError(fmt)
    return untile(p, w, h)


GT1G_FMT = {0x3d: 'rgba4', 0x3b: 'rgb565', 0x09: 'rgba8', 0x44: 'a4', 0x47: 'etc1', 0x48: 'etc1a4'}
PICA = ['l8', 'a8', 'la4', 'la8', 'hilo8', 'rgb565', 'rgb8', 'rgba5551', 'rgba4', 'rgba8', 'etc1', 'etc1a4', 'l4', 'a4']


def gt1g(d):
    """yield (index, fmt, w, h, data_offset, data_len)"""
    size, toff, num = struct.unpack_from('<III', d, 8)
    offs = [toff + struct.unpack_from('<I', d, toff + 4 * i)[0] for i in range(num)] + [len(d)]
    for i in range(num):
        o = offs[i]
        fm = d[o + 1]
        w = 1 << (d[o + 2] & 15)
        h = 1 << (d[o + 2] >> 4)
        hl = 8 + (struct.unpack_from('<I', d, o + 8)[0] if d[o + 7] & 0x10 else 0)
        fmt = GT1G_FMT.get(fm)
        if fmt is None:
            continue
        ln = w * h * BPP[fmt] // 8
        # extended header if bytes between header and next texture exceed size
        if offs[i + 1] - o - 8 >= ln + 12 and d[o + 4:o + 8] != b'\0\0\0\0' and False:
            hl = 0x14
        yield i, fmt, w, h, o + hl, ln


def bflim(b):
    """returns fmt,w,h,data_len (data at 0)"""
    ih = len(b) - 0x28
    if b[ih:ih + 4] != b'FLIM':
        ih = len(b) - 0x28
    im = len(b) - 0x14
    assert b[im:im + 4] == b'imag', b[im:im + 4]
    w, h, al, fm, sw, sz = struct.unpack_from('<HHHBBI', b, im + 8)
    return PICA[fm], w, h, sz
