import json,re,glob,os
# 第62篇初稿（逐词对照）：S = [(段, [chunk, ...])]，chunk = ([(英文组, 中文组), ...], 可选 note)
# 2026-11-07 重点词中文沿用文章定稿（铁律）；标色词优先逐词对齐（用户 11-07 原话，篇“61-65”），没标色的尽量；短语型用法整体标（T22）；不用破折号（T36）；形容词的“的”进粗体。
S=[
(1,[[[("Dolly was born at Roslin, Scotland, on 5 July 1996.","1996年7月5日，多莉在苏格兰罗斯林出生。")]]]),
(1,[[[("Her","她的"),("**genome**","**基因组**(genome)"),("came from","来自"),("a Finn Dorset ewe's","一只芬兰多塞特母羊的"),("mammary","乳腺"),("cell,","细胞，")]],
    [[("**fused** with","这个细胞**融合了**(fused)"),("a Blackface","一枚黑脸羊"),("egg","卵细胞，"),("stripped of","这枚卵已去除了"),("its **nucleus**.","**细胞核**(nucleus)。")],
     "（fused with…：过去分词短语作后置定语，修饰 cell；\nstripped of…：过去分词短语作后置定语，修饰 egg；\nbe stripped of：被去除）"]]),
(1,[[[("A Blackface","一只黑脸羊"),("**surrogate**","**代孕母羊**(surrogate)"),("carried","怀着"),("the **embryo**","这个**胚胎**(embryo)"),("through **pregnancy**,","度过了**孕期**(pregnancy)，")]],
    [[("yet","然而"),("her","多莉的"),("white","白"),("face","脸"),("was **proof of**","**证明**(proof of)"),("a","她来自"),("**genetically**","**遗传上**(genetically)"),("different","不同的"),("**lineage**.","**血统**(lineage)。")],
     "（proof of：……的证据；her 指 Dolly）"]]),
(1,[[[("She alone survived from 277 attempts,","在277次尝试中只有她存活下来，"),("an **extraordinary**","这是**惊人的**(extraordinary)"),("failure","失败"),("rate.","率。")],
     "（an extraordinary failure rate：同位语，评述前面整件事）"]]),
(2,[[[("Dolly","多莉"),("is **popularly**","被**普遍**(popularly)"),("called","称为"),("the first clone,","第一个克隆体，"),("a **misconception**.","这是一种**误解**(misconception)。")],
     "（a misconception：同位语，评述前面整句）"]]),
(2,[[[("Her **predecessors**","她的**前辈**(predecessors)"),("included","包括")]],
    [[("frogs cloned from **transplanted** nuclei in 1962","1962年用**移植**(transplanted)细胞核克隆的青蛙，")],
     "（cloned from…：过去分词短语作后置定语，修饰 frogs；\nnuclei 是 nucleus 的复数）"],
    [[("and Roslin's","以及罗斯林"),("embryo-derived **duo**, Megan and Morag, in 1995.","1995年用胚胎细胞培育的**一对**(duo)绵羊梅根和莫拉格。")],
     "（Megan and Morag：同位语，补充说明 duo）"]]),
(2,[[[("She","她"),("was **genuinely**","**确实**(genuinely)是"),("the first **mammal** cloned from an adult cell.","第一个用成年细胞克隆的**哺乳动物**(mammal)。")],
     "（cloned from an adult cell：\n过去分词短语作后置定语，修饰 mammal）"]]),
(2,[[[("Roslin's **announcement** on 22 February 1997","1997年2月22日，罗斯林研究所的**公布**(announcement)"),("**coincided with** the paper,","**与**(coincided with)论文发表**同时**(coincided with)进行；")],
     "（coincide with：与……同时发生）"],
    [[("and her name,","她的名字"),("a","是一个关于"),("mammary","乳腺的"),("**pun**,","**双关语**(pun)，"),("honoured Dolly Parton.","向多莉·帕顿致敬。")],
     "（a mammary pun：同位语，补充说明 her name）"]]),
(3,[[[("The news","这一消息"),("**provoked**","**引发了**(provoked)"),("**uproar**","**轩然大波**(uproar)，")]],
    [[("and **apprehension**","也引发了**忧虑**(apprehension)，"),("about the **ethics** of human cloning.","关乎人类克隆的**伦理**(ethics)问题。")],
     "（provoked 带两个宾语 uproar 和 apprehension；\nabout the ethics…：后置定语，修饰 apprehension）"]]),
(3,[[[("In March 1997","1997年3月，"),("Clinton","克林顿"),("**prohibited**","**禁止**(prohibited)"),("federal","联邦"),("funding","资金"),("for such experiments.","用于这类实验。")]]]),
(3,[[[("In 1999","1999年，"),("her telomeres,","她的端粒，"),("or **chromosome** tips,","即**染色体**(chromosome)末端，")],
     "（or chromosome tips：or 表示“即，也就是”，解释 telomeres）"],
    [[("were reported","据报道"),("**shortened** by about 20% for her age.","比同龄羊**缩短了**(shortened)约20%。")],
     "（be reported shortened：被报道为缩短了，shortened 作补语；\nfor her age：就她的年龄而言）"]]),
(3,[[[("That","这"),("fed","加剧了"),("**anxiety**;","人们的**焦虑**(anxiety)；")],
     "（feed：加剧，助长）"],
    [[("some","有人"),("**speculated**","**推测**(speculated)"),("she was ageing **prematurely**.","她正在**过早**(prematurely)衰老。")],
     "（she was ageing…：宾语从句，省略了 that）"]]),
(4,[[[("Dolly","多莉"),("was put down,","被实施安乐死，"),("aged six,","时年六岁，"),("on 14 February 2003,","那是2003年2月14日；")],
     "（put down：（给动物）实施安乐死；aged six：插入语，说明年龄）"],
    [[("with **arthritis**","她患有**关节炎**(arthritis)"),("and a","和一种"),("**progressive**","**进行性的**(progressive)"),("**lung**","**肺部**(lung)"),("disease","疾病，"),("caused by","引起它的是"),("a sheep","绵羊"),("**virus**.","**病毒**(virus)。")],
     "（with…：介词短语作伴随状语，说明她的病情；\ncaused by…：过去分词短语作后置定语，修饰 disease）"]]),
(4,[[[("Indoor **confinement**","**圈养**(confinement)在室内"),("probably","很可能"),("**contributed**.","是**原因之一**(contributed)。")],
     "（contribute：促成，是……的原因之一；这里省略了宾语）"]]),
(4,[[[("In July 2016,","2016年7月，"),("13 clones,","13只克隆羊，"),("four","其中4只"),("from her","来自与她相同的"),("cell","细胞"),("line,","系，")],
     "（four from her cell line：插入语，补充说明 13 clones）"],
    [[("were ageing normally,","正在正常衰老，"),("without","没有"),("**hypertension**","**高血压**(hypertension)，"),("or **diabetes**.","也没有**糖尿病**(diabetes)。")]]]),
(4,[[[("In November 2017,","2017年11月，"),("her **skeletal** X-rays","她的**骨骼**(skeletal)X光片"),("showed","显示出"),("ordinary","普通的"),("arthritis,","关节炎，")]],
    [[("and fears of early onset","关节炎提早发病的担忧"),("were judged","被判定为"),("**unfounded**.","**毫无根据的**(unfounded)。")],
     "（fears of early onset：of 结构作后置定语，onset 指关节炎发病；\nbe judged＋形容词：被判定为……）"]]),
(5,[[[("She","她"),("bore","产下"),("six lambs","六只小羊，"),("by","是通过"),("natural","自然"),("**mating**;","**交配**(mating)；")],
     "（bore：bear 的过去式，“生（孩子），产下”）"],
    [[("Bonnie,","邦妮"),("first of these **descendants**,","是这些**后代**(descendants)中的第一只，"),("arrived","生于"),("in April 1998.","1998年4月。")],
     "（first of these descendants：同位语，补充说明 Bonnie）"]]),
(5,[[[("Since 2003","自2003年起，"),("her **stuffed** body,","她的**填充标本**(stuffed)，")]],
    [[("now **famously**","如今已成为**出了名**(famously)的"),("an **icon**","**标志**(icon)"),("and **memorial**,","和**纪念物**(memorial)，")],
     "（now famously an icon and memorial：插入语，补充说明 her stuffed body）"],
    [[("has been","一直"),("**encased in**","**封存在**(encased in)"),("the National Museum of Scotland.","苏格兰国家博物馆。")],
     "（has been encased：现在完成时被动语态，与 Since 2003 呼应；\nencase in：把……封在……里）"]]),
(5,[[[("Behind glass,","隔着玻璃，"),("her","她的"),("white","白"),("face","脸"),("**plainly**","**清楚地**(plainly)"),("**testifies to**","**见证**(testifies to)着"),("her","她的"),("Finn Dorset","芬兰多塞特"),("**ancestry**.","**祖源**(ancestry)。")],
     "（testify to：证明，见证）\n"
     "（简述：1996年7月，多莉在苏格兰罗斯林出生，她的基因组来自芬兰多塞特母羊的乳腺细胞，由黑脸羊代孕，白脸证明了她的血统；277次尝试中只有她活了下来。\n"
     "她常被误称为第一个克隆体，其实此前已有克隆青蛙和梅根、莫拉格，她是第一个用成年细胞克隆的哺乳动物；1997年2月公布，名字向多莉·帕顿致敬。\n"
     "消息引发轩然大波和伦理忧虑，克林顿禁止联邦资金用于这类实验；1999年她的端粒被报道偏短，有人推测她过早衰老。\n"
     "2003年2月，六岁的她因关节炎和病毒引起的肺病被实施安乐死；后来的研究表明克隆羊正常衰老，早发关节炎的担忧毫无根据。\n"
     "她自然产下六只小羊，如今她的标本陈列在苏格兰国家博物馆，白脸依然见证着她的祖源。）"]]),
]
G={
 "S1 Dolly was born at Roslin, Scotland, on 5 July 1996":"对齐不了：时间状语 on 5 July 1996 放在句末，中文日期必须提前到句首（文章定稿原文“1996年7月5日，多莉在苏格兰罗斯林出生”）",
 "S4 She alone survived from 277 attempts":"对齐不了：from 277 attempts 是范围状语，中文“在277次尝试中”必须提前，“只有她存活下来”才通顺",
 "S6 frogs cloned from transplanted nuclei in 1962":"对齐不了：cloned from… in 1962 是过去分词短语作后置定语，修饰 frogs，中文定语“1962年用移植细胞核克隆的”必须提前",
 "S6 embryo-derived duo, Megan and Morag, in 1995":"对齐不了：in 1995 和 embryo-derived 都修饰 duo，中文“1995年用胚胎细胞培育的一对绵羊”定语必须提前，同位语人名跟在后面",
 "S7 the first mammal cloned from an adult cell":"对齐不了：cloned from an adult cell 是过去分词短语作后置定语，修饰 mammal，中文“用成年细胞克隆的”必须提前",
 "S8 Roslin's announcement on 22 February 1997":"对齐不了：on 22 February 1997 是后置定语，修饰 announcement，中文日期必须提前",
 "S9 about the ethics of human cloning":"对齐不了：of human cloning 是 of 结构作后置定语，修饰 ethics，中文“人类克隆的伦理问题”必须提前",
 "S11 shortened by about 20% for her age":"对齐不了：for her age 中文“比同龄羊”必须放到动词前",
 "S12 she was ageing prematurely":"对齐不了：副词 prematurely 中文“过早”必须放到动词“衰老”前",
 "S14 Indoor confinement":"对齐不了：Indoor confinement 中文“圈养在室内”，状语必须放到后面才通顺（文章定稿原文）",
 "S15 were ageing normally":"对齐不了：副词 normally 中文“正常”必须放到动词“衰老”前",
 "S16 and fears of early onset":"对齐不了：of early onset 是 of 结构作后置定语，修饰 fears，中文“关节炎提早发病的担忧”必须提前",
 "S16 her skeletal X-rays":"对齐不了：X-rays 是一个词“X光片”，skeletal 在前已单独对“骨骼”，her skeletal X-rays 三个中文顺序与英文一样，不用拆得更细",
 "S18 her stuffed body":"对齐不了：stuffed body 中文“填充标本”是一个整体说法（文章定稿原文），拆开不通",
 "S18 the National Museum of Scotland":"对齐不了：机构名“苏格兰国家博物馆”，拆开不通",
}
CONF={"合组":G,
"对齐":{
 "S1-1 Dolly was born at Roslin, Scot":"时间状语 on 5 July 1996 在句末，中文日期必须提前到句首（文章定稿原文）",
 "S4-1 She alone survived from 277 at":"from 277 attempts 是范围状语，中文“在277次尝试中”必须提前",
 "S6-2 frogs cloned from transplanted":"cloned from… in 1962 是过去分词短语作后置定语，修饰 frogs，中文定语必须提前",
 "S6-3 embryo-derived duo, Megan and ":"embryo-derived、in 1995 都修饰 duo，中文定语“1995年用胚胎细胞培育的”必须提前",
 "S7-1 the first mammal cloned from a":"cloned from an adult cell 是后置定语，修饰 mammal，中文定语必须提前",
 "S8-1 Roslin's announcement on 22 Fe":"on 22 February 1997 是后置定语，修饰 announcement，中文日期必须提前",
 "S9-2 about the ethics of human clon":"of human cloning 是 of 结构作后置定语，中文“人类克隆的伦理问题”必须提前",
 "S11-2 shortened by about 20% for her":"for her age 中文“比同龄羊”必须放到动词前",
 "S16-2 and fears of early onset":"of early onset 是 of 结构作后置定语，修饰 fears，中文“关节炎提早发病的担忧”必须提前",
 "S18-3 the National Museum of Scotlan":"机构名“苏格兰国家博物馆”，拆开不通"},
"同词异译":{"coincided with：与/同时":"不是两种译法：coincide with 的意思“与……同时”被“论文发表”隔开，“与”和“同时”是同一个意思的两部分（T23）"},
"短语":{
 "S2 fused … with":"不是搭配：with 只引出融合的另一方（与卵细胞融合），速查表搭配是 fuse two cells / be fused together，fuse 单独就是“融合”",
 "S2 fused … of":"不是搭配：of 属于 stripped of（被去除），和 fused 无关",
 "S6 predecessors … in":"不是搭配：in 属于 in 1962（时间），和 predecessors 无关",
 "S9 provoked … of":"不是搭配：of 属于 the ethics of human cloning（后置定语），和 provoked 无关",
 "S10 prohibited … for":"不是搭配：for 属于 funding for such experiments（用于这类实验的资金），和 prohibited 无关",
 "S11 shortened … for":"不是搭配：for her age 表示“就她的年龄而言”，shorten 单独就是“缩短”",
 "S13 with … arthritis":"不是搭配：with 表示伴随，“患有”关节炎和肺病，with 管两个名词，arthritis 单独就是“关节炎”",
 "S15 without … hypertension":"不是搭配：without 只表示“没有”，管 hypertension 和 diabetes 两个名词",
 "S18 encased … of":"不是搭配：of 属于机构名 National Museum of Scotland，encase 的搭配是 in，已整体标"},
"中文意思":{"S14 contributed":"不是被隔开：中文“是原因之一”连在一起，“是”是系动词，沿用文章定稿只标“原因之一”"},
"牛津逗号":{
 "S6 and Roslin's embryo-derived duo, Megan and":"不是三项并列：Megan and Morag 是两项，作 duo 的同位语；predecessors 只有青蛙和 duo 两项",
 "S13 on 14 February 2003, with arthritis and":"不是三项并列：arthritis 和 a progressive lung disease 两项",
 "S15 were ageing normally, without hypertension or":"不是三项并列：hypertension 和 diabetes 两项",
 "S18 2003 her stuffed body, now famously an icon and":"不是三项并列：icon 和 memorial 两项"},
"是的":{"S4-1 是**惊人的**":"不是“是…的”句式：“这是惊人的失败率”是“是”带名词短语，“惊人的”修饰失败率，对应同位语 an extraordinary failure rate"},
"即":{"S11-1 即":"文章定稿原文“她的端粒，即染色体末端”，对应 or（即，也就是），中文意思不改（守则4）"},
"数字写法":{"S15-1 four":"文章定稿原文“其中4只”，与前面“13只”一致，读法“四只”对"}}
out={"no":"62","title_en":"Dolly, the Copied Sheep","title_zh":"多莉：一只羊的复制","title_fx":{"hl":["Dolly","Sheep"],"ghost":[]},"sentences":[],"核对确认":CONF,"结尾解说":"简述",
     "高亮按实际开口":True,"高亮开口门槛":40,
     "术语":{"Dolly":"多莉","Roslin":"罗斯林","Scotland":"苏格兰","Finn Dorset":"芬兰多塞特","Blackface":"黑脸羊","Megan":"梅根","Morag":"莫拉格","Dolly Parton":"多莉·帕顿","Clinton":"克林顿","Bonnie":"邦妮","National Museum of Scotland":"苏格兰国家博物馆"}}
