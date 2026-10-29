import json,re,glob,os
# 第32篇初稿（逐词对照）：S = [(段, [chunk, ...])]，chunk = ([(英文组, 中文组), ...], 可选 note)
# 2026-10-29 重点词中文沿用文章定稿（铁律），只按《翻译风格》调格式；非重点词也逐词对齐（G47）；短语型用法整体标（T22）；不用破折号（T36）。
S=[
(1,[[[("On 18 February 1930,","1930年2月18日，"),("comparing **photographic** plates at the Lowell Observatory,","在洛厄尔天文台比对**照相**(photographic)底片时，")],
     "（comparing…：现在分词短语作时间状语；\nLowell Observatory：洛厄尔天文台）"],
    [[("the **astronomer**","**天文学家**(astronomer)"),("Clyde Tombaugh","克莱德·汤博"),("**perceived**","**察觉**(perceived)到"),("a **dim**","一个**暗淡的**(dim)"),("**dot**","**小点**(dot)，")],
     "（the astronomer Clyde Tombaugh：\nthe astronomer 和人名是同位关系）"],
    [[("that","它"),("shifted between them.","在底片之间移动过。")],
     "（that shifted between them：定语从句，修饰 a dim dot；\nthem 指 plates）"]]),
(1,[[[("An eleven-year-old","一名11岁的"),("English girl","英国女孩"),("**put forward**","**提议了**(put forward)"),("the name,","它的名字，")],
     "（put forward：提出，提议）"],
    [[("after","名字取自"),("the Roman **deity** of the **underworld**.","罗马神话中的**冥界**(underworld)**神灵**(deity)。")],
     "（after…：以……命名；\nthe Roman deity of the underworld：罗马神话中的冥界之神）"]]),
(1,[[[("For 76 years","此后76年里，"),("Pluto","冥王星"),("held","一直占据"),("the ninth **slot** on the **planetary** **roster**.","**行星**(planetary)**名单**(roster)上的第九个**位置**(slot)。")],
     "（hold the ninth slot：占据第九个位置；\nslot：指名单、序列或时间表上的“位置、名额”；\non the planetary roster：介词短语作后置定语，修饰 slot）"]]),
(2,[[[("In January 2005,","2005年1月，"),("astronomers","天文学家"),("found","发现了"),("a **far-off** body,","一个**遥远的**(far-off)天体，")],
     "（body：天体）"],
    [[("later","它后来"),("named Eris,","被命名为厄里斯，"),("at first thought","起初被认为"),("larger than Pluto.","比冥王星还要大。")],
     "（later named Eris、at first thought larger than Pluto：\n两个过去分词短语作后置定语，修饰 a far-off body）"]]),
(2,[[[("NASA","美国航天局"),("briefly","曾短暂地"),("called it","称它为"),("the tenth","第十大"),("planet.","行星。")],
     "（call A B：称 A 为 B；\nNASA：美国国家航空航天局）"]]),
(2,[[[("The **contender**","这个**竞争者**(contender)"),("posed","造成了"),("an **awkward**","一个**尴尬的**(awkward)"),("**dilemma**.","**两难困境**(dilemma)。")],
     "（pose：造成，引发（问题、困难）；\ncontender 指 Eris；\ndilemma：指陷入“进退维谷”的境地，\n无论选择哪一方，都必须承受相应的损失或代价）"]]),
(2,[[[("The term \"planet\"","“行星”一词"),("had **hitherto**","**此前**(hitherto)一直被"),("been used **loosely**,","用得很**不严谨/宽泛**(loosely)，")],
     "（had been used：过去完成时的被动语态；\nhitherto：迄今，此前）"],
    [[("and with","而随着"),("more **icy** worlds","更多**冰冷**(icy)天体"),("likely","很可能"),("to be found,","被发现，")],
     "（with + 名词 + 不定式：with 复合结构，作原因状语）"],
    [[("a **precise**","一个**精确的**(precise)"),("**definition**","**定义**(definition)"),("became a **necessity**.","便成了**必需**(necessity)。")],
     "（become a necessity：成为必需）"]]),
(3,[[[("On 24 August 2006","2006年8月24日，"),("the International Astronomical Union,","国际天文学联合会"),("**convened** in Prague,","在布拉格**召开大会**(convened)，")],
     "（convened in Prague：过去分词短语作插入语，\n补充说明 the International Astronomical Union）"],
    [[("voted that","投票决定，"),("a planet","行星"),("must","必须"),("**revolve around**","**环绕**(revolve around)"),("the Sun,","太阳**运行**(revolve around)、")],
     "（that 引导宾语从句，作 voted 的宾语；\nrevolve around…：绕……运行）"],
    [[("be nearly **spherical**,","接近**球形**(spherical)，"),("and have cleared","并且已经清空"),("the **neighbourhood** around its orbit.","其轨道附近的**区域**(neighbourhood)。")],
     "（must revolve…, be…, and have cleared…：\n三个并列谓语，共用 must）"]]),
(3,[[[("Pluto","冥王星"),("failed","不符合"),("that last **criterion**","最后一条**标准**(criterion)，")],
     "（fail a criterion：不符合标准）"],
    [[("and","并"),("was **reclassified as**","被**重新归类为**(reclassified as)"),("a **dwarf** planet,","**矮行星**(dwarf)，"),("leaving eight.","行星只剩下八颗。")],
     "（reclassify A as B：把 A 重新归类为 B；\nleaving eight：现在分词短语作结果状语）"]]),
(3,[[[("Pluto","冥王星"),("was **physically**","在**物理上**(physically)"),("**unaltered**;","**毫无改变**(unaltered)，")],
     "（physically：物理上，实际上）"],
    [[("only","只有"),("the **boundary**","**界线**(boundary)"),("had moved.","移动了。")],
     "（分号连接两个前后对照的分句）"]]),
(4,[[[("The vote","这次表决"),("was **valid**,","**有效**(valid)，"),("yet","但"),("its **legitimacy**","其**正当性**(legitimacy)"),("drew **criticism**:","受到了**批评**(criticism)，")],
     "（draw criticism：招致批评；\n冒号后面说明受批评的原因）"],
    [[("only 424 of some 10,000 members","因为约1万名会员中只有424人"),("took part.","参加了投票。")],
     "（424 of some 10,000 members：约1万名会员中的424人；\nsome：大约）"]]),
(4,[[[("Hundreds of","数百名"),("**dissenting** astronomers","持**异议**(dissenting)的天文学家"),("signed","签署了"),("a **petition**.","一份**请愿书**(petition)。")],
     "（dissenting：持异议的，持不同意见的）"]]),
(4,[[[("The American Dialect Society","美国方言学会"),("made","把"),("\"plutoed\",","“plutoed”，"),("**playful**","这个**戏谑的**(playful)"),("**slang**","**俚语**(slang)，"),("for \"to **devalue**\",","意思是“**贬低**(devalue)”，"),("its word of 2006,","评为2006年度词汇，")],
     "（made A B：把 A 评为 B；\nplayful slang for \"to devalue\"：同位语，补充说明 plutoed）"],
    [[("and","而"),("New Mexico and Illinois","新墨西哥州和伊利诺伊州的"),("**lawmakers**","**立法者**(lawmakers)"),("passed","通过"),("resolutions","决议，"),("**affirming** that","**确认**(affirming)"),("Pluto was a planet.","冥王星是行星。")],
     "（affirming that…：现在分词短语作后置定语，修饰 resolutions）"]]),
(5,[[[("Amid the **controversy**,","就在一片**争议**(controversy)声中，"),("an **irony**","一件颇具**讽刺**(irony)意味的事"),("was already","早已"),("**in transit**.","**在途中**(in transit)。")],
     "（in transit：在途中，在运送中；\nirony：具有讽刺意味的事）"]]),
(5,[[[("New Horizons","新视野号"),("was launched on 19 January 2006,","于2006年1月19日发射，"),("seven months before the vote,","比那次表决早七个月，")],
     "（seven months before the vote：补充说明发射的时间）"],
    [[("carrying","携带着"),("a **pinch** of","**一小撮**(pinch)"),("Tombaugh's ashes.","汤博的骨灰。")],
     "（carrying…：现在分词短语作伴随状语；\na pinch of…：一小撮……）"]]),
(5,[[[("On 14 July 2015","2015年7月14日，"),("the **unmanned** craft","这艘**无人**(unmanned)飞船"),("flew","飞"),("past Pluto,","掠过冥王星，")],
     "（craft：飞行器，这里指飞船）"],
    [[("**transmitting**","**传回了**(transmitting)"),("images","图像，"),("of an **enormous**","图像上是一片**巨大的**(enormous)"),("**heart-shaped** plain,","**心形**(heart-shaped)平原，")],
     "（transmitting…：现在分词短语作伴随状语；\nof…：介词短语作后置定语，修饰 images）"],
    [[("**fittingly**","这片平原**恰如其分地**(fittingly)"),("named Tombaugh Regio.","被命名为汤博区。")],
     "（fittingly named…：过去分词短语作后置定语，修饰 plain；\nTombaugh Regio：汤博区）"]]),
(5,[[[("The **discoverer**'s","这位**发现者**(discoverer)的"),("ashes","骨灰"),("swept","掠"),("past","过了"),("the heart that bears his name.","那颗以他命名的心。")],
     "（that bears his name：定语从句，修饰 the heart；\nbear one's name：以某人的名字命名）\n"
     "（简述：1930年2月18日，汤博在洛厄尔天文台比对底片时发现了冥王星，\n"
     "名字由一名11岁的英国女孩提议，取自罗马神话中的冥界之神。\n"
     "此后76年里，它一直占据行星名单上的第九个位置。2005年1月发现的厄里斯\n"
     "起初被认为比冥王星还要大，“行星”需要一个精确的定义。2006年8月24日，\n"
     "国际天文学联合会在布拉格投票，规定行星必须绕日运行、接近球形，并且清空轨道附近区域；\n"
     "冥王星被重新归类为矮行星，行星只剩八颗。表决有效，但约1万名会员中只有424人投票，\n"
     "正当性受到批评：数百名天文学家签署请愿书，“plutoed”成了2006年度词汇，\n"
     "新墨西哥州和伊利诺伊州的立法者通过决议，确认冥王星是行星。\n"
     "新视野号在表决前七个月发射，带着汤博的一小撮骨灰，2015年7月14日飞掠冥王星，\n"
     "传回了心形平原的图像，这片平原被命名为汤博区。）"]]),
]
CONF={"合组":{
 "S1 comparing photographic plates at the Lowell Observatory":"对齐不了：at the Lowell Observatory 是地点状语，中文“在洛厄尔天文台比对照相底片时”地点必须放到动词前",
 "S2 the Roman deity of the underworld":"对齐不了：the deity of the underworld 是 of 结构，中文“冥界神灵”语序必须倒过来",
 "S3 the ninth slot on the planetary roster":"对齐不了：on the planetary roster 是后置定语修饰 slot，中文“行星名单上的第九个位置”定语必须提前",
 "S11 only 424 of some 10,000 members":"对齐不了：424 of some 10,000 members 中文“约1万名会员中只有424人”，of 结构语序必须倒过来",
 "S1 shifted between them":"对齐不了：between them 是地点状语，中文“在底片之间移动过”地点必须放到动词前",
 "S17 the heart that bears his name":"对齐不了：定语从句 that bears his name 中文“以他命名的心”定语必须提前"}}
