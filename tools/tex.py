# 3DS tiled texture helpers (8x8 tiles, morton within)
import numpy as np
def morton_table():
    t=[]
    for i in range(64):
        x=y=0
        for b in range(3):
            x|=((i>>(2*b))&1)<<b; y|=((i>>(2*b+1))&1)<<b
        t.append((x,y))
    return t
MT=morton_table()
def untile(data,w,h,bpp):
    out=np.zeros((h,w,bpp),np.uint8);a=np.frombuffer(data,np.uint8);i=0
    for ty in range(0,h,8):
        for tx in range(0,w,8):
            for x,y in MT:
                out[ty+y,tx+x]=a[i:i+bpp];i+=bpp
    return out
def tile(img):
    h,w,bpp=img.shape;out=bytearray()
    for ty in range(0,h,8):
        for tx in range(0,w,8):
            for x,y in MT: out+=img[ty+y,tx+x].tobytes()
    return bytes(out)
def untile4(data,w,h):
    a=np.frombuffer(data,np.uint8);px=np.empty(len(a)*2,np.uint8);px[0::2]=a&15;px[1::2]=a>>4
    out=np.zeros((h,w),np.uint8);i=0
    for ty in range(0,h,8):
        for tx in range(0,w,8):
            for x,y in MT: out[ty+y,tx+x]=px[i]*17;i+=1
    return out
def tile4(img):
    h,w=img.shape;px=[]
    for ty in range(0,h,8):
        for tx in range(0,w,8):
            for x,y in MT: px.append(int(img[ty+y,tx+x])//17 if img[ty+y,tx+x]<255 else 15)
    px=np.array(px,np.uint8);return bytes((px[0::2]|(px[1::2]<<4)).astype(np.uint8))
