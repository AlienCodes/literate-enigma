import json,re,glob
# 第07篇初稿（逐词对照）：S = [(段, [chunk, ...])]，chunk = ([(英文组, 中文组), ...], 可选 note)
# 2026-10-09 按现行做法：程序打底（英文、重点词与文章逐字核对），按 01–06 定稿风格一次成稿，再做两视角独立审校。
S=[
(1,[[[("One night in early 2016,","2016年初的一个夜晚，")]],
    [[("after","在"),("**keepers** at New Zealand's National Aquarium in Napier","新西兰内皮尔国家水族馆的**饲养员**(keepers)"),("had left,","离开之后，")]],
    [[("an octopus named Inky","一只名叫Inky的章鱼")]],
    [[("**crept** through an **aperture** in the **mesh** **atop** its tank.","从水箱**顶部**(atop)**网罩**(mesh)上的一道**开口**(aperture)**悄悄爬了出去**(crept)。")]]]),
(1,[[[("The **fugitive**","这名**逃犯**(fugitive)"),("**presumably**","**想必**(presumably)"),("dropped","落到了"),("to the floor,","地上，")]],
    [[("crossed","穿过了"),("the room,","房间，")]],
    [[("and","然后"),("**compressed** its **elastic** body","把它**有弹性的**(elastic)身体**挤**(compressed){{（压缩/挤压）|compressed}}"),("into a drain,","进了一个排水口，")]],
    [[("whose pipe","排水口的管道"),("**stretched** some 50 metres","**延伸**(stretched)约50米，"),("to the Pacific.","通到太平洋。")],"（whose pipe…：非限制性定语从句，whose pipe = the drain's pipe）"]]),
(2,[[[("Staff","工作人员"),("**reconstructed** that route from the **slime** **residue** it **deposited**.","根据它**留下**(deposited)的**黏液**(slime)**残迹**(residue)，**还原了**(reconstructed){{（使重现）|reconstructed}}这条路线。")]]]),
(2,[[[("Inky","Inky"),("had **resided** in **captivity** since 2014,","从2014年起就一直**居住**(resided)在**圈养**(captivity)环境中；")]],
    [[("when","那一年，"),("a fisherman","一名渔民"),("**retrieved** it from a **crayfish pot** off Napier.","从内皮尔附近海域的一个**捕龙虾的笼子**(crayfish pot){{（专门捕虾的笼子）|crayfish pot}}里**取出了**(retrieved)它。")],"（since 2014, when…：when 引出非限制性定语从句，说明2014年发生的事）"]]),
(2,[[[("The **breakout**","这次**越狱**(breakout)"),("went **unreported** for about three months.","大约三个月都**没有被报道**(unreported)。")],"（go + 形容词：处于某种状态；go unreported：没有被报道）"]]),
(2,[[[("Made public in April 2016,","2016年4月被公开之后，"),("the story","这个故事"),("travelled the **globe**.","传遍了**全球**(globe)。")],"（Made public…：过去分词短语作状语，= After it was made public…）"]]),
(3,[[[("Such **agility**","这样**灵巧的身手**(agility){{（动作敏捷）|agility}}"),("**stems** from","**源于**(stems)"),("an octopus's **pliable** body,","章鱼**柔韧的**(pliable)身体，")]],
    [[("which","这种身体"),("has no **skeleton**","没有**骨骼**(skeleton)，"),("or shell.","也没有外壳。")]]]),
(3,[[[("Its only","它唯一"),("hard part","坚硬的部位"),("is its **beak**,","是**喙**(beak)，")]],
    [[("so","所以"),("any **crevice** that **accommodates** the beak","任何**容得下**(accommodates)喙的**缝隙**(crevice)"),("will do.","都行。")],"（will do：行得通，够用）"]]),
(3,[[[("Roughly two-thirds of its 500 million **neurons**","它的5亿个**神经元**(neurons)中，大约三分之二"),("lie in the **limbs**,","位于**腕足**(limbs)里；")]],
    [[("which","腕足"),("handle","处理"),("**sensory** input","**感官**(sensory)信息，")]],
    [[("and react","并且在作出反应时"),("with some **autonomy**.","有一定的**自主性**(autonomy)。")]]]),
(4,[[[("Its **wits**","它的**机智/智慧**(wits)"),("are as **versatile** as its **anatomy**.","和它的**身体构造**(anatomy)一样**用途广泛**(versatile)。")]]]),
(4,[[[("A giant Pacific octopus in Seattle","西雅图的一只巨型太平洋章鱼"),("learned","学会了"),("to open","打开"),("screw-top **jars**,","螺旋盖的**罐子**(jars)，")]],
    [[("needing 15 minutes **at the outset**,","**起初/最开始的时候**(at the outset)需要15分钟，"),("later about two.","后来大约要两分钟。")],"（needing…：分词短语作伴随状语；later about two 省略了 needing … minutes）"]]),
(4,[[[("In a 2010 study,","在2010年的一项研究中，"),("octopuses","章鱼"),("came to","逐渐能够"),("**discriminate** between two strangers,","**区分**(discriminate)两个陌生人，")]],
    [[("a **feeder**","一个是**喂食者**(feeder)，"),("and one","另一个"),("who touched them with a bristly stick,","用带刺毛的棍子碰它们；")]],
    [[("**adopting** a different **hue** and **posture** for each.","章鱼对每个人**呈现出**(adopting)不同的**颜色**(hue)和**姿态**(posture)。")],"（adopting…：分词短语作伴随状语，说明章鱼区分两人时的表现）"]]),
(5,[[[("In July 2012","2012年7月，"),("the Cambridge Declaration on Consciousness","《剑桥意识宣言》"),("listed octopuses","把章鱼列入了")]],
    [[("among animals **possessing** the **neurological** **substrates** for **conscious** **awareness**.","**具备**(possessing)**神经**(neurological)**基质**(substrates)的动物之列，这种神经基质专门用来**有意识的**(conscious)**认识**(awareness)。")],"（possessing…：现在分词短语作后置定语，修饰 animals）"]]),
(5,[[[("A November 2021","2021年11月，"),("UK government review","英国政府的一份评估报告"),("recommended","建议"),("treating them as","认定它们"),("**sentient**,","**有感知力**(sentient)；")]],
    [[("and","而"),("the Animal Welfare (Sentience) Act","《动物福利（感知）法》"),("**encompassed** them in April 2022.","于2022年4月把它们**纳入了/包括**(encompassed)其中。")]]]),
(5,[[[("None of this","这些都不能"),("proves","证明"),("an **inner** life.","（章鱼）有**内心**(inner)世界。")]]]),
(5,[[[("Inky,","Inky"),("somewhere beyond the pipe,","在管道另一头的某个地方，")]],
    [[("remained","始终"),("**wholly** **oblivious** to the debate.","对这场争论**全然**(wholly)**不知**(oblivious)。")],"（remain + 形容词：仍然处于某种状态；oblivious to：对……毫无察觉）"]]),
]
out={"no":"07","title_en":"The Octopus That Escaped","title_zh":"越狱的章鱼","title_fx":{"hl":["Octopus","Escaped"],"ghost":[]},"sentences":[]}
out["换行变更已获同意"]={"S7":"用户 2026-10-09 原话：“那严格按照我这个word文档里面这个方式来……严格按照我这个word文档来”——S7 按用户 Word 加了（动作敏捷），这一屏中文变长，自动换行随之改变"}
out["核对确认"]={"牛津逗号":{
  "S7 an octopus's pliable body, which has no skeleton or":"不是并列：no skeleton or shell 只有两项",
  "S9 lie in the limbs, which handle sensory input and":"不是并列：逗号后是定语从句，handle … and react … 只有两项",
  "S12 discriminate between two strangers, a feeder and":"不是并列：逗号后是同位语，a feeder and one who… 只有两项",
  "S12 with a bristly stick, adopting a different hue and":"不是并列：逗号后是分词短语，hue and posture 只有两项"},
 "数字":{"S9-1 500":"500 million 译作“5亿”，数值正确"},
 "牛津逗号改动":{"S2":"原文 dropped to the floor, crossed the room and compressed… 是三项并列，按 T18 加牛津逗号：crossed the room, and compressed（文章原文同步改）"}}
for p,chs in S:
    cs=[]
    for c in chs:
        al=[list(x) for x in c[0]]
        d={"en":" ".join(a for a,b in al if a!="\n"),"zh":"".join(b for a,b in al),"align":al}
        if len(c)>1: d["note"]=c[1]
        cs.append(d)
    out["sentences"].append({"para":p,"chunks":cs})
json.dump(out,open("scripts/07.json","w"),ensure_ascii=False,indent=1)
art=open(glob.glob("/home/user/postgraduate-vocabulary/新版定稿/07-*.md")[0]).read()
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
