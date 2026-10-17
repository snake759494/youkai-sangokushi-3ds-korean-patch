import os,sys,hashlib,json
sys.path.insert(0,os.path.dirname(__file__))
import texdec as T
from sarc import parse
def build(dec):
    idx={}
    for n in sorted(os.listdir(dec)):
        p=os.path.join(dec,n)
        with open(p,'rb') as f: h=f.read(4)
        if h==b'GT1G':
            d=open(p,'rb').read()
            for i,fmt,w,hh,o,ln in T.gt1g(d): idx['%s/%d'%(n,i)]=hashlib.md5(d[o:o+ln]).hexdigest()
        elif h==b'SARC':
            d=open(p,'rb').read()
            for nm,s,e in parse(d):
                if nm.endswith('.bflim'): idx['%s/%s'%(n,nm.split('/')[-1])]=hashlib.md5(d[s:e]).hexdigest()
    return idx
def propagate(rep,idx):
    byh={}
    for k,h in idx.items(): byh.setdefault(h,[]).append(k)
    out=dict(rep)
    for k,img in rep.items():
        for k2 in byh.get(idx.get(k),[]):
            out.setdefault(k2,img)
    return out