def K(lab,en): return lab+" "+en[:30]
CONF["合组"].update({
 "S7 The term \"planet\"":"对齐不了：the term \"planet\" 中文“‘行星’一词”，“一词”(term) 必须放到“行星”后面",
 "S11 took part":"对齐不了：take part 是固定短语“参加”，拆开 took、part 中文没有各自的字",
 "S15 seven months before the vote":"对齐不了：seven months before the vote 中文“比那次表决早七个月”，时间量“七个月”必须放到后面"})
CONF["对齐"]={
 K("S1-1","comparing photographic plates at the Lowell Observatory,"):"at the Lowell Observatory 是地点状语，中文“在洛厄尔天文台比对照相底片时”地点必须放到动词前",
 K("S2-2","the Roman deity of the underworld."):"the deity of the underworld 是 of 结构，中文“冥界神灵”语序必须倒过来",
 K("S3-1","the ninth slot on the planetary roster."):"on the planetary roster 是后置定语修饰 slot，中文“行星名单上的第九个位置”定语必须提前",
 K("S8-3","the neighbourhood around its orbit."):"around its orbit 是后置定语修饰 neighbourhood，中文“其轨道附近的区域”定语必须提前",
 K("S11-2","only 424 of some 10,000 members"):"424 of some 10,000 members 中文“约1万名会员中只有424人”，of 结构语序必须倒过来",
 K("S15-1","was launched on 19 January 2006,"):"on 19 January 2006 是时间状语，中文“于2006年1月19日发射”时间必须放到动词前",
 K("S15-1","seven months before the vote,"):"before the vote 是比较，中文“比那次表决早七个月”，“七个月”必须放到后面",
 K("S17-1","the heart that bears his name."):"定语从句 that bears his name 中文“以他命名的心”定语必须提前"}
