import sys, re
from html.parser import HTMLParser
VOID={'img','br','hr','meta','link','input','col','area','base','wbr','source'}
class P(HTMLParser):
    def __init__(s):
        super().__init__(); s.st=[]; s.err=[]
    def handle_starttag(s,t,a):
        if t in VOID: return
        s.st.append((t,s.getpos()))
    def handle_endtag(s,t):
        if t in VOID: return
        if not s.st: s.err.append(('extra close',t,s.getpos())); return
        if s.st[-1][0]==t: s.st.pop(); return
        # implicit close of li/p etc?
        s.err.append(('mismatch close',t,'open',s.st[-1],s.getpos()))
        for i in range(len(s.st)-1,-1,-1):
            if s.st[i][0]==t: del s.st[i:]; break
for f in sys.argv[1:]:
    p=P(); p.feed(open(f,encoding='utf-8').read()); p.close()
    print(f, 'errors:',p.err[:10],'unclosed:',p.st[:10])
    txt=open(f,encoding='utf-8').read()
    for m in re.finditer(r'<img src="\.\./images/([^"]+)"',txt):
        import os
        print('  img',m.group(1), os.path.exists('../images/'+m.group(1)))
    for m in re.finditer(r'<b>图 ([0-9]+-[0-9]+)</b>',txt): print('  fig',m.group(1))
