# Validate translations: python tools/check.py tr/chunks/XX.json tr/out/XX.json
import json, re, sys, os, collections
B = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
TAG = re.compile(r'【[^】]*】')
FMT = re.compile(r'%[-+ 0#]*\d*(?:\.\d+)?[dsxXcfu%]')
SYMS = set(json.load(open(os.path.join(B, 'tr', 'symbols.json'), encoding='utf-8')))


def ksx():
    s = set()
    for hi in range(0xb0, 0xc9):
        for lo in range(0xa1, 0xff):
            try:
                s.add(bytes([hi, lo]).decode('euc-kr'))
            except UnicodeDecodeError:
                pass
    return s


KSX = ksx()


def width(line):
    line = TAG.sub('', line)
    return len(line)


def tags(s):
    return collections.Counter(t for t in TAG.findall(s) if '：' not in t)


def check(item, ko):
    errs = []
    src = item['src'] if 'src' in item else item['jp']
    if tags(src) != tags(ko):
        errs.append('tags %s != %s' % (dict(tags(src)), dict(tags(ko))))
    if collections.Counter(FMT.findall(src)) != collections.Counter(FMT.findall(ko)):
        errs.append('format specifiers differ')
    body = TAG.sub('', ko)
    bad = []
    for c in body:
        o = ord(c)
        if c == '\n':
            continue
        if 0x20 <= o <= 0x7d:
            continue
        if c in SYMS:
            continue
        if 0xac00 <= o <= 0xd7a3:
            if c not in KSX:
                bad.append(c + '(KSX외)')
            continue
        if 0xe000 <= o <= 0xf8ff and c in src:
            continue
        bad.append(c)
    if bad:
        errs.append('chars ' + ''.join(sorted(set(bad))))
    lines = ko.split('\n')
    w = item.get('w', 99)
    over = [round(width(l), 1) for l in lines if width(l) > w]
    if over:
        errs.append('line width %s > %s' % (over, w))
    if len(lines) > src.count('\n') + 1:
        errs.append('lines %d > %d' % (len(lines), item.get('l')))
    if src.strip() and not ko.strip():
        errs.append('empty')
    return errs


if __name__ == '__main__':
    chunk = json.load(open(sys.argv[1], encoding='utf-8'))
    out = json.load(open(sys.argv[2], encoding='utf-8'))
    n = 0
    missing = [str(it['id']) for it in chunk if str(it['id']) not in out]
    for it in chunk:
        k = str(it['id'])
        if k not in out:
            continue
        e = check(it, out[k])
        if e:
            n += 1
            print(k, '|', '; '.join(e))
    print('checked %d, errors %d, missing %d' % (len(out), n, len(missing)))
    if missing:
        print('missing ids:', ' '.join(missing[:50]))
