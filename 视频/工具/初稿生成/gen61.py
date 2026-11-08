import json,re,glob,os
# 第61篇初稿（逐词对照）：S = [(段, [chunk, ...])]，chunk = ([(英文组, 中文组), ...], 可选 note)
# 2026-11-07 重点词中文沿用文章定稿（铁律）；中英对齐按用户 11-07 原话（篇“61-65”）：标色的优先逐词对齐，没标色的尽量；
# 两处三项并列加牛津逗号（T18）；at the expense of 整体标、被隔开两处都标（T22/T23）。
# 2026-11-08 用户：“Converted 标注重点词汇，标注重点词汇，意思为改造过的。”（与 57 converted 撞车，用户坚持加，allow_clash）
# 2026-11-08 用户改 S2：“固定在她甲板上的是58个集装箱——其实就是从车轮和底盘上拆卸下来的挂车车厢。”“wheel 标注重点词汇，标注重点词汇。”“下面的小字改成：trailor body 挂车车厢 就是在trailer body后面，就是加上挂车车厢这四个字。就整体翻译为挂车车厢。”“字小字部分额外附加: detach from 指将某物从原本附着、连接或所属的主体上分离或拆卸下来。”（破折号按 T36 由 做.sh 自动换）
# 2026-11-08 用户改 S3：“翻译不准，改成这个翻译: 极少数旁观者会把一批如此平淡无奇的货物当作一个里程碑。”
# 2026-11-08 用户改 S4：“那时，货物都是散装运输。”（freight 与 S3 cargo 中文都成“货物”，用户原话定）
# 2026-11-08 用户改 S5：“一帮二十多名或更多的码头工人，一件件地搬运麻袋、 桶和板条箱。”“dockworker 标注重点词汇。”“crates 标注重点词汇。特批，特批，特批，特批。”（“、 桶”中间的空格去掉；crates 与 47 撞车，用户特批 allow_clash）
# 2026-11-08 用户改 S1 中文（原话见 用户同意记录 篇 61）：说啥改啥
S=[
(1,[[[("On 26 April 1956","1956年4月26日，"),("a","一艘"),("**converted**","**改造过的**(converted)"),("Second World War","二战"),("**tanker**,","**油轮**(tanker)"),("the Ideal X,","“理想X号”，")],
     "（a converted…tanker：主语；the Ideal X：同位语，补充说明 tanker）"],
    [[("**slipped out of**","**悄然驶离**(slipped out of)"),("Port Newark, New Jersey,","新泽西州纽瓦克港，"),("for Houston.","开往休斯敦。")],
     "（slip out of：悄悄离开；for：表示去向，开往）"]]),
(1,[[[("**Clamped**","**固定**(clamped)"),("to her deck","在她甲板上的"),("were","是"),("58","58个"),("**containers**,","**集装箱**(containers)——")],
     "（倒装句：表语 Clamped to her deck 提前，主语是 58 containers；\nclamp A to B：把 A 固定在 B 上；her 指船）"],
    [[("**trailer** bodies **detached from** their **wheels** and **chassis**.","其实就是**从**(detached from)**车轮**(wheels)和**底盘**(chassis)**上拆卸下来的**(detached from)**挂车**(trailer)车厢。")],
     "（trailer bodies 挂车车厢：同位语，补充说明 containers；\ndetached from…：过去分词短语作后置定语，修饰 bodies；\ndetach from：指将某物从原本附着、连接或所属的主体上分离或拆卸下来）"]]),
(1,[[[("Few","极少数"),("**spectators**","**旁观者**(spectators)"),("would have taken","会把"),("so","一批如此"),("**unremarkable**","**平淡无奇的**(unremarkable)"),("a **cargo**","**货物**(cargo)"),("for a **landmark**.","当作一个**里程碑**(landmark)。")],
     "（take A for B：把 A 当作 B；\nso＋形容词＋a＋名词：这样……的一个；\nwould have done：对过去情况的推测）"]]),
(2,[[[("At the time,","那时，"),("**freight**","**货物**(freight)"),("travelled **loose**.","都是**散装**(loose)运输。")],
     "（travelled loose：loose 作补语，\n说明货物运输时的状态）"]]),
(2,[[[("**Gangs**","一**帮**(gangs)"),("of twenty or more","二十多名或更多的"),("**dockworkers**","**码头工人**(dockworkers)，")],
     "（of twenty or more dockworkers：of 结构作后置定语，修饰 Gangs）"],
    [[("carried","一件件地搬运"),("**sacks**,","**麻袋**(sacks)、"),("**barrels**,","**桶**(barrels)"),("and **crates** piece by piece.","和**板条箱**(crates)。")],
     "（piece by piece：一件一件地）"]]),
(2,[[[("It was","这是"),("**strenuous**","**繁重的**(strenuous)"),("**drudgery**.","**苦差事**(drudgery)。")]]]),
(2,[[[("Ships","船舶"),("could spend","有时"),("up to half their time","多达一半时间"),("**berthed**,","**停泊**(berthed)在港，")],
     "（spend time＋过去分词：花时间处于……状态；up to：多达）"],
    [[("and **theft**","**偷窃**(theft)"),("was **rampant**.","**猖獗**(rampant)。")]]]),
(2,[[[("In 1956","1956年，"),("loading","装运"),("loose cargo","散货"),("cost about $5.83 a ton;","每吨约需5.83美元；")],
     "（loading loose cargo：动名词短语作主语）"],
    [[("loading the Ideal X cost, by the company's reckoning,","而据公司估算，给理想X号装货"),("about 16 cents.","每吨只要约16美分。")],
     "（by the company's reckoning：插入语，据公司估算）"]]),
(3,[[[("Containers","集装箱"),("were not new.","并不新鲜。")]]]),
(3,[[[("The **hurdle**","真正的**障碍**(hurdle)"),("was **consensus**:","在于**共识**(consensus)：")]],
    [[("**rival**","**相互竞争的**(rival)"),("firms'","各家公司，"),("boxes","箱子"),("had **incompatible** **dimensions** and **latches**.","**尺寸**(dimensions)和**锁扣**(latches)**互不兼容**(incompatible)。")],
     "（had incompatible dimensions：\n中文把 incompatible 放到最后作谓语）"]]),
(3,[[[("An international standards committee formed in 1961.","1961年，一个国际标准委员会成立。")],
     "（form：（组织）成立）"]]),
(3,[[[("In January 1963","1963年1月，"),("Sea-Land, the Ideal X's renamed operator,","理想X号的运营方、已更名的海陆公司（Sea-Land）")],
     "（the Ideal X's renamed operator：同位语，补充说明 Sea-Land）"],
    [[("let","允许"),("the committee","该委员会"),("use","使用"),("its **patents**","其**专利**(patents)，"),("free of","不收"),("**royalties**,","**专利费**(royalties)，")],
     "（let sb do：让某人做；free of：免除，不收）"],
    [[("including","其中包括"),("those on corner **fittings** for **hoisting**.","用于**吊装**(hoisting)的角**配件**(fittings)。")],
     "（those 指 patents；for hoisting：后置定语，修饰 fittings）"]]),
(3,[[[("Lifted by **crane**,","由**吊机**(crane)吊起，"),("a box","一只箱子")],
     "（Lifted by crane：过去分词短语作状语）"],
    [[("could be","便能"),("**transferred** **smoothly** between ship, **lorry**, and train.","在船舶、**卡车**(lorry)和火车之间**顺畅地**(smoothly)**转运**(transferred)。")],
     "（between A, B, and C：在 A、B 和 C 之间，中文状语提前）"]]),
(4,[[[("This **efficiency**","这种**效率**(efficiency)"),("came **at the expense of** **livelihoods**.","是**以**(at the expense of)**生计**(livelihoods)**为代价**(at the expense of)换来的。")],
     "（come at the expense of：以……为代价换来）"]]),
(4,[[[("New York's","1963年至1976年间，纽约"),("**waterfront**","**滨水区**(waterfront)"),("employment","的就业"),("**shrank**","**缩减了**(shrank)"),("by about three quarters between 1963 and 1976.","约四分之三。")],
     "（shrink by：缩减了（幅度）；between 1963 and 1976：中文时间状语提前）"]]),
(4,[[[("Much of the cargo","大量货物"),("crossed","越过"),("the harbour","港湾，")]],
    [[("to a new **terminal** at Elizabeth, **inaugurated** in August 1962.","转往伊丽莎白港1962年8月**启用**(inaugurated)的新**货运站**(terminal)。")],
     "（inaugurated in August 1962：过去分词短语作后置定语，\n修饰 terminal）"]]),
(4,[[[("Most of London's","1967年到1980年，伦敦大部分"),("**historic**","**历史悠久的**(historic)"),("**docks**","**码头**(docks)"),("closed one after another from 1967 to 1980,","接连关闭，")],
     "（one after another：一个接一个地；from 1967 to 1980：中文时间状语提前）"],
    [[("while","而"),("Felixstowe, on the Suffolk coast,","萨福克海岸的费利克斯托港"),("**expanded**.","则不断**扩张**(expanded)。")],
     "（while：表示对比，而；on the Suffolk coast：插入语，补充说明 Felixstowe）"]]),
(5,[[[("The **rewards**","**回报**(rewards)"),("were **substantial**.","相当**可观**(substantial)。")]]]),
(5,[[[("A study published in the Journal of International Economics in 2016","2016年发表于《国际经济学杂志》（Journal of International Economics）的一项研究"),("estimated","估计，")],
     "（published in…：过去分词短语作后置定语，修饰 study）"],
    [[("that containerisation","20年间，集装箱化"),("had lifted trade between","使"),("**industrialised**","**工业化**(industrialised)"),("countries","国家之间的贸易"),("by a **cumulative**","**累计**(cumulative)"),("700 per cent over 20 years.","增长了700%。")],
     "（that…：宾语从句；lift A by B：使 A 增长 B；over 20 years：20年间）"]]),
(5,[[[("**Tireless**","如今，**不知疲倦的**(tireless)"),("cranes now","吊机"),("lift","把"),("identical","一模一样的"),("containers","集装箱吊起，"),("into","码成"),("**orderly**,","**整齐的**(orderly)、"),("**immense**","**巨大的**(immense)"),("**stacks**.","**箱垛**(stacks)。")],
     "（lift A into B：把 A 吊起码成 B）\n"
     "（简述：1956年4月，改装的二战油轮理想X号载着58个集装箱驶离纽瓦克港，开往休斯敦。\n"
     "那时货物都是散装，码头工人逐件搬运，船舶多半时间停泊在港，偷窃猖獗；据公司估算，理想X号装货每吨只要约16美分。\n"
     "集装箱早已有之，难的是统一标准；1963年海陆公司把专利免费给标准委员会使用，箱子从此能在船舶、卡车和火车之间顺畅转运。\n"
     "效率的代价是码头工人的生计：纽约滨水区就业缩减约四分之三，伦敦的老码头接连关闭，费利克斯托港则不断扩张。\n"
     "回报也相当可观：研究估计，集装箱化20年间使工业化国家之间的贸易累计增长700%。）"]]),
]
G={
 "S2 trailer bodies detached from their wheels and chassis":"对齐不了：detached from their wheels and chassis 是后置定语，修饰 bodies，中文“从车轮和底盘上拆卸下来的挂车车厢”定语必须提前；detach from 被“车轮和底盘”隔开（T23 两处都标）；重点词中文先后与英文相反",
 "S8 cost about $5.83 a ton":"对齐不了：a ton 中文“每吨”必须提前到金额前",
 "S8 loading the Ideal X cost, by the company's reckoning":"对齐不了：插入语 by the company's reckoning 中文“据公司估算”必须提前到句首",
 "S10 had incompatible dimensions and latches":"对齐不了：incompatible 作定语修饰 dimensions and latches，中文“尺寸和锁扣互不兼容”放到最后作谓语；重点词中文先后与英文相反",
 "S5 carried":"对齐不了：piece by piece 中文“一件件地”提前到“搬运”前，只能和 carried 放一组",
 "S5 and crates piece by piece":"对齐不了：piece by piece 已随“搬运”提前，这里只剩“和板条箱”",
 "S8 loose cargo":"对齐不了：loose cargo 中文是一个词“散货”，拆开不通",
 "S12 Sea-Land, the Ideal X's renamed operator":"对齐不了：同位语 the Ideal X's renamed operator 中文“理想X号的运营方、已更名的”必须提前到“海陆公司”前",
 "S15 by about three quarters between 1963 and 1976":"对齐不了：between 1963 and 1976 中文“1963年至1976年间”提前到句首（在 New York's 下面），这里只剩“约四分之三”",
 "S17 closed one after another from 1967 to 1980":"对齐不了：one after another 中文“接连”必须放到“关闭”前，from 1967 to 1980 中文提前到句首",
 "S19 had lifted trade between":"对齐不了：lift A by B 中文“使 A 增长了 B”，lifted 的“增长了”必须放到句末；trade between… 中文“国家之间的贸易”定语提前，trade 的“贸易”只能放到 countries 下面",
 "S19 700 per cent over 20 years":"对齐不了：700 per cent 中文“700%”是一个数；over 20 years 中文“20年间”提前到句首",
 "S20 cranes now":"对齐不了：now 中文“如今”必须提前到句首（在 Tireless 下面）",
 "S11 An international standards committee formed in 1961":"对齐不了：in 1961 中文“1961年”必须提前到句首",
 "S12 those on corner fittings for hoisting":"对齐不了：for hoisting 是后置定语，修饰 fittings，中文“用于吊装的角配件”必须提前；两个重点词中文先后与英文相反",
 "S13 transferred smoothly between ship, lorry, and train":"对齐不了：between… 介词短语中文“在船舶、卡车和火车之间”必须提前到动词前，smoothly 中文“顺畅地”也在“转运”前；重点词中文先后与英文相反",
 "S14 came at the expense of livelihoods":"对齐不了：come at the expense of B 中文“是以 B 为代价换来的”，被“生计”隔开，只能整组",
 "S16 to a new terminal at Elizabeth, inaugurated in August 1962":"对齐不了：at Elizabeth 和 inaugurated in August 1962 都是后置定语，修饰 terminal，中文“伊丽莎白港1962年8月启用的新货运站”必须提前；两个重点词中文先后与英文相反",
 "S17 Felixstowe, on the Suffolk coast":"对齐不了：插入语 on the Suffolk coast 中文“萨福克海岸的”作定语必须提前",
 "S19 A study published in the Journal of International Economics in 2016":"对齐不了：published in… in 2016 是后置定语，修饰 study，中文“2016年发表于《国际经济学杂志》的一项研究”必须提前，刊名不能拆",
}
DQ={
 "S2-2 trailer bodies detached from t":"detached from… 是后置定语，修饰 bodies，中文“从车轮和底盘上拆卸下来的挂车车厢”定语必须提前，重点词中文先后与英文相反",
 "S8-1 cost about $5.83 a ton;":"a ton 中文“每吨”必须提前到金额前",
 "S8-2 loading the Ideal X cost, by t":"插入语 by the company's reckoning 中文“据公司估算”必须提前到句首",
 "S10-2 had incompatible dimensions an":"incompatible 中文“互不兼容”放到最后作谓语，重点词中文先后与英文相反",
 "S11-1 An international standards com":"in 1961 中文“1961年”必须提前到句首",
 "S12-1 Sea-Land, the Ideal X's rename":"同位语 the Ideal X's renamed operator 中文“理想X号的运营方、已更名的”必须提前到“海陆公司”前",
 "S12-3 those on corner fittings for h":"for hoisting 是后置定语，修饰 fittings，中文必须提前",
 "S13-2 transferred smoothly between s":"between… 介词短语中文必须提前到动词前",
 "S14-1 came at the expense of livelih":"come at the expense of B 中文“是以 B 为代价换来的”，被“生计”隔开，只能整组",
 "S15-1 by about three quarters betwee":"between 1963 and 1976 中文“1963年至1976年间”提前到句首（放在 New York's 下面）",
 "S16-2 to a new terminal at Elizabeth":"at Elizabeth、inaugurated in August 1962 都是后置定语，修饰 terminal，中文必须提前",
 "S17-1 closed one after another from ":"from 1967 to 1980 中文“1967年到1980年”提前到句首（放在 Most of London's 下面）",
 "S17-2 Felixstowe, on the Suffolk coa":"插入语 on the Suffolk coast 中文作定语必须提前",
 "S19-1 A study published in the Journ":"published in… in 2016 是后置定语，修饰 study，中文必须提前，刊名不能拆",
 "S19-2 700 per cent over 20 years.":"over 20 years 中文“20年间”提前到句首（放在 that containerisation 下面）",
 "S7-1 up to half their time":"up to half their time 是一个数量意群“多达一半时间”，拆开不通",
}
CONF={"合组":G,"对齐":DQ,
"引号":{"S1-1 “”":"用户 2026-11-08 原话（converted 后按用户“意思为改造过的”改成“改造过的”）“1956年4月26日，一艘改装过的二战油轮“理想X号”，悄然驶离新泽西州纽瓦克港，开往休斯敦。”自带引号，照用户原话保留（T10）"},
"是的":{"S6-1 是**繁重的**":"“是”对应 was（这是），“的”是形容词 strenuous 的“的”（T38），不是“是……的”句式；文章定稿原文“这是繁重的苦差事”"},
"方向":{"S5-1 more→二十多名或更多的":"or more 是“或更多”，中文“或更多的”，方向一致","S17-1 after→接连关闭，":"one after another 是“一个接一个”，不是时间先后；中文“接连”，方向一致"},
"停顿位置":{
 "S1 Jersey, / for @9.675":"2026-11-07 逐 2.5 ms 实测（S1 w）：Jersey 的 i 浊音到 9.665（周期 0.47），9.675–9.69 是两词之间的低谷（-39～-40 dB、周期 0.18），9.6975 起 for 的 /f/（重心 4.9–6.4 kHz）；停顿 9.675 落在低谷里，在两词之间",
 "S5 barrels, / and @3.800":"2026-11-07 逐 2.5 ms 实测（S5 w）：barrels 的 /z/ 擦音到 3.7975（重心 4.7–5.6 kHz），3.80 是低谷（-22.8 dB），3.805 起 and 的元音（周期 0.49、重心 2 kHz 以下）；停顿 3.800 正落在两词之间",
 "S4 time, / freight @0.643":"2026-11-07 逐 2.5 ms 实测（S4 w）：time 的 m 浊音到 0.6385（周期 0.37–0.41、重心 0.8 kHz），0.641 低谷 -30.6 dB，0.6435 起 freight 的 /f/（重心 2.7→5–7 kHz，到 0.78），0.785 起 r 元音；停顿插入点写在交界过零点 0.642792，在两词之间（离前词末音素起点 +19 ms 是因为 m 本身就短）",
 "S1 Newark, / New @8.870":"2026-11-07 逐 2.5 ms 实测（S1 w）：Newark 的 /k/ 原声除阻 8.8325–8.845（-27 dB）、送气到 8.865（-39～-45 dB），8.8675–8.8725 低谷（-45.8～-47.8 dB），8.8725 起 New 的 n 起音（周期 0.28→0.38，8.8925 -12.8 dB）；停顿 8.870 落在低谷里，/k/ 除阻送气在前、n 在后，在两词之间",
 "S13 lorry, / and @4.665":"2026-11-07 逐 2.5 ms 实测（S13 w）：lorry 的 i 与 and 的 æ 浊音连读、没有静音（周期 0.46–0.48 一直连着）；i 的重心 1.5–2.7 kHz 到 4.67，4.675 起降到 0.6–1 kHz（æ）；停顿 4.665 落在两个元音的交界上，在两词之间，同 60 S11 law, / which"},
"非人声":{"27.32–27.36s": {"配音指纹": "7499cce91ea3", "依据": "S3 w 4.59–4.635s：2026-11-07 逐 2.5 ms 实测（疑点清单 dossier_61）：S3 landmark. 的 /k/ 除阻：4.53–4.585 闭塞 -63～-69 dB，4.5925 爆出 -32 dB（重心 3.5 kHz、低频 -20 dB），衰减到 4.64；句末词尾塞音除阻", "实测": {"最响dB": -32.8, "重心Hz": 3414, "周期": 0.22, "低频dB": -14.0}}, "35.06–35.08s": {"配音指纹": "7499cce91ea3", "依据": "S5 w 3.25–3.265s：2026-11-07 逐 2.5 ms 实测：S5 barrels 的 /b/ 浊音杠起头（3.25 -42 dB、周期 0.59），15 ms 后 3.265 起 -24 dB、重心 0.3–0.4 kHz 的浊音杠，接 æ；词头的一部分", "实测": {"最响dB": -38.7, "重心Hz": 1571, "周期": 0.0, "低频dB": -1.9}}, "54.44–54.48s": {"配音指纹": "7499cce91ea3", "依据": "S8 w 8.63–8.67s：2026-11-07 逐 2.5 ms 实测：S8 cost, 的 /t/ 除阻：/s/ 到 8.60（重心 5.5 kHz），8.6175–8.625 闭塞 -65～-67 dB，8.6325 爆出 -34 dB（重心 3.5 kHz），衰减到 8.665；词尾塞音除阻", "实测": {"最响dB": -31.9, "重心Hz": 3334, "周期": 0.15, "低频dB": -11.3}}, "80.02–80.03s": {"配音指纹": "7499cce91ea3", "依据": "S12 w 6.465–6.48s：2026-11-07 逐 2.5 ms 实测：S12 let 起音前 15 ms 的气流（-48～-55 dB），6.48 起 /l/（-39.5→-25.9 dB），中间没有低谷；紧贴词头，起音的一部分", "实测": {"最响dB": -48.1, "重心Hz": 3102, "周期": 0.0, "低频dB": -2.9}}, "91.42–91.47s": {"配音指纹": "7499cce91ea3", "依据": "S13 w 3.955–3.995s：2026-11-07 逐 2.5 ms 实测：S13 ship, 的 /p/ 除阻：3.89–3.95 闭塞 -55～-68 dB，3.9575 爆出 -40.6 dB（重心 2.6→1.2 kHz），衰减到 3.99；词尾塞音除阻", "实测": {"最响dB": -30.5, "重心Hz": 2007, "周期": 0.31, "低频dB": -9.4}}, "103.84–103.88s": {"配音指纹": "7499cce91ea3", "依据": "S15 w 5.71–5.74s：2026-11-07 逐 2.5 ms 实测：S15 and 的浊音起头（-40～-43 dB、低频 -0.2～-0.9 dB、周期 0.46），5.75 起 -26 dB 元音；前面的吸气已删到 5.7125；词头的一部分", "实测": {"最响dB": -41.0, "重心Hz": 2531, "周期": 0.35, "低频dB": -0.5}}, "121.16–121.20s": {"配音指纹": "7499cce91ea3", "依据": "S17 w 6.51–6.555s：2026-11-07 逐 2.5 ms 实测：S17 while 的 /w/ 浊音起头（-41～-47 dB、低频 -0.4～-1.3 dB、周期 0.2–0.36），6.56 起 -27.5 dB、重心 0.8 kHz；前面的吸气删到 6.51 低谷；词头的一部分", "实测": {"最响dB": -42.3, "重心Hz": 1918, "周期": 0.37, "低频dB": -0.5}}, "123.83–123.88s": {"配音指纹": "7499cce91ea3", "依据": "S17 w 8.85–8.90s：2026-11-07 逐 2.5 ms 实测：S17 coast, 的 /t/ 除阻：/s/ 到 8.82，8.83–8.845 闭塞 -56～-62 dB，8.8525 爆出 -33 dB（重心 3.1 kHz），衰减到 8.89；词尾塞音除阻", "实测": {"最响dB": -30.2, "重心Hz": 3329, "周期": 0.18, "低频dB": -12.7}}, "142.91–143.07s": {"配音指纹": "7499cce91ea3", "依据": "S19 w 14.675–14.835s：2026-11-07 逐 2.5 ms 实测：S19 years. 词内：ɹ 元音到 14.67（-20～-30 dB），14.68–14.81 是 -37～-56 dB、重心 1–2 kHz、低频 -2～-10 dB 的浊音过渡，14.8125 起 /z/ 擦音（3.5–5.5 kHz）；在 ɹ 和 z 之间，词的一部分", "实测": {"最响dB": -35.3, "重心Hz": 1767, "周期": 0.19, "低频dB": -2.5}}, "142.98–143.00s": {"配音指纹": "7499cce91ea3", "依据": "S19 w 14.74–14.755s：同上，years. 的 ɹ→z 浊音过渡中间一帧（-43 dB、低频 -1.3 dB），词的一部分", "实测": {"最响dB": -43.4, "重心Hz": 1358, "周期": 0.0, "低频dB": -1.3}}},
"机器复听":{"S2": {"配音指纹": "7499cce91ea3", "依据": "2026-11-07：Clamped to her deck，clamped 的 /t/ 与后面 to 的 /t/ 连读成一个闭塞（正常连读），small.en 拼成 clamp；parakeet 听对。读音按词典，非读错"}, "S8": {"配音指纹": "7499cce91ea3", "依据": "2026-11-07：$5.83 按 spoken() 读 five dollars eighty-three cents（数字读法清单已核），脚本原文是 $5.83 符号，比对时“dollars”“cents”算多出/对不上；两个识别器都听到 dollars，读法正确"}, "S12": {"配音指纹": "7499cce91ea3", "依据": "2026-11-07：the Ideal X's renamed operator，X's 的 /ɪz/ 连到 renamed 的 /ɹɪ/，small.en 断成 X were named；parakeet 听对 renamed。整句音标 ˈɛksᵻz ɹᵻnˈeɪmd，读音正确"}},
"删除段":{
 "S13 raw 1.1150-1.3636":{"类型": "紧贴词头的非人声", "配音指纹": "7499cce91ea3", "依据": "2026-11-07 S13 crane, 后停顿里的吸气（自动切点 非人声区间 S13 [1.12, 1.353625, 紧贴词头]，删掉最响 -38.3 dB、无周期），一直贴到 a 的起音，词头切在过零点，a 本身不动"},
 "S15 raw 5.5100-5.7224":{"类型": "紧贴词头的非人声", "配音指纹": "7499cce91ea3", "依据": "2026-11-07 逐 2.5 ms 实测（S15 w）：sixty-three 与 and 之间（无标点）5.51–5.705 约 200 ms -43～-50 dB、周期 0.15–0.26、重心 2.3–3 kHz 的吸气（删掉最响 -37.3 dB 即此）；5.72 起 and 的浊音起头，紧贴词头切在过零点 5.7125"},
 "S17 raw 6.1350-6.5301":{"类型": "紧贴词头的非人声", "配音指纹": "7499cce91ea3", "依据": "2026-11-07 逐 2.5 ms 实测（S17 w）：1980, 后停顿里的吸气（-40～-45 dB、低频 -17～-22 dB，删掉最响 -39.4 dB 即此）到 6.505，6.51 是 -54.6 dB 低谷，6.515 起 while 的 /w/ 浊音起头；终点在过零点 6.510167，/w/ 不动"},
 "S19 raw 5.0312-5.5400":{"类型": "紧贴词尾的非人声", "配音指纹": "7499cce91ea3", "依据": "2026-11-07 逐 2.5 ms 实测（S19 w）：2016 的 n 到 5.02 收尾，5.04 一下 -47.5 dB 残声，5.25–5.455 约 210 ms -44～-56 dB、重心 2.0–2.9 kHz 的吸气（删掉最响 -41.3 dB 即此），5.47 一帧 -59 dB 残声，5.545 起 estimated；起点在过零点 5.03125 紧贴 2016 词尾，终点外侧 5 ms < -55 dB"},
 "S12 raw 3.1700-3.5850":"2026-11-07 逐 2.5 ms 实测（S12 w）：Sea-Land, 后停顿：3.17–3.19 -61 dB 静音，3.21–3.53 -42～-54 dB 的吸气（删掉最响 -39.5 dB 即此），3.55–3.57 -60～-61 dB，3.59 起 the（-31 dB）；两侧 -55.2/-61.6 dB 已衰减干净，删掉的是停顿中间的换气声",
 "S19 raw 10.8450-11.2300":"2026-11-07 逐 2.5 ms 实测（S19 w）：countries 后、by 前：10.85 -60 dB，10.87–11.15 -44～-53 dB 的吸气，11.17 一下 -37.7 dB 声门噪声，11.21–11.23 -64～-68 dB；两侧 -63.1/-61.4 dB 已衰减干净，删掉的是换气声"},
"同词异译":{"at the expense of：为代价/以":"不是两种译法：at the expense of 的意思“以……为代价”被“生计”隔开，“以”和“为代价”是同一个意思的两部分（T23）"},
"短语":{
 "S1 slipped … for":"不是搭配：for Houston 只表示去向（开往休斯敦），slip out of 已整体标",
 "S2 Clamped … to":"不是搭配：to her deck 只表示固定的位置（甲板上），clamp 单独就是“固定”，同 60 S2 observed … from",
 "S5 Gangs … of":"不是搭配：of twenty or more dockworkers 只说明是什么人的一帮，gang 单独就是“（工人）一帮”",
 "S12 patents … on":"不是搭配：on 属于 those on corner fittings（关于角配件的那些专利），和 patents 本身无关",
 "S12 royalties … on":"不是搭配：on 属于 those on corner fittings，和 royalties 无关",
 "S13 by … crane":"不是搭配：by crane 是 by＋工具（用吊机），和 by lorry、by hand 一样是普通用法，不像 in flocks 那样有独立意思；crane 单独就是“吊机”，“由”已译出 by",
 "S15 shrank … by":"不是搭配：by about three quarters 只表示幅度（缩减了约四分之三），shrink 单独就是“缩减”",
 "S16 inaugurated … in":"不是搭配：in August 1962 只表示时间"}}
