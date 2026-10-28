import json,re,glob,os
# 第30篇初稿（逐词对照）：S = [(段, [chunk, ...])]，chunk = ([(英文组, 中文组), ...], 可选 note)
# 2026-10-28 重点词中文沿用文章定稿（铁律），形容词“的”、动词“了”进粗体（28 用户改稿惯例）；非重点词也逐词对齐（G47）；三项并列加牛津逗号（T35）。
S=[
(1,[[[("In the","在"),("**fierce** heat","**酷热**(fierce)"),("of","的"),("summer 1858,","1858年夏天，"),("the curtains of the new Houses of Parliament","新落成的议会大厦里的窗帘"),("hung heavy with","浸透了"),("chloride of **lime**,","氯化**石灰**(lime)，")],
     "（hang heavy with…：沉甸甸地浸满……；\nchloride of lime：氯化石灰，即漂白粉）"],
    [[("a **bleach**","这是一种**漂白剂**(bleach)，"),("to make","用来让"),("the air","空气"),("**tolerable**.","变得**可以忍受**(tolerable)。")],
     "（a bleach…：同位语，补充说明 chloride of lime；\nmake + 宾语 + 形容词：使……变得……）"]]),
(1,[[[("The Thames","泰晤士河"),("**festered**,","正在**溃烂发臭**(festered)，"),("and","而"),("MPs","议员们"),("**contemplated**","**考虑**(contemplated)过"),("moving out.","搬离这里。")],
     "（contemplate doing…：考虑做……；\nMP：议员，即 Member of Parliament）"]]),
(2,[[[("The river","这条河"),("had become","已经成了"),("London's","伦敦的"),("**lavatory**.","**厕所**(lavatory)。")],
     "（had become：过去完成时，表示到那时已经……）"]]),
(2,[[[("**Antiquated**","**老旧的**(Antiquated)"),("sewers","下水道"),("and","和"),("**outlets**","**排污口**(outlets)"),("**discharged**","**排放**(discharged)"),("the **untreated**","**未经处理的**(untreated)"),("**sewage**","**污水**(sewage)，"),("of","它们来自"),("some three million","约三百万"),("city **dwellers**","城市**居民**(dwellers)，"),("into","排入"),("its **currents**,","河的**水流**(currents)中，")],
     "（discharge A into B：把 A 排放到 B 中；\nsome three million：约三百万，some 表示“大约”；\ncity dweller：城市居民）"],
    [[("where","在那里，"),("the **excrement**","**粪便**(excrement)"),("**stewed**","**闷沤**(stewed)"),("and","并"),("**decayed**.","**腐败**(decayed)。")],
     "（where…：非限制性定语从句，where 指 its currents；\nstew：炖，这里指在闷热中闷着、沤着）"]]),
(2,[[[("The **vile**","**污浊的**(vile)"),("**fumes**","**臭气**(fumes)"),("grew so","变得如此"),("**overpowering**","**令人难以招架**(overpowering)，"),("that","以至于"),("the episode","这段日子"),("earned","得到了"),("a name,","一个名字，"),("the Great Stink.","大恶臭。")],
     "（so…that…：如此……以至于……；\nthe Great Stink：同位语，补充说明 a name）"]]),
(3,[[[("**Disgust**","这股**厌恶**(Disgust)"),("found a voice","有了代言人，"),("on 15 July,","是在7月15日，")],
     "（find a voice：找到表达的出口，这里指有了代言人）"],
    [[("when","当时"),("the **Chancellor** of the Exchequer,","**财政大臣**(Chancellor)"),("Benjamin Disraeli,","本杰明·迪斯雷利"),("**denounced**","**痛斥**(denounced)"),("the river","这条河"),("as","是"),("a **hellish** pool","一潭**地狱般的**(hellish)池水，"),("of **unbearable** horrors.","满是**令人无法忍受的**(unbearable)恐怖。")],
     "（the Chancellor of the Exchequer：英国财政大臣；\nBenjamin Disraeli：同位语，补充说明 the Chancellor；\ndenounce A as B：痛斥 A 是 B）"]]),
(3,[[[("A bill funding new sewers","一项为新下水道拨款的法案"),("was **fast-tracked**","被**快速推进**(fast-tracked)，"),("into law","成为法律，"),("in about 18 days.","只用了约18天。")],
     "（funding new sewers：现在分词短语作后置定语，修饰 a bill；\nfast-track A into law：加快把 A 变成法律）"]]),
(4,[[[("The engineer","工程师"),("Joseph Bazalgette","约瑟夫·巴泽尔杰特"),("**masterminded**","**主持策划了**(masterminded)"),("the response.","这次应对。")],
     "（mastermind：策划，主持）"]]),
(4,[[[("His","他修建的"),("82 miles of","82英里"),("**stout**","**坚固的**(stout)"),("intercepting sewers","截流下水道"),("caught","截住了"),("the flow","污水，"),("short of the river","在它入河之前，")],
     "（82 miles of…：82英里长的……；\nintercepting sewer：截流下水道；\nshort of…：在到达……之前）"],
    [[("and **diverted** it","并把它**改道**(diverted)"),("east,","向东，"),("**downstream** of the city.","送往城市**下游**(downstream)。")],
     "（divert：使改道；downstream of…：在……的下游）"]]),
(4,[[[("With","有"),("some 1,100 miles of","约1,100英里的"),("street sewers","街道下水道"),("as **tributaries**,","作为**支流**(tributaries)，")],
     "（with A as B：以 A 作为 B，with 复合结构作状语）"],
    [[("the **infrastructure**","整套**基础设施**(infrastructure)"),("took","用了"),("318 million","三亿一千八百万块"),("**bricks**.","**砖块**(bricks)。")],
     "（take：这里指耗用，需要）"]]),
(4,[[[("Having calculated","先算出"),("an **adequate** **calibre** for each pipe,","每条管道**足够的**(adequate)**管径**(calibre)，"),("he","他"),("doubled it.","再把它加倍。")],
     "（Having calculated…：现在分词完成式作状语，\n表示动作先于 doubled 发生）"]]),
(4,[[[("The **backbone**","系统的**主干**(backbone)"),("lies **buried**","就**埋藏**(buried)在"),("**underneath** the **newly** built Victoria, Albert, and Chelsea Embankments.","**新近**(newly)修成的维多利亚、阿尔伯特和切尔西河堤**之下**(underneath)。")],
     "（lie buried：埋藏着，lie + 过去分词表示处于某种状态；\nEmbankment：河堤，泰晤士河沿岸的堤岸大道）"]]),
(4,[[[("**Substantially** complete by 1875,","到1875年已**基本**(Substantially)完工，"),("much of the network","这套管网的大部分"),("is in use today.","至今仍在使用。")],
     "（Substantially complete by 1875：形容词短语作状语，\n逻辑主语是 the network；in use：在使用中）"]]),
(5,[[[("Yet","然而，"),("that **sanitation**","这套**卫生设施**(sanitation)"),("rested on","建立在"),("a **fallacy**.","一个**谬误**(fallacy)之上。")],
     "（rest on…：建立在……之上，以……为基础）"]]),
(5,[[[("The **predominant** **belief**,","当时**占主导地位的**(predominant)**看法**(belief)"),("miasma,","是瘴气说，"),("blamed disease on","把疾病归咎于"),("foul air","污浊的空气"),("and **vapours**,","和**秽气**(vapours)，")],
     "（miasma：瘴气说，同位语，补充说明 belief；\nblame A on B：把 A 归咎于 B）"],
    [[("so","所以"),("the sewers","下水道"),("were intended","修建的目的"),("**principally**","**主要**(principally)"),("to **suppress**","是为了**压住**(suppress)"),("the smell.","臭味。")],
     "（be intended to do：目的是做……，打算用来……）"]]),
(5,[[[("They","它们"),("worked","奏效，"),("for","却是出于"),("an **unintended** reason,","一个**意料之外的**(unintended)原因，")],
     "（work：这里指奏效，起作用）"],
    [[("guarding","那就是守住了"),("the **purity** of the water Londoners drank.","伦敦人饮用水的**洁净**(purity)。")],
     "（guarding…：现在分词短语，解释 reason；\nthe water Londoners drank：省略 that 的定语从句）"]]),
(6,[[[("Cholera","霍乱"),("**resurfaced**","**卷土重来**(resurfaced)"),("in 1866","于1866年，"),("and killed","夺去了"),("about 5,600 people","约5,600人的生命，"),("in the East End,","在伦敦东区，")],
     "（the East End：伦敦东区）"],
    [[("the one **locality** not yet connected.","那是唯一尚未接入的**地区**(locality)。")],
     "（the one locality…：同位语，补充说明 the East End；\nnot yet connected：过去分词短语作后置定语）"]]),
(7,[[[("A remedy aimed at the nose","一项冲着鼻子去的补救措施，"),("protected","护住的却是"),("the gut.","肠胃。")],
     "（aimed at…：过去分词短语作后置定语，修饰 remedy；\nthe gut：肠胃，与 the nose 对比）\n"
     "（简述：1858年夏天酷热，伦敦约三百万居民的污水直接排进泰晤士河，\n"
     "臭气熏天，史称大恶臭；议会大厦的窗帘浸满氯化石灰，议员们考虑过搬走。\n"
     "7月15日，财政大臣迪斯雷利痛斥这条河，修新下水道的法案约18天成为法律。\n"
     "工程师巴泽尔杰特修了82英里截流下水道，把污水截住送往城市下游，\n"
     "另有约1,100英里街道下水道汇入，用砖三亿一千八百万块，管径算出后再加倍，\n"
     "到1875年基本完工，大部分至今仍在使用。当时人们相信瘴气说，\n"
     "修下水道主要为了除臭，它奏效却是因为守住了饮用水的洁净。\n"
     "1866年霍乱再起，夺去约5,600人生命的东区，正是唯一尚未接入的地区。）"]]),
]
CONF={"牛津逗号":{},
"合组":{
 "S1 the curtains of the new Houses of Parliament":"对齐不了：of 结构作后置定语，中文“新落成的议会大厦里的窗帘”定语必须提前，拆开后中文语序就乱了",
 "S7 A bill funding new sewers":"对齐不了：funding new sewers 是现在分词短语作后置定语，中文“为新下水道拨款的法案”定语必须提前",
 "S11 an adequate calibre for each pipe":"对齐不了：for each pipe 中文“每条管道的”必须放在“足够的管径”前面",
 "S12 underneath the newly built Victoria, Albert, and Chelsea Embankments.":"对齐不了：underneath 中文是方位词“……之下”，必须放在“河堤”后面",
 "S13 Substantially complete by 1875":"对齐不了：by 1875 中文“到1875年”必须放在“基本完工”前面",
 "S13 is in use today":"对齐不了：today 中文“至今”必须放在“仍在使用”前面",
 "S16 the purity of the water Londoners drank":"对齐不了：the purity of A 中文“A 的洁净”，of 结构语序必须倒过来",
 "S17 the one locality not yet connected":"对齐不了：not yet connected 是后置定语，中文“唯一尚未接入的地区”定语必须提前",
 "S18 A remedy aimed at the nose":"对齐不了：aimed at the nose 是后置定语，中文“冲着鼻子去的补救措施”定语必须提前"}}
out={"no":"30","title_en":"The Stink That Built London's Sewers","title_zh":"大恶臭逼出了下水道","title_fx":{"hl":["Stink","Sewers"],"ghost":[]},"sentences":[],"核对确认":CONF,"结尾解说":"简述",
     "高亮按实际开口":True,"高亮开口门槛":40,
     "术语":{"Houses of Parliament":"议会大厦","Thames":"泰晤士河","London":"伦敦","Londoners":"伦敦人","Great Stink":"大恶臭","Exchequer":"财政部","Benjamin Disraeli":"本杰明·迪斯雷利","Joseph Bazalgette":"约瑟夫·巴泽尔杰特","Victoria":"维多利亚","Albert":"阿尔伯特","Chelsea":"切尔西","Embankments":"河堤","East End":"伦敦东区"}}
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 核对 import 生成并核对
生成并核对(S, out)
