import json,re,glob
# 第05篇初稿（逐词对照）：S = [(段, [chunk, ...])]，chunk = ([(英文组, 中文组), ...], 可选 note)
S=[
(1,[[[("In November 1983","1983年11月，"),("a 15-year-old girl","一名15岁的女孩")]],
    [[("was murdered in the Leicestershire village of Narborough,","在莱斯特郡的纳伯勒村遇害，")]],
    [[("and the **homicide**","这起**凶杀案**(homicide)"),("went","一直"),("**unsolved**.","**未能侦破**(unsolved)。")],"（go + 形容词：处于某种状态；go unsolved：一直没破案）"]]),
(1,[[[("In the summer of 1986","1986年夏天，"),("a second 15-year-old","又一名15岁的女孩")]],
    [[("was **slain** near **neighbouring** Enderby.","在**邻近的**(neighbouring)恩德比附近**被杀害**(slain)。")]]]),
(1,[[[("A 17-year-old local youth","一名17岁的当地青年"),("**confessed** to the second killing,","**供认了**(confessed)第二起命案，")]],
    [[("and to **detectives**","在**警探**(detectives)看来，"),("the **perplexing** **investigation**","这场**扑朔迷离的**(perplexing)**调查**(investigation)"),("was **seemingly** **resolved**.","**似乎**(seemingly)已经**了结**(resolved)。")],"（to sb：在某人看来）"]]),
(2,[[[("The **revelation**","这个**意外发现**(revelation)，"),("had come two years **previously**.","早在两年**以前**(previously)就已经出现了。")],"（had come：过去完成时，比上一段1986年的事更早）"]]),
(2,[[[("On 10 September 1984","1984年9月10日，")]],
    [[("Alec Jeffreys,","亚历克·杰弗里斯，"),("a **geneticist**","一位**遗传学家**(geneticist)"),("at the University of Leicester,","在莱斯特大学（任职），")]],
    [[("**discerned** on an X-ray film","在一张X光片上**辨认出**(discerned)"),("**molecular** **markers**","一些**分子**(molecular)**标记**(markers)，")],"（宾语 molecular markers 带着 whose 从句，所以放到了状语后面）"],
    [[("whose **layout**","这些标记的**排布**(layout)"),("**varied** **considerably** from person to person.","人与人之间**相差**(varied)**相当大**(considerably)。")]]]),
(2,[[[("He called them","他把这些标记称为"),("DNA fingerprints,","DNA指纹，")]],
    [[("since,","因为"),("like fingerprints,","像指纹一样，"),("they **differentiated** individuals.","它们能把不同的人**区分**(differentiated)开来。")],"（since：因为（不是“自从”）；like fingerprints 是插入成分）"]]),
(2,[[[("The journal Nature","《自然》期刊"),("**promptly**","**很快**(promptly)就"),("carried his paper in March 1985.","在1985年3月刊登了他的论文。")],"（carry：（报刊）刊登、登载）"]]),
(3,[[[("Police","警方"),("**enlisted** Jeffreys,","**请来了**(enlisted)杰弗里斯，")],"（enlist：争取（帮助）、请来帮忙；本义是“征募入伍”）"],
    [[("and his **genetic** tests","他的**基因**(genetic)检测"),("**overturned**","**推翻了**(overturned)"),("the **erroneous** **confession**.","那份**错误的**(erroneous)**供词**(confession)。")]]]),
(3,[[[("The youth","那名青年"),("was not the **perpetrator**,","不是**行凶者**(perpetrator)，")]],
    [[("and the same **attacker**","而且是同一个**袭击者**(attacker)"),("had killed both girls.","杀害了这两名女孩。")]]]),
(3,[[[("The youth","这名青年"),("became","成了")]],
    [[("the first person known to be cleared by DNA evidence.","已知第一个凭DNA证据被证明清白的人。")],"（known to be cleared…：后置定语，修饰 the first person）"]]),
(3,[[[("The **forensic** **innovation**","这项**法医学**(forensic)**创新**(innovation)"),("had freed an **innocent**","先让一名**无辜者**(innocent)重获自由，")]],
    [[("before it **implicated** anyone.","之后才**牵连**(implicated)到别人。")],"（A before B：先 A 后 B；implicate：牵连，表明……涉案）"]]),
(4,[[[("In January 1987","1987年1月，"),("police","警方"),("**commenced**","**开始了**(commenced)")]],
    [[("the world's first **large-scale** DNA screening,","世界上首次**大规模的**(large-scale)DNA筛查，")]],
    [[("asking","要求"),("more than 5,000 men in three villages","三个村庄的5,000多名男子"),("for blood or **saliva**.","提供血液或**唾液**(saliva)。")],"（ask sb for sth：要求某人提供某物；asking… 是伴随状语）"]]),
(4,[[[("None","没有一份（样本）"),("matched.","吻合。")]]]),
(4,[[[("The **elusive** killer,","这个**难以捉摸的**(elusive)凶手，"),("a local baker,","一名当地的面包师，")]],
    [[("had **induced**","事先**诱使**(induced)"),("a **co-worker**","一名**同事**(co-worker)"),("to give a sample in his name,","冒他的名字提供了样本，")],"（induce sb to do sth：诱使某人做某事；in his name：以他的名义）"],
    [[("**evading** **suspicion**.","**躲过了**(evading)**嫌疑**(suspicion)。")],"（evading suspicion：分词作结果状语）"]]),
(4,[[[("In August 1987","1987年8月，"),("someone","有人"),("**overheard**","**无意中听到**(overheard)")]],
    [[("the co-worker","这名同事"),("discussing the **substitution**","在谈论**冒名顶替**(substitution)的事，")],"（overhear sb doing sth：无意中听到某人在做某事）"],
    [[("and **notified** police.","并**通知了**(notified)警方。")]]]),
(5,[[[("Colin Pitchfork","科林·皮奇福克"),("was **detained** on 19 September 1987,","在1987年9月19日**被拘留**(detained)，")]],
    [[("and his DNA **profile**","他的DNA**图谱**(profile)"),("matched.","（与凶手的）吻合。")]]]),
(5,[[[("In January 1988","1988年1月，"),("he","他"),("**pleaded** guilty","**承认**(pleaded)有罪"),("and was **jailed** for life,","并被判处终身**监禁**(jailed)，")]],
    [[("the first person convicted of murder on the basis of DNA evidence.","（成为）第一个依据DNA证据被判谋杀罪的人。")],"（the first person… 是 he 的同位语；convicted of：被判……罪）"]]),
(5,[[[("A **tip-off**,","是一条**举报**(tip-off)，"),("not the screening,","而不是那次筛查，"),("had **unmasked** him.","**揭穿了**(unmasked)他的真面目。")],"（A, not B, had done：是 A 而不是 B 做了……）"]]),
(5,[[[("The test's first **beneficiary**","这项检测的第一个**受益者**(beneficiary)"),("had been","是"),("a **blameless** **juvenile**","一名**清白的**(blameless)**少年**(juvenile)，")]],
    [[("who had **falsely** admitted the **offence**.","他曾**虚假地**(falsely)认下这项**罪行**(offence)。")]]]),
]
out={"no":"05","title_en":"The Fingerprint in the Blood","title_zh":"血里的指纹","title_fx":{"hl":["Fingerprint","Blood"],"ghost":[]},"sentences":[]}
for p,chs in S:
    cs=[]
    for c in chs:
        al=[list(x) for x in c[0]]
        d={"en":" ".join(a for a,b in al if a!="\n"),"zh":"".join(b for a,b in al),"align":al}
        if len(c)>1: d["note"]=c[1]
        cs.append(d)
    out["sentences"].append({"para":p,"chunks":cs})
