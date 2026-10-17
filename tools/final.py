# Full build: translations -> LINKDATA + code.bin + font -> Korean .3ds
import os, sys, json, glob, re, struct, collections
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(__file__))
from tree import walk, table, JP
from extract import plain
from link import repack
from ykfont import build as fbuild
from build import build as rbuild
import subs62

B = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
GAME = os.environ.get('YK_GAME', os.path.join(B, '..')) + '/'
ROM = GAME + 'Youkai Sangokushi (Japan) Decrypted.3ds'
OUT = sys.argv[1] if len(sys.argv) > 1 else GAME + 'Youkai Sangokushi (Korean).3ds'
TTF = GAME + 'NanumSquareNeo-cBd.ttf'
DEC = os.path.join(B, 'dec')
T = os.path.join(B, 'tr')

items = json.load(open(os.path.join(T, 'items.json'), encoding='utf-8'))
ko = {}
for f in sorted(glob.glob(os.path.join(T, 'out', '*.json')), key=lambda x: (os.path.basename(x).startswith('F'), x)):
    nm = os.path.basename(f)[:-5]
    if '_' in nm:
        continue
    for k, v in json.load(open(f, encoding='utf-8')).items():
        ko[k] = v
FIX = {'노루카': '노르카', '소루카': '소르카'}
for k in list(ko):
    for a, b in FIX.items():
        ko[k] = ko[k].replace(a, b)
for k in list(ko):
    if k.startswith('s16131_'):
        ko[k] = ''  # song lyrics: subtitles left blank
bysrc = {}
for it in items:
    if it['g'].startswith('00055/'):
        continue  # password phrases: keep original kana
    if str(it['id']) in ko:
        bysrc[it['src']] = ko[str(it['id'])]
print('translated unique', len(bysrc), '/', len(items))

# keyboard/menu labels inside code.bin (in-place, byte budget)
CODE_LABELS = {
    'けってい': '결정', 'カナ': '받침', 'わすれる': '지우기', '１つもどる': '한칸뒤로',
    'はんだくてん': '바꾸기2', 'だくてん': '바꾸기', 'かな': '기본', 'キャンセル': '취소', 'スペース': '띄우기',
}

used = collections.Counter()
missing = collections.Counter()
repl_entries = {}
READMAP = {(1,): (0,), (26,): (25,)}

for n in sorted(os.listdir(DEC)):
    p = os.path.join(DEC, n)
    d = open(p, 'rb').read()
    if d[:4] == b'b)\0\0':
        ents = subs62.parse(d)
        r = {}
        for i, (tm, s) in enumerate(ents):
            k = 's%s_%d' % (n, i)
            if k in ko:
                r[i] = ko[k]
                used.update(ko[k])
            elif JP.search(s):
                missing['sub'] += 1
        if r:
            repl_entries[int(n)] = subs62.build(d, r)
        continue
    if table(d) is None:
        continue
    rows = {pp: v for pp, kk, v in walk(d) if kk == 's'}
    if not any(JP.search(v) for v in rows.values()):
        continue
    repl = {}
    for pp, v in rows.items():
        if not JP.search(v):
            continue
        t = None
        if n == '00057' and pp[:-1] in READMAP:
            src = rows.get(READMAP[pp[:-1]] + pp[-1:])
            if src is not None:
                t = bysrc.get(src)
        if t is None:
            t = bysrc.get(v)
        if t is None:
            missing[n] += 1
            continue
        repl[pp] = t
        used.update(t)
    if repl:
        from tree import rebuild
        nd = rebuild(d, repl)
        if nd != d:
            repl_entries[int(n)] = nd
print('missing', sum(missing.values()), dict(missing.most_common(10)))

hang = [c for c, _ in used.most_common() if 0xac00 <= ord(c) <= 0xd7a3]
print('hangul used', len(hang))
g = open(os.path.join(DEC, '00000'), 'rb').read()
code = open(os.path.join(B, 'ext', 'code.bin'), 'rb').read()
font, code, chars = fbuild(g, code, TTF, hang)
cs = set(chars)
lack = sorted(c for c in set(used) if c not in cs and ord(c) > 0x7d and c != '\n' and not (0xe000 <= ord(c) <= 0xf8ff))
if lack:
    print('glyphs missing from font:', ' '.join('%s(U+%04X)'%(c,ord(c)) for c in lack[:60]))
repl_entries[0] = font
code = bytearray(code)
for jp, k in CODE_LABELS.items():
    a = jp.encode() + b'\0'
    i = code.find(b'\0' + a, 0x50c000) + 1
    if i <= 0:
        print('label not found', jp)
        continue
    b = k.encode() + b'\0'
    assert len(b) <= len(a), (jp, k)
    code[i:i + len(a)] = b + b'\0' * (len(a) - len(b))
# SPACEFIX: measure ASCII space as full cell like the renderer does
import struct as _st
assert _st.unpack_from('<I',code,0x52d20c-0x100000)[0]==0x0a000007
_st.pack_into('<I',code,0x52d20c-0x100000,0xe320f000)
# texture replacements
from texpatch import apply as tapply
import numpy as _np
from PIL import Image as _Im
_rep = {}
for _f in sorted(glob.glob(os.path.join(T, 'img', '*.png'))):
    _b = os.path.basename(_f)[:-4]
    _rep[_b[:5] + '/' + _b[6:]] = _np.array(_Im.open(_f).convert('RGBA'))
from texindex import build as _tib, propagate as _tpr
_rep = _tpr(_rep, _tib(DEC))
repl_entries = tapply(DEC, _rep, repl_entries)
print('textures replaced', len(_rep))
print('entries replaced', len(repl_entries))
lk = OUT + '.linkdata'
repack(os.path.join(B, 'ext', 'romfs', 'Data', 'LINKDATA_A.BIN'), lk, repl_entries)
rbuild(ROM, OUT, {'Data/LINKDATA_A.BIN': open(lk, 'rb').read()}, newcode=bytes(code))
os.remove(lk)
print('built', OUT, os.path.getsize(OUT))