out={"no":"61","title_en":"The Steel Box That Remade the World","title_zh":"集装箱：重塑世界的铁盒子","title_fx":{"hl":["Box","World"],"ghost":[]},"sentences":[],"核对确认":CONF,"结尾解说":"简述",
     "allow_clash":["converted","crates"],"高亮按实际开口":True,"高亮开口门槛":40,
     "术语":{"Second World War":"二战","Ideal X":"理想X号","Port Newark":"纽瓦克港","New Jersey":"新泽西州","Houston":"休斯敦","Sea-Land":"海陆公司","New York":"纽约","Elizabeth":"伊丽莎白港","London":"伦敦","Felixstowe":"费利克斯托港","Suffolk":"萨福克","Journal of International Economics":"《国际经济学杂志》"}}
out.update({"停顿插入点":{"S4":{"1":[0.642792,"交界"]}},"停顿删除区间":{"S7":{"1":[2.3725,2.6625]}},"除阻加强":{"S1":{"3":[8.8325,8.8475,4.5]}},"句子增益dB":{"S9":-0.3,"S6":-0.5,"S18":-0.5},"高亮开始":{"S19 第2块":134.64},"段内渐变dB":{"S12":{"2":[0,3]}},
 "非人声区间":{"S1":[[5.535,5.83]],"S15":[[5.5,5.7125,"紧贴词头"]],"S16":[[7.310625,7.3925,"紧贴词尾"]],"S17":[[6.245,6.510167,"紧贴词头"]],"S19":[[5.03125,5.54,"紧贴词尾"],[10.855,11.195]]}})
