import json,re,glob,os
# 第42篇初稿（逐词对照）：S = [(段, [chunk, ...])]，chunk = ([(英文组, 中文组), ...], 可选 note)
# 2026-11-03 重点词中文沿用文章定稿（铁律），只按《翻译风格》调格式；短语型用法整体标（T22）；三项并列加牛津逗号（T18）；不用破折号（T36）。
S=[
(1,[[[("On 24 April 1990","1990年4月24日，"),("the space shuttle Discovery","发现号航天飞机"),("**lofted** the Hubble Space Telescope into orbit.","把哈勃空间望远镜**送上**(lofted)轨道。")],
     "（loft A into orbit：把 A 送上轨道）"]]),
(1,[[[("The **observatory** **cradled** in the **payload** bay","这座**安放**(cradled)在**有效载荷**(payload)舱里的**天文台**(observatory)"),("had cost","耗资"),("about","约"),("$1.5 billion,","15亿美元，")],
     "（cradled in…：过去分词短语作后置定语，修饰 observatory）"],
    [[("a **lavish**","是一笔**巨额**(lavish)"),("**investment**","**投资**(investment)，"),("meant to","旨在"),("fix its **gaze** on","把**目光**(gaze)投向"),("the **cosmos**","**宇宙**(cosmos)"),("and its **galaxies**.","及其中的**星系**(galaxies)。")],
     "（a lavish investment…：同位语，补充说明前面这笔钱；\nmeant to…：过去分词短语作后置定语，修饰 investment；\nfix one's gaze on…：把目光投向……）"]]),
(1,[[[("Money, it soon emerged,","人们很快发现，钱"),("could not buy **clarity**.","买不来**清晰**(clarity)。")],
     "（it soon emerged：插入语，人们很快发现）"]]),
(2,[[[("Its first **snapshots**","它最初的**快照**(snapshots)"),("came back","传回来时"),("**blurred**","**模糊**(blurred)不清、"),("and **fuzzy**.","**朦胧**(fuzzy)一片。")],
     "（come back＋形容词：传回来时是……的样子）"]]),
(2,[[[("In June 1990","1990年6月，"),("NASA","美国航天局"),("announced","宣布"),("a flaw in the main mirror:","主镜有缺陷，")],
     "（in the main mirror：介词短语作后置定语，修饰 flaw；\n冒号后面具体说明缺陷）"],
    [[("its outer **rim**","主镜外侧**边缘**(rim)"),("had been **flattened**","被**磨平了**(flattened)"),("by 2.2 micrometres,","2.2微米，")],
     "（by：表示相差的量）"],
    [[("roughly","大约相当于"),("a fiftieth of the **width** of a hair.","头发丝**宽度**(width)的五十分之一。")],
     "（a fiftieth：五十分之一；\nroughly a fiftieth of…：同位语，补充说明 2.2 micrometres）"]]),
(2,[[[("That **deviation**","这一**偏差**(deviation)"),("**marred**","**损害了**(marred)"),("the **optics**,","**光学系统**(optics)，")]],
    [[("leaving","使"),("light","光线"),("without","无法形成"),("a **sharp** focus.","**锐利的**(sharp)焦点。")],
     "（leaving…：现在分词短语作结果状语；\nleave A without B：使 A 没有 B）"]]),
(3,[[[("The trouble","问题"),("began with **calibration**.","始于**校准**(calibration)。")],
     "（begin with…：始于……）"]]),
(3,[[[("A **lens** in the **assembly** that checked the mirror's shape","检测主镜形状的那套**组件**(assembly)中，一块**透镜**(lens)"),("had been **offset**","**错位了**(offset)"),("by about","约"),("1.3 **millimetres**,","1.3**毫米**(millimetres)，")],
     "（in the assembly…：介词短语作后置定语，修饰 lens；\nthat checked…：定语从句，修饰 assembly）"],
    [[("so the mirror","主镜因此"),("was ground to","被磨成了"),("the wrong **curve**.","错误的**曲面**(curve)。")],
     "（ground：grind 的过去分词，研磨；\nbe ground to…：被磨成……）"]]),
(3,[[[("A second, independent test by the contractor, Perkin-Elmer,","承包商珀金-埃尔默公司做的第二次独立测试"),("gave","给出了"),("a **divergent** result,","**不同的**(divergent)结果，")],
     "（by the contractor：介词短语作后置定语，修饰 test；\nPerkin-Elmer：同位语，补充说明 the contractor）"],
    [[("but","但"),("engineers","工程师"),("and","和"),("NASA","美国航天局的"),("managers","管理人员"),("judged","认为"),("it","它"),("less **reliable**","不太**可靠**(reliable)，")],
     "（judge A＋形容词：认为 A……）"],
    [[("and left the **contradictory** reading","这一**相互矛盾的**(contradictory)读数也就"),("**unexplored**.","**无人深究**(unexplored)。")],
     "（leave A＋形容词：使 A 处于某种状态）"]]),
(4,[[[("The mirror","主镜"),("could not be repaired in orbit,","无法在轨道上修复，")],
     "（in orbit：在轨道上）"],
    [[("so","于是"),("engineers","工程师"),("**prescribed**","**开出了**(prescribed)"),("**tailored** glasses.","一副**量身定制的**(tailored)眼镜。")],
     "（prescribe：开（药方），这里把矫正装置比作眼镜）"]]),
(4,[[[("COSTAR,","COSTAR "),("a **corrective**","是一个冰箱大小的**矫正**(corrective)"),("**cabinet**","**箱体**(cabinet)，"),("the size of a refrigerator,","")],
     "（a corrective cabinet…：同位语，补充说明 COSTAR；\nthe size of…：……那么大）"],
    [[("carried small mirrors on **adjustable** arms","**可调节的**(adjustable)机械臂上装着小镜子，")],
     "（on adjustable arms：介词短语作后置定语，修饰 mirrors）"],
    [[("that **intercepted** the light","在光线到达仪器之前将光**截住**(intercepted)，"),("and **compensated for**","**抵消**(compensated for)"),("the **imperfect**","**有缺陷的**(imperfect)"),("mirror's","主镜造成的"),("**distortion** before the light reached the instruments.","**畸变**(distortion)。")],
     "（that intercepted…and compensated for…：定语从句，\n修饰 small mirrors；\ncompensate for…：抵消，弥补……；\nbefore…：时间状语从句）"]]),
(4,[[[("The mirror itself","主镜本身"),("would stay **untouched**,","将保持**原封不动**(untouched)，")],
     "（stay＋形容词：保持某种状态）"],
    [[("and a new","一台新的"),("main","主"),("camera","相机"),("was prepared.","也已准备就绪。")]]]),
(5,[[[("On 2 December 1993","1993年12月2日，"),("Endeavour","奋进号"),("**ascended** with seven astronauts.","载着七名宇航员**升空**(ascended)。")],
     "（with seven astronauts：伴随状语）"]]),
(5,[[[("After a **rendezvous**,","完成**交会**(rendezvous)后，")],
     "（rendezvous：航天器在轨道上会合）"],
    [[("they","他们"),("worked **in tandem**","**协同**(in tandem)进行了"),("across five","五次"),("spacewalks,","太空行走，")],
     "（in tandem：协力，配合；\nacross five spacewalks：在五次太空行走中）"],
    [[("about 35 and a half hours of **exertion**,","**辛苦作业**(exertion)共约35个半小时，")],
     "（about 35 and a half hours of exertion：\n同位语，补充说明五次太空行走的工作量）"],
    [[("**installing**","**安装了**(installing)"),("COSTAR","COSTAR "),("and","和"),("the new","新"),("camera.","相机。")],
     "（installing…：现在分词短语作伴随状语）"]]),
(5,[[[("The **imagery**","**影像**(imagery)"),("turned **crisp**,","变得**清楚分明**(crisp)，")],
     "（turn＋形容词：变得……）"],
    [[("Hubble's **vision**","哈勃的**视力**(vision)"),("**renewed**.","得以**恢复**(renewed)。")],
     "（Hubble's vision renewed：\n独立主格结构，相当于\nand Hubble's vision was renewed）"]]),
(5,[[[("The mirror","主镜"),("still carries","至今仍带着"),("that 2.2-micrometre","那2.2微米的"),("flaw,","缺陷，")]],
    [[("and the light it **gathers**","它**收集**(gathers)的光"),("is corrected only after leaving it.","要离开镜面之后才得到矫正。")],
     "（it gathers：定语从句，省略了关系代词，修饰 light；\nonly after…：只有在……之后才）\n"
     "（简述：1990年，航天飞机把耗资约15亿美元的\n"
     "哈勃空间望远镜送上轨道，传回的照片却模糊不清。\n"
     "原来检测主镜的组件里有一块透镜错位，\n"
     "主镜外缘被磨平了2.2微米。\n"
     "另一次独立测试给出过不同结果，却没人追查。\n"
     "主镜无法在轨道上修复，工程师就给它配了一副眼镜：\n"
     "冰箱大小的矫正装置 COSTAR。\n"
     "1993年，七名宇航员经过五次太空行走，\n"
     "装好了 COSTAR 和新相机，哈勃的视力得以恢复。\n"
     "主镜至今仍带着原有的缺陷。）"]]),
]
CONF={
"合组":{
 "S1 the space shuttle Discovery":"对齐不了：Discovery 是航天飞机的名字，中文“发现号航天飞机”名字必须放在前面",
 "S3 Money, it soon emerged":"对齐不了：it soon emerged 是插入语，中文“人们很快发现”必须提到句首，Money 中文“钱”接在后面（沿用文章定稿）",
 "S5 a flaw in the main mirror":"对齐不了：in the main mirror 是后置定语，修饰 flaw，中文“主镜有缺陷”主镜必须提前",
 "S5 a fiftieth of the width of a hair":"对齐不了：两层 of 结构，中文“头发丝宽度的五十分之一”语序必须整个倒过来",
 "S8 A lens in the assembly that checked the mirror's shape":"对齐不了：in the assembly 是后置定语，that checked the mirror's shape 是定语从句修饰 assembly，中文“检测主镜形状的那套组件中，一块透镜”从句和地点必须提前",
 "S9 A second, independent test by the contractor, Perkin-Elmer":"对齐不了：by the contractor 是后置定语，Perkin-Elmer 是同位语，中文“承包商珀金-埃尔默公司做的第二次独立测试”定语必须整体提前",
 "S9 and left the contradictory reading":"对齐不了：leave A unexplored 中文“A 也就无人深究”，A 必须提到前面，left 化成“也就”（沿用文章定稿）",
 "S10 could not be repaired in orbit":"对齐不了：in orbit 是地点状语，中文“无法在轨道上修复”地点必须放到动词前",
 "S11 carried small mirrors on adjustable arms":"对齐不了：on adjustable arms 是地点（后置定语），中文“可调节的机械臂上装着小镜子”地点必须提前，carried 化成“装着”",
 "S11 the size of a refrigerator":"对齐不了：the size of a refrigerator 是后置定语，修饰 cabinet，中文“冰箱大小的”按文章定稿提到“矫正箱体”前（放在 corrective 那组），这里没有中文",
 "S11 distortion before the light reached the instruments":"对齐不了：before the light reached the instruments 是时间状语从句，中文“在光线到达仪器之前”按文章定稿提到这半句开头（放在 intercepted 那组），这里只剩“畸变”",
 "S16 is corrected only after leaving it":"对齐不了：only after leaving it 是时间状语，中文“要离开镜面之后才得到矫正”时间必须放到“得到矫正”前"},
"对齐":{
 "S1-1 lofted the Hubble Space Telesc":"loft A into orbit，中文“把 A 送上轨道”，把字句宾语必须提前",
 "S2-1 The observatory cradled in the":"cradled in the payload bay 是过去分词短语作后置定语，修饰 observatory，中文“安放在有效载荷舱里的天文台”定语必须提前",
 "S5-1 a flaw in the main mirror:":"in the main mirror 是后置定语，中文“主镜有缺陷”主镜必须提前",
 "S5-3 a fiftieth of the width of a h":"两层 of 结构，中文“头发丝宽度的五十分之一”语序必须整个倒过来",
 "S8-1 A lens in the assembly that ch":"in the assembly 是后置定语、that checked… 是定语从句，中文从句和地点必须提前",
 "S9-1 A second, independent test by ":"by the contractor 是后置定语、Perkin-Elmer 是同位语，中文定语必须整体提前",
 "S9-3 and left the contradictory rea":"leave A unexplored，中文“A 也就无人深究”，A 必须提前",
 "S10-1 could not be repaired in orbit":"in orbit 是地点状语，中文“在轨道上”必须放到“修复”前",
 "S11-1 the size of a refrigerator,":"the size of a refrigerator 是后置定语，中文“冰箱大小的”必须提到“矫正箱体”前（放在 corrective 那组）",
 "S11-2 carried small mirrors on adjus":"on adjustable arms 是地点（后置定语），中文“机械臂上装着小镜子”地点必须提前",
 "S11-3 distortion before the light re":"before… 是时间状语从句，中文“在光线到达仪器之前”按文章定稿提到这半句开头（intercepted 那组），这里只剩“畸变”",
 "S14-3 about 35 and a half hours of e":"同位语里 hours of exertion 是 of 结构，中文“辛苦作业共约35个半小时”语序必须倒过来",
 "S16-2 and the light it gathers":"it gathers 是省略关系代词的定语从句，修饰 light，中文“它收集的光”从句必须提前",
 "S16-2 is corrected only after leavin":"only after leaving it 是时间状语，中文“要离开镜面之后才”必须放到“得到矫正”前"},
"牛津逗号":{
 "S9 gave a divergent result, but engineers and":"不是三项并列：逗号后 but 连接两个分句，engineers and NASA managers 只有两项",
 "S14 tandem across five spacewalks, about 35 and":"不是三项并列：about 35 and a half hours of exertion 是同位语，and a half 是数字读法",
 "S14 half hours of exertion, installing COSTAR and":"不是三项并列：installing… 是现在分词短语，COSTAR and the new camera 只有两项"},
"方向":{"S9-2 less→不太可靠，":"less reliable 中文“不太可靠”，“不太”就是 less，方向一致",
 "S11-3 before→畸变。":"before 引出的从句中文“在光线到达仪器之前”按文章定稿提到这半句开头（intercepted 那组），“之前”与 before 方向一致"},
"短语":{
 "S1 lofted … into":"不是搭配：into 只引出方向（送入轨道），lofted 本身就是“送上”",
 "S2 cradled … in":"不是搭配：in 只引出地点（在有效载荷舱里），cradled 本身就是“安放”",
 "S2 gaze … on":"不是搭配：gaze 在这里是名词“目光”，on 属于动词短语 fix … on（把……投向），中文“把目光投向”整组已对上",
 "S5 rim … of":"不是搭配：of 属于后面的 a fiftieth of the width，和 rim 无关",
 "S5 flattened … of":"不是搭配：of 属于后面的 a fiftieth of the width，和 flattened 无关",
 "S5 width … of":"不是搭配：of 只引出所属（头发丝的宽度），width 本身就是“宽度”（同 16 beads … of 的判法）",
 "S7 with … calibration":"不是搭配：with 属于 began with（始于），calibration 本身就是“校准”",
 "S8 offset … by":"不是搭配：by 表示偏移的量（约1.3毫米），offset 本身就是“错位”",
 "S13 ascended … with":"不是搭配：with 表示伴随（载着七名宇航员），ascended 本身就是“升空”"}}