CONF["数字写法"]={"S2-1 eleven":"文章定稿中文写“11岁”（史实 T2：11岁英国女孩），数值相同；中文年龄用阿拉伯数字"}
CONF["数字"]={"S11-2 10,000":"some 10,000 中文按文章定稿写“约1万”，数值相同（10,000 = 1万）"}
CONF["牛津逗号"]={"S13 its word of 2006, and New Mexico and":"不是三项并列：第一个 and 连接两个分句（方言学会评词、两州立法者通过决议），New Mexico and Illinois 只有两项"}
CONF["短语"]={"S2 deity … of":"不是搭配：of the underworld 是后置定语，说明是哪里的神（冥界之神），deity 单独就是“神灵”",
 "S8 convened … in":"不是搭配：in Prague 是地点状语，convene 单独就是“召开（大会）”",
 "S13 slang … for":"不是搭配：for 引出这个俚语所表示的意思，中文“意思是”对应 for，slang 单独就是“俚语”",
 "S13 devalue … of":"不是搭配：of 属于后面的 its word of 2006（2006年度词汇），和 devalue 无关",
 "S15 pinch … of":"不是搭配：a pinch of A 是普通量词结构（一撮 A），同 a sum of；pinch 单独就是“一撮”，中文“一小撮”",
 "S16 transmitting … of":"不是搭配：of 属于 images of an enormous plain（……的图像），transmit 的宾语是 images"}
