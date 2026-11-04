import json,re,glob,os
# 第41篇初稿（逐词对照）：S = [(段, [chunk, ...])]，chunk = ([(英文组, 中文组), ...], 可选 note)
# 2026-11-03 用户改稿 S19：“lobbying   overrode ally loose  都标为重点词汇”；loose 与 61 撞车用户“特批保留”；简述“改成停止……改成带刺的梨”；S13 括号“可以可以”
# 2026-11-03 用户改稿 S18：“你把这个审查改成 认真彻底的审查。”
# 2026-11-03 用户改稿 S17：“幼虫和饿死在这地方都标注为重点词汇。Larve 和starve。”；prickly：“多刺的特皮，特皮，特皮。特批，特批，特批。prickly”
# 2026-11-03 用户改稿 S16：“在10年内清除了大部分 “带刺的梨”，这是一种外来入侵的仙人掌。……仙人掌标注为重点词汇。prickly 也标注重点词汇。对应中文意思，带刺的。”；from/within 的译法用户选“清除范围遍及昆士兰州和新南威尔士州”“约十年”
# 2026-11-03 用户改稿 S14：“wreaked 为重点词汇为重点词汇。”（wreak havoc 整体标，T22）；“蟾蜍造成了严重破坏，但损害并不均衡；有些物种反而繁荣了起来。……改一下翻译”
# 2026-11-03 用户改稿 S13：“Lizard 没重点词汇标注为重点词汇。……marsupial 也标注重点词汇”
# 2026-11-03 用户改稿 S10：“起初每年 缓慢行进 约十公里”“改为它们的入侵前沿。它们 后面有一个白勺。”；S12：“它们皮肤里的毒素腺体，使它们成为了一顿致命的餐食。翻译改成这个”
# 2026-11-03 用户看 S9 they multiplied unchecked：“这两个颜色太相近了”——multiplied 琥珀黄 #FBBF24、unchecked 青绿 #2DD4BF（K140 重点词颜色）
# 2026-11-03 用户改稿 S4/S6/S7：“biological下面对应的意思改为 生物的”“halt 叫停改为停止。”“这套方案以失败告终。改为这套计划/方案 彻底失败。”
# 2026-11-03 用户改稿 S2：“bulky 意思对应 庞大笨重的”“Native to 标注重点词汇”“那就按照你说的来，原产于美洲”
# 2026-11-03 用户改稿 S1：“的 改为 它的”；“最后一句改为 此种植园位于澳大利亚东北部的昆士兰州。把前面那个正困扰着后面的澳大利亚东北部昆士兰州给去掉。”
# 2026-11-03 重点词中文沿用文章定稿（铁律），只按《翻译风格》调格式；短语型用法整体标（T22）；不用破折号（T36）。
S=[
(1,[[[("Greyback","灰背"),("cane","蔗"),("**beetles**,","**甲虫**(beetles)"),("whose","它的"),("**larvae**","**幼虫**(larvae)"),("**devour**","**啃食**(devour)"),("roots,","根系，")],
     "（whose larvae devour roots：定语从句，修饰 beetles）"],
    [[("were **plaguing**","正**困扰**(plaguing)着"),("**lucrative**","**利润丰厚的**(lucrative)"),("sugar","甘蔗"),("**plantations**","**种植园**(plantations)，"),("in Queensland, north-eastern Australia.","此种植园位于澳大利亚东北部的昆士兰州。")],
     "（in Queensland：后置定语，修饰 plantations；\nnorth-eastern Australia：同位语，补充说明 Queensland）"]]),
(1,[[[("In June 1935","1935年6月，"),("Queensland","昆士兰州"),("**imported**","从夏威夷**引进了**(imported)"),("102","102只"),("cane","甘蔗"),("toads,","蟾蜍，")]],
    [[("**bulky**","这是一种**原产于**(native to)美洲、**庞大笨重的**(bulky)"),("**amphibians** **native to** the Americas, from Hawaii.","**两栖动物**(amphibians)。")],
     "（bulky amphibians native to the Americas：同位语，补充说明 cane toads；\nnative to…：原产于……；from Hawaii：修饰 imported）"]]),
(1,[[[("That August","同年8月，"),("about 2,400 of their young","它们的约2,400只后代"),("were **released**.","被**释放**(released)到野外。")],
     "（young：名词，指动物的幼崽、后代）"]]),
(1,[[[("**Biological**","**生物的**(Biological)"),("control,","防治，"),("setting","即用"),("one **species**","一个**物种**(species)"),("against","去对付"),("a **pest**,","一种**害虫**(pest)，")],
     "（setting one species against a pest：现在分词短语，补充说明 Biological control；\nset A against B：用 A 对付 B）"],
    [[("had","就此迎来了"),("an","一名"),("**ambitious**","**雄心勃勃的**(ambitious)"),("new **recruit**.","**新兵**(recruit)。")],
     "（recruit：新兵，这里指刚被派上场的甘蔗蟾蜍）"]]),
(2,[[[("The **hasty** plan","这个**草率的**(hasty)计划"),("met **opposition**.","遭到了**反对**(opposition)。")],
     "（meet opposition：遭到反对）"]]),
(2,[[[("In November 1935","1935年11月，"),("an insect","昆虫"),("expert,","专家"),("Walter Froggatt,","沃尔特·弗罗格特"),("**persuaded**","**说服**(persuaded)"),("officials","官员"),("to **halt**","**停止**(halt)"),("releases;","释放；")],
     "（Walter Froggatt：同位语，补充说明 an insect expert；\npersuade sb to do sth：说服某人做某事）"],
    [[("after","经"),("Queensland's **lobbying**,","昆士兰州**游说**(lobbying)，"),("they","释放"),("**resumed** in September 1936.","于1936年9月**恢复**(resumed)。")],
     "（they：指 releases，即释放）"]]),
(2,[[[("The **scheme**","这套**计划/方案**(scheme)"),("**flopped**:","**彻底失败**(flopped)："),("the toads","蟾蜍"),("barely","几乎没能"),("**dented**","**削减**(dented)"),("beetle","甲虫的"),("numbers,","数量，")],
     "（barely：几乎不，带否定意味；\n冒号后的分句具体说明 flopped）"],
    [[("perhaps","或许"),("because","是因为"),("the insects","这些昆虫"),("stayed","一直待在"),("high up on cane **stalks**.","甘蔗**茎秆**(stalks)的高处。")],
     "（perhaps because…：原因状语从句，表推测）"]]),
(3,[[[("The toads","蟾蜍自己"),("**thrived** instead.","反倒**兴旺**(thrived)起来。")],
     "（instead：反而，\n和上文甲虫没被消灭形成对照）"]]),
(3,[[[("With few **foes**","**天敌**(foes)寥寥，"),("and **fertile** females","**能生育的**(fertile)雌蟾"),("**spawning**","**产下**(spawning)"),("thousands of","数千枚"),("eggs,","卵，")],
     "（with＋名词＋现在分词：with 复合结构作原因状语；\nfoes：敌人，这里指天敌）"],
    [[("they","它们"),("**multiplied** **unchecked**.","**不受遏制地**(unchecked)**大量繁殖**(multiplied)。")],
     "（unchecked：形容词作状语，说明繁殖的状态）"]]),
(3,[[[("Their","它们的"),("**invasion**","**入侵**(invasion)"),("**frontier**,","**前沿**(frontier)"),("creeping about ten kilometres a year at first,","起初每年缓慢行进约十公里，")],
     "（creeping…：现在分词短语作插入语，补充说明 frontier；\ncreep：缓慢移动）"],
    [[("**accelerated** to about 50 a year in the **tropical** north.","到了**热带**(tropical)北部，**加快**(accelerated)到每年约50公里。")],
     "（about 50 a year：省略了 kilometres）"]]),
(3,[[[("In February 2009","2009年2月，"),("the first known","已知的第一只"),("toad","蟾蜍"),("**breached**","**突破了**(breached)"),("Western Australia's border.","西澳大利亚州的边界。")],
     "（first known：已知的第一个）"]]),
(4,[[[("**Toxin**","它们皮肤里的**毒素**(Toxin)"),("**glands** in their skin","**腺体**(glands)，"),("make","使"),("them","它们成为了"),("a","一顿"),("deadly","致命的"),("meal.","餐食。")],
     "（make A B：使 A 成为 B；\nToxin glands：毒腺，toxin 作定语）"]]),
(4,[[[("Numbers of goannas","巨蜥"),("(large","（大型"),("**lizards**)","**蜥蜴**(lizards)）"),("and","和"),("northern","北"),("quolls","袋鼬"),("(small","（一种小型"),("**marsupial**","**有袋类**(marsupial)"),("hunters)","猎手）的数量")],
     "（Numbers of…：……的数量，of 结构语序倒过来；\ngoannas：巨蜥，括号里 large lizards 意为大型蜥蜴）"],
    [[("have **slumped** in places;","在一些地方**锐减**(slumped)；")],
     "（in places：在一些地方）"],
    [[("some","部分"),("local","地方的"),("quoll","袋鼬"),("populations","种群"),("were **wiped out**.","被**彻底消灭**(wiped out)。")],
     "（wipe out：彻底消灭）"]]),
(4,[[[("The toads","蟾蜍"),("have **wreaked**","**造成了**(wreaked havoc)"),("**havoc**,","**严重破坏**(wreaked havoc)，")],
     "（wreak havoc：造成严重破坏）"],
    [[("but","但"),("the damage","损害"),("is **uneven**;","并**不均衡**(uneven)；"),("some","有些"),("species","物种"),("have **prospered**.","反而**繁荣了**(prospered)起来。")],
     "（the damage is uneven：各地受害程度不一样）"]]),
(5,[[[("Biological control","生物防治"),("can **triumph**.","也能**大获成功**(triumph)。")]]]),
(5,[[[("From 1926","从1926年起，"),("the cactus **moth**, Cactoblastis,","仙人掌螟这种**蛾子**(moth)")],
     "（Cactoblastis：同位语，补充说明 the cactus moth，即仙人掌螟）"],
    [[("cleared","在约十年内清除了"),("most","大部分"),("**prickly** pear,","“**带刺的**(prickly)梨”，"),("an","这是一种"),("**invasive**","**外来入侵的**(invasive)"),("**cactus**,","**仙人掌**(cactus)，"),("{{=}}from Queensland and New South Wales within about a decade.","清除范围遍及昆士兰州和新南威尔士州。")],
     "（an invasive cactus：同位语，补充说明 prickly pear；\nclear A from B：把 A 从 B 清除掉）"]]),
(5,[[[("Tested first,","这种蛾子放出前经过检验，"),("its **larvae**","其**幼虫**(larvae)"),("**starved** rather than eat","宁可**饿死**(starved)也不吃"),("fifteen other","另外十五种"),("plants;","植物；")],
     "（Tested first：过去分词短语作状语，逻辑主语是这种蛾子；\nrather than：宁可……也不……）"],
    [[("the toads","蟾蜍却"),("faced no such","从未受过这样的"),("test.","检验。")],
     "（no such…：没有这样的……）"]]),
(5,[[[("Under an October 1984 law,","根据1984年10月通过的一部法律，"),("recruits now","如今新兵")],
     "（Under…law：依据……法律；\nrecruits：新兵，这里指准备引进来做生物防治的物种）"],
    [[("face **stringent**","都要经过**严格的**(stringent)"),("**scrutiny**.","**认真彻底的审查**(scrutiny)。")]]]),
(5,[[[("The **blunder**","这个**大错**(blunder)"),("was born of **haste**","起于**仓促**(haste)，"),("and","又因"),("sealed by **lobbying**","**游说**(lobbying)"),("that **overrode** a warning:","**压过了**(overrode)警告而成定局：")],
     "（be born of…：源于……；\nthat overrode a warning：定语从句，修饰 lobbying）"],
    [[("an **untested**","**未经检验的**(untested)"),("**ally**,","**盟友**(ally)"),("once","一旦"),("**loose**,","**放出**(loose)，"),("may never be **recalled**.","就可能再也**召不回来**(recalled)。")],
     "（once loose：省略的状语从句，等于 once it is loose）\n"
     "（简述：1935年，为对付啃食甘蔗根系的灰背蔗甲虫，\n"
     "昆士兰州从夏威夷引进了102只甘蔗蟾蜍，同年放出约2,400只后代。\n"
     "昆虫专家弗罗格特说服官员停止，但经昆士兰州游说，释放于1936年恢复。\n"
     "蟾蜍几乎没能削减甲虫，自己却天敌寥寥、大量繁殖，\n"
     "入侵前沿越推越快，2009年突破了西澳大利亚州的边界。\n"
     "它们皮肤有毒，巨蜥和北袋鼬在一些地方锐减。\n"
     "相比之下，仙人掌螟放出前经过检验，约十年就清除了大部分带刺的梨。\n"
     "根据1984年的一部法律，如今新引进的物种都要经过严格审查。）"]]),
]
CONF={
"合组":{
 "S7 high up on cane stalks":"对齐不了：high up on cane stalks 是地点状语，中文“甘蔗茎秆的高处”方位词 high up 必须放到后面，on 结构语序倒过来",
 "S10 creeping about ten kilometres a year at first":"对齐不了：a year、at first 是时间状语，中文“起初每年缓慢行进约十公里”（用户 2026-11-03 改）时间必须放到动词前（沿用文章定稿语序）",
 "S10 accelerated to about 50 a year in the tropical north":"对齐不了：in the tropical north 是地点状语，中文“到了热带北部”必须放到“加快”前；a year 中文“每年”放到数字前（沿用文章定稿语序）",
 "S13 Numbers of goannas":"对齐不了：Numbers of 是 of 结构，“的数量”必须放到后面（沿用文章定稿）",
 "S16 cleared":"对齐不了：within about a decade 是时间状语，中文“在约十年内”必须放到“清除了”前（用户 2026-11-03 定的译文）",
 "S16 from Queensland and New South Wales within about a decade":"对齐不了：用户 2026-11-03 定的译文“清除范围遍及昆士兰州和新南威尔士州”，from 两州化成“清除范围遍及”，within about a decade 已提到前面“在约十年内”",
 "S17 starved rather than eat":"对齐不了：rather than 中文“宁可……也不……”，“宁可”必须放到 starved 前，拆开语序不通",
 "S17 fifteen other":"对齐不了：fifteen other 中文“另外十五种”，other 必须放到数字前",
 "S18 recruits now":"对齐不了：now 是时间状语，中文沿用文章定稿“如今新兵”，“如今”放到主语前",
 "S19 sealed by lobbying that overrode a warning":"对齐不了：by lobbying that overrode a warning 是方式状语加定语从句，中文“游说压过了警告而成定局”必须放到 sealed 前"},
"对齐":{
 "S2-2 amphibians native to the Ameri":"native to the Americas 是后置定语，中文“原产美洲”必须提前（放到 bulky 下面）；from Hawaii 修饰 imported，中文“从夏威夷”放到“引进了”前",
 "S3-1 about 2,400 of their young":"of 结构：about 2,400 of their young，中文“它们的约2,400只后代”语序必须倒过来",
 "S7-2 high up on cane stalks.":"high up on cane stalks 是地点状语，中文“甘蔗茎秆的高处”方位词必须放到后面",
 "S10-1 creeping about ten kilometres ":"a year、at first 是时间状语，中文“起初每年”必须放到动词前",
 "S10-2 accelerated to about 50 a year":"in the tropical north 是地点状语，中文“到了热带北部”必须放到“加快”前",
 "S16-2 from Queensland and New South ":"用户 2026-11-03 选定的译文“清除范围遍及昆士兰州和新南威尔士州”，from 两州化成“清除范围遍及”，within about a decade 已提到前面“在约十年内”",
 "S18-1 Under an October 1984 law,":"Under…law 中文“根据1984年10月通过的一部法律”，时间定语 October 1984 必须放到“一部法律”前",
},
"牛津逗号":{
 "S16 an invasive cactus, from Queensland and":"不是三项并列：an invasive cactus 是 prickly pear 的同位语，逗号后 from Queensland and New South Wales 是地点状语，and 只连接两个州"},
"方向":{"S6-2 after→经":"after Queensland's lobbying 中文“经昆士兰州游说”，“经”就是经过……之后，方向一致（沿用文章定稿）"},
"词性":{"S9-2 unchecked 不受遏制地":"unchecked 是 adj.，在 multiplied unchecked 里作状语（说明繁殖的状态），中文“不受遏制地”作状语，沿用文章定稿"},
"即":{"S4-1 即":"沿用文章定稿中文“即用一个物种去对付一种害虫”，同位说明 Biological control，用“即”简洁准确"},
"引号":{"S16-2 “”":"用户 2026-11-03 原话自带引号：“在10年内清除了大部分 “带刺的梨”，这是一种外来入侵的仙人掌。来自于昆士兰和新南威尔士州。仙人掌，仙人掌标注为重点词汇。prickly 也标注重点词汇。对应中文意思，带刺的。Invasive 后面那个仙人掌要标注为重点词汇。”（“带刺的梨”）"},
"同词异译":{"wreaked havoc：严重破坏/造成了":"不是两种译法：wreak havoc 的意思“造成了严重破坏”，wreaked 对“造成了”、havoc 对“严重破坏”，整体标同一个英文（T22/T23，用户 2026-11-03 原话“wreaked 为重点词汇”）"},
"括号含重点词":{"S13-1 （大型**蜥蜴**(lizards)）":"英文原文就是括号 (large lizards)，中文照英文括号对应，不是补充说明；用户原话：“Lizard 没重点词汇标注为重点词汇。标注意重点词汇。 marsupial 也标注重点词汇，也标注重点词汇。”——lizards 在英文括号里，按用户原话标重点词","S13-1 （一种小型**有袋类**(marsupial)猎手）":"英文原文就是括号 (small marsupial hunters)，中文照英文括号对应（沿用文章定稿），不是补充说明；用户原话：“Lizard 没重点词汇标注为重点词汇。标注意重点词汇。 marsupial 也标注重点词汇，也标注重点词汇。”——marsupial 在英文括号里，按用户原话标重点词"},
"中文意思":{"S2 native to":"不是被隔开的两处：用户 2026-11-03 原话定的“原产于美洲”，native to 只对应“原产于”，后面直接接“美洲、”，没有“……的”"},
"短语":{
 "S19 by … lobbying":"不是搭配：by 只引出 sealed 的方式（被游说定局），lobbying 本身就是“游说”（同 S2 imported … from 的判法）",
 "S2 imported … from":"不是搭配：from Hawaii 只引出来源（从夏威夷），imported 本身就是“引进”（同 40 dispensed … to 的判法）",
 "S2 imported … to":"不是搭配：to 属于 native to the Americas，和 imported 无关",
 "S4 species … against":"不是搭配：against 属于 setting one species against a pest（set A against B 用 A 对付 B），和 species 无关",
 "S6 persuaded … to":"不是搭配：to 是不定式符号，引出 halt releases（persuade sb to do sth 句型），halt 本身是重点词已标；中文“说服官员叫停释放”",
 "S7 dented … on":"不是搭配：on 属于 high up on cane stalks，和 dented 无关",
 "S9 spawning … of":"不是搭配：of 属于 thousands of eggs，和 spawning 无关",
 "S10 accelerated … to":"不是搭配：to 只引出加快后达到的速度（到每年约50公里），accelerated 本身就是“加快”"}}
