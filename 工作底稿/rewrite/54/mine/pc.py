import re,sys
sys.path.insert(0,"/home/user/postgraduate-vocabulary/scripts")
from core import count_words
t=open(sys.argv[1]).read()
body=re.sub(r"^#.*$","",t,flags=re.M)
paras=[p.strip() for p in re.split(r"\n\s*\n",body.strip()) if p.strip()]
for i,p in enumerate(paras,1):
    b=re.findall(r"\*\*([^*]+)\*\*",p)
    print("P%d words=%d bold=%d"%(i,count_words(p),len(b)))
    for s in re.split(r"(?<=[.!?])\s+",p.replace("**","")):
        print("   %2d  %s"%(count_words(s),s))
