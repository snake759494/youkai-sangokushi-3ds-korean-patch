import ctypes,ctypes.wintypes as W,subprocess,time,os,sys
from PIL import Image
u=ctypes.windll.user32;g=ctypes.windll.gdi32
EXE=os.path.join(os.path.dirname(__file__),'..','azahar','azahar.exe')
WM_KEYDOWN,WM_KEYUP=0x100,0x101
KEYS=dict(A=65,B=83,X=90,Y=88,UP=84,DOWN=71,LEFT=70,RIGHT=72,L=81,R=87,START=77,SELECT=78)
def wins(pid):
    res=[]
    @ctypes.WINFUNCTYPE(W.BOOL,W.HWND,W.LPARAM)
    def cb(h,l):
        p=W.DWORD();u.GetWindowThreadProcessId(h,ctypes.byref(p))
        if p.value==pid and u.IsWindowVisible(h): res.append(h)
        return True
    u.EnumWindows(cb,0);return res
def children(h):
    res=[]
    @ctypes.WINFUNCTYPE(W.BOOL,W.HWND,W.LPARAM)
    def cb(c,l): res.append(c);return True
    u.EnumChildWindows(h,cb,0);return res
def title(h):
    b=ctypes.create_unicode_buffer(256);u.GetWindowTextW(h,b,256);return b.value
def cls(h):
    b=ctypes.create_unicode_buffer(256);u.GetClassNameW(h,b,256);return b.value
def capture(h,path=None):
    r=W.RECT();u.GetWindowRect(h,ctypes.byref(r));w=r.right-r.left;hh=r.bottom-r.top
    dc=u.GetWindowDC(h);mdc=g.CreateCompatibleDC(dc);bm=g.CreateCompatibleBitmap(dc,w,hh);g.SelectObject(mdc,bm)
    u.PrintWindow(h,mdc,2)
    class BIH(ctypes.Structure):_fields_=[('a',W.DWORD),('w',W.LONG),('h',W.LONG),('p',W.WORD),('b',W.WORD),('c',W.DWORD),('s',W.DWORD),('x',W.LONG),('y',W.LONG),('u',W.DWORD),('i',W.DWORD)]
    bi=BIH(40,w,-hh,1,32,0,0,0,0,0,0);buf=ctypes.create_string_buffer(w*hh*4)
    g.GetDIBits(mdc,bm,0,hh,buf,ctypes.byref(bi),0)
    im=Image.frombuffer('RGBA',(w,hh),buf,'raw','BGRA',0,1).convert('RGB')
    g.DeleteObject(bm);g.DeleteDC(mdc);u.ReleaseDC(h,dc)
    if path: im.save(path)
    return im
def key(h,k,hold=0.08):
    vk=KEYS.get(k,k) if isinstance(k,str) else k
    sc=u.MapVirtualKeyW(vk,0)
    u.PostMessageW(h,WM_KEYDOWN,vk,1|(sc<<16));time.sleep(hold)
    u.PostMessageW(h,WM_KEYUP,vk,1|(sc<<16)|(0xC0<<24))
