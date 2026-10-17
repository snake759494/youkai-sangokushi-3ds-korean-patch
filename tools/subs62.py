import struct
def parse(d):
    cnt=struct.unpack_from('<I',d,4)[0]
    offs=[struct.unpack_from('<I',d,8+4*i)[0] for i in range(cnt)]
    ents=[]
    for o in offs:
        a,b=struct.unpack_from('<ff',d,o);e=d.index(b'\0',o+8)
        ents.append((d[o:o+8],d[o+8:e].decode('utf-8')))
    return ents
def build(d,repl):
    ents=parse(d);cnt=len(ents)
    out=bytearray(d[:4]+struct.pack('<I',cnt)+b'\0'*(4*cnt))
    for i,(tm,s) in enumerate(ents):
        while len(out)%4: out+=b'\0'
        struct.pack_into('<I',out,8+4*i,len(out))
        out+=tm+repl.get(i,s).encode('utf-8')+b'\0'
    while len(out)%4: out+=b'\0'
    return bytes(out)
