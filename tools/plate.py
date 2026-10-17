import numpy as np,sys,os
sys.path.insert(0,os.path.dirname(__file__))
from koimg import text_mask,fit,dilate
from PIL import Image,ImageDraw
def plate(text,W,H=32,y0=6,y1=19,size=13):
    m=text_mask(text,size,'xbold')
    th=y1-y0-1
    m=fit(m,W-10,th)
    h,w=m.shape
    pw=min(W,w+12)
    img=np.zeros((H,W,4),np.uint8)
    pl=Image.new('L',(W,H),0);ImageDraw.Draw(pl).rounded_rectangle((0,y0,pw-1,y1),radius=(y1-y0)//2,fill=204)
    pa=np.array(pl)
    img[...,:3]=16;img[...,3]=pa
    x=6;y=y0+(y1-y0+1-h)//2
    a=m.astype(np.float32)/255
    reg=img[y:y+h,x:x+w].astype(np.float32)
    reg[...,:3]=reg[...,:3]*(1-a[...,None])+240*a[...,None]
    reg[...,3]=np.maximum(reg[...,3],a*255)
    img[y:y+h,x:x+w]=reg.astype(np.uint8)
    return img
