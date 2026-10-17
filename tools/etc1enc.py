# Simple vectorized ETC1 / ETC1A4 encoder (3DS layout). Re-encodes only changed blocks when original given.
import numpy as np
from texdec import ETC_MOD, etc1_blocks


def _block_coords(w, h):
    nb = (w // 4) * (h // 4)
    b = np.arange(nb)
    t = b // 4
    s = b % 4
    tiles_x = w // 8
    by = (t // tiles_x) * 8 + (s // 2) * 4
    bx = (t % tiles_x) * 8 + (s % 2) * 4
    return by, bx


def _gather(img_bu, by, bx):
    # img_bu: bottom-up (h,w,C) ; returns (N,4,4,C) with [n,y,x]
    N = len(by)
    out = np.zeros((N, 4, 4, img_bu.shape[2]), img_bu.dtype)
    for yy in range(4):
        for xx in range(4):
            out[:, yy, xx] = img_bu[by + yy, bx + xx]
    return out


def encode_blocks(rgb):
    """rgb (N,4,4,3) uint8 -> (N,) uint64 ETC1 values (individual mode, best flip/table)"""
    N = len(rgb)
    px = rgb.astype(np.int32)
    best_err = np.full(N, 1 << 60, np.int64)
    best_val = np.zeros(N, np.uint64)
    for flip in (0, 1):
        # subblock masks over (y,x)
        if flip:
            m1 = np.zeros((4, 4), bool); m1[:2, :] = True
        else:
            m1 = np.zeros((4, 4), bool); m1[:, :2] = True
        subs = []
        for m in (m1, ~m1):
            p = px[:, m]  # (N,8,3)
            avg = p.mean(1)
            c4 = np.clip(np.round(avg / 17), 0, 15).astype(np.int64)
            base = c4 * 17
            # choose table per subblock
            berr = np.full(N, 1 << 60, np.int64)
            btab = np.zeros(N, np.int64)
            bidx = np.zeros((N, 8), np.int64)
            for t in range(8):
                cand = base[:, None, None, :] + ETC_MOD[t][None, None, :, None]  # (N,1,4,3)
                cand = np.clip(cand, 0, 255)
                err = ((p[:, :, None, :] - cand) ** 2).sum(-1)  # (N,8,4)
                idx = err.argmin(-1)
                e = np.take_along_axis(err, idx[..., None], -1)[..., 0].sum(1)
                better = e < berr
                berr = np.where(better, e, berr)
                btab = np.where(better, t, btab)
                bidx = np.where(better[:, None], idx, bidx)
            subs.append((c4, btab, bidx, berr, m))
        err = subs[0][3] + subs[1][3]
        (c1, t1, i1, _, mA), (c2, t2, i2, _, mB) = subs
        hi = (c1[:, 0] << 28) | (c2[:, 0] << 24) | (c1[:, 1] << 20) | (c2[:, 1] << 16) | (c1[:, 2] << 12) | (c2[:, 2] << 8) | (t1 << 5) | (t2 << 2) | flip
        lo = np.zeros(N, np.int64)
        posA = np.argwhere(mA)
        posB = np.argwhere(mB)
        for (pos, idxs) in ((posA, i1), (posB, i2)):
            for j, (y, x) in enumerate(pos):
                k = x * 4 + y
                v = idxs[:, j]
                msb = (v >> 1) & 1
                lsb = v & 1
                lo |= (msb << (k + 16)) | (lsb << k)
        val = (hi.astype(np.uint64) << np.uint64(32)) | lo.astype(np.uint64)
        better = err < best_err
        best_err = np.where(better, err, best_err)
        best_val = np.where(better, val, best_val)
    return best_val


def encode_etc(img, alpha, orig=None):
    """img top-down (h,w,4). orig: original texture bytes -> keep unchanged blocks"""
    h, w = img.shape[:2]
    bu = img[::-1]
    by, bx = _block_coords(w, h)
    blocks = _gather(bu, by, bx)  # (N,4,4,4)
    N = len(by)
    bs = 16 if alpha else 8
    if orig is not None:
        out = np.frombuffer(orig, np.uint8).reshape(N, bs).copy()
        from texdec import decode_etc
        od = decode_etc(orig, w, h, alpha)[::-1]  # top-down
        ob = _gather(od[::-1], by, bx)
        changed = np.any(np.abs(ob.astype(np.int32) - blocks.astype(np.int32)) > (0 if alpha else 3), axis=(1, 2, 3))
    else:
        out = np.zeros((N, bs), np.uint8)
        changed = np.ones(N, bool)
    idx = np.flatnonzero(changed)
    if len(idx):
        vals = encode_blocks(blocks[idx, :, :, :3])
        col = vals.astype('<u8').view(np.uint8).reshape(-1, 8)
        if alpha:
            a = (blocks[idx, :, :, 3].astype(np.int32) * 15 + 127) // 255
            av = np.zeros(len(idx), np.uint64)
            for x in range(4):
                for y in range(4):
                    av |= a[:, y, x].astype(np.uint64) << np.uint64((x * 4 + y) * 4)
            out[idx, :8] = av.astype('<u8').view(np.uint8).reshape(-1, 8)
            out[idx, 8:] = col
        else:
            out[idx] = col
    return out.tobytes()
