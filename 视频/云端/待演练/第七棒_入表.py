import json,sys,collections
V=sys.argv[1]; ks=json.load(open(sys.argv[2]))
p=f'{V}/制作硬性标准与踩坑总结.md'; L=open(p).read().split('\n')
T=json.load(open(f'{V}/工具/规则执行表.json'),object_pairs_hook=collections.OrderedDict)
for k in ks:
    n=k['号']
    if any(l.startswith(f'| {n} |') for l in L): continue
    i=max(j for j,l in enumerate(L) if l.startswith('| G') and l.split('|')[1].strip()[1:].isdigit() and int(l.split('|')[1].strip()[1:])<int(n[1:]))
    L.insert(i+1,f'| {n} | {k["行"]} |'); T[n]=collections.OrderedDict([('门',k['门']),('自检',k['自检'])])
open(p,'w').write('\n'.join(L)); open(f'{V}/工具/规则执行表.json','w').write(json.dumps(T,ensure_ascii=False,indent=1)+'\n')
