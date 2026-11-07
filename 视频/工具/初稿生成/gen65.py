import json,re,glob,os
# 第65篇初稿（逐词对照）：S = [(段, [chunk, ...])]，chunk = ([(英文组, 中文组), ...], 可选 note)
# 2026-11-07 重点词中文沿用文章定稿（铁律）；中英尽量对齐、标色优先（用户 11-07 原话，篇“61-65”）；不用破折号（T36）；三项并列加牛津逗号（T18）。
S=[
(1,[[[("On Spitsbergen, in Norway's Svalbard **archipelago**,","在挪威斯瓦尔巴**群岛**(archipelago)的斯匹次卑尔根岛上，")],
     "（in Norway's Svalbard archipelago：同位语，补充说明 Spitsbergen 的位置）"],
    [[("a **corridor**","一条**通道**(corridor)"),("has been","已经"),("**drilled** deep","深深地**钻进**(drilled)"),("into a","一面"),("**frosted**","**覆着白霜的**(frosted)"),("**hillside**.","**山坡**(hillside)。")],
     "（has been drilled：现在完成时的被动语态）"]]),
(1,[[[("At its end,","通道尽头，"),("**cartons**","一个个**纸箱**(cartons)里装着"),("of **precious**","**珍贵的**(precious)"),("seed","种子，")],
     "（its 指 corridor）"],
    [[("sit **silently**","它们**静静地**(silently)躺"),("in a","在一座"),("**sub-zero**","**零度以下的**(sub-zero)"),("**repository**,","**储藏库**(repository)里，")]],
    [[("**insulated** by **permanently** frozen ground.","四周**永久**(permanently)冻结的土层为它们**隔热**(insulated)保冷。")],
     "（insulated by…：过去分词短语，补充说明 repository）"]]),
(2,[[[("The Svalbard Global Seed Vault","斯瓦尔巴全球种子库"),("opened near Longyearbyen in February 2008","于2008年2月在朗伊尔城附近启用，")]],
    [[("to **insure** crops such as **beans**, rice, and wheat","**为**(insure against)**豆类**(beans)、水稻、小麦等作物**投保**(insure against)，")],
     "（to insure…：不定式作目的状语；\ninsure A against B：为 A 投保，防范 B（被隔开的搭配））"],
    [[("**against**","**防范**(insure against)"),("the **horrors** people **dread**,","人们所**畏惧**(dread)的种种**灾难**(horrors)，"),("from **atomic** war","从**原子**(atomic)战争"),("to disease.","到疾病。")],
     "（people dread：定语从句，省略了关系代词，修饰 horrors；\nfrom A to B：从 A 到 B）"]]),
(2,[[[("It has","它有"),("**ample**","**充足的**(ample)"),("room","空间，"),("for about","可容纳约"),("four and a half million","450万份"),("samples.","样本。")]]]),
(2,[[[("**Essentially**","它**本质上**(Essentially)是"),("the planet's","这颗星球"),("**ultimate**","**终极的**(ultimate)"),("**backup**,","**备份**(backup)，")],
     "（Essentially the planet's ultimate backup：\n名词短语作状语，补充说明 it）"],
    [[("it is run","运作起来"),("like","就像"),("a bank's","银行的"),("**safe-deposit** box.","**保险箱**(safe-deposit)。")]]]),
(2,[[[("**Depositors**","**存放者**(Depositors)"),("keep","仍保有"),("**ownership**,","**所有权**(ownership)，")]],
    [[("and only they","也只有他们"),("can take their seeds out.","能取出自己的种子。")],
     "（take A out：把 A 取出）"]]),
(3,[[[("The first","第一次"),("**retrieval**","**取种**(retrieval)"),("came not","不是发生在"),("after an **asteroid**","**小行星**(asteroid)"),("strike","撞击之后，")],
     "（not A but B：不是 A，而是 B）"],
    [[("but","而是发生在"),("amid **strife** on the ground.","地面上的**纷争**(strife)之中。")]]]),
(3,[[[("ICARDA, a research centre","国际干旱地区农业研究中心的"),("whose **gene**","**基因**(gene)"),("bank","库"),("stood","原在"),("near Aleppo,","阿勒颇附近，")],
     "（a research centre whose…：同位语，补充说明 ICARDA；\nwhose 引导定语从句，修饰 centre）"],
    [[("had moved its headquarters to Beirut during Syria's civil war.","在叙利亚内战期间，它已把总部迁到了贝鲁特。")],
     "（had moved：过去完成时，迁总部在申请取种之前）"]]),
(3,[[[("In September 2015","2015年9月，"),("it asked for","它申请取回"),("about 116,000 samples,","约11.6万份样本，")]],
    [[("130 of the 325 boxes it had sent to the Arctic before the **hostilities**.","也就是**战事**(hostilities)爆发前它送往北极的325箱中的130箱。")],
     "（130 of the 325 boxes：同位语，补充说明 samples；\nit had sent…：定语从句，修饰 boxes）"]]),
(3,[[[("They included","其中有"),("**robust** strains of wheat and **barley** **tolerant of** drought and heat.","能**耐受**(tolerant of)干旱和高温的**强健**(robust)小麦和**大麦**(barley)品种。")],
     "（tolerant of drought and heat：后置定语，\n修饰 strains；\ntolerant of：耐……的）"]]),
(4,[[[("In Lebanon and Morocco, ICARDA","国际干旱地区农业研究中心在黎巴嫩和摩洛哥"),("**sowed**","**播下**(sowed)"),("the seeds,","这些种子，")]],
    [[("and **vigorous** plants **sprouted**","种子**萌发**(sprouted)，长成**茁壮的**(vigorous)植株，"),("to **regenerate** its collection.","让收藏得以**再生**(regenerate)。")],
     "（to regenerate…：不定式作结果状语）"]]),
(4,[[[("Once **multiplication**","**繁育**(multiplication)"),("had gone far enough,","达到足够规模后，")],
     "（once：一旦……就，引导时间状语从句）"],
    [[("a **homecoming** began in 2017,","2017年开始了**回归之旅**(homecoming)，"),("**consignment** by consignment,","种子**一批**(consignment)一批地运回，")],
     "（consignment by consignment：一批接一批）"],
    [[("**restocking**","重新**充实**(restocking)"),("the Arctic","这座北极"),("**stronghold**.","**堡垒**(stronghold)。")],
     "（restocking…：现在分词短语作伴随状语）"]]),
(5,[[[("That same","同一"),("year","年"),("brought","还有过"),("a **scare**.","一场**虚惊**(scare)。")]]]),
(5,[[[("After **record-breaking** warmth,","在一段**破纪录的**(record-breaking)温暖天气之后，")]],
    [[("meltwater","融水"),("ran into","流进"),("the roughly","大约"),("100-metre","100米长的"),("entrance","入口"),("tunnel","隧道，"),("and **solidified**.","随后**凝固**(solidified)成冰。")]]]),
(5,[[[("The **intrusion**","这次**入侵**(intrusion)"),("stopped short of","没有到达"),("the seeds,","种子，")],
     "（stop short of：没有到达）"],
    [[("which","它们"),("stayed **safely**","**安然**(safely)保持在"),("at minus 18","零下18"),("degrees Celsius.","摄氏度。")],
     "（which…：非限制性定语从句，修饰 seeds）"]]),
(5,[[[("Norway","挪威"),("**waterproofed** the tunnel","给隧道做了**防水**(waterproofed)，"),("and dug","并挖了"),("**drainage**","**排水**(drainage)用的"),("**ditches**.","**沟渠**(ditches)。")]]]),
(6,[[[("A **haven** built against the **apocalypse**","一座为抵御**末日**(apocalypse)而建的**避风港**(haven)，")],
     "（built against the apocalypse：过去分词短语作后置定语，\n修饰 haven）"],
    [[("had a **weakness** at its own entrance,","在自家入口处却有一个**弱点**(weakness)，"),("and","而"),("warmer","更暖的"),("weather","天气"),("found it.","找到了它。")],
     "（it 指 weakness）\n"
     "（简述：斯瓦尔巴全球种子库2008年2月在挪威北极群岛启用，深藏山体，永久冻土为种子隔热保冷。\n"
     "它是全球作物的终极备份，像银行保险箱一样，只有存放者能取回自己的种子。\n"
     "第一次取种不是在天灾之后，而是在叙利亚内战之中：2015年9月，总部已迁到贝鲁特的国际干旱地区农业研究中心取回约11.6万份样本。\n"
     "研究中心在黎巴嫩和摩洛哥种下这些种子，重建收藏，2017年起把繁育的新种子一批批送回北极。\n"
     "同一年，破纪录的暖天过后，融水流进入口隧道并结冰，没有到达种子，挪威随后给隧道防水，挖了排水沟。）"]]),
]
G={
 "S2 insulated by permanently frozen ground":"对齐不了：被动结构 insulated by…，中文“四周永久冻结的土层为它们隔热保冷”施事提前作主语，“隔热”必须放到最后；两个重点词中文先后与英文相反",
 "S3 opened near Longyearbyen in February 2008":"对齐不了：地点、时间状语 near Longyearbyen、in February 2008，中文“于2008年2月在朗伊尔城附近”必须放到动词“启用”前",
 "S3 to insure crops such as beans, rice, and wheat":"对齐不了：insure A 中文“为 A 投保”，A 必须放到动词前；such as 列举中文“豆类、水稻、小麦等作物”必须提前",
 "S6 can take their seeds out":"对齐不了：take … out 被宾语隔开，中文“取出自己的种子”动词在前、宾语在后，只能整组",
 "S7 amid strife on the ground":"对齐不了：on the ground 是后置定语，修饰 strife，中文“地面上的纷争”必须提前；amid 中文“……之中”后置",
 "S8 ICARDA, a research centre":"对齐不了：a research centre 是 ICARDA 的同位语，中文机构全名“国际干旱地区农业研究中心”已含“研究中心”，名称不能拆",
 "S8 had moved its headquarters to Beirut during Syria's civil war":"对齐不了：时间状语 during Syria's civil war 中文“在叙利亚内战期间”必须放到句首；move A to B 中文“把 A 迁到 B”",
 "S9 130 of the 325 boxes it had sent to the Arctic before the hostilities":"对齐不了：130 of the 325 boxes 中文“325箱中的130箱”必须倒过来；it had sent… 是定语从句，修饰 boxes，中文必须提前",
 "S10 robust strains of wheat and barley tolerant of drought and heat":"对齐不了：tolerant of drought and heat 是后置定语，修饰 strains，中文“能耐受干旱和高温的……品种”必须提前；三个重点词中文先后与英文不同",
 "S11 In Lebanon and Morocco, ICARDA":"对齐不了：地点状语 In Lebanon and Morocco，中文“在黎巴嫩和摩洛哥”必须放到主语后；机构全名不能拆",
 "S12 had gone far enough":"对齐不了：go far enough 中文“达到足够规模”是整体说法，拆开不通；once 引导的从句中文“……后”后置",
 "S15 stopped short of":"对齐不了：stop short of 是固定说法“没有到达”，拆开不通",
 "S17 A haven built against the apocalypse":"对齐不了：built against the apocalypse 是后置定语，修饰 haven，中文“为抵御末日而建的避风港”必须提前；两个重点词中文先后与英文相反",
 "S17 had a weakness at its own entrance":"对齐不了：地点状语 at its own entrance，中文“在自家入口处”必须放到动词前",
}
DZ={
 "S1-1 On Spitsbergen, in Norway's Sv":"in Norway's Svalbard archipelago 是同位语，补充说明 Spitsbergen 的位置，中文“在挪威斯瓦尔巴群岛的斯匹次卑尔根岛上”大地名必须放前面",
 "S2-3 insulated by permanently froze":"被动结构 insulated by…，中文施事“永久冻结的土层”提前作主语，“隔热”必须放到最后",
 "S3-1 The Svalbard Global Seed Vault":"专名“斯瓦尔巴全球种子库”，拆开不通",
 "S3-1 opened near Longyearbyen in Fe":"地点、时间状语中文必须放到动词“启用”前",
 "S3-2 to insure crops such as beans,":"insure A 中文“为 A 投保”，such as 列举中文“豆类、水稻、小麦等作物”必须提前",
 "S6-2 can take their seeds out.":"take … out 被宾语隔开，中文“取出自己的种子”动词在前，只能整组",
 "S7-2 amid strife on the ground.":"on the ground 是后置定语，修饰 strife，中文“地面上的纷争”必须提前",
 "S8-2 had moved its headquarters to ":"时间状语 during Syria's civil war 中文“在叙利亚内战期间”必须放到句首",
 "S9-2 130 of the 325 boxes it had se":"130 of the 325 boxes 中文“325箱中的130箱”必须倒过来，定语从句 it had sent… 中文必须提前",
 "S10-1 robust strains of wheat and ba":"tolerant of drought and heat 是后置定语，修饰 strains，中文“能耐受干旱和高温的……品种”必须提前",
 "S11-1 In Lebanon and Morocco, ICARDA":"地点状语中文“在黎巴嫩和摩洛哥”必须放到主语后；机构全名不能拆",
 "S12-2 a homecoming began in 2017,":"时间状语 in 2017 中文“2017年”必须放到动词“开始了”前",
 "S17-1 A haven built against the apoc":"built against the apocalypse 是后置定语，修饰 haven，中文“为抵御末日而建的避风港”必须提前",
 "S4-1 four and a half million":"数词“四百五十万”中文写作“450万”，一个数不能拆",
 "S17-2 had a weakness at its own entr":"地点状语 at its own entrance 中文“在自家入口处”必须放到动词前",
}
G["S12 a homecoming began in 2017"]="对齐不了：时间状语 in 2017，中文“2017年”必须放到动词“开始了”前"
# S8 非人声 [3.865, 4.184625]：2026-11-07 逐 2.5 ms 实测（dossier_65 #14）：Aleppo, 后停顿 3.81–3.86 删除段之后，3.87–4.17 是吸气（-41～-55 dB、重心 2.2–3.0 kHz、低频 -12～-25 dB、周期 ≤0.3），4.1725–4.19 低谷 -55 dB，4.2025 起 had 的 /h/；止点过零 4.184625，h 不动
# S9 非人声 [6.305, 6.480083]：同上（#18–#21）：samples, 后删除段止 6.305，6.315–6.475 吸气（-43～-55 dB、重心 1.8–2.3 kHz、低频 -13～-26 dB），6.48–6.55 是 one 的 /w/ 浊音前导（低频 -1～-2 dB）保留；止点过零 6.480083
# S15 非人声 [2.215, 2.482542]：同上（#33–#36）：seeds, 后删除段止 2.215，2.22–2.48 吸气（-45～-57 dB、重心 1.7–2.3 kHz、低频 -10～-17 dB），2.49–2.54 是 which 的 /w/ 浊音前导（低频 -0.5～-3.5 dB）保留；止点过零 2.482542
# S17 非人声 [6.732, 6.80] + 词尾除阻 句末 6.70 t：同上（#39）：found it. 的 /t/ 闭塞 6.70–6.73（-62～-67 dB），6.735–6.775 原声除阻只有 -41 dB、2 kHz 以上 -45.7 dB（A21 不合格），加强 6 dB 也不够；删掉这一下，再由 词尾辅音核对.py --写入 移植一下合格的 /t/，只剩一下除阻
CONF={"合组":G,"对齐":DZ,
"同词异译":{"insure against：为/投保/防范":"不是两种译法：insure A against B 的意思“为……投保，防范……”被“豆类、水稻、小麦等作物”隔开，“为”“投保”“防范”是同一个意思的三部分（T23）"},
"们":{"S2-3 **(permanently)冻结的土层为它们**":"们不在加粗里，是代词“它们”（指种子），沿用文章定稿“为它们隔热保冷”；被报出只因紧跟在加粗后面"},
"数字":{"S9-1 116,000":"about 116,000 samples 译作“约11.6万份样本”，数值正确，读法 one hundred and sixteen thousand"},
"方向":{"S7-1 after→小行星":"after an asteroid strike 中文“小行星撞击之后”，“之后”在 strike 下面，方向一致"},
"短语":{
 "S1 drilled … into":"不是搭配：into a frosted hillside 只表示方向（钻进山坡），drill 单独就是“钻”，中文“钻进”沿用文章定稿",
 "S2 cartons … of":"不是搭配：cartons of seed 是“一箱箱种子”的量词结构，carton 单独就是“纸箱”",
 "S2 insulated … by":"不是搭配：by 引出被动的施事（永久冻土），insulate 单独就是“隔热”",
 "S3 dread … from":"不是搭配：from 属于 from atomic war to disease（从……到……），和 dread 无关",
 "S3 dread … to":"不是搭配：to 属于 from atomic war to disease，和 dread 无关",
 "S11 sowed … to":"不是搭配：to 属于不定式 to regenerate（结果状语），和 sowed 无关",
 "S11 sprouted … to":"不是搭配：to 属于不定式 to regenerate（结果状语），sprout 单独就是“萌发”",
 "S12 consignment … by":"不是搭配：consignment by consignment 是同一个名词重复（一批接一批），by 不和重点词组成短语，consignment 单独就是“一批货”"}}
