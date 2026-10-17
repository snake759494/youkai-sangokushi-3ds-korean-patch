import sys,os,time,ctypes,ctypes.wintypes as W
sys.path.insert(0,os.path.dirname(__file__))
from emu import *
k=ctypes.windll.kernel32
def ctrl_key(h,vk):
    tid=u.GetWindowThreadProcessId(h,None);me=k.GetCurrentThreadId()
    u.AttachThreadInput(me,tid,True)
    st=(ctypes.c_ubyte*256)();u.GetKeyboardState(st);old=bytes(st)
    st[0x11]=0x80;st[0xA2]=0x80;u.SetKeyboardState(st)
    u.PostMessageW(h,0x100,0x11,1|(u.MapVirtualKeyW(0x11,0)<<16))
    u.PostMessageW(h,0x100,vk,1|(u.MapVirtualKeyW(vk,0)<<16))
    time.sleep(0.3)
    u.PostMessageW(h,0x101,vk,1|(u.MapVirtualKeyW(vk,0)<<16)|(0xC0<<24))
    u.PostMessageW(h,0x101,0x11,1|(u.MapVirtualKeyW(0x11,0)<<16)|(0xC0<<24))
    time.sleep(0.3)
    st2=(ctypes.c_ubyte*256).from_buffer_copy(old);u.SetKeyboardState(st2)
    u.AttachThreadInput(me,tid,False)
if __name__=='__main__':
    ctrl_key(int(sys.argv[1],16),ord(sys.argv[2]))
