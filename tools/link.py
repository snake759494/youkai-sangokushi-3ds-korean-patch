import struct,zlib,sys,os,collections
def entries(b):
    n=struct.unpack_from('<I',b,4)[0]
    return [struct.unpack_from('<IIII',b,0x10+i*16) for i in range(n)]
def unpack(b,e):
    off,_,cs,ds=e;p=off*0x20
    raw=b[p:p+cs]
    if ds==0: return raw,False
    tot=struct.unpack_from('<I',raw,0)[0];q=4;out=bytearray()
    while len(out)<tot:
        n=struct.unpack_from('<I',raw,q)[0];q+=4
        out+=zlib.decompress(raw[q:q+n]);q+=n
        q=(q+0x7f)&~0x7f if False else q
    return bytes(out),True
if __name__=='__main__':
    b=open(sys.argv[1],'rb').read();out=sys.argv[2];os.makedirs(out,exist_ok=True)
    c=collections.Counter()
    for i,e in enumerate(entries(b)):
        try: d,z=unpack(b,e)
        except Exception as ex: print('ERR',i,e,ex);continue
        open(f'{out}/{i:05d}','wb').write(d);c[d[:4]]+=1
    print(c.most_common(40))
def compress(data):
    out=bytearray(struct.pack('<I',len(data)))
    for i in range(0,len(data),0x8000):
        c=zlib.compress(data[i:i+0x8000],9);out+=struct.pack('<I',len(c))+c
    out+=bytes(4)
    return bytes(out)
def repack(src,dst,repl):
    """repl: {index: decompressed bytes}"""
    f=open(src,'rb');hdr=f.read(0x10);n=struct.unpack_from('<I',hdr,4)[0]
    E=[struct.unpack('<IIII',f.read(16)) for i in range(n)]
    o=open(dst,'wb');o.write(b'\0'*(0x10+n*16));cur=0x10+n*16
    newE=[]
    for i,(off,z,cs,ds) in enumerate(E):
        if i in repl:
            d=repl[i]
            if ds==0: raw=d;nds=0
            else: raw=compress(d);nds=len(d)
        else:
            f.seek(off*0x20);raw=f.read(cs);nds=ds
        assert cur%0x20==0
        newE.append((cur//0x20,z,len(raw),nds));o.write(raw);cur+=len(raw)
        pad=(-cur)%0x20;o.write(b'\0'*pad);cur+=pad
    o.seek(0);o.write(hdr)
    for e in newE: o.write(struct.pack('<IIII',*e))
    o.close()
