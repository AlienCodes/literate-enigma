import json,re,glob
# 第08篇初稿（逐词对照）：S = [(段, [chunk, ...])]，chunk = ([(英文组, 中文组), ...], 可选 note)
# 2026-10-10 按现行做法：程序打底（英文、重点词与文章逐字核对），重点词中文沿用文章定稿（新版定稿/08）的意思，
# 只按《翻译风格》调格式（作定语的形容词“的”放进粗体、正文不用“即”、阿拉伯数字照写），再做两视角独立审校。
S=[
(1,[[[("In the first ten days of September 1854,","1854年9月上旬，")]],
    [[("cholera","霍乱"),("**ravaged** an **overcrowded** corner of London's Soho;","在伦敦苏豪区一个**拥挤不堪的**(overcrowded)角落**肆虐**(ravaged)；")]],
    [[("**upwards of**","**逾**(upwards of)"),("500 people","500人"),("**perished**.","**丧命**(perished)。")]]]),
(1,[[[("Most doctors","多数医生"),("**attributed** **epidemics** to miasma,","把**流行病**(epidemics)**归因于**(attributed)瘴气，")]],
    [[("**foul** air **arising** from **filth**.","也就是从**污秽**(filth)中**产生**(arising)的、**污浊的**(foul)空气。")],"（attribute A to B：把A归因于B；foul air…：同位语，解释 miasma）"]]),
(1,[[[("John Snow,","约翰·斯诺，"),("a **physician**","一位**内科医生**(physician)，")]],
    [[("who had been **convinced** since 1849","自1849年起就**确信**(convinced)"),("that cholera's poison","霍乱的毒素"),("was **swallowed**,","是**吞**(swallowed)进去的，"),("not **inhaled**,","而不是**吸**(inhaled)进去的，")]],
    [[("suspected","他怀疑"),("the Broad Street pump.","问题出在宽街那口水泵上。")]]]),
(2,[[[("Finding little visible impurity,","在泵水里没发现多少肉眼可见的杂质，")]],
    [[("he","他"),("**hesitated**,","一时**犹豫**(hesitated)，")]],
    [[("then","随后"),("**consulted**","**查阅了**(consulted)"),("the death **register**","死亡**登记册**(register)，"),("and questioned","又去询问"),("**bereaved** families.","**痛失亲人的**(bereaved)家庭。")],"（Finding…：现在分词短语作状语，表示原因）"]]),
(2,[[[("Most victims","死者大多"),("lived near the pump","住在这口泵附近，"),("and drank from it.","也喝过它的水。")]]]),
(2,[[[("At his **urging**,","在他的**敦促**(urging)下，"),("**parish** officials","**教区**(parish)官员"),("removed the handle,","卸下了泵柄，")]],
    [[("but","可这时"),("daily","每天新发的"),("**fatal** attacks","**致死**(fatal)病例"),("had already","早已"),("**plunged** from a **peak** of 143","从143例的**峰值**(peak)**骤降**(plunged)"),("to 12.","到12例。")],"（attack：疾病发作；plunge from A to B：从A骤降到B）"]]),
(2,[[[("He","他"),("later","后来"),("mapped the deaths.","把死亡病例标在了地图上。")]]]),
(3,[[[("In 1855","1855年，"),("Edmund Parkes,","埃德蒙·帕克斯，"),("a professor of **clinical** medicine,","一位**临床**(clinical)医学教授，")]],
    [[("**interpreted** the **cluster** on that map","看到那张地图上死者扎堆，便把这种**聚集**(cluster)**解读**(interpreted)"),("as a **poison** **drifting** through the air.","为空气中**飘散**(drifting)的**毒素**(poison)所致。")],"（interpret A as B：把A解读为B；drifting…：现在分词短语作后置定语）"]]),
(3,[[[("Yet","可"),("a map","地图"),("could **chart**","只能**标出**(chart)"),("where people died,","人死在哪里，"),("not what they drank.","标不出他们喝了什么。")]]]),
(4,[[[("The **crucial** evidence,","**关键**(crucial)证据"),("gathered in 1854,","早在1854年就已收集到，"),("lay in **exceptions**.","就藏在那些**例外**(exceptions)里。")],"（gathered…：过去分词短语作后置定语；lay：lie 的过去式，lie in 存在于）"]]),
(4,[[[("**Amid** the deaths in the **surrounding** streets,","在**周围的**(surrounding)街巷死者接连不断**之际**(Amid)，")]],
    [[("a workhouse with its own well","一所自有水井的济贫院（收容贫民的机构）里，"),("lost **a mere** five of 535 **inmates**.","535名**收容者**(inmates)只死了**区区**(a mere)五人。")],"（lose：失去某人，这里指有人死去；five of 535：535人中的五人）"]]),
(4,[[[("More than 70 nearby brewery workers,","附近一家啤酒厂的70多名工人"),("with a beer **allowance**","有啤酒**配给**(allowance)，"),("and their own well,","厂里也有自己的水井，")]],
    [[("escaped","结果都没有染上"),("severe cholera.","重症霍乱。")]]]),
(5,[[[("**Conversely**,","**反过来**(Conversely)，"),("a Hampstead **widow**","汉普斯特德的一位**寡妇**(widow)"),("who had not set foot in Soho for months","已有几个月没踏进过苏豪，")]],
    [[("had the pump's water","却让人把这口泵的水"),("**carted** to her daily.","每天**用车运来**(carted)。")],"（have sth done：让人做某事；set foot in：踏进）"]]),
(5,[[[("She died,","她死了，"),("as did a visiting **niece** who drank it.","来探望她并喝了这水的**侄女**(niece)也死了。")],"（as did…：倒装，= and so did a visiting niece）"]]),
(5,[[[("Hampstead","汉普斯特德"),("then","当时"),("had no cholera.","并没有霍乱。")]]]),
(6,[[[("In 1855","1855年，"),("a government **inquiry**","政府的**调查委员会**(inquiry)"),("**declined** to","**不肯**(declined)"),("**condemn** the pump,","给这口泵**定罪**(condemn)，")]],
    [[("**contending**","**坚称**(contending)"),("its water","泵水"),("had at most","至多是"),("**absorbed** **airborne** poison.","**吸收了**(absorbed)**经空气传播的**(airborne)毒素。")],"（contending…：现在分词短语作伴随状语，后面省略了 that；at most：充其量）"]]),
(6,[[[("**Meanwhile**,","**与此同时**(Meanwhile)，"),("the **sceptical** curate","**心存怀疑的**(sceptical)副牧师（协助教区牧师的低级神职人员）"),("Henry Whitehead","亨利·怀特黑德")]],
    [[("set out to","一心想"),("**refute** Snow","**驳倒**(refute)斯诺，"),("but found","却发现")]],
    [[("that those who drank from the pump","喝泵水的人"),("were far more likely to **succumb** to the disease than others,","**死于**(succumb)这种病的可能性远高于旁人，")]],
    [[("**vindicating** him.","反倒**证明了**(vindicating)斯诺是对的。")],"（succumb to：本义屈服于，这里指死于某病；vindicating…：现在分词短语作结果状语）"]]),
]
CONF={"牛津逗号":{"S12 70 nearby brewery workers, with a beer allowance and":"不是三项并列：逗号之间是插入的介词短语 with a beer allowance and their own well，只有两项"}}
out={"no":"08","title_en":"The Doctor Who Solved the Cholera Mystery","title_zh":"破解霍乱之谜的医生","title_fx":{"hl":["Cholera","Mystery"],"ghost":[]},"sentences":[],"核对确认":CONF}
for p,chs in S:
    cs=[]
    for c in chs:
        al=[list(x) for x in c[0]]
        d={"en":" ".join(a for a,b in al if a!="\n"),"zh":"".join(b for a,b in al),"align":al}
        if len(c)>1: d["note"]=c[1]
        cs.append(d)
    out["sentences"].append({"para":p,"chunks":cs})
