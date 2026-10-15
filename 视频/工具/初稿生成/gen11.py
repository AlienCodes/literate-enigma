import json,re,glob,os
# 第11篇初稿（逐词对照）：S = [(段, [chunk, ...])]，chunk = ([(英文组, 中文组), ...], 可选 note)
# 2026-10-15 程序打底：英文、重点词与文章逐字核对，重点词中文沿用文章定稿（铁律），只按《翻译风格》调格式（“的”“了”进粗体）。
# 08–10 用户定下的规矩一开始就照做：短语型用法整体标（T22：adjacent to、heralded … as、withdrew from、turned the tide），
# 习语整体标（用户 2026-10-15：“turn the tide……单独用一个 tide 不就是潮汐吗……要把这个整体做出来”）：撞词也保留，写进 allow_clash。
# 被隔开的意思每处都标（T23：与……紧邻、把……誉为），过去时“了”，顺着英文语序排（字不变），结尾解说（T28）。
# 2026-10-15 用户要求省 token：不再派多视角审校，程序核查 + 我只看程序拿不准的几处。
S=[
(1,[[[("Go is said to","据说围棋"),("allow","可能出现的"),("more **configurations** than the universe has **atoms**,","**局面**(configurations)比宇宙中的**原子**(atoms)还多，")]],
    [[("a **daunting**","这是一项**艰巨的**(daunting)"),("**computational** challenge.","**计算**(computational)挑战。")],
     "（be said to do：据说……；a daunting … challenge：同位语，说明前面整句）"]]),
(1,[[[("In October 2015","2015年10月，"),("DeepMind's AlphaGo","DeepMind 的 AlphaGo"),("reached a **milestone**,","达成了一个**里程碑**(milestone)，")]],
    [[("becoming","成为"),("the first program to beat a professional on a full board without a **handicap**.","首个在全尺寸棋盘上不**让子**(handicap)击败职业棋手的程序。")],
     "（becoming…：现在分词短语，补充说明这个里程碑；\nthe first program to do：第一个做……的程序）"]]),
(1,[[[("In March 2016","2016年3月，"),("its **opponent** in a **televised** Seoul **showdown**","在首尔一场**电视转播的**(televised)**对决**(showdown)中，它的**对手**(opponent)")]],
    [[("was Lee Sedol,","是李世石，"),("a South Korean **strategist**","一位善于**谋略**(strategist)的韩国棋手，"),("with 18 international titles.","拥有18个国际冠军头衔。")]]]),
(2,[[[("In game two, on 10 March,","第二局于3月10日进行，"),("AlphaGo's 37th move","AlphaGo 的第37手"),("was a shoulder hit,","是一记肩冲。")]],
    [[("a **tactic**","这种**招法**(tactic)是"),("placing a stone","把一枚棋子下在"),("**adjacent to** an opponent's on the **diagonal**.","对方棋子的**斜对角**(diagonal)，并**与**(adjacent to)之**紧邻**(adjacent to)。")],
     "（shoulder hit：肩冲，围棋术语；\na tactic placing…：同位语，解释 shoulder hit，placing… 作后置定语）"]]),
(2,[[[("On the **grid**'s fifth line,","落在**棋盘**(grid)的第五线上，"),("it","这一手"),("was hardly **orthodox**.","算不上**正统**(orthodox)下法。")]]]),
(2,[[[("Commentators","解说员"),("found","觉得"),("the **unexpected** **placement**","这步**出人意料的**(unexpected)**落子**(placement)"),("**bizarre**;","**十分怪异**(bizarre)；")]],
    [[("one","其中一人还"),("took it for a mistake.","以为是失误。")],
     "（find + 宾语 + 形容词：觉得……怎么样；take A for B：把A当成B）"]]),
(2,[[[("Lee","李世石"),("left the room,","离开了对局室，")]],
    [[("his **pause** for **deliberation**","他这次**暂停**(pause)**思考**(deliberation)"),("lasting over ten minutes.","持续了十多分钟。")],
     "（his pause … lasting…：独立主格，= and his pause … lasted…）"]]),
(3,[[[("DeepMind's **diagnostic** tools","DeepMind 的**诊断**(diagnostic)工具"),("showed","显示，")]],
    [[("AlphaGo","AlphaGo"),("had put the **odds** of a human playing that stone","曾把人类下出这一手的**概率**(odds)"),("at one in 10,000,","估算为万分之一，")]],
    [[("a **staggering** **rarity**.","**罕见**(rarity)得**惊人**(staggering)。")],
     "（put the odds of … at …：把……的概率估算为……；\na staggering rarity：同位语，补充说明这个概率）"]]),
(3,[[[("AlphaGo had first","AlphaGo 起初"),("learned to **imitate**","学习**模仿**(imitate)"),("strong **amateurs** online,","网上强**业余棋手**(amateurs)的下法，")]],
    [[("then","随后"),("**sharpened** its play over tens of millions of **simulated** games against itself.","通过数千万盘与自己的**模拟**(simulated)对局**磨炼了**(sharpened)棋艺。")]]]),
(3,[[[("Lee","李世石"),("later","后来"),("**acknowledged**","**承认了**(acknowledged)"),("the stone's **originality** and beauty.","这一手的**独创性**(originality)和美感。")]]]),
(4,[[[("The fourth game, on 13 March,","第四局于3月13日进行，"),("**reversed** the roles","双方角色**互换了**(reversed)，")]],
    [[("in **neat** **symmetry**.","形成**工整的**(neat)**对称**(symmetry)。")]]]),
(4,[[[("Lee's 78th move","李世石的第78手"),("**turned the tide**,","**扭转了局势**(turned the tide)，")]],
    [[("and many professionals","许多职业棋手"),("**heralded** it **as**","**把**(heralded as)它**誉为**(heralded as)"),("**divine**.","**神之一手**(divine)。")],
     "（herald A as B：把A誉为B；\ndivine：神的，神妙的，“神之一手”指围棋中绝妙的一手）"]]),
(4,[[[("DeepMind's team","DeepMind 团队"),("**computed**","**算出了**(computed)")]],
    [[("a professional's **likelihood** of finding it:","职业棋手找到这一手的**可能性**(likelihood)："),("about one in 10,000.","约为万分之一。")]]]),
(4,[[[("Lee's only win","李世石唯一的胜局，")]],
    [[("was","是"),("a **consolation** amid AlphaGo's **overwhelming** 4–1 victory.","AlphaGo 4比1**压倒性的**(overwhelming)胜利中的一点**安慰**(consolation)。")],
     "（amid：在……之中）"]]),
(5,[[[("In November 2019","2019年11月，"),("Lee","李世石"),("**withdrew from** the professional **circuit**,","**退出了**(withdrew from)职业**赛场**(circuit)，")]],
    [[("a **farewell** he tied","他把这次**告别**(farewell)"),("to","归因于"),("AI's **unrivalled** **dominance**.","人工智能**无可匹敌的**(unrivalled)**统治地位**(dominance)。")],
     "（a farewell he tied to…：同位语，说明前面整件事；\ntie A to B：把A和B联系起来，这里指把A归因于B）"]]),
(5,[[[("Calling AI an **invincible** **entity**,","称人工智能是**无法击败的**(invincible)**存在**(entity)，"),("he said","他说"),("the **summit** was beyond him.","自己已无法登上**顶峰**(summit)。")],
     "（Calling…：现在分词短语作伴随状语；call A B：称A为B；\nbe beyond sb：超出某人的能力）"]]),
(5,[[[("Yet","然而，"),("his one win came from a stone","为他赢下唯一一局的那一子，")]],
    [[("whose odds, by DeepMind's figures,","按 DeepMind 的数据，它的概率")]],
    [[("were as **slim** as those of AlphaGo's **audacious** shoulder hit.","和 AlphaGo 那记**大胆的**(audacious)肩冲一样**渺茫**(slim)。")],
     "（whose…：定语从句，修饰 a stone；by DeepMind's figures：插入语；\nas slim as those of…：those = the odds）\n（结局：第二局，AlphaGo 下出了人类只有万分之一可能会下的第37手；\n第四局，李世石也下出了职业棋手只有万分之一可能找到的第78手，\n并靠它赢下了五局里唯一的一局。李世石退役时说人工智能无法击败，\n可他唯一的胜利，恰恰来自一手和 AlphaGo 的肩冲一样罕见、\n一样大胆的棋：人类赢机器，用的正是机器赢人类的方式。）"]]),
]
CONF={"短语":{
 "S7 pause … for":"for deliberation 表目的（为思考而暂停），pause 本身就是“暂停”，意思不靠 for 产生（同 09 pleas for 的判法）",
 "S8 odds … of":"odds of sth 里 of 引出概率的内容，odds 本身就是“概率”，意思不靠 of 产生（同 10 involvement in 的判法）",
 "S13 likelihood … of":"likelihood of doing 里 of 引出可能发生的事，likelihood 本身就是“可能性”，意思不靠 of 产生（同 10 involvement in 的判法）",
 "S15 farewell … to":"to 属于 he tied … to（tie A to B），与 farewell 无关，本句不是 bid farewell to",
 "S17 slim … as":"as slim as 是 as … as 比较结构（和……一样渺茫），不是 slim 的固定搭配；中文“和……一样渺茫”与 slim 同组（T13）"},
 "口述":{"S6-2 觉得":"note 里“find + 宾语 + 形容词：觉得……怎么样”是句型说明本身，不是语音输入多出来的词"},
 "数字":{"S8-2 10,000":"one in 10,000 中文按习惯写“万分之一”（分数），读法 one in ten thousand","S13-2 10,000":"同 S8：about one in 10,000 → 约为万分之一"},
 "是的":{"S16-1 是**无法击败的**":"“是 + 无法击败的存在”是“是 + 定语 + 名词”（称A为B），不是“是……的”表语句式"}}
