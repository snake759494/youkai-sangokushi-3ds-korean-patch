import struct,sys
def decompress(d):
    enc,inc=struct.unpack_from('<II',d,len(d)-8)
    top=enc>>24; bottom=enc&0xffffff
    out=bytearray(d+bytes(inc)); src=len(d)-top; dst=len(out); end=len(d)-bottom
    while src>end:
        src-=1;fl=out[src]
        for i in range(8):
            if src<=end: break
            if fl&0x80:
                src-=2;v=out[src]|(out[src+1]<<8)
                n=(v>>12)+3;disp=(v&0xfff)+3
                for _ in range(n):
                    dst-=1;out[dst]=out[dst+disp]
            else:
                src-=1;dst-=1;out[dst]=out[src]
            fl<<=1
    return bytes(out)
if __name__=='__main__':
    open(sys.argv[2],'wb').write(decompress(open(sys.argv[1],'rb').read()))
