import json,re,glob
# 第06篇初稿（逐词对照）：S = [(段, [chunk, ...])]，chunk = ([(英文组, 中文组), ...], 可选 note)
S=[
(1,[[[("Wilhelm von Osten,","威廉·冯·奥斯滕，"),("a mathematics teacher and **trainer** in Berlin,","柏林的一位数学教师兼**驯马师**(trainer)，")]],
    [[("owned a **stallion**,","拥有一匹**公马**(stallion)，"),("Hans.","名叫汉斯。")]]]),
(1,[[[("Asked to","当被要求"),("**calculate** a sum,","**计算**(calculate)一道算术题、")],"（Asked to…：过去分词短语作状语，= When he was asked to…）"],
    [[("attempt **subtraction**,","试做**减法**(subtraction)"),("or name a date,","或说出一个日期时，")]],
    [[("Hans","汉斯"),("tapped out the answer with a hoof.","就会用一只蹄子把答案敲出来。")]]]),
(1,[[[("Such **aptitude**","这样的**天资**(aptitude)"),("suggested **brilliance**,","暗示着它的**聪慧**(brilliance)，")]],
    [[("and **demonstrations** in his owner's **courtyard**","在它主人**庭院**(courtyard)里的**展示**(demonstrations)"),("made him seem **intelligent**.","也让它显得很**聪明**(intelligent)。")]]]),
(1,[[[("The New York Times","《纽约时报》"),("reported the **stunning** act in 1904.","在1904年报道了这场**令人惊叹的**(stunning)表演。")]]]),
(2,[[[("A **commission** of thirteen","一个由十三人组成的**委员会**(commission)"),("was formed","被组建起来，"),("to **investigate**.","进行**调查**(investigate)。")]]]),
(2,[[[("It included","委员会成员包括"),("a **veterinarian**,","一名**兽医**(veterinarian)、"),("a circus manager,","一名马戏团经理、")]],
    [[("a **cavalry** officer,","一名**骑兵**(cavalry)军官、"),("schoolteachers,","几名中小学教师")]],
    [[("and the director of the Berlin **zoological** garden.","以及柏林**动物**(zoological)园的园长。")]]]),
(2,[[[("Its members","委员们"),("looked for","查找"),("**trickery**","有没有**诡计**(trickery)"),("and **collusion**.","和**串通**(collusion)。")]]]),
(2,[[[("In September 1904","1904年9月，"),("they","他们"),("found no **deception**,","没有发现任何**骗局**(deception)，")]],
    [[("in effect","这实际上等于"),("**certifying**","**认证了**(certifying)"),("the act **authentic**.","这场表演**真实可信**(authentic)。")],"（in effect：实际上；certify sth + 形容词：证明某物……；分词作结果状语）"]]),
(3,[[[("In 1907","1907年，"),("the **psychologist**","**心理学家**(psychologist)"),("Oskar Pfungst","奥斯卡·普丰斯特")]],
    [[("tested the act **systematically**,","**系统地**(systematically)测试了这场表演，")]],
    [[("altering one **variable** after another.","一个接一个地改变**变量**(variable)。")],"（altering…：分词作伴随状语；one … after another：一个接一个）"]]),
(3,[[[("He","他"),("kept onlookers away,","不让围观者靠近，"),("**rotated** **questioners**,","**轮换**(rotated)**提问者**(questioners)，")]],
    [[("fitted **blinders**,","给马戴上**眼罩**(blinders)，"),("and sometimes","有时还"),("used people **ignorant** of the answer.","找对答案**一无所知的**(ignorant)人（来提问）。")],"（ignorant of sth：不知道某事的；people ignorant of… 是后置定语）"]]),
(3,[[[("When Hans","当汉斯"),("could see the questioner,","能看见提问者时，")]],
    [[("he answered **correctly** 50 times in 56.","它在56次里有50次回答**正确**(correctly)。")]]]),
(3,[[[("With the questioner **invisible**,","当提问者**不可见**(invisible)时，")],"（with + 名词 + 形容词：在……的情况下；invisible 指汉斯看不见提问者）"],
    [[("his **accuracy**","它的**准确率**(accuracy)"),("fell to two in 35.","降到了35次里只对两次。")]]]),
(4,[[[("The **cues**","这些**提示**(cues)"),("came from the questioners.","来自提问者。")]]]),
(4,[[[("Each","每个提问者"),("would **lean** forward as tapping began,","都会在敲击开始时向前**倾身**(lean)，")]],
    [[("and **tension** rose as the taps neared the answer.","敲击越接近答案，**紧张**(tension)感就越强。")],"（as：随着，表示两件事同时变化）"]]),
(4,[[[("At the right tap","敲到正确的那一下时，"),("it eased,","紧张感就缓和下来，")]],
    [[("and the questioner","提问者"),("would **straighten**","会**挺直**(straighten)身子"),("or **jerk** the head upward.","或者把头向上**猛地一抬**(jerk)。")],"（straighten 后面省略了宾语；jerk the head upward：把头猛地往上一抬）"]]),
(4,[[[("Every **gesture**","每一个**手势**(gesture)"),("and **motion**","和**动作**(motion)"),("was **subconscious**,","都是**下意识的**(subconscious)，")]],
    [[("made **innocently** by people with no wish to **deceive**.","是那些毫无**欺骗**(deceive)之意的人**无心地**(innocently)做出的。")],"（made … 是过去分词短语，补充说明这些动作；with no wish to do：并不想做……）"]]),
(5,[[[("**Double-blind** designs in **psychology** and animal **cognition**","**心理学**(psychology)和动物**认知**(cognition)研究中的**双盲**(Double-blind)设计")]],
    [[("guard against the Clever Hans effect,","用来防范聪明汉斯效应，")]],
    [[("a **phenomenon** of **bias**","这是一种**偏差**(bias)**现象**(phenomenon)，")]],
    [[("in which **expectancy** shapes **behavioural** results.","在这种现象中，**预期**(expectancy)会影响**行为**(behavioural)结果。")],"（a phenomenon of bias 是 the Clever Hans effect 的同位语；in which = in this phenomenon）"]]),
(5,[[[("In the laboratory,","在实验室里，"),("Pfungst","普丰斯特"),("took the animal's place","代替了那匹马的位置，")]],
    [[("and proved **sensitive** to the cues of **attentive** volunteers.","结果证明，他对**专注的**(attentive)志愿者给出的提示也很**敏感**(sensitive)。")],"（prove + 形容词：结果证明是……；sensitive to：对……敏感）"]]),
(5,[[[("Hans","汉斯"),("went, on his owner's death in June 1909,","在它的主人于1909年6月去世后，")],"（went … to：归……所有；on his owner's death 插在 went 和 to 之间）"],
    [[("to a **jeweller**","归了一位**珠宝商**(jeweller)，"),("still convinced that such animals reasoned.","这位珠宝商仍然坚信这类动物会推理。")]]]),
]
out={"no":"06","title_en":"The Horse That Could Count","title_zh":"会算术的马","title_fx":{"hl":["Horse","Count"],"ghost":[]},"sentences":[]}
for p,chs in S:
    cs=[]
    for c in chs:
        al=[list(x) for x in c[0]]
        d={"en":" ".join(a for a,b in al if a!="\n"),"zh":"".join(b for a,b in al),"align":al}
        if len(c)>1: d["note"]=c[1]
        cs.append(d)
    out["sentences"].append({"para":p,"chunks":cs})
json.dump(out,open("scripts/06.json","w"),ensure_ascii=False,indent=1)
art=open(glob.glob("/home/user/postgraduate-vocabulary/新版定稿/06-*.md")[0]).read()
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
g=[a for s in out["sentences"] for c in s["chunks"] for a,z in c["align"]]
print('句数',len(out["sentences"]),'chunk',sum(len(s["chunks"]) for s in out["sentences"]),'组',len(g),'每组英文词',round(sum(len(re.sub(r"\*\*","",a).split()) for a in g)/len(g),2),'note',sum(1 for s in out["sentences"] for c in s["chunks"] if c.get("note")))
