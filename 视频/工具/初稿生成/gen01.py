import json,re
S=[(1,[("On 6 January 1995, McArthur Wheeler and an accomplice","1995年1月6日，麦克阿瑟·惠勒和一名同伙"),
("**raided** two Pittsburgh-area banks at gunpoint","持枪**抢劫了**(raided)匹兹堡地区的两家银行，"),
("**in broad daylight**, without **disguise**.","在**光天化日之下**(in broad daylight)，也没做任何**乔装**(disguise)。")]),
(1,[("Their only **camouflage** was lemon juice,","他们唯一的**伪装**(camouflage)是柠檬汁，"),
("**rubbed on** in the **earnest** **conviction**","是怀着**真心实意的**(earnest)**信念**(conviction)**抹上**(rubbed on)的，"),
("that it would **render** them invisible to cameras.","相信它能**让**(render)他们在摄像头前隐形。")]),
(2,[("The **rationale** had a **kernel** of truth.","这套**理由**(rationale)倒也有几分真实的**内核**(kernel)。")]),
(2,[("Lemon juice is a **time-honoured** invisible ink,","柠檬汁是一种**由来已久的**(time-honoured)隐形墨水，"),
("and Wheeler made an **inventive** **leap** from paper to skin.","惠勒则做了一次**富有创意的**(inventive)**跳跃**(leap)，把它从纸上搬到了皮肤上。")]),
(2,[("His Polaroid **self-portrait** came out **devoid of** its subject,","他那张宝丽来**自拍照**(self-portrait)洗出来，**全无**(devoid of)本人的身影，"),
("a result he took as **conclusive**.","这个结果在他看来**确凿无疑**(conclusive)。")]),
(3,[("The security cameras **begged to differ**.","监控摄像头**恕难苟同**(begged to differ)。")]),
(3,[("On 19 April the eleven o'clock news","4月19日，11点新闻"),
("showed **viewers** the **damning** images,","向**观众**(viewers)播出了那些**足以定罪的**(damning)画面，"),
("and Wheeler was arrested shortly after midnight.","午夜刚过不久，惠勒就被捕了。")]),
(3,[("**Confronted with** the tapes,","**面对**(Confronted with)录像，"),
("he protested in **sheer** **disbelief** that he had worn the juice.","他在**极度的**(sheer)**难以置信**(disbelief)中辩称，自己明明抹了柠檬汁。")]),
(4,[("Reading about the case,","读到这个案子时，"),
("the Cornell psychologist David Dunning **pondered** a **disquieting** **proposition**.","康奈尔大学心理学家戴维·邓宁**思索**(pondered)起一个**令人不安的**(disquieting)**命题**(proposition)。")]),
(4,[("Perhaps **incompetence** can **cloak** itself,","也许，**无能**(incompetence)会把自身**掩盖**(cloak)起来，"),
("**robbing** people of the **discernment** to notice their **deficiencies**.","**剥夺**(robbing)人们察觉自身**不足**(deficiencies)的**辨别力**(discernment)。")]),
(5,[("For a 1999 paper, Dunning and his student Justin Kruger","为了1999年的一篇论文，邓宁和他的学生贾斯汀·克鲁格"),
("**quizzed** Cornell **undergraduates** on humour, grammar and **logical** reasoning.","就幽默、语法和**逻辑**(logical)推理**测试了**(quizzed)康奈尔的**本科生**(undergraduates)。")]),
(5,[("The bottom quarter of **scorers** averaged the 12th percentile","成绩垫底的四分之一**答题者**(scorers)，平均只处在第12百分位，"),
("but **generously** placed themselves near the 62nd,","却**慷慨地**(generously)把自己估在第62百分位附近，"),
("whereas **high achievers** showed **undue** **modesty**.","而**成绩优异者**(high achievers)却表现出**过分的**(undue)**谦虚**(modesty)。")]),
(5,[("The **unskilled**, the authors argued, bear a **dual** burden,","两位作者认为，**能力不足的**(unskilled)人背负着**双重**(dual)负担，"),
("since **appraisal** calls for the same skills as **execution**.","因为**评估**(appraisal)与**执行**(execution)需要的是同一套技能。")]),
(6,[("**Detractors** traced part of the Dunning-Kruger **disparity**","**批评者**(Detractors)把邓宁-克鲁格**差距**(disparity)部分地"),
("to regression to the mean,","归因于向均值回归，"),
("a statistical **mirage** the paper **partially** acknowledged.","这种统计**假象**(mirage)，论文本身也曾**部分地**(partially)承认过。")]),
(6,[("Studies designed to avoid it","专为避开这一问题而设计的研究"),
("still find a smaller but **tangible** effect.","仍发现了一个较小但**确实存在的**(tangible)效应。")]),
(6,[("In 2023 the pair **garnered** the Grawemeyer psychology award.","2023年，两人**赢得了**(garnered)格文美尔心理学奖。")]),
(7,[("**In fairness**, Wheeler had tested his method **empirically**","**平心而论**(In fairness)，惠勒确实**用实验**(empirically)检验过他的方法，"),
("before **staking** his **liberty** on it.","之后才把自己的**自由**(liberty)**押了上去**(staking)。")]),
(7,[("The camera that missed him","漏拍了他的那台相机，"),
("was the one he turned on himself.","恰恰是他对准自己的那一台。")]),
]
out={"no":"01","title_en":"The Robber Who Thought Lemon Juice Made Him Invisible","title_zh":"以为柠檬汁能隐身的劫匪",
"sentences":[{"para":p,"chunks":[{"en":e,"zh":z} for e,z in c]} for p,c in S]}
json.dump(out,open("scripts/01.json","w"),ensure_ascii=False,indent=1)
# validate
src=open("/home/user/postgraduate-vocabulary/新版定稿/01-the-robber-who-thought-lemon-juice-made-him-invisible.md").read()
body=src.split("## 英文")[1].split("## 中文")[0]
paras=[x.strip() for x in body.strip().split("\n\n")]
mine={}
for s in out["sentences"]: mine.setdefault(s["para"],[]).append(" ".join(c["en"] for c in s["chunks"]))
assert len(paras)==len(mine)
for i,p in enumerate(paras,1): assert " ".join(mine[i]).replace("**","")==p.replace("**",""),i
allb=re.findall(r"\*\*(.+?)\*\*",body); n=0
for s in out["sentences"]:
  for c in s["chunks"]:
    w=len(re.sub(r"\*","",c["en"]).split()); assert 3<=w<=14,(w,c["en"])
    for b in re.findall(r"\*\*(.+?)\*\*",c["en"]):
      assert c["zh"].count(f"({b})")==1 and re.search(r"\*\*[^*]+\*\*\("+re.escape(b)+r"\)",c["zh"]),(b,c); n+=1
    assert len(re.findall(r"\*\*[^*]+\*\*\(",c["zh"]))==len(re.findall(r"\*\*(.+?)\*\*",c["en"])),c
units=[b for s_ in out["sentences"] for c in s_["chunks"] for b in re.findall(r"\*\*(.+?)\*\*",c["en"])]
assert len(units)==len(allb) and all(w in u for w,u in zip(allb,units)),list(zip(allb,units))
print("OK bold",n,"chunks",sum(len(s["chunks"]) for s in out["sentences"]),"sentences",len(out["sentences"]))
