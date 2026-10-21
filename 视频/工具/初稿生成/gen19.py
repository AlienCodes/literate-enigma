import json,re,glob,os
# 第19篇初稿（逐词对照）：S = [(段, [chunk, ...])]，chunk = ([(英文组, 中文组), ...], 可选 note)
# 2026-10-16 程序打底：英文、重点词与文章逐字核对，重点词中文沿用文章定稿（铁律），只按《翻译风格》调格式（“的”“了”进粗体）。
# 08–12 用户定下的规矩一开始就照做：过去时“了”、顺着英文语序排、代词译出（their→他们的）、英文没有引号中文不加、结尾解说（T28）、术语不漏（T30）、
#   短语型用法整体标（T22：piled up、shorthand for、relied on、preached against），被隔开的中文意思每处都标（T23：劝诫……戒除）。
S=[
(1,[[[("In the winter of 1636–37,","1636至1637年的冬天，"),("Dutch **merchants** and **brokers**","荷兰的**商人**(merchants)和**经纪人**(brokers)"),("met in **taverns**","聚在**小酒馆**(taverns)里，")]],
    [[("to trade **contracts** for **tulip** bulbs still in the ground,","买卖尚埋在地下的**郁金香**(tulip)球茎的**合同**(contracts)。")]],
    [[("a **speculative** business","这是一门**投机**(speculative)生意，"),("they called windhandel,","他们称之为windhandel，"),("\"trading in the wind\".","也就是“风中交易”。")],
     "（still in the ground：后置定语，修饰 tulip bulbs；\na speculative business…：同位语，补充说明这种买卖）"]]),
(1,[[[("Prices of prized \"broken\" tulips, with **streaked** **petals**,","名贵的“碎色”郁金香**花瓣**(petals)**带有条纹**(streaked)，价格"),("**soared**.","一路**飙升**(soared)。")],
     "（with streaked petals：介词短语作插入语，说明碎色郁金香的样子）"]]),
(2,[[[("In early February 1637,","1637年2月初，"),("at a sale in Haarlem, the **hub** of the trade,","在郁金香交易的**中心**(hub)哈勒姆，一场交易会上"),("no one would **bid**.","无人**出价**(bid)。")],
     "（the hub of the trade：同位语，说明 Haarlem；\nwould：表示过去的意愿，no one would bid 即没有人愿意出价）"]]),
(2,[[[("Days later,","几天后，"),("at an **auction** in Alkmaar,","在阿尔克马尔的一场**拍卖会**(auction)上，"),("one bulb","一只球茎"),("still fetched 5,200 guilders,","仍卖出了5,200荷兰盾——")]],
    [[("the Dutch **currency** of the day,","当时荷兰的**货币**(currency)——"),("more than a decade's **wages** for a skilled craftsman.","比一名熟练工匠十多年的**工钱**(wages)还多。")],
     "（fetch：卖得某个价钱；the Dutch currency of the day：同位语，说明 guilders；\nmore than…：同位语，换算这笔钱）"]]),
(2,[[[("But","但"),("the **frenzy**","这股**狂潮**(frenzy)"),("was over.","已是强弩之末。")]]]),
(2,[[[("Prices **collapsed**,","价格**暴跌**(collapsed)，"),("many buyers **defaulted**,","许多买家**违约**(defaulted)，"),("and **unsettled** contracts **piled up**.","**悬而未决的**(unsettled)合同**越积越多**(piled up)。")]]]),
(2,[[[("Why the market turned so **swiftly**","市场为何转向得如此**迅速**(swiftly)，"),("is still **contested**.","至今仍**众说纷纭**(contested)。")],
     "（Why…swiftly：主语从句，作句子的主语）"]]),
(3,[[[("Two centuries later,","两个世纪后，"),("Charles Mackay, a Scottish **journalist**,","苏格兰**记者**(journalist)查尔斯·麦凯")]],
    [[("**recounted** the **episode** in a book on popular delusions,","在一本论述大众错觉的书中**讲述了**(recounted)这段**往事**(episode)，")]],
    [[("casting it as national **hysteria**.","把它写成一场举国上下的**集体歇斯底里**(hysteria)。")],
     "（a Scottish journalist：同位语，说明 Charles Mackay；\ncasting…：现在分词短语作伴随状语；cast A as B：把A描绘成B）"]]),
(3,[[[("In his telling,","照他的说法，"),("rich and poor **gambled**,","富人穷人都在**豪赌**(gambled)，")]],
    [[("great merchants","大商人"),("were reduced almost to begging,","几乎沦落到乞讨的地步，"),("and Dutch **commerce** **reeled**.","荷兰的**商业**(commerce)**大受震荡**(reeled)。")],
     "（In his telling：照他的说法，后面三件事都是麦凯的说法；\nbe reduced to doing：沦落到……的地步）"]]),
(3,[[[("His **vivid** account","他的描述**绘声绘色**(vivid)，"),("made tulip **mania**","从此郁金香**狂热**(mania)成了"),("**shorthand for** **bubbles**","**泡沫**(bubbles)的**代名词**(shorthand for)，")]],
    [[("fuelled by **reckless** buying.","专指由**不计后果的**(reckless)抢购吹大的泡沫。")],
     "（make A B：使A成为B；\nshorthand for…：……的代名词，……的简称；\nfuelled by…：过去分词短语作后置定语，修饰 bubbles）"]]),
(4,[[[("Yet","然而，"),("the **archives**","**档案**(archives)"),("tell a smaller story.","讲述的故事要小得多。")]]]),
(4,[[[("Mackay's story","麦凯的故事"),("**relied** largely **on**","所**依据**(relied on)的，大多是"),("**satirical** **pamphlets** of 1637","1637年的**讽刺**(satirical)**小册子**(pamphlets)，")]],
    [[("that **preached** **against** **greed**.","这些小册子意在**劝诫**(preached against)世人**戒除**(preached against)**贪婪**(greed)。")],
     "（rely on：依靠，依据；\nthat…：定语从句，修饰 pamphlets；\npreach against：劝诫勿……）"]]),
(4,[[[("Anne Goldgar, a **historian** at King's College London,","伦敦国王学院的**历史学家**(historian)安妮·戈德加")]],
    [[("**scoured** Dutch records","**遍查了**(scoured)荷兰的文献记录，"),("and counted only a few hundred traders,","只数出了几百名交易者，"),("mostly merchants and craftsmen.","大多是商人和工匠。")],
     "（a historian at King's College London：同位语，说明 Anne Goldgar；\nmostly merchants and craftsmen：补充说明这些交易者）"]]),
(4,[[[("She found no **bankruptcy** caused by tulips","她没有找到一桩因郁金香而起的**破产**(bankruptcy)，")]],
    [[("and no **measurable** **harm** to the **economy**.","也没有发现荷兰**经济**(economy)受到任何**可以衡量的**(measurable)**损害**(harm)。")],
     "（caused by tulips：过去分词短语作后置定语，修饰 bankruptcy；\nno … harm to sth：对某物没有……损害）"]]),
(4,[[[("Many buyers","许多买家"),("were later allowed","后来获准")]],
    [[("to **settle** their contracts by paying a small **fraction** of the price,","只付价格的**一小部分**(fraction)，就能**了结**(settle)他们的合同，"),("and few were ruined.","倾家荡产的人也寥寥无几。")],
     "（be allowed to do：获准做……；\nby doing：通过……的方式；\nfew：很少的人，几乎没有人）"]]),
(5,[[[("The **boom**","这场**繁荣**(boom)"),("was real","确有其事，"),("but **fleeting**.","却**转瞬即逝**(fleeting)。")]]]),
(5,[[[("What spread,","真正传开、"),("and still **circulates** nearly four centuries on,","在近四个世纪后仍在**流传**(circulates)的，"),("was the **moral**:","是其中的**寓意**(moral)——")]],
    [[("a **sermon** drawn from those pamphlets","一篇取材于那些小册子的**训诫**(sermon)，"),("and retold by Mackay as history.","被麦凯当作历史重新讲了一遍。")],
     "（What spread…：主语从句；\nnearly four centuries on：近四个世纪之后；\na sermon…：同位语，说明 the moral；\ndrawn from… 和 retold by… 都是过去分词短语，修饰 sermon）\n"
     "（结局：1637年2月初，郁金香价格暴跌，许多买家违约；\n后来许多买家只付价格的一小部分就了结了合同，\n倾家荡产的人寥寥无几，\n荷兰经济也没有受到可以衡量的损害。\n两个世纪后，麦凯把它写成举国上下的集体歇斯底里，\n郁金香狂热从此成了泡沫的代名词。\n泡沫确有其事，却转瞬即逝；\n流传近四个世纪的，\n是取材于讽刺小册子、劝诫贪婪的寓意。）"]]),
]
CONF={"牛津逗号":{"S1 37, Dutch merchants and":"不是三项并列：In the winter of 1636–37 是时间状语，merchants and brokers 只有两项",
   "S9 In his telling, rich and":"In his telling 是状语，rich and poor 只有两项；本句三个分句并列已在 and Dutch commerce 前加牛津逗号（文章英文同步）",
   "S13 at King's College London, scoured Dutch records and":"不是三项并列：a historian at King's College London 是同位语，scoured … and counted 只有两项",
   "S13 a few hundred traders, mostly merchants and":"不是三项并列：mostly merchants and craftsmen 是同位语，补充说明 traders，merchants and craftsmen 只有两项"},
 "短语":{"S1 in … taverns":"met in taverns 里 in 是普通地点介词（在小酒馆里），不是 in + 名词的固定用法（in flocks 一类）",
   "S3 hub … of":"the hub of the trade 里 of 只引出所属（交易的中心），hub 本身就是“中心”，意思不靠 of 产生（同 16 beads … of 的判法）",
   "S4 currency … of":"of the day 是“当时的”，修饰 currency，currency 本身就是“货币”，不是 currency of 的固定搭配",
   "S10 mania … for":"tulip mania 是宾语，后面 shorthand for 已整体标；mania 与 for 不相连，不是 mania for 的用法",
   "S13 historian … at":"a historian at King's College London 里 at 只引出任职的机构，historian 本身就是“历史学家”，不是固定搭配",
   "S14 harm … to":"no measurable harm to the economy 里 to 只引出受损的对象（对……的损害），harm 本身就是“损害”，意思不靠 to 产生（同 15 testimony … from 的判法）",
   "S15 fraction … of":"a small fraction of the price 里 of 只引出整体（价格的一小部分），fraction 本身就是“一小部分”，意思不靠 of 产生（同 16 beads … of 的判法）",
   "S6 Prices collapsed":"Prices 是主语，collapse 用于价格时本身就是“暴跌”（速查表第一个义项，搭配 prices collapsed 只是例句），不是靠搭配整体成义的习语（同 13 short-term memory 的判法）"}}
out={"no":"19","title_en":"Tulip Mania: The Bubble and the Legend","title_zh":"郁金香狂热：泡沫与传说","title_fx":{"hl":["Tulip","Legend"],"ghost":[]},"sentences":[],"核对确认":CONF,"结尾解说":"结局",
     "高亮按实际开口":True,"高亮开口门槛":40,
     "术语":{"Haarlem":"哈勒姆","Alkmaar":"阿尔克马尔","guilders":"荷兰盾","Charles Mackay":"查尔斯·麦凯","Mackay":"麦凯","Scottish":"苏格兰",
            "Anne Goldgar":"安妮·戈德加","King's College London":"伦敦国王学院","Dutch":"荷兰","windhandel":"windhandel"}}
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 核对 import 生成并核对
生成并核对(S, out)
