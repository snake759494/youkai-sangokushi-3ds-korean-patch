import sys, re, os
p = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'azahar', 'user', 'config', 'qt-config.ini')
s = open(p, encoding='utf-8').read()
BS = chr(92)
for kv in sys.argv[1:]:
    k, v = kv.split('=', 1)
    lines = s.split('\n')
    for i, l in enumerate(lines):
        if l.startswith(k + BS + 'default='):
            lines[i] = k + BS + 'default=false'
        elif l.startswith(k + '='):
            lines[i] = k + '=' + v
    s = '\n'.join(lines)
open(p, 'w', encoding='utf-8').write(s)
