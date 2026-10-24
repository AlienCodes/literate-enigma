import sys, json,re,glob,os
# 初稿共用部分（2026-10-15 方法升级，省 token）：genNN.py 只写 S（逐词对照）、CONF、out，最后一行调用 生成并核对(S, out)。
# 生成 scripts/NN.json（合并旧脚本里后来写进的核对确认和其他键），核对英文与文章逐字一致、重点词一个不漏、align 一致、
# 不同重点词中文不重复、重点词中文与文章定稿只差“的/地/了”进粗体（同 gen10 末尾，原样搬过来）。
def 缺的重点词(abold, sb):
    """文章里加粗的重点词，对照里没有的。多词重点词（hinge on、dead reckoning）整体加粗、或每个词都加粗了，都算在
    （24 草稿报的误报：原来把多词重点词整体去和单个词比，报“缺”）"""
    p_ = lambda x: re.sub(r"\*\*", "", x).lower(); low = [p_(x) for x in sb]; sw = set()
    for w in low: sw |= set(w.split())
    return sorted(w for w in {p_(x) for x in abold} if not (w in sw or any(w in x for x in low) or any(w in x for x in sw) or all(t in sw for t in w.split())))


def 生成并核对(S, out):
    no = out["no"]
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")); import 重点词被去掉 as _QD
    if _QD.提醒(no): print(_QD.提醒(no))   # 用户 2026-10-17：做这一篇时告诉用户哪些重点词被去掉了
    for p,chs in S:
        cs=[]
        for c in chs:
            al=[list(x) for x in c[0]]
            d={"en":" ".join(a for a,b in al if a!="\n"),"zh":"".join(b for a,b in al),"align":al}
            if len(c)>1: d["note"]=c[1]
            cs.append(d)
        out["sentences"].append({"para":p,"chunks":cs})
    if os.path.exists(f"scripts/{no}.json"):                      # 保留后来写进脚本的核对确认、列举逗号、结尾句等（初稿程序只管句子）；核对确认合并，程序里写的这几条为准
        old=json.load(open(f"scripts/{no}.json"))
        for k_,v_ in old.items():
            if k_ == "核对确认":
                for kk,vv in v_.items():
                    if isinstance(vv,dict) and isinstance(out[k_].get(kk,{}),dict): out[k_][kk]={**vv,**out[k_].get(kk,{})}
                    else: out[k_].setdefault(kk,vv)   # 字符串值的确认（已告诉用户被去掉的重点词）：程序里写的为准（21 重跑生成时这里报 TypeError）
            elif k_ not in ("no","title_en","title_zh","title_fx","sentences"): out[k_]=v_
    json.dump(out,open(f"scripts/{no}.json","w"),ensure_ascii=False,indent=1)
    art=open(glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "新版定稿", f"{no}-*.md"))[0]).read()   # 按本程序所在仓库找文章（演练镜像里读冻结拷贝）
    eng=art.split("## 英文")[1].split("## 中文")[0].strip().split("\n\n")
    ok=True; plain=lambda x:re.sub(r"\*\*","",x)
    for i,pp in enumerate(eng,1):
        got=" ".join(c["en"] for s in out["sentences"] if s["para"]==i for c in s["chunks"])
        if plain(got)!=plain(pp.strip()): ok=False; print('段',i,'英文（去掉加粗）不一致'); print(got); print(pp)
        elif got!=pp.strip(): print('段',i,'只有加粗范围不同（短语整体标 T22，出片前由 sync_article 同步进文章）')
    abold=re.findall(r"\*\*(.+?)\*\*","\n".join(eng)); sb=[]
    for s in out["sentences"]:
      for c in s["chunks"]:
        assert c["zh"]=="".join(b for a,b in c["align"])
        keys=re.findall(r"\*\*[^*]+\*\*\(([^)]+)\)",c["zh"])
        for w in re.findall(r"\*\*(.+?)\*\*",c["en"]):
            sb.append(w); assert "("+w+")" in c["zh"] or any(w in k.split() or w in k for k in keys),w
        sen=" ".join(x["en"] for x in s["chunks"])               # 被隔开的短语可以跨块（elevated … to 分在两块）
        for w in keys: assert "**"+w+"**" in c["en"] or all("**"+x+"**" in sen or x in plain(sen) for x in w.split()),w
    miss=缺的重点词(abold, sb)
    print('英文与文章逐字一致（不计加粗）' if ok else '英文不一致', '| 文章重点词', len(abold), '个，对照里都在' if not miss else ('缺：'+str(miss)))
    zh=[(e, z) for s in out["sentences"] for c in s["chunks"] for e, z in dict((e_, z_) for z_, e_ in re.findall(r"\*\*([^*]+)\*\*\(([^)]+)\)", c["zh"])).items()]
    dup={}
    for w,z in zh: dup.setdefault(z,[]).append(w)
    print('不同英文用了同一个中文：',{k:v for k,v in dup.items() if len(set(x.lower() for x in v))>1} or '无')
    # 重点词中文与文章定稿逐个比对（只许格式差别：“的”“地”“了”进粗体）；短语整体标后英文标签变了的另列
    artzh={e.lower():z for z,e in re.findall(r"\*\*([^*]+)\*\*\(([^)]+)\)",art.split("## 中文")[1].split("## 速查表")[0])}
    fmt=lambda z:re.sub(r'[的地了]$','',z)
    diff=[(w,z,artzh.get(w.lower())) for w,z in zh if w.lower() in artzh and fmt(z)!=fmt(artzh[w.lower()]) and z!=artzh[w.lower()]]
    print('重点词中文与文章定稿不同：', diff or '无（只有“的”“地”“了”进粗体的格式差别）')
    print('短语整体标后英文标签变了（中文沿用文章）：', [(w,z) for w,z in zh if w.lower() not in artzh])
    g=[a for s in out["sentences"] for c in s["chunks"] for a,z in c["align"]]
    print('句数',len(out["sentences"]),'chunk',sum(len(s["chunks"]) for s in out["sentences"]),'组',len(g),'每组英文词',round(sum(len(plain(a).split()) for a in g)/len(g),2),'note',sum(1 for s in out["sentences"] for c in s["chunks"] if c.get("note")))
