import struct,re
JP=re.compile('[぀-ヿ㐀-鿿！-～]')
def table(d):
    """count + (off,size) pairs, contiguous-ish, inside d"""
    if len(d)<12: return None
    n=struct.unpack_from('<I',d,0)[0]
    if n==0 or n>100000 or 4+n*8>len(d): return None
    t=[struct.unpack_from('<II',d,4+i*8) for i in range(n)]
    if t[0][0]<4+n*8 or t[0][0]>4+n*8+0x80: return None
    prev=4+n*8
    for o,s in t:
        if o<prev or o+s>len(d) or o-prev>0x80: return None
        prev=o+s
    if len(d)-prev>0x80: return None
    return t
def isstr(x):
    if not x or x[-1]!=0: return False
    try: s=x[:-1].decode('utf-8')
    except: return False
    return '\0' not in s
def walk(d,path=()):
    """yield (path, kind, value) ; kind 's' string leaf (path to entry)"""
    t=table(d)
    if t is None:
        yield path,'b',d;return
    if all(isstr(d[o:o+s]) for o,s in t):
        for i,(o,s) in enumerate(t): yield path+(i,),'s',d[o:o+s-1].decode('utf-8')
        return
    for i,(o,s) in enumerate(t): yield from walk(d[o:o+s],path+(i,))
def rebuild(d,repl,path=()):
    """repl: dict path->new string; returns new bytes"""
    t=table(d)
    if t is None: return d
    leaf=all(isstr(d[o:o+s]) for o,s in t)
    parts=[]
    for i,(o,s) in enumerate(t):
        p=path+(i,)
        if leaf: parts.append(repl[p].encode('utf-8')+b'\0' if p in repl else d[o:o+s])
        else: parts.append(rebuild(d[o:o+s],repl,p))
    # reproduce alignment: measure original gaps
    n=len(t);hdr=4+n*8
    out=bytearray(struct.pack('<I',n)+b'\0'*(n*8))
    out+=d[hdr:t[0][0]]
    al=align_of(d,t)
    for i,x in enumerate(parts):
        while len(out)%al: out+=b'\0'
        if i==0 and len(out)<t[0][0]: out+=b'\0'*(t[0][0]-len(out))
        struct.pack_into('<II',out,4+i*8,len(out),len(x));out+=x
    tail=len(d)-(t[-1][0]+t[-1][1])
    out+=b'\0'*tail
    return bytes(out)
def align_of(d,t):
    for a in (16,4,1):
        if all(o%a==0 for o,s in t): return a
    return 1
