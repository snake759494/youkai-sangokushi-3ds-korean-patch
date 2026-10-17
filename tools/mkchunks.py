import json, os, sys, collections
B = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
it = json.load(open(os.path.join(B, 'tr', 'items.json'), encoding='utf-8'))
a1 = {x['id'] for x in json.load(open(os.path.join(B, 'tr', 'chunks', 'A1.json'), encoding='utf-8'))}
READ = {'00057/1', '00057/26'}
SKILLS = ['00057/%d' % i for i in (2, 3, 4, 6, 8, 9, 30)]
MISC = ['00057/%d' % i for i in (14, 16, 17, 18, 19, 20, 21, 23, 24, 25, 32, 33, 35, 37, 42, 43, 44, 46, 50, 54, 56, 57, 58, 59, 65, 67, 74, 75)] + ['00056/1', '00056/2', '00056/7', '00055/0', '00058/0']


def rec(i):
    return dict(id=i['id'], jp=i['jp'], w=i['gw'], l=i['gl'], g=i['g'])


def dump(name, lst):
    json.dump(lst, open(os.path.join(B, 'tr', 'chunks', name + '.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print(name, len(lst), sum(len(x['jp']) for x in lst))


used = set(a1)
for nm, gs in (('A2', SKILLS), ('A3', MISC)):
    sel = [rec(i) for i in it if i['g'] in gs and i['id'] not in used]
    used |= {x['id'] for x in sel}
    dump(nm, sel)
rest = [i for i in it if i['id'] not in used and i['g'] not in READ]
# chunk by size, try to break at group boundary
LIM = int(sys.argv[1]) if len(sys.argv) > 1 else 7000
chunks = []
cur = []
cs = 0
for i in rest:
    if cur and cs + len(i['jp']) > LIM and (i['g'] != cur[-1]['g'] or cs > LIM * 1.3):
        chunks.append(cur)
        cur = []
        cs = 0
    cur.append(rec(i))
    cs += len(i['jp'])
if cur:
    chunks.append(cur)
for k, c in enumerate(chunks):
    dump('B%02d' % (k + 1), c)
