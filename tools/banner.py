import numpy as np,sys,os
sys.path.insert(0,os.path.dirname(__file__))
from koimg import styled,paste
def banner(text,W=256,H=64):
    img=np.zeros((H,W,4),np.uint8)
    s=styled(text,30,'heavy',(255,255,255),(17,17,17),3,(170,85,170),(3,3),skew=-0.18,maxw=W-16,maxh=44)
    h,w=s.shape[:2]
    paste(img,s,(W-w)//2,(H-h)//2+2)
    return img
