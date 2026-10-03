import json,re,sys
sys.path.insert(0,'.'); from draft_check import lemma_key
d=json.load(open(__import__('os').path.join(__import__('os').path.dirname(__file__),'used_words.json')))
def check(path,own=None):
    en=open(path).read().split('## 中文')[0]
    out=[]
    for w in re.findall(r'\*\*([^*]+)\*\*',en):
        parts=re.split(r'[ \-]',w)
        if len(parts)<2: continue
        for p in parts:
            if len(p)<3: continue
            k=lemma_key(p)
            if k in d and d[k]!=own: out.append((w,p,d[k]))
    return out
if __name__=='__main__':
    for f in sys.argv[1:]:
        print(f, check(f))
