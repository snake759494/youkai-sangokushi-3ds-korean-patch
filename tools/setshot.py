import os, re
base = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
p = os.path.join(base, 'azahar', 'user', 'config', 'qt-config.ini')
s = open(p, encoding='utf-8').read()
new = os.path.abspath(os.path.join(base, 'shots')).replace(os.sep, os.sep * 2)
s = re.sub(r'(?m)^Paths\\screenshotPath=.*$', lambda m: 'Paths\\screenshotPath=' + new, s)
open(p, 'w', encoding='utf-8').write(s)
print([l for l in s.splitlines() if 'screenshotPath=' in l])