out={"no":"11","title_en":"Move 37","title_zh":"第37手","title_fx":{"hl":["37"],"ghost":[]},"sentences":[],"核对确认":CONF,"结尾解说":"结局","allow_clash":["turned the tide"]}   # T28
for p,chs in S:
    cs=[]
    for c in chs:
        al=[list(x) for x in c[0]]
        d={"en":" ".join(a for a,b in al if a!="\n"),"zh":"".join(b for a,b in al),"align":al}
        if len(c)>1: d["note"]=c[1]
        cs.append(d)
    out["sentences"].append({"para":p,"chunks":cs})
if os.path.exists("scripts/11.json"):                      # 保留后来写进脚本的核对确认、列举逗号、结尾句等（初稿程序只管句子）；核对确认合并，程序里写的这几条为准
    old=json.load(open("scripts/11.json"))
    for k_,v_ in old.items():
        if k_ == "核对确认":
            for kk,vv in v_.items(): out[k_].setdefault(kk,{}); out[k_][kk]={**vv,**out[k_][kk]}
        elif k_ not in ("no","title_en","title_zh","title_fx","sentences"): out[k_]=v_
json.dump(out,open("scripts/11.json","w"),ensure_ascii=False,indent=1)
art=open(glob.glob("/home/user/postgraduate-vocabulary/新版定稿/11-*.md")[0]).read()
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