out={"no":"41","title_en":"The Toad That Invaded Australia","title_zh":"入侵澳洲的毒蟾","title_fx":{"hl":["Toad","Invaded"],"ghost":[]},"sentences":[],"核对确认":CONF,"结尾解说":"简述",
     "换行变更已获同意":{"S16":"用户 2026-11-03 原话：“在10年内清除了大部分 “带刺的梨”，这是一种外来入侵的仙人掌。来自于昆士兰和新南威尔士州。仙人掌，仙人掌标注为重点词汇。prickly 也标注重点词汇。对应中文意思，带刺的。Invasive 后面那个仙人掌要标注为重点词汇。”，并选定译文“在约十年内清除了大部分“带刺的梨”，这是一种外来入侵的仙人掌，清除范围遍及昆士兰州和新南威尔士州。”","S1":"用户 2026-11-03 原话：“最后一句，最后一句。改为 此种植园位于澳大利亚东北部的昆士兰州。把前面那个正困扰着 后面的澳大利亚东北部昆士兰州给去掉。”"},"allow_clash":["prickly","starved","loose","ally"],"重点词颜色":{"multiplied":"#FBBF24","unchecked":"#2DD4BF"},"高亮按实际开口":True,"高亮开口门槛":40,
     "术语":{"Biological":"生物","Queensland":"昆士兰州","Australia":"澳大利亚","Hawaii":"夏威夷","Americas":"美洲","Walter Froggatt":"沃尔特·弗罗格特","Western Australia":"西澳大利亚州","goannas":"巨蜥","northern quolls":"北袋鼬","quoll":"袋鼬","Cactoblastis":"仙人掌螟","prickly pear":"梨","New South Wales":"新南威尔士州"}}
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 核对 import 生成并核对
生成并核对(S, out)
