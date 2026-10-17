# Apply texture replacements: key "NNNNN/idx" (GT1G) or "NNNNN/name.bflim" (SARC) -> RGBA top-down image
import os, sys, struct
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
import texdec as T
from imgenc import encode
from sarc import parse as sarc


def load_tex(dec_dir, key):
    n, sub = key.split('/', 1)
    d = open(os.path.join(dec_dir, n), 'rb').read()
    if d[:4] == b'GT1G':
        for i, fmt, w, h, o, ln in T.gt1g(d):
            if str(i) == sub:
                return T.decode(fmt, d[o:o + ln], w, h)[::-1].copy(), fmt
    else:
        for nm, s, e in sarc(d):
            if nm.split('/')[-1] == sub:
                b = d[s:e]
                return flim_decode(b)
    raise KeyError(key)


def _sw(b):
    return struct.unpack_from('<B', b, len(b) - 0x14 + 8 + 7)[0]


def flim_decode(b):
    fmt, w, h, sz = T.bflim(b)
    if _sw(b) == 4:
        W, H = _pow2(h, w, sz, fmt)
        st = T.decode(fmt, b[:sz], W, H)
        return np.ascontiguousarray(np.rot90(st, 1)), fmt
    W, H = _pow2(w, h, sz, fmt)
    return T.decode(fmt, b[:sz], W, H)[::-1].copy(), fmt


def flim_encode(b, img):
    fmt, w, h, sz = T.bflim(b)
    if _sw(b) == 4:
        st = np.rot90(img, -1)
        return encode(fmt, np.ascontiguousarray(st[::-1]), b[:sz])
    return encode(fmt, img, b[:sz])


def _pow2(w, h, sz, fmt):
    W = 1
    H = 1
    while W < w:
        W *= 2
    while H < h:
        H *= 2
    if sz < W * H * T.BPP[fmt] // 8:
        return w, h
    return W, H


def apply(dec_dir, repl, base=None):
    """repl: {key: img}. base: {entry_index: bytes} already modified. returns {entry_index: bytes}"""
    out = dict(base or {})
    byfile = {}
    for k, img in repl.items():
        byfile.setdefault(k.split('/', 1)[0], []).append((k.split('/', 1)[1], img))
    for n, lst in byfile.items():
        e = int(n)
        d = bytearray(out[e] if e in out else open(os.path.join(dec_dir, n), 'rb').read())
        subs = dict(lst)
        if d[:4] == b'GT1G':
            for i, fmt, w, h, o, ln in T.gt1g(bytes(d)):
                if str(i) in subs:
                    img = subs[str(i)]
                    assert img.shape[:2] == (h, w), (n, i, img.shape, w, h)
                    d[o:o + ln] = encode(fmt, img, bytes(d[o:o + ln]))
        else:
            for nm, s, en in sarc(bytes(d)):
                sub = nm.split('/')[-1]
                if sub in subs:
                    b = bytes(d[s:en])
                    fmt, w, h, sz = T.bflim(b)
                    img = subs[sub]
                    ref, _ = flim_decode(b)
                    assert img.shape == ref.shape, (n, sub, img.shape, ref.shape)
                    enc = flim_encode(b, img)
                    assert len(enc) == sz
                    d[s:s + sz] = enc
        out[e] = bytes(d)
    return out
