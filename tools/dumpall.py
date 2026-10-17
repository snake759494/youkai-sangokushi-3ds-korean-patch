import os,sys,hashlib,json,traceback
sys.path.insert(0,os.path.dirname(__file__))
import numpy as np
import texdec as T
from sarc import parse as sarc
from PIL import Image
out='view/all';idx={};seen={}
def save(key,fmt,w,h,data):
    hsh=hashlib.md5(data).hexdigest()
    if hsh in seen: idx[key]=seen[hsh];return
    im=T.decode(fmt,data,w,h)[::-1]
    a=im[:,:,3].astype(np.float32)/255
    rgb=im[:,:,:3].astype(np.float32)
    bg=np.array([100,100,100],np.float32)
    comp=(rgb*a[...,None]+bg*(1-a[...,None])).astype(np.uint8)
    fn=key.replace('/','_')+'.png'
    Image.fromarray(comp).save(os.path.join(out,fn));seen[hsh]=fn;idx[key]=fn
for n in sorted(os.listdir('dec')):
    p='dec/'+n
    with open(p,'rb') as f: h4=f.read(4)
    try:
        if h4==b'GT1G':
            d=open(p,'rb').read()
            for i,fmt,w,h,o,ln in T.gt1g(d):
                if w*h<64*32: continue
                save('%s/%d'%(n,i),fmt,w,h,d[o:o+ln])
        elif h4==b'SARC':
            d=open(p,'rb').read()
            for nm,s,e in sarc(d):
                if not nm.endswith('.bflim'): continue
                b=d[s:e];fmt,w,h,sz=T.bflim(b)
                if w*h<64*32: continue
                # bflim dims may be non-pow2 in header; stored size is pow2-padded
                W=1;H=1
                while W<w: W*=2
                while H<h: H*=2
                if sz < W*H*T.BPP[fmt]//8: W,H=w,h
                save('%s/%s'%(n,nm.split('/')[-1]),fmt,W,H,b[:sz])
    except Exception as ex:
        print('ERR',n,ex)
json.dump(idx,open('view/all_index.json','w'))
print(len(idx),len(seen))
