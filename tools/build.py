# Rebuild NCSD with replaced RomFS files (hash-named, flat+subdirs) and optional new code.bin
import struct,hashlib,os,sys,io
MU=0x200
def al(x,a): return (x+a-1)//a*a
def read_romfs_layout(f,off):
    f.seek(off);iv=f.read(0x60)
    mh=struct.unpack_from('<I',iv,8)[0]
    l3=al(0x60+mh,0x1000)
    b=off+l3;f.seek(b);hdr=f.read(0x28)
    v=struct.unpack('<10I',hdr)
    f.seek(b);meta=bytearray(f.read(v[9]))  # header+tables up to data offset
    return iv,l3,v,meta
def iter_files(meta,v):
    fmo,fms=v[7],v[8];o=0
    while o<fms:
        pa,fs,do,sz,hn,nl=struct.unpack_from('<IIQQII',meta,fmo+o)
        name=meta[fmo+o+32:fmo+o+32+nl].decode('utf-16le')
        yield fmo+o,pa,name,do,sz
        o+=al(32+nl,4)
def dir_paths(meta,v):
    dmo=v[3];res={}
    def rec(o,path):
        p,sib,ch,fi,hn,nl=struct.unpack_from('<6I',meta,dmo+o)
        name=meta[dmo+o+24:dmo+o+24+nl].decode('utf-16le')
        cur=path+'/'+name if o else ''
        res[o]=cur
        if ch!=0xffffffff: rec(ch,cur)
        if sib!=0xffffffff: rec(sib,path)
    rec(0,'');return res
def build_romfs(f,off,repl,out):
    iv,l3,v,meta=read_romfs_layout(f,off)
    dp=dir_paths(meta,v)
    files=list(iter_files(meta,v))
    dataoff=v[9];base=off+l3
    # sequential layout in original order of data offset
    files.sort(key=lambda x:x[3])
    body=io.BytesIO();cur=0
    for eo,pa,name,do,sz in files:
        rel=(dp[pa]+'/'+name).lstrip('/')
        cur=al(cur,0x10);body.seek(cur)
        if rel in repl: data=repl[rel]
        else: f.seek(base+dataoff+do);data=f.read(sz)
        body.write(data)
        struct.pack_into('<QQ',meta,eo+8,cur,len(data));cur+=len(data)
    lvl3=bytes(meta)+body.getvalue()[:cur]
    # IVFC
    bs=0x1000
    def hashes(data):
        h=bytearray()
        for i in range(0,len(data),bs):
            blk=data[i:i+bs]
            if len(blk)<bs: blk=blk+b'\0'*(bs-len(blk))
            h+=hashlib.sha256(blk).digest()
        return bytes(h)
    lvl2=hashes(lvl3);lvl1=hashes(lvl2);master=hashes(lvl1)
    l1off=0;l2off=al(len(lvl1),bs);l3off_=l2off+al(len(lvl2),bs)
    ivh=bytearray(iv[:0x5c])
    struct.pack_into('<I',ivh,8,len(master))
    struct.pack_into('<QQI',ivh,0x0c,l1off,len(lvl1),12)
    struct.pack_into('<QQI',ivh,0x24,l2off,len(lvl2),12)
    struct.pack_into('<QQI',ivh,0x3c,l3off_,len(lvl3),12)
    hdr=bytes(ivh)+b'\0'*4+master
    # layout: header+master padded to 0x1000 -> level3, then level1, level2 (3DS order)
    l3start=al(len(hdr),bs)
    out.write(hdr+b'\0'*(l3start-len(hdr)));out.write(lvl3)
    p=al(l3start+len(lvl3),bs);out.write(b'\0'*(p-(l3start+len(lvl3))))
    out.write(lvl1+b'\0'*(al(len(lvl1),bs)-len(lvl1)));out.write(lvl2+b'\0'*(al(len(lvl2),bs)-len(lvl2)))
    return hashlib.sha256(hdr[:al(len(hdr),0x200)] if False else (hdr+b'\0'*(l3start-len(hdr)))[:0x200]).digest()