CONF["停顿位置"]={
 "S3 Money, / it @0.428":"2026-11-03 逐 2.5 ms 看声音实测（S3 w）：Money 的 /i/ 元音 0.34–0.40 从 -11 dB 衰减，0.4025–0.4275 降到 -37～-44 dB（0.4275 -44.3 dB、周期 0.05 无周期，是两词交界最低处，过零 0.427792），0.4325 起 it 的元音起音 -35.8→-8.3 dB；原自动插入点 0.520 落在 it 的 ɪ 与 /t/ 闭塞之间（0.5325 起 /t/ 除阻和 soon 的 /s/，重心 4.1–6.3 kHz），改用停顿插入点 0.427792，不切 Money 也不切 it",
 "S14 rendezvous, / they @1.053":"2026-11-03 逐 2.5/10 ms 看声音实测（S14 w）：rendezvous 的 /uː/ 0.98–1.0375（-15～-25 dB、周期 0.5、低频占优），1.04 起降到 they 的 /ð/ 浊音杠（1.04–1.07，-24～-30 dB，3 kHz 以上只占 -28～-34 dB），1.08–1.10 /ð/ 摩擦（3 kHz 以上升到 -7 dB），1.1075 起 eɪ 元音 -10 dB；原自动插入点 1.225 落在 they 的元音里，改用停顿插入点 1.053083（/uː/ 结束后浊音杠里的最低点 -35.4 dB，过零），不切 rendezvous 的 /uː/，they 的 /ð/ 整段留在停顿后"}