# 2026-11-07 出片后核查逐 2.5 ms 实测（疑点清单 dossier_61，各句 w）：
# S1 非人声区间终点 5.785→5.8475：tanker, 停顿后 5.80–5.83 一团 -46～-51 dB 低频（低频占比 -0.4 dB）小声，与 the 的 ð（5.865 起 -27.8 dB）之间隔着 5.83–5.845 的 -57 dB 低谷，不是词；收在 5.83（后 5 ms -57.7 dB，出片守门要求不贴词的一头外侧 < -55 dB）
# S15 非人声区间 [5.4975, 5.7125]：sixty-three 的 iː 到 5.475，5.51–5.705 约 200 ms -43～-50 dB、周期 0.15–0.26、低频 -6～-25 dB、重心 2.3–3 kHz 的吸气（无标点处换气）；5.72 起 and 的浊音起头（低频 -0.2～-0.9 dB），紧贴词头切
# S16 非人声区间 [7.31, 7.3925]：1962. 句末 two 的 uː 衰减到 7.305，7.31 -54.2 dB 低谷后又起一小团 -36.5～-48 dB 浊音（挤喉收尾），不是词的元音；删到 7.3925（-60.9 dB）
# S17 非人声区间终点 6.529167→6.51：1980, 后吸气（-40～-45 dB、低频 -17～-22 dB）到 6.505，6.51 是 -54.6 dB 低谷，6.515 起 while 的 /w/ 浊音起头（低频 -0.4～-1.3 dB），原终点切进起头 10 ms（独立复核 onset=10ms），改到低谷
# S19 非人声区间加 [5.03125, 5.4625, 紧贴词尾]（起点原 5.245：无标点停顿核对把 5.04 一下 -47.5 dB 的残声（前后 -57/-61 dB）并进停顿量出 0.26 s，出片压缩不并它；起点提前到过零点 5.03125 把它一起换成静音，2016 的 n 到 5.02 不动；终点原 5.4625 再延到 5.54：5.47 还有一帧 -59 dB 残声把静音隔成 0.17＋0.075 两段，出片不压缩、核对并起来量 0.26 s；5.54 外侧 5 ms 仍 < -55 dB，estimated 5.545 起不动）：2016 与 estimated 之间（无标点）5.25–5.455 约 210 ms -44～-56 dB、重心 2.0–2.9 kHz、低频 -10～-23 dB 的吸气，5.44–5.455 低频小声；两头 5.245 -60.1 dB、5.4625 -66.9 dB；5.545 起 estimated
# S19 高亮开始 第2块 134.64：高亮同步核对两种独立办法一致（乙 134.63、甲 134.65），自动高亮 134.84 推后 0.21 s，取两法之中
# S6/S18 句子增益 -0.5：响度一致性 S6（It was strenuous drudgery.）+2.3 LU、S18（The rewards were substantial.）+2.2 LU，短句偏响，各压 0.5 dB 到 ±2 LU 内
# S12 段内渐变 第2段 [0, +3]：自动音频检查 79.2–79.6s 比全片低 5.1 dB（K129），即第 2 段 the Ideal X's renamed operator, 段尾 operator 收尾偏轻；只抬段尾，段头不动
# S9 句子增益 -0.3 dB（主会话 2026-11-07 定②“S9 重合成换一版”；合成是确定的、S9 无逗号可换合成标点，没有换版开关，改用听不出的 -0.3 dB 换一版）：成片（AF＋AAC 后）S9 直流偏移 0.000158 超 01–24 最差 0.000147；实测 S9 均值 -1.2e-5 是编码的随机残差（各句 0～0.00008 乱跳，S9 最短 1.4 秒比值最大），模拟 -0.3 dB 后 0.000023
# S1 除阻加强 第3个标点（Newark, 的 /k/，K124 照 46 S4）：2026-11-07 逐 2.5 ms 实测（S1 w）：ɚ 衰减后 8.80–8.83 闭塞（-53～-60 dB），8.8325–8.845 原声除阻（-27 dB、重心 2.7–3.3 kHz、低频 -23～-29 dB），8.85–8.88 送气 -39～-45 dB，8.885 起 New 的 n；程序自动移植的 [8.865, 8.87] 落在送气里，成两下 /k/（双爆破），删掉移植，只加强原声那一下；加 3 dB 后 2 kHz 以上 -36.1 dB 差 0.1 dB，改 4.5 dB
# S4 停顿插入点：2026-11-07 逐 2.5 ms 实测（S4 w）：time 的 m 浊音到 0.6385（周期 0.37–0.41、重心 0.8 kHz），0.641 低谷 -30.6 dB，0.6435 起 freight 的 /f/（重心 2.7→5–7 kHz，到 0.78），0.785 起 r 元音；程序原定 0.690 切在 /f/ 中间，改到交界过零点 0.642792
# S7 停顿删除区间：2026-11-07 逐 2.5 ms 实测（S7 w）：berthed 的 /t/ 闭塞 2.30（-63 dB）、除阻 2.3125–2.35，衰减到 2.3625（-54.8）；2.3725–2.6625 约 290 ms 是 -48～-55 dB、周期 0.1–0.3、重心 2–2.6 kHz 的气声（吸气）；2.6825 起 and；删 [2.3725, 2.6625)，两头 -61.9 / -58.4 dB，/t/ 除阻和 and 都不动
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 核对 import 生成并核对
生成并核对(S, out)