def build(rom,outp,repl,newcode=None):
    f=open(rom,'rb');f.seek(0);ncsd=bytearray(f.read(0x4000))
    parts=list(struct.unpack_from('<16I',ncsd,0x120))
    b0=parts[0]*MU;f.seek(b0);h=bytearray(f.read(0x200))
    g=lambda o:struct.unpack_from('<I',h,o)[0]*MU
    exo,exs=g(0x1a0),g(0x1a4);rfo,rfs=g(0x1b0),g(0x1b4)
    tmp=open(outp+'.romfs','w+b')
    build_romfs(f,b0+rfo,repl,tmp);tmp.flush();rlen=tmp.tell()
    out=open(outp,'w+b')
    # NCCH: header, exheader, logo/plain, exefs as original up to romfs
    f.seek(b0);pre=bytearray(f.read(rfo))
    if newcode is not None:
        ex=pre[0x200:0xa00]; ex[0xd]&=~1; pre[0x200:0xa00]=ex
        struct.pack_into('<I',ex,0x18,struct.unpack_from('<I',ex,0x18)[0])
        h2=hashlib.sha256(bytes(pre[0x200:0x600])).digest();pre[0x160:0x180]=h2
        # rebuild exefs
        eh=pre[exo:exo+0x200];secs=[]
        for i in range(10):
            n,o,s=struct.unpack_from('<8sII',eh,i*16)
            if s: secs.append([n,bytes(pre[exo+0x200+o:exo+0x200+o+s])])
        for s in secs:
            if s[0].rstrip(b'\0')==b'.code': s[1]=newcode
        neh=bytearray(0x200);body=bytearray();o=0
        for i,(n,d) in enumerate(secs):
            struct.pack_into('<8sII',neh,i*16,n,o,len(d))
            neh[0x200-32*(i+1):0x200-32*i]=hashlib.sha256(d).digest()
            body+=d;pad=al(len(body),0x200)-len(body);body+=b'\0'*pad;o=len(body)
        exefs=bytes(neh)+bytes(body)
        newexs=al(len(exefs),MU)
        exefs+=b'\0'*(newexs-len(exefs))
        pre=pre[:exo]+exefs
        rfo_new=al(len(pre),0x1000)
        pre+=b'\0'*(rfo_new-len(pre))
        struct.pack_into('<I',pre,0x1a4,newexs//MU)
        struct.pack_into('<I',pre,0x1a8,1)  # hash region size 0x200
        pre[0x1c0:0x1e0]=hashlib.sha256(exefs[:0x200]).digest()
        rfo=rfo_new
    pre[0x18b]=0;pre[0x18f]|=4  # NoCrypto
    struct.pack_into('<I',pre,0x1b0,rfo//MU)
    struct.pack_into('<I',pre,0x1b4,al(rlen,MU)//MU)
    tmp.seek(0);sb=tmp.read(0x200)
    pre[0x1e0:0x200]=hashlib.sha256(sb).digest()
    ncchsize=al(rfo+rlen,MU)
    struct.pack_into('<I',pre,0x104,ncchsize//MU)
    # write ncsd
    out.write(b'\0'*0x4000)
    out.write(pre);tmp.seek(0)
    while True:
        c=tmp.read(1<<24)
        if not c:break
        out.write(c)
    out.write(b'\0'*(ncchsize-(rfo+rlen)))
    cur=0x4000+ncchsize
    newparts=[0]*16;newparts[0]=0x4000//MU;newparts[1]=ncchsize//MU
    for i in range(1,8):
        po,ps=parts[i*2],parts[i*2+1]
        if not ps: continue
        cur=al(cur,MU);f.seek(po*MU);d=f.read(ps*MU);out.seek(cur);out.write(d)
        newparts[i*2]=cur//MU;newparts[i*2+1]=ps;cur+=len(d)
    struct.pack_into('<16I',ncsd,0x120,*newparts)
    # card image size: keep media size field (0x104) as original
    out.seek(0);out.write(ncsd)
    tmp.close();os.remove(outp+'.romfs');out.close()
if __name__=='__main__':
    build(sys.argv[1],sys.argv[2],{})