out.update({"非人声区间": {"S8": [[4.4865, 4.6, "紧贴词尾"], [8.725, 8.91], [6.5105, 6.683167, "紧贴两头"]], "S9": [[2.743792, 2.953625, "紧贴两头"]], "S10": [[2.085, 2.42]], "S18": [[5.435, 5.71], [2.720208, 2.925083, "紧贴两头"]], "S6": [[5.82, 6.171125, "紧贴词头"]], "S11": [[1.43, 1.62]], "S17": [[7.587708, 7.69, "紧贴词尾"]], "S13": [[5.465167, 5.808792, "紧贴两头"]]}, "词尾除阻": {"S4": {"句末": [5.79, "t"]}, "S17": {"句末": [7.565, "t"]}}, "停顿插入点": {"S1": {"1": 1.8455}, "S15": {"2": 3.587667}}, "区间声音指纹": {"S1": "454d381d6f01", "S4": "ee0ac63304a5", "S6": "e438ac173af0", "S8": "4113f91f97e1", "S9": "1b7f462eb31d", "S10": "4400c8094261", "S11": "67eeedaee00f", "S13": "8317afcfde07", "S15": "d0af91d053ec", "S17": "c332d4e6032d", "S18": "4c4d336c155d"}, "结尾句": {"S19": {"前段语速": 0.9, "最后一段语速": 0.78, "最后一段前停顿": 0.7, "接点": [30900, 40860], "依据": "全篇结尾句按 07 定下的标准（用户 2026-10-10 同意并要求所有视频统一）：前段 0.9、最后一段“her white face plainly testifies to her Finn Dorset ancestry.” 0.78、前面停 0.7 秒。接点由 结尾句接点.py 自动找：0.9 那遍最后一个标点后最长静音（40 ms）的正中 1.288 s，0.78 那遍（125 ms）的正中 1.702 s，所在帧和两侧各 5 ms 都低于 -55 dB（程序以 08 校准：与人工核实的接点落在同一段静音里）"}}})   # 声音程序与实测写进脚本的区间、除阻、插入点（并进 gen62）
CONF['停顿位置']={"S11 telomeres, / or @2.580": "2026-11-07 逐 2.5 ms 实测（S11 w）：telomeres 的 /z/ 衰减到 2.575（-49 dB），2.58–2.59 低谷 -53～-54 dB，2.595 起 or 的元音（-35→-13 dB、周期 0.5–0.7）；停顿 2.580 落在两词之间的低谷", "S15 line, / were @4.845": "2026-11-07 逐 2.5 ms 实测（S15 w）：line 的 n 鼻音（重心 0.4–0.7 kHz、周期 0.5）到约 4.85，4.855 起重心升到 1.1 kHz 是 were 的 /w/；n 与 w 两个浊音连读没有静音，停顿 4.845 在 n 末尾，不进 /w/，在两词交界处", "S17 descendants, / arrived @5.120": "2026-11-07 逐 2.5 ms 实测（S17 w）：descendants 后 5.05–5.11 是气声（-34～-42 dB、重心 1.9–2.6 kHz、低频 -18～-30 dB），5.12 低谷 -51.3 dB，5.15 起 arrived 的元音（-29→-15 dB）；停顿 5.120 正落在两词之间的低谷", "S1 Roslin, / Scotland, @1.845": "2026-11-07 逐 2.5 ms 实测（S1 w）：Roslin 的 n 浊音到 1.843（周期 0.4–0.5、重心 0.6–1.1 kHz），1.845 低谷 -38.9 dB，1.8475 起 Scotland 的 /s/（重心升到 5.9 kHz）；程序原插在 1.990，落在 /s/ 与 /k/ 闭塞之间（切词），改插在低谷过零点 1.8455", "S15 clones, / four @3.588": "2026-11-07 逐 2.5 ms 实测（S15 w）：clones 的 /z/ 3.55–3.585（重心 6–7.5 kHz），3.5875 起重心降到 5.2→4.1→3.5→2.2 kHz（four 的 /f/ 转元音），3.6025 起元音；擦音连读没有静音，程序原插在 3.595 落在 /f/ 里，改插在 /z/ 与 /f/ 交界的过零点 3.587667"}
# S17 非人声区间 [7.587708, 7.69, 紧贴词尾]：2026-11-07 逐 2.5 ms 实测（S17 w）：eighteen 的 eɪ 衰减到 7.55，7.55–7.59 是 /t/ 闭塞（-60～-68 dB），7.6025–7.66 是一下弱除阻（-34～-64 dB，2 kHz 以上 -43 dB，加强 6 dB 也不够），照 54 S4 August.（主会话 11-05 同意）删掉，由 词尾辅音核对 --写入 移植供体 /t/
# S8/S13/S18 紧贴两头的非人声区间：A19 停顿后吸气（-44～-57 dB、重心 2–3 kHz、周期 0.1–0.3），起点接停顿删除段，终点在下一个词起音前的过零点（S8 and 6.685、S13 with 5.81、S18 now 2.93）
# S10 [2.085, 2.42]：1997 与 Clinton 之间无标点的自然停顿，2.16–2.35 吸气（-47～-55 dB、重心 2–2.5 kHz），连同前面的静音一起换成静音，让程序把无标点长停顿压到 0.18 s
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 核对 import 生成并核对
生成并核对(S, out)