json.dump(out,open("scripts/05.json","w"),ensure_ascii=False,indent=1)
# 核对：英文与文章逐字一致、重点词一个不漏、中文与分组拼接一致
art=open(glob.glob("/home/user/postgraduate-vocabulary/新版定稿/05-*.md")[0]).read()
eng=art.split("## 英文")[1].split("## 中文")[0].strip().split("\n\n")
norm=lambda s:re.sub(r"\s|\*\*","",s)
ok=True
for i,pp in enumerate(eng,1):
    got="".join(c["en"] for s in out["sentences"] if s["para"]==i for c in s["chunks"])
    if norm(got)!=norm(pp): ok=False; print('段',i,'英文不一致'); print(norm(got)); print(norm(pp))
abold=re.findall(r"\*\*(.+?)\*\*","\n".join(eng)); sb=[]
for s in out["sentences"]:
  for c in s["chunks"]:
    assert c["zh"]=="".join(b for a,b in c["align"])
    for w in re.findall(r"\*\*(.+?)\*\*",c["en"]):
        sb.append(w); assert "("+w+")" in c["zh"],w
    for w in re.findall(r"\*\*[^*]+\*\*\(([^)]+)\)",c["zh"]): assert "**"+w+"**" in c["en"],w
print('英文一致' if ok else '英文不一致', '| 重点词', len(abold), '个，对照里', len(sb), '个，完全一致' if sorted(abold)==sorted(sb) else set(abold)^set(sb))
zh=[(w, re.findall(r"\*\*([^*]+)\*\*\("+re.escape(w)+r"\)", c["zh"])[0]) for s in out["sentences"] for c in s["chunks"] for w in re.findall(r"\*\*(.+?)\*\*",c["en"])]
dup={}
for w,z in zh: dup.setdefault(z,[]).append(w)
print('不同英文用了同一个中文：',{k:v for k,v in dup.items() if len(v)>1} or '无')
print('句数',len(out["sentences"]),'chunk',sum(len(s["chunks"]) for s in out["sentences"]),'组',sum(len(c["align"]) for s in out["sentences"] for c in s["chunks"]),'note',sum(1 for s in out["sentences"] for c in s["chunks"] if c.get("note")))