out={"no":"65","title_en":"The Day the Doomsday Vault Opened","title_zh":"末日种子库的第一次取种","title_fx":{"hl":["Doomsday","Vault"],"ghost":[]},"sentences":[],"核对确认":CONF,"结尾解说":"简述",
     "高亮按实际开口":True,"高亮开口门槛":40,
     "术语":{"Spitsbergen":"斯匹次卑尔根岛","Norway":"挪威","Svalbard":"斯瓦尔巴","Svalbard Global Seed Vault":"斯瓦尔巴全球种子库","Longyearbyen":"朗伊尔城","ICARDA":"国际干旱地区农业研究中心","Aleppo":"阿勒颇","Beirut":"贝鲁特","Syria":"叙利亚","Arctic":"北极","Lebanon":"黎巴嫩","Morocco":"摩洛哥","Celsius":"摄氏"}}
out.update({"非人声区间": {"S1": [[3.565, 3.910792, "紧贴词头"]], "S3": [[5.46, 5.8]], "S6": [[1.815, 2.036125, "紧贴词头"]], "S7": [[3.46, 3.72]], "S9": [[2.03, 2.276, "紧贴词头"], [6.305, 6.480083, "紧贴词头"]], "S10": [[2.765, 3.045]], "S11": [[1.692, 1.98, "紧贴词尾"]], "S12": [[5.96, 6.275]], "S16": [[1.63, 1.875]], "S8": [[3.865, 4.184625, "紧贴词头"]], "S15": [[2.215, 2.482542, "紧贴词头"]], "S17": [[6.732, 6.8]]}, "词尾除阻": {"S6": {"句末": [4.235, "t"]}, "S12": {"3": [8.11, "t"]}, "S17": {"句末": [6.7, "t"]}}, "除阻加强": {"S5": {"1": [2.29, 2.34, 3.0]}}})   # 声音程序写进脚本的区间、除阻＋手动实测（S8/S9/S15 停顿后吸气、S17 句末 it 弱除阻删掉后移植），并进 gen65
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 核对 import 生成并核对
生成并核对(S, out)
