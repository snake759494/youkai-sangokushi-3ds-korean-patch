import socket,time,struct,binascii
class G:
    def __init__(s,port=24689):
        for i in range(60):
            try: s.k=socket.create_connection(('127.0.0.1',port));break
            except OSError: time.sleep(0.5)
        s.k.settimeout(120);s.buf=b''
    def _rd(s):
        while True:
            i=s.buf.find(b'$')
            if i>=0:
                j=s.buf.find(b'#',i)
                if j>=0 and len(s.buf)>=j+3:
                    p=s.buf[i+1:j];s.buf=s.buf[j+3:];s.k.sendall(b'+');return p.decode('latin1')
            d=s.k.recv(65536)
            if not d: raise EOFError
            s.buf+=d
    def cmd(s,c,wait=True):
        pk=b'$'+c.encode()+b'#%02x'%(sum(c.encode())&0xff);s.k.sendall(pk)
        return s._rd() if wait else None
    def regs(s):
        r=s.cmd('g');return [struct.unpack('<I',binascii.unhexlify(r[i*8:i*8+8]))[0] for i in range(16)]
    def mem(s,a,n):
        out=b''
        while n>0:
            k=min(n,0x400);r=s.cmd('m%x,%x'%(a,k));out+=binascii.unhexlify(r);a+=k;n-=k
        return out
    def wmem(s,a,b): return s.cmd('M%x,%x:%s'%(a,len(b),b.hex()))
    def bp(s,a): return s.cmd('Z0,%x,4'%a)
    def rbp(s,a): return s.cmd('z0,%x,4'%a)
    def cont(s): return s.cmd('c')
    def go(s,bps):
        """continue; on stop at a bp, return regs. bps: set of addrs (already inserted)"""
        r=s.regs();pc=r[15]
        if pc in bps:
            s.rbp(pc);s.cmd('s');s.bp(pc)
        s.cont();return s.regs()
