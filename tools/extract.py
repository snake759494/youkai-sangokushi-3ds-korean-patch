import os, sys, re, json, collections
sys.path.insert(0, os.path.dirname(__file__))
from tree import *

FUR = re.compile(r'【([^：】]*)：[^】]*】')
TAG = re.compile(r'【[^】]*】')


def plain(s):
    return FUR.sub(r'\1', s)


def width(line):
    line = TAG.sub('', line)
    return sum(0.5 if ord(ch) < 0x80 else 1 for ch in line)


def main():
    groups = collections.OrderedDict()
    for n in sorted(os.listdir('dec')):
        d = open('dec/' + n, 'rb').read()
        if table(d) is None:
            continue
        for p, k, v in walk(d):
            if k != 's' or not JP.search(v):
                continue
            g = (n,) + p[:-1]
            groups.setdefault(g, []).append((p, v))
    items = []
    sid = {}
    for g, lst in groups.items():
        gw = max(width(l) for p, v in lst for l in plain(v).split('\n'))
        gl = max(plain(v).count('\n') + 1 for p, v in lst)
        for p, v in lst:
            if v in sid:
                continue
            sid[v] = len(items)
            items.append(dict(id=len(items), g='/'.join(map(str, g)), src=v, jp=plain(v), gw=gw, gl=gl))
    json.dump(items, open('tr/items.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print(len(items), len(groups))


if __name__ == '__main__':
    main()
