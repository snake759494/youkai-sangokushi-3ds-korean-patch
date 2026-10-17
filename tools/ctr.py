import struct,os,sys
MU=0x200
def ncch_info(f,base):
    f.seek(base);h=f.read(0x200)
    assert h[0x100:0x104]==b'NCCH'
    g=lambda o:struct.unpack_from('<I',h,o)[0]*MU
    return dict(h=h,exh_size=struct.unpack_from('<I',h,0x180)[0],
      plain=(g(0x190),g(0x194)),logo=(g(0x198),g(0x19c)),exefs=(g(0x1a0),g(0x1a4)),exefs_hash=g(0x1a8),
      romfs=(g(0x1b0),g(0x1b4)),romfs_hash=g(0x1b8))
def romfs_extract(f,off,out):
    f.seek(off);iv=f.read(0x5c);assert iv[:4]==b'IVFC'
    masterhash=struct.unpack_from('<I',iv,8)[0]
    l3off=(0x60+masterhash+0xfff)&~0xfff  # level3 block size 0x1000
    b=off+l3off
    f.seek(b);hd=struct.unpack('<10I',f.read(40))
    _,dho,dhs,dmo,dms,fho,fhs,fmo,fms,fdo=hd
    f.seek(b+dmo);dm=f.read(dms);f.seek(b+fmo);fm=f.read(fms)
    def walk_dir(o,path):
        p,sib,child,file,_,nl=struct.unpack_from('<6I',dm,o)
        name=dm[o+24:o+24+nl].decode('utf-16le')
        cur=os.path.join(path,name) if o else path
        os.makedirs(cur,exist_ok=True)
        fo=file
        while fo!=0xffffffff:
            pa,fs,do,sz,_,nl2=struct.unpack_from('<IIQQII',fm,fo)
            fn=fm[fo+32:fo+32+nl2].decode('utf-16le')
            f.seek(b+fdo+do);open(os.path.join(cur,fn),'wb').write(f.read(sz))
            fo=fs
        if child!=0xffffffff: walk_dir(child,cur)
        if sib!=0xffffffff and o: walk_dir(sib,path)
    walk_dir(0,out)
def exefs_extract(f,off,out):
    os.makedirs(out,exist_ok=True);f.seek(off);h=f.read(0x200)
    for i in range(10):
        n,o,s=struct.unpack_from('<8sII',h,i*16)
        if s: f.seek(off+0x200+o);open(os.path.join(out,n.rstrip(b'\0').decode()),'wb').write(f.read(s))
if __name__=='__main__':
    rom,out=sys.argv[1],sys.argv[2]
    f=open(rom,'rb');f.seek(0x120);parts=struct.unpack('<16I',f.read(64))
    base=parts[0]*MU;i=ncch_info(f,base)
    os.makedirs(out,exist_ok=True)
    open(out+'/ncch0_header.bin','wb').write(i['h'])
    f.seek(base+0x200);open(out+'/exheader.bin','wb').write(f.read(0x800))
    exefs_extract(f,base+i['exefs'][0],out+'/exefs')
    romfs_extract(f,base+i['romfs'][0],out+'/romfs')
    print(i['exefs'],i['romfs'])
