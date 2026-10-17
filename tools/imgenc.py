# encode RGBA image (top-down) into 3DS tiled texture bytes
import numpy as np
from texdec import tile


def _q(v, bits):
    return (v.astype(np.int32) * ((1 << bits) - 1) + 127) // 255


def encode(fmt, img, orig=None):
    """img: (h,w,4) uint8 top-down"""
    p = tile(img[::-1].copy())  # (n,4) stream order, bottom-up rows
    if fmt == 'rgba4':
        v = (_q(p[:, 0], 4) << 12) | (_q(p[:, 1], 4) << 8) | (_q(p[:, 2], 4) << 4) | _q(p[:, 3], 4)
        return v.astype('<u2').tobytes()
    if fmt == 'rgb565':
        v = (_q(p[:, 0], 5) << 11) | (_q(p[:, 1], 6) << 5) | _q(p[:, 2], 5)
        return v.astype('<u2').tobytes()
    if fmt == 'rgba5551':
        v = (_q(p[:, 0], 5) << 11) | (_q(p[:, 1], 5) << 6) | (_q(p[:, 2], 5) << 1) | (p[:, 3] >= 128)
        return v.astype('<u2').tobytes()
    if fmt == 'rgba8':
        return p[:, ::-1].astype(np.uint8).tobytes()
    if fmt == 'rgb8':
        return p[:, 2::-1].astype(np.uint8).tobytes()
    if fmt == 'la8':
        return np.stack([p[:, 3], p[:, 0]], 1).astype(np.uint8).tobytes()
    if fmt in ('a4', 'l4'):
        v = _q(p[:, 3] if fmt == 'a4' else p[:, 0], 4).astype(np.uint8)
        return (v[0::2] | (v[1::2] << 4)).astype(np.uint8).tobytes()
    if fmt in ('a8', 'l8'):
        return (p[:, 3] if fmt == 'a8' else p[:, 0]).astype(np.uint8).tobytes()
    if fmt == 'la4':
        return ((_q(p[:, 0], 4) << 4) | _q(p[:, 3], 4)).astype(np.uint8).tobytes()
    if fmt in ('etc1', 'etc1a4'):
        from etc1enc import encode_etc
        return encode_etc(img, fmt == 'etc1a4', orig)
    raise ValueError(fmt)
