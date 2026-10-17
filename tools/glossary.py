# Build master glossary (jp -> ko) from finished term chunks and attach per-chunk subsets
import json, os, sys, re, glob
B = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
T = os.path.join(B, 'tr')


def load(p):
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else {}


def master():
    g = {}
    for nm in ('A1', 'A2', 'A3'):
        ch = os.path.join(T, 'chunks', nm + '.json')
        out = load(os.path.join(T, 'out', nm + '.json'))
        if not out:
            continue
        for it in json.load(open(ch, encoding='utf-8')):
            k = str(it['id'])
            if k in out and it['jp'].strip() and '\n' not in it['jp'] and len(it['jp']) <= 16:
                g[it['jp']] = out[k]
                # general names "金旋 元機" -> also bare name
                if it['g'] == '00057/72' and ' ' in it['jp'] and ' ' in out[k]:
                    g.setdefault(it['jp'].split(' ')[0], out[k].split(' ')[0])
    for f in ('A1_yokai.json', 'A3_terms.json'):
        for k, v in load(os.path.join(T, 'out', f)).items():
            g.setdefault(k, v)
    return g


def attach(chunk_name, g):
    ch = json.load(open(os.path.join(T, 'chunks', chunk_name + '.json'), encoding='utf-8'))
    text = '\n'.join(it['jp'] for it in ch)
    sub = {k: v for k, v in g.items() if len(k) >= 2 and k in text}
    # drop keys contained in longer matched keys only when the longer key covers all occurrences
    json.dump(sub, open(os.path.join(T, 'chunks', chunk_name + '_terms.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    return len(sub)


if __name__ == '__main__':
    g = master()
    json.dump(g, open(os.path.join(T, 'glossary.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print('master', len(g))
    for nm in sys.argv[1:]:
        print(nm, attach(nm, g))
