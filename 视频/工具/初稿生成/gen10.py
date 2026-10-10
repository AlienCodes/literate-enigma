import json,re,glob,os
# 第10篇初稿（逐词对照）：S = [(段, [chunk, ...])]，chunk = ([(英文组, 中文组), ...], 可选 note)
# 2026-10-10 按现行做法：程序打底（英文、重点词与文章逐字核对），重点词中文沿用文章定稿（新版定稿/10）的意思（铁律），
# 只按《翻译风格》调格式：作定语的形容词“的”、方式副词“地”、过去时的“了”放进粗体，阿拉伯数字照写（第17条），语序必须倒过来的整组。
# 用户在 08、09 定下的规矩一并照做（09 用户 21 条修改的规律）：
#   短语型用法整体标（T22，两个方向：stare at、in custody、at the invitation of、elevate … to），被隔开的中文意思每一处都标（T23：应……邀请、把……推上了）；
#   不是重点词的过去时动词按语境译出“了”；同一篇不同重点词的中文不能一样（T26）。
S=[
(1,[[[("On Monday 21 August 1911,","1911年8月21日是星期一，")]],
    [[("when the Louvre was","卢浮宫"),("**customarily**","**照例**(customarily)"),("closed,","闭馆，")]],
    [[("the Mona Lisa","《蒙娜丽莎》就在这一天"),("was **discreetly** **plucked** from its wall.","被人从墙上**悄悄地**(discreetly)**摘走了**(plucked)。")]]]),
(1,[[[("The **disappearance**","画作的**失踪**(disappearance)"),("went **unnoticed**","一直**无人察觉**(unnoticed)，")]],
    [[("until the next day,","直到第二天，")]],
    [[("when a painter arriving to **sketch**","一位前来画**素描**(sketch)的画家"),("found","发现，")]],
    [[("a **conspicuous** **gap** of bare **plaster**.","**灰泥**(plaster)墙面上露出一块**显眼的**(conspicuous)**空缺**(gap)。")]]]),
(1,[[[("**Custodians**","**管理人员**(Custodians)"),("**shuttered** the museum","把博物馆**关闭了**(shuttered)"),("for a week.","一周。")]]]),
(2,[[[("When the museum **reopened**,","博物馆**重新开放**(reopened)后，")]],
    [[("**curious** **onlookers**","**好奇的**(curious)**围观者**(onlookers)"),("queued","排队前来，")]],
    [[("to **stare at**","**凝视**(stare at)"),("the **vacant** space","那块**空荡荡的**(vacant)地方，")]],
    [[("where the **masterpiece**","那幅**杰作**(masterpiece)"),("had hung.","原先就挂在那里。")]]]),
(2,[[[("On 7 September 1911","1911年9月7日，"),("the poet Guillaume Apollinaire","诗人纪尧姆·阿波利奈尔")]],
    [[("was held **in custody**","被**拘押了**(in custody)"),("for about a week,","约一周，")]],
    [[("and Pablo Picasso","巴勃罗·毕加索也"),("was **interrogated**.","受到了**审问**(interrogated)。")]]]),
(2,[[[("Both","两人都"),("were cleared of **involvement** in the **burglary**.","洗清了**牵涉**(involvement)这起**盗窃案**(burglary)的嫌疑。")],
     "（be cleared of：洗清……的嫌疑）"]]),
(3,[[[("The **intruder**","**闯入者**(intruder)"),("was","是"),("Vincenzo Peruggia,","文森佐·佩鲁贾，")]],
    [[("an Italian who had **temporarily** worked at the Louvre as a glazier.","一个曾在卢浮宫**短期**(temporarily)做过玻璃工的意大利人。")],
     "（an Italian who…：同位语，说明 Peruggia）"]]),
(3,[[[("Having **lurked** in a storeroom on Sunday,","他星期天**潜伏**(lurked)在一间储藏室里，")]],
    [[("he **strode** out **unchallenged** in a workman's smock,","之后穿着一件工作罩衫**大步**(strode)走了出去，**无人盘问**(unchallenged)，")]],
    [[("the painting","画就"),("**tucked** **beneath** his clothes.","**塞**(tucked)在他的衣服**底下**(beneath)。")],
     "（Having lurked…：完成式分词，表示先发生；\nthe painting tucked…：独立主格，说明当时的情形）"]]),
(3,[[[("For more than two years","此后两年多，"),("it","这幅画"),("lay **stashed**","一直**藏匿**(stashed)")]],
    [[("in a false-bottomed **trunk** in his Paris **lodgings**.","在他巴黎**住处**(lodgings)一只带夹层底的**箱子**(trunk)里。")],
     "（lie + 过去分词：一直处于……状态）"]]),
(4,[[[("In December 1913","1913年12月，"),("Peruggia","佩鲁贾"),("**contacted**","**联系了**(contacted)")]],
    [[("Alfredo Geri, an art **dealer** in Florence.","佛罗伦萨的艺术品**商人**(dealer)阿尔弗雷多·杰里。")]]]),
(4,[[[("The Uffizi's director","乌菲齐美术馆馆长"),("**authenticated** the painting at Peruggia's hotel;","在佩鲁贾下榻的旅馆**鉴定了**(authenticated)这幅画，")]],
    [[("Peruggia was **apprehended** on 11 December 1913.","1913年12月11日，佩鲁贾被**逮捕**(apprehended)。")]]]),
(4,[[[("Citing **patriotism**,","他以**爱国**(patriotism)为由，")]],
    [[("he said","说"),("he wanted it **repatriated**,","想把画**送回**(repatriated)祖国；")]],
    [[("**mistakenly** believing","他**误以为**(mistakenly)"),("Napoleon","拿破仑"),("had **looted** it.","**掠走了**(looted)这幅画。")],
     "（Citing…：现在分词短语作原因状语；\nmistakenly believing…：现在分词短语作伴随状语）"]]),
(4,[[[("In fact","事实上，"),("Leonardo da Vinci","列奥纳多·达·芬奇")]],
    [[("had **accompanied** it to France **at the invitation of** King Francis I.","**应**(at the invitation of)国王弗朗索瓦一世的**邀请**(at the invitation of)，**随身带着**(accompanied)这幅画去了法国。")]]]),
(5,[[[("After **showings** in Italy,","在意大利**展出**(showings)之后，")]],
    [[("the painting","这幅画"),("was **reinstated** in the Louvre on 4 January 1914.","于1914年1月4日**重回**(reinstated)卢浮宫。")]]]),
(5,[[[("In June 1914","1914年6月，"),("a **tribunal**","**法庭**(tribunal)"),("**imposed**","**判处了**(imposed)佩鲁贾")]],
    [[("a **penalty** of a year and 15 days,","一年零15天的**刑罚**(penalty)，")]],
    [[("but he","但他实际"),("was **imprisoned**","**坐牢**(imprisoned)"),("for about seven months.","约七个月。")]]]),
(5,[[[("Many historians","许多史学家"),("argue","认为，")]],
    [[("the **heist** **elevated** one **esteemed** **gem** among many","这幅画原本是众多**备受推崇的**(esteemed)**珍品**(gem)之一，这起**盗画案**(heist)**把**(elevated to)它")]],
    [[("**to** the world's most **renowned** painting.","**推上了**(elevated to)世界最**著名的**(renowned)画作的位置。")],
     "（elevate A to B：把A提升到B的位置；one … among many：众多……之一）"]]),
(5,[[[("If so,","若真如此，"),("its **fame**","它的**名气**(fame)"),("began with","始于"),("a **bare** wall.","一面**光秃秃的**(bare)墙。")]]]),
]
CONF={}
out={"no":"10","title_en":"The Stolen Smile","title_zh":"被偷走的微笑","title_fx":{"hl":["Stolen","Smile"],"ghost":[]},"sentences":[],"核对确认":CONF}
for p,chs in S:
    cs=[]
    for c in chs:
        al=[list(x) for x in c[0]]
        d={"en":" ".join(a for a,b in al if a!="\n"),"zh":"".join(b for a,b in al),"align":al}
        if len(c)>1: d["note"]=c[1]
        cs.append(d)
    out["sentences"].append({"para":p,"chunks":cs})
if os.path.exists("scripts/10.json"):                      # 保留后来写进脚本的核对确认、列举逗号、结尾句等（初稿程序只管句子）
    old=json.load(open("scripts/10.json"))
    for k_,v_ in old.items():
        if k_ not in ("no","title_en","title_zh","title_fx","sentences"): out[k_]=v_
json.dump(out,open("scripts/10.json","w"),ensure_ascii=False,indent=1)
art=open(glob.glob("/home/user/postgraduate-vocabulary/新版定稿/10-*.md")[0]).read()
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
aw={plain(w).lower() for w in abold}; sw=set()
for w in sb: sw|=set(w.lower().split())
miss=[w for w in aw if not (w in sw or any(w in x for x in sw))]
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
