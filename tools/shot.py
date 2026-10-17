import sys,os,time,glob,shutil
sys.path.insert(0,os.path.dirname(__file__))
from emu import *
from ctrlkey import ctrl_key
B=os.path.join(os.path.dirname(__file__),'..')
pid=int(open(os.path.join(B,'emu.pid')).read())
h=[w for w in wins(pid) if 'Azahar' in title(w)][0]
for s in sys.argv[2:]:
    if s.startswith('w'): time.sleep(float(s[1:]));continue
    k,_,n=s.partition('*')
    for i in range(int(n or 1)): key(h,k);time.sleep(0.35)
old=set(glob.glob(os.path.join(B,'shots','*.png')))
ctrl_key(h,ord('P'))
for i in range(40):
    time.sleep(0.25);new=set(glob.glob(os.path.join(B,'shots','*.png')))-old
    if new: break
f=list(new)[0];time.sleep(0.3);shutil.move(f,sys.argv[1]);print('saved',sys.argv[1])
