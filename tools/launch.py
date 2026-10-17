import subprocess,sys,time,os,ctypes
sys.path.insert(0,os.path.dirname(__file__))
from emu import *
rom=os.path.abspath(sys.argv[1])
si=subprocess.STARTUPINFO();si.dwFlags=1;si.wShowWindow=4  # SW_SHOWNOACTIVATE
fg=u.GetForegroundWindow()
p=subprocess.Popen([os.path.abspath(EXE),rom],startupinfo=si,creationflags=0x00000008|0x00000200)
open(os.path.join(os.path.dirname(__file__),'..','emu.pid'),'w').write(str(p.pid))
for i in range(60):
    time.sleep(0.5);ws=wins(p.pid)
    if ws: break
time.sleep(1)
for h in wins(p.pid):
    u.SetWindowPos(h,1,0,0,0,0,0x0001|0x0002|0x0010)  # HWND_BOTTOM, NOSIZE|NOMOVE|NOACTIVATE
if fg: u.SetForegroundWindow(fg)
print(p.pid,[(hex(h),title(h),cls(h)) for h in wins(p.pid)])