CONF["非人声"]={
 "17.67–17.77s":{"配音指纹":"961c831462c1","依据":"2026-11-03 42 逐 2.5/10 ms 看实际声音（dossier_42）：S2 w 5.87–5.965：dollars, 的 ɚ 到 /z/ 的过渡：5.79–5.83 ɚ 浊音（-23～-34 dB、周期 0.4），5.84–5.95 浊音减弱（-38～-50 dB、低频 -3～-5 dB 占优），5.96 起 /z/ 摩擦升到 -18 dB（重心 4.4–5.6 kHz），中间没有缝，属于 dollars"},
 "22.30–22.34s":{"配音指纹":"961c831462c1","依据":"2026-11-03 42 逐 2.5/10 ms 看实际声音（dossier_42）：S2 w 10.58–10.615：its 的 /s/ 到 10.57 降到 -64.5 dB 后，10.59–10.61 是 galaxies 的 /ɡ/ 闭塞浊音杠（-35～-41 dB、周期 0.43–0.45、低频 -0.6～-0.9 dB、重心 650–700 Hz），10.62 /ɡ/ 除阻（重心 4.2 kHz），10.64 起 æ 元音 -14→-8 dB，属于 galaxies"},
 "22.92–23.02s":{"配音指纹":"961c831462c1","依据":"2026-11-03 42 逐 2.5/10 ms 看实际声音（dossier_42）：S2 w 11.195–11.295：galaxies. 的 i 到 /z/ 的过渡：11.14 i 元音 -21 dB，11.17–11.27 浊音减弱（-40～-52 dB、低频 -1.6～-8 dB），11.28 起 /z/ 摩擦升到 -22 dB（重心 4.5–5.7 kHz），中间没有缝，属于 galaxies"},
 "36.47–36.55s":{"配音指纹":"961c831462c1","依据":"2026-11-03 42 逐 2.5/10 ms 看实际声音（dossier_42）：S5 w 3.99–4.075：mirror: 的 ɚ 收尾：3.93–3.98 ɚ 浊音（-16～-25 dB、周期 0.44–0.51），3.99–4.06 浊音衰减（-36～-46 dB、周期 0.27–0.41、重心 1.2–2 kHz），一路降到 4.07 -56 dB、4.09 -69 dB，中间没有缝，属于 mirror"},
 "40.77–40.86s":{"配音指纹":"961c831462c1","依据":"2026-11-03 42 逐 2.5/10 ms 看实际声音（dossier_42）：S5 w 8.41–8.505：micrometres, 的 ɚ 到 /z/ 的过渡：8.36–8.49 浊音减弱（-32～-48 dB、低频 -2～-7 dB 占优、重心 0.8–2 kHz），8.50 起 /z/ 摩擦升到 -14 dB（重心 4.5–5.7 kHz），中间没有缝，属于 micrometres"},
 "40.82–40.84s":{"配音指纹":"961c831462c1","依据":"2026-11-03 42 逐 2.5/10 ms 看实际声音（dossier_42）：S5 w 8.465–8.48：micrometres, 的 ɚ 到 /z/ 过渡中段（-40～-42 dB、低频 -2.9～-4.6 dB），前后连续，属于 micrometres"},
 "43.66–43.74s":{"配音指纹":"961c831462c1","依据":"2026-11-03 42 逐 2.5/10 ms 看实际声音（dossier_42）：S5 w 11.285–11.37：hair. 句末 ɚ 的收尾：11.23–11.34 浊音衰减（-26～-46 dB、重心 1.2–2 kHz），连续降到 11.37 -61 dB、11.39 -75 dB、11.42 数字静音，属于 hair"},
 "44.74–44.76s":{"配音指纹":"961c831462c1","依据":"2026-11-03 42 逐 2.5/10 ms 看实际声音（dossier_42）：S6 w 0.015–0.03：句首 That 的 /ð/ 浊音起音：0.01 -57、0.02 -38.7、0.03 -32、0.04 -26.8 dB 连续升起（低频 -2～-6 dB 占优），0.05 起 æ 元音 -2.4 dB，属于 That"},
 "52.48–52.55s":{"配音指纹":"961c831462c1","依据":"2026-11-03 42 逐 2.5/10 ms 看实际声音（dossier_42）：S7 w 1.92–2.00：calibration. 句末 /n/ 的收尾：1.86–1.92 鼻音 -24～-36 dB，1.93–2.00 连续衰减（-45～-57 dB、周期 0.27–0.41），2.04 降到 -95 dB，中间没有缝，属于 calibration"},
 "59.76–59.85s":{"配音指纹":"961c831462c1","依据":"2026-11-03 42 逐 2.5/10 ms 看实际声音（dossier_42）：S8 w 6.28–6.375：millimetres, 的 ɚ 到 /z/ 的过渡：6.28–6.36 浊音减弱（-38～-50 dB、低频 -2.3～-7 dB 占优），6.37 起 /z/ 摩擦升到 -16 dB（重心 4.6–5.9 kHz），中间没有缝，属于 millimetres"},
 "59.80–59.82s":{"配音指纹":"961c831462c1","依据":"2026-11-03 42 逐 2.5/10 ms 看实际声音（dossier_42）：S8 w 6.32–6.345：millimetres, 的 ɚ 到 /z/ 过渡中段（-44～-46 dB、低频 -2.3～-3.4 dB），前后连续，属于 millimetres"},
 "62.88–63.02s":{"配音指纹":"961c831462c1","依据":"2026-11-03 42 逐 2.5/10 ms 看实际声音（dossier_42）：S8 w 9.40–9.535：curve. 句末 /v/：9.34–9.40 /v/ 浊音（-25～-40 dB），9.41–9.48 浊音杠（-44～-49 dB、低频 -1.6～-7 dB），9.49–9.58 清化成擦音（-36～-41 dB、重心 4–5.3 kHz），9.59 降到 -49 dB，属于 curve"},
 "66.20–66.22s":{"配音指纹":"961c831462c1","依据":"2026-11-03 42 逐 2.5/10 ms 看实际声音（dossier_42）：S9 w 1.935–1.955：test 的 /t/ 闭塞（1.90–1.93 -50～-66 dB）后，1.94–1.95 是 by 的 /b/ 闭塞浊音杠（-38～-42 dB、低频 -1.5～-1.8 dB、重心 0.8–1.2 kHz），1.96 /b/ 除阻 -21 dB、1.97 起 aɪ 元音 -7 dB，属于 by"},
 "70.31–70.36s":{"配音指纹":"961c831462c1","依据":"2026-11-03 42 逐 2.5/10 ms 看实际声音（dossier_42）：S9 w 5.735–5.785：result, 词尾 /t/ 的除阻：5.69–5.73 /t/ 闭塞（-57～-68 dB），5.74 爆出 -31.5 dB（重心 3.4 kHz），5.75–5.78 送气衰减（-34～-47 dB、重心 2.6–4.8 kHz），5.79 -60 dB，属于 result"},
 "77.58–77.67s":{"配音指纹":"961c831462c1","依据":"2026-11-03 42 逐 2.5/10 ms 看实际声音（dossier_42）：S9 w 13.135–13.23：unexplored. 词尾 /d/ 的闭塞浊音杠：13.08–13.13 ɔːɹ 元音（-26～-35 dB），13.14–13.22 浊音杠（-35～-47 dB、低频 -1.2～-4.6 dB 占优、周期 0.25–0.40），13.23–13.24 闭塞 -57 dB，13.25 /d/ 除阻 -29 dB，属于 unexplored"},
 "77.65–77.67s":{"配音指纹":"961c831462c1","依据":"2026-11-03 42 逐 2.5/10 ms 看实际声音（dossier_42）：S9 w 13.205–13.23：unexplored. 词尾 /d/ 浊音杠后段（-35～-46 dB、低频 -1.2～-1.7 dB、重心 0.8–1.3 kHz），接 13.23 闭塞和 13.25 除阻，属于 unexplored"},
 "93.26–93.28s":{"配音指纹":"961c831462c1","依据":"2026-11-03 42 逐 2.5/10 ms 看实际声音（dossier_42）：S11 w 7.79–7.805：intercepted 词尾 /d/：7.74–7.79 浊音杠（-45～-59 dB、低频 -1.0～-2.6 dB 占优），7.80 /d/ 除阻 -53.8 dB（单帧，2.5 ms 最响 -40.5），7.81–7.82 -63～-65 dB，7.83 起 the 的 /ð/ -25 dB，属于 intercepted"},
 "124.91–124.95s":{"配音指纹":"961c831462c1","依据":"2026-11-03 42 逐 2.5/10 ms 看实际声音（dossier_42）：S15 w 1.375–1.415：crisp, 词尾 /p/ 的除阻：1.33–1.37 /p/ 闭塞（-62～-67 dB），1.38 爆出 -37.8 dB（重心 3.4 kHz），1.39–1.41 衰减（-44～-51 dB），1.43 -62 dB，属于 crisp"},
 "134.43–134.46s":{"配音指纹":"961c831462c1","依据":"2026-11-03 42 逐 2.5/10 ms 看实际声音（dossier_42）：S16 w 6.525–6.55：corrected 词尾 /d/：6.47–6.50 浊音杠（-41～-54 dB、低频 -0.4～-3 dB），6.51–6.52 闭塞 -61～-70 dB，6.53 除阻 -48 dB，6.54–6.56 衰减（-47～-57 dB），6.57 -67 dB，属于 corrected"},
 "136.53–136.59s":{"配音指纹":"961c831462c1","依据":"2026-11-03 42 逐 2.5/10 ms 看实际声音（dossier_42）：S16 w 8.63–8.69：it. 句末 /t/ 的除阻：8.60–8.62 /t/ 闭塞（-62～-66 dB），8.63 爆出 -34.4 dB（重心 2.6–3.8 kHz），8.64–8.69 送气衰减（-35～-53 dB），8.70 -62 dB，8.74 -100 dB，属于 it"}}
