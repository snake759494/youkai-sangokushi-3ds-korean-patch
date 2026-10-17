import capstone,struct,sys
C=open(__import__('os').path.join(__import__('os').path.dirname(__file__),'..','ext','code.bin'),'rb').read()
B=0x100000
md=capstone.Cs(capstone.CS_ARCH_ARM,capstone.CS_MODE_ARM);md.detail=False
def u32(va): return struct.unpack_from('<I',C,va-B)[0]
def dis(va,n=40):
    out=[]
    for i in md.disasm(C[va-B:va-B+n*4],va):
        s='%08x: %-8s %s'%(i.address,i.mnemonic,i.op_str)
        if i.mnemonic.startswith('ldr') and '[pc, #' in i.op_str:
            try:
                o=int(i.op_str.split('#')[1].rstrip(']'),0);s+='   ; =%08x'%u32(i.address+8+o)
            except: pass
        out.append(s)
    return '\n'.join(out)
def find_word(w):
    p=struct.pack('<I',w);r=[];i=-1
    while True:
        i=C.find(p,i+1)
        if i<0:break
        r.append(B+i)
    return r
def callers(target):
    r=[]
    for off in range(0,0x50be14,4):
        x=struct.unpack_from('<I',C,off)[0]
        if (x>>24)&0xf in (0xb,0xa) and (x>>28)!=0xf:
            imm=x&0xffffff
            if imm&0x800000: imm-=0x1000000
            if B+off+8+imm*4==target: r.append(B+off)
    return r
if __name__=='__main__':
    print(dis(int(sys.argv[1],16),int(sys.argv[2]) if len(sys.argv)>2 else 40))
