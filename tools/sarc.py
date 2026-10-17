import struct
def parse(d):
    hl,bom,size,doff=struct.unpack_from('<HHII',d,4)
    o=hl;sh,n,hm=struct.unpack_from('<HHI',d,o+4)
    ents=[struct.unpack_from('<IIII',d,o+12+16*i) for i in range(n)]
    fo=o+12+16*n;names=fo+8
    out=[]
    for h,attr,s,e in ents:
        nm=d[names+(attr&0xffff)*4:].split(b'\0')[0].decode() if attr>>24 else '%08x'%h
        out.append((nm,doff+s,doff+e))
    return out