CONF["机器复听"]={"S5":{"配音指纹":"961c831462c1","依据":"2026-11-03 实测（S5 w）：roughly a fiftieth 每个音都在：roughly 的 /f/ 9.17–9.29、li 和 a 的弱读 ɐ 9.30–9.48 连续浊音，fiftieth 的 /f/ 9.50–9.64（重心 6–7.6 kHz）、ɪ 9.66–9.71（-3 dB）、/f/ 9.72–9.78、/t/ 闭塞 9.79–9.83、除阻 9.84、i 9.87–10.03、/θ/ 10.04–10.11（-30 dB、重心 6.9–7.6 kHz）；配音音标 fˈɪftiəθ，读音核对 0；small.en 把序数词 fiftieth 写成数字 50（转写习惯），parakeet 没报；交用户听"}}
CONF["高亮"]={"S11 第3块":{"开始读":92.58,"配音指纹":"961c831462c1","依据":"2026-11-03 直接读 work_42/a.wav 逐 10 ms：arms 的 /z/ 92.48–92.55（-17～-28 dB、重心 4.8–7.6 kHz），92.56–92.57 降到 -36～-38 dB，92.58 起 that 的 /ð/（-30.6 dB），92.59 起 æ 元音 -19.9→-7.2 dB（重心 2.0–2.2 kHz），92.67–92.72 衰减进 /t/ 闭塞，92.73–92.77 静音，92.78 /t/ 除阻接 intercepted 的 ɪ（92.79 -9.5 dB）；第3块在 92.58 开始读，与甲 92.59、乙 92.58 一致，原高亮 92.77 落在 that 的 /t/ 闭塞末尾，推后 0.19 秒（w 里对应：ð 8.895 起音、æ 8.91 起）"}}
out={"no":"42","title_en":"The Telescope That Needed Glasses","title_zh":"需要戴眼镜的望远镜","title_fx":{"hl":["Telescope","Glasses"],"ghost":[]},"sentences":[],"核对确认":CONF,"结尾解说":"简述",
     "非人声区间":{"S3":[[1.422875,1.545,"紧贴词尾"]],"S6":[[1.7225,1.7375],[2.195,2.467625,"紧贴词头"]],"S13":[[2.4435,2.8475]]},
     "停顿插入点":{"S3":{"1":[0.427792,"交界"]},"S14":{"1":[1.053083,"交界"]}},
     "高亮按实际开口":True,"高亮开口门槛":40,
     "术语":{"Discovery":"发现号","Hubble Space Telescope":"哈勃空间望远镜","Hubble":"哈勃","NASA":"美国航天局","Perkin-Elmer":"珀金-埃尔默公司","COSTAR":"COSTAR","Endeavour":"奋进号"}}
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 核对 import 生成并核对
生成并核对(S, out)