json.dump(out,open("scripts/08.json","w"),ensure_ascii=False,indent=1)
art=open(glob.glob("/home/user/postgraduate-vocabulary/新版定稿/08-*.md")[0]).read()
eng=art.split("## 英文")[1].split("## 中文")[0].strip().split("\n\n")
ok=True
for i,pp in enumerate(eng,1):
    got=" ".join(c["en"] for s in out["sentences"] if s["para"]==i for c in s["chunks"])
    if got!=pp.strip(): ok=False; print('段',i,'英文不一致'); print(got); print(pp)
abold=re.findall(r"\*\*(.+?)\*\*","\n".join(eng)); sb=[]
for s in out["sentences"]:
  for c in s["chunks"]:
    assert c["zh"]=="".join(b for a,b in c["align"])
    for w in re.findall(r"\*\*(.+?)\*\*",c["en"]):
        sb.append(w); assert "("+w+")" in c["zh"],w
    for w in re.findall(r"\*\*[^*]+\*\*\(([^)]+)\)",c["zh"]): assert "**"+w+"**" in c["en"],w
print('英文与文章逐字一致' if ok else '英文不一致', '| 重点词', len(abold), '个，对照里', len(sb), '个，完全一致' if sorted(abold)==sorted(sb) else set(abold)^set(sb))
zh=[(w, re.findall(r"\*\*([^*]+)\*\*\("+re.escape(w)+r"\)", c["zh"])[0]) for s in out["sentences"] for c in s["chunks"] for w in re.findall(r"\*\*(.+?)\*\*",c["en"])]
dup={}
for w,z in zh: dup.setdefault(z,[]).append(w)
print('不同英文用了同一个中文：',{k:v for k,v in dup.items() if len(v)>1} or '无')
# 重点词中文与文章定稿逐个比对（只许格式差别：“的”进粗体）
artzh={e.lower():z for z,e in re.findall(r"\*\*([^*]+)\*\*\(([^)]+)\)",art.split("## 中文")[1].split("## 速查表")[0])}
diff=[(w,z,artzh.get(w.lower())) for w,z in zh if artzh.get(w.lower()) not in (z, z.rstrip('的'), z.replace('了',''), z.replace('委员会',''))]
print('重点词中文与文章定稿不同：', diff or '无（只有“的”“了”进粗体的格式差别）')
g=[a for s in out["sentences"] for c in s["chunks"] for a,z in c["align"]]
print('句数',len(out["sentences"]),'chunk',sum(len(s["chunks"]) for s in out["sentences"]),'组',len(g),'每组英文词',round(sum(len(re.sub(r"\*\*","",a).split()) for a in g)/len(g),2),'note',sum(1 for s in out["sentences"] for c in s["chunks"] if c.get("note")))