CONF["同词异译"]={"revolve around：环绕/运行":"不是两种译法：revolve around 的意思“绕……运行”被“太阳”隔开，“环绕”和“运行”是同一个意思的两段（T23）"}
CONF["方向"]={"S2-2 after→名字取自":"after 这里是“以……命名、取自”，不是时间先后，中文“名字取自”意思对"}
CONF["非人声"]={"21.39–21.48s": {"配音指纹": "a784afd9344b", "依据": "2026-10-29 32（S2 w 5.860–5.950s）：词尾浊音衰减：underworld 末尾 /l/→/d/ 闭塞前的浊音（重心 1.0–2.5 kHz、周期 0.2–0.3），从 -26 dB 连续衰减，/d/ 除阻在 w 5.98–6.01（-26 dB、3.3 kHz），属于 world 这个词（逐 5 ms 实测）", "实测": {"最响dB": -35.2, "重心Hz": 1655, "周期": 0.26, "低频dB": -2.5}}, "32.38–32.39s": {"配音指纹": "a784afd9344b", "依据": "2026-10-29 32（S4 w 4.075–4.090s）：词头浊音起始：body 的 /b/ 浊音杠，far-off 的 /f/（7 kHz）衰减到 -66 dB（w 4.0675）之后，重心从 2.7 kHz 降到 0.2–0.3 kHz、周期升到 0.5，接上 /b/ 后的元音（逐 2.5 ms 实测）", "实测": {"最响dB": -32.5, "重心Hz": 790, "周期": 0.0, "低频dB": -1.4}}, "51.09–51.12s": {"配音指纹": "a784afd9344b", "依据": "2026-10-29 32（S7 w 6.585–6.605s）：词头除阻前段：precise 的 /p/ 闭塞段里 -50～-54 dB 的低电平声，紧接 /p/ 除阻（w 6.605–6.61，-47→-12 dB、3.5–4.1 kHz），a 的元音已在 w 6.575 衰减到 -65 dB（逐 5 ms 实测）", "实测": {"最响dB": -50.4, "重心Hz": 2089, "周期": 0.44, "低频dB": -0.4}}, "51.73–51.75s": {"配音指纹": "a784afd9344b", "依据": "2026-10-29 32（S7 w 7.215–7.240s）：词头浊音起始：definition 的 /d/ 浊音杠（重心 0.5–0.7 kHz、周期 0.4），precise 的 /s/（5.8 kHz）在 w 7.195 衰减到 -66 dB 之后，紧接 /d/ 除阻（w 7.245，-19 dB、3.2 kHz）（逐 5 ms 实测）", "实测": {"最响dB": -30.6, "重心Hz": 805, "周期": 0.44, "低频dB": -0.1}}, "141.03–141.05s": {"配音指纹": "a784afd9344b", "依据": "2026-10-29 32（S17 w 1.600–1.615s）：词尾除阻：swept 的 /p/ 除阻（-42 dB、3.5 kHz），前面 /p/ 闭塞 w 1.585–1.595（-58～-61 dB），后面 /t/ 闭塞 w 1.615–1.63（-62 dB）再接 /t/ 除阻 w 1.635（逐 5 ms 实测）", "实测": {"最响dB": -35.6, "重心Hz": 3653, "周期": 0.0, "低频dB": -18.7}}}
CONF["删除段"]={"S4 raw 1.9550-2.2150": {"类型": "紧贴词尾的非人声", "配音指纹": "a784afd9344b", "依据": "2026-10-29 32 程序切的停顿（2005, 后）：five 的 /v/（4.7–5.2 kHz）衰减到 -54 dB（raw 1.955）直接接上停顿里的呼吸声（raw 1.96–2.17，-39～-47 dB、重心 2.0–3.2 kHz、周期 0.2），中间没有 -55 dB 低谷，只能紧贴切；右边 raw 2.21–2.215 降到 -57 dB，astronomers 元音 raw 2.23 起没碰（逐 5 ms 实测）"}, "S7 raw 2.8500-3.2857": "2026-10-29 32 实测：loosely, 后停顿里的吸气声（raw 3.08–3.285，-39～-55 dB、重心 2.1–2.6 kHz、周期 0.2）连同停顿删除；左边 raw 2.845 已降到 -57 dB，右边 raw 3.285 -55 dB、and 元音 raw 3.29 起没碰", "S7 raw 6.1000-6.4699": "2026-10-29 32 实测：found, 后停顿里的吸气声（raw 6.13–6.42，-41～-49 dB、重心 1.9–2.4 kHz）；左边 found 的 /d/ 除阻 raw 6.05 衰减到 -59 dB（raw 6.10），右边 raw 6.465 -62 dB，a 的元音 raw 6.475 起没碰", "S8 raw 7.1300-7.5082": {"类型": "紧贴两头的非人声", "配音指纹": "a784afd9344b", "依据": "2026-10-29 32 Prague, 后停顿：/g/ 除阻 raw 7.08（-21 dB、3 kHz）衰减到 -53 dB 后接上呼吸声（raw 7.14–7.17 回升到 -45 dB、重心 2.3–2.7 kHz），中间没有 -55 dB 低谷；右边停顿后残留 -46～-56 dB 低电平声紧贴 voted 的 /v/（raw 7.515 起 -38 dB、1.6 kHz），切在过零点 raw 7.5082，/v/ 没碰（逐 5 ms 实测）"}, "S11 raw 1.3200-1.6553": {"类型": "紧贴词头的非人声", "配音指纹": "a784afd9344b", "依据": "2026-10-29 32 valid, 后停顿：左边 raw 1.315 已降到 -57 dB；停顿后残留 -49～-57 dB 低电平声紧贴 yet 的 /j/（raw 1.66 起 -38→-20 dB、1.5 kHz），切在过零点 raw 1.6553，/j/ 没碰（逐 5 ms 实测）"}, "S13 raw 2.9355-3.1350": {"类型": "紧贴词尾的非人声", "配音指纹": "a784afd9344b", "依据": "2026-10-29 32 plutoed, 后：/d/ 除阻 raw 2.895–2.905（-20 dB、1.4–1.9 kHz）衰减到 -50 dB（raw 2.93）后接上呼出的气声（raw 2.945 起回升到 -44 dB、重心 2.2–2.4 kHz、周期 0.2，持续 150 ms），中间没有 -55 dB 低谷，切在过零点 raw 2.9355；右边 raw 3.09 起 -55～-67 dB（逐 5 ms 实测）"}, "S13 raw 10.1650-10.1800": "2026-10-29 32 实测：去底噪清掉的是 lawmakers 的 /k/ 闭塞段里 -56～-67 dB 的部分（最响 -55.9 dB），/eɪ/ 在 raw 10.16 已衰减到 -56 dB，/k/ 除阻 raw 10.19（-25 dB、4.2 kHz）没碰", "S13 raw 10.4735-10.6700": {"类型": "紧贴词尾的非人声", "配音指纹": "a784afd9344b", "依据": "2026-10-29 32 lawmakers 和 passed 之间：/z/（4.3–5 kHz）在 raw 10.47 衰减到 -55 dB，紧接回升的气声（raw 10.475 起 -44 dB、重心 3.3→2.3 kHz、周期 0.1–0.3）和低电平喉音（raw 10.595–10.63，-40～-50 dB），中间低谷只有一帧，切在低谷的过零点 raw 10.4735；“词尾被切 5 ms”是被删气声的头 5 ms（-44 dB、3.3 kHz，不是 /z/ 的 4.3–5 kHz）；右边 raw 10.635–10.67 -57～-65 dB，passed 的 /p/ 除阻 raw 10.68 起没碰（逐 5 ms 实测）"}, "S16 raw 2.7385-3.0350": "2026-10-29 32 实测：fifteen 和 the 之间的吸气声（raw 2.74–2.98，-38～-50 dB、重心 2.0–3.4 kHz、周期 0.2）；左边 /n/ 在 raw 2.735 降到 -57 dB，右边 raw 3.03–3.035 -61 dB，the 的 /ð/ raw 3.045 起没碰"}
out={"no":"32","title_en":"The Planet That Was Demoted","title_zh":"被降级的冥王星","title_fx":{"hl":["Planet","Demoted"],"ghost":[]},"sentences":[],"核对确认":CONF,"结尾解说":"简述",
     "说明放宽特批":{"S17":{"倍数":"整屏","依据":"用户 2026-10-25 看 25 简述截图：“以后以后一定要合理的安排，不要压缩成这个样子……这个地方特批一下”（用户同意记录：原话适用以后各篇，26 起沿用）"}},
     "合成标点":{"S4":[["body, later","body; later"]]},
     "非人声区间":{"S4":[[1.945042,2.2,"紧贴词尾"]],"S7":[[3.08,3.285708,"紧贴词头"]],"S8":[[2.809,3.095],[7.05,7.38,"紧贴词尾"],[7.385,7.42825,"紧贴词头"]],"S11":[[1.612,1.645292,"紧贴词头"]],
                  "S13":[[2.9155,3.075,"紧贴词尾"],[10.4535,10.615]],"S16":[[2.7285,3.02]]},
     "allow_clash":["dot"],"高亮按实际开口":True,"高亮开口门槛":40,
     "术语":{"Lowell Observatory":"洛厄尔天文台","Clyde Tombaugh":"克莱德·汤博","Tombaugh":"汤博","Pluto":"冥王星","Eris":"厄里斯","NASA":"美国航天局","International Astronomical Union":"国际天文学联合会","Prague":"布拉格","American Dialect Society":"美国方言学会","New Mexico":"新墨西哥州","Illinois":"伊利诺伊州","New Horizons":"新视野号","Tombaugh Regio":"汤博区"}}
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 核对 import 生成并核对
生成并核对(S, out)
