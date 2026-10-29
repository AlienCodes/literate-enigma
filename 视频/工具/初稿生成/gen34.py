import json,re,glob,os
# 第34篇初稿（逐词对照）：S = [(段, [chunk, ...])]，chunk = ([(英文组, 中文组), ...], 可选 note)
# 2026-10-29 重点词中文沿用文章定稿（铁律），只按《翻译风格》调格式；短语型用法整体标（T22）；不用破折号（T36）。
S=[
(1,[[[("In June 1984","1984年6月，"),("Alexey Pajitnov,","阿列克谢·帕基特诺夫，"),("a 29-year-old","一位29岁的"),("Moscow **coder**,","莫斯科**程序员**(coder)，")],
     "（a 29-year-old Moscow coder：同位语，补充说明 Alexey Pajitnov）"],
    [[("grew","渐渐"),("**engrossed in**","**沉迷于**(engrossed in)"),("a **diversion** he had built.","自己编写的一个**消遣**(diversion)。")],
     "（grow engrossed in…：变得沉迷于……；\nhe had built：定语从句，省略了关系代词，修饰 diversion）"]]),
(1,[[[("His **primitive**","他那台**简陋的**(primitive)"),("Elektronika 60","Elektronika 60"),("had a **purely**","**只能**(purely)"),("**textual** display,","显示**文字**(textual)，")],
     "（Elektronika 60：一种计算机型号；\na purely textual display：只能显示文字的屏幕）"],
    [[("so","所以"),("every","每个"),("**geometric** piece","**几何**(geometric)方块"),("of four **tiles**","都由四个**小格**(tiles)组成，"),("was assembled from characters.","全是用字符拼出来的。")],
     "（of four tiles：of 结构作后置定语，修饰 piece；\nbe assembled from…：由……拼成）"]]),
(1,[[[("The result","结果，"),("proved **addictive**.","这个游戏让人**上瘾**(addictive)。")],
     "（prove＋形容词：结果是……，\n事实证明……）"]]),
(1,[[[("He","他"),("called it Tetris,","给它取名 Tetris（俄罗斯方块），")],
     "（call A B：把 A 叫作 B）"],
    [[("a **fusion** of the Greek tetra- and tennis,","这是希腊语前缀 tetra- 和网球 tennis 的**融合**(fusion)，")],
     "（a fusion of…：同位语，补充说明 Tetris；\ntetra-：希腊语前缀，意为“四”）"],
    [[("his favourite **pastime**.","网球是他最爱的**消闲**(pastime)运动。")],
     "（his favourite pastime：同位语，补充说明 tennis）"]]),
(2,[[[("Under the **communist** system,","在**共产主义**(communist)体制下，")],
     "（under…system：在……体制下）"],
    [[("the state,","国家，"),("not its **salaried**","而不是领**工资的**(salaried)"),("**designer**,","**设计者**(designer)，"),("was the **proprietor** of this **intellectual property**,","是这份**知识产权**(intellectual property)的**所有者**(proprietor)，")],
     "（not its salaried designer：插入语，和 the state 对比；\nintellectual property：知识产权）"],
    [[("and","而"),("Pajitnov","帕基特诺夫"),("held no **entitlement** to it.","对它没有任何**权利**(entitlement)。")],
     "（hold no entitlement to…：对……没有任何权利）"]]),
(2,[[[("Copies","拷贝"),("**mushroomed**","**遍地开花**(mushroomed)，"),("**freely**","**自由**(freely)流传，"),("on floppy **disks**","靠**软盘**(disks)"),("across the **Eastern bloc**.","遍及整个**东欧集团**(Eastern bloc)。")],
     "（mushroom：像蘑菇一样迅速增长，遍地开花；\nthe Eastern bloc：东欧集团）"]]),
(3,[[[("In 1986","1986年，"),("Robert Stein,","罗伯特·斯坦因，"),("an **enterprising**","一位**富有进取心的**(enterprising)"),("British software **vendor**,","英国软件**商人**(vendor)，")],
     "（an enterprising British software vendor：\n同位语，补充说明 Robert Stein）"],
    [[("**stumbled upon** Tetris in Hungary.","在匈牙利**偶然碰到了**(stumbled upon)俄罗斯方块。")],
     "（stumble upon…：偶然碰到，偶然发现……；\nin Hungary：地点状语）"]]),
(3,[[[("In his **ignorance** of Elorg,","他对 Elorg 毫不**知情**(ignorance)，"),("the state **bureau**","那是一个国家**机构**(bureau)，"),("**regulating**","负责**管理**(regulating)"),("Soviet software","苏联软件"),("exports,","出口，")],
     "（the state bureau…：同位语，补充说明 Elorg；\nregulating…：现在分词短语作后置定语）"],
    [[("he","他就"),("**hastily**","**草率地**(hastily)"),("**hawked**","**兜售**(hawked)起"),("rights he did not yet **legitimately** hold.","他尚未**合法**(legitimately)拥有的版权。")],
     "（hawk：叫卖，兜售；rights he did not yet…：\n定语从句，省略了关系代词，修饰 rights）"]]),
(3,[[[("The rights","这些版权"),("were **shuffled**","被**倒来倒去**(shuffled)，"),("**onward**","一路**传下去**(onward)，")],
     "（shuffle：来回挪动；onward：向前，往后传）"],
    [[("through a **chaotic**","陷入一团**混乱的**(chaotic)"),("**muddle**","**乱麻**(muddle)，"),("of **overlapping** deals","交易彼此**重叠**(overlapping)，"),("among Western firms,","发生在西方公司之间，")],
     "（a chaotic muddle of…：一团……的乱麻；\namong Western firms：后置定语，修饰 deals）"],
    [[("one","其中一家公司"),("owned by","归"),("the **magnate**","**大亨**(magnate)"),("Robert Maxwell.","罗伯特·马克斯韦尔所有。")],
     "（one owned by…：one 指其中一家公司，\nowned by…：过去分词短语作后置定语）"]]),
(4,[[[("In February 1989","1989年2月，"),("Henk Rogers,","亨克·罗杰斯，"),("a **resourceful**","一位**足智多谋的**(resourceful)"),("Dutch-born **publisher**,","荷兰裔**发行商**(publisher)，")],
     "（a resourceful Dutch-born publisher：\n同位语，补充说明 Henk Rogers）"],
    [[("reached Moscow on a tourist **visa**","持旅游**签证**(visa)来到莫斯科，"),("and found his way to Elorg.","设法找到了 Elorg。")],
     "（on a tourist visa：持旅游签证；\nfind one's way to…：设法找到……）"]]),
(4,[[[("Stein","斯坦因"),("and Kevin Maxwell,","和凯文·马克斯韦尔，"),("the magnate's","那位大亨的"),("son,","儿子，")],
     "（the magnate's son：同位语，补充说明 Kevin Maxwell）"],
    [[("were in Moscow","都在莫斯科，"),("that same **hectic**","就在同一个**忙乱的**(hectic)"),("week of **negotiations**,","**谈判**(negotiations)周里，"),("each a **bidder**.","各自都是**竞标者**(bidder)。")],
     "（that same hectic week…：时间状语；\neach a bidder：each 指两人各自）"]]),
(4,[[[("Pajitnov","帕基特诺夫"),("felt a **fondness** for Rogers,","对罗杰斯颇有**好感**(fondness)，")],
     "（feel a fondness for…：对……有好感）"],
    [[("and Nintendo","任天堂"),("**scooped**","**拿下了**(scooped)"),("the handheld","掌机"),("rights,","版权，"),("then","后来又拿下了"),("worldwide","全球"),("**console**","**游戏主机**(console)"),("rights.","版权。")],
     "（scoop：抢先获得；\nthen worldwide console rights：省略了 scooped）"]]),
(5,[[[("Nintendo","任天堂"),("**bundled** Tetris with its **pocket-sized** Game Boy,","把俄罗斯方块和它那款**口袋大小的**(pocket-sized) Game Boy **捆绑**(bundled)销售，")],
     "（bundle A with B：把 A 和 B 捆绑在一起（销售））"],
    [[("and that version","这个版本"),("shipped","出货"),("over 35 million copies.","超过3,500万份。")],
     "（ship：发货，出货；over：超过）"]]),
(5,[[[("Pajitnov","帕基特诺夫"),("**reaped** none","没有**分到**(reaped)"),("of the **spoils**","任何**好处**(spoils)，"),("for years.","长达多年。")],
     "（reap：收获，获得；none of…：……中一点也没有；\nspoils：战利品，这里指收益）"]]),
(5,[[[("His **earnings** began only after his arrangement's **expiry** around 1995.","直到1995年前后他的协议**到期**(expiry)之后，他才开始有**收入**(earnings)。")],
     "（only after…：只有在……之后，才……；\narrangement's expiry：协议到期）"]]),
(5,[[[("In 1996","1996年，"),("he and Rogers","他和罗杰斯"),("founded The Tetris Company","成立了俄罗斯方块公司，"),("to manage","来管理"),("the rights.","这些版权。")],
     "（to manage the rights：不定式作目的状语）"]]),
(6,[[[("The man","那个人，"),("whose puzzle","他的游戏"),("once","曾经"),("spread for nothing","免费四处流传，"),("later","后来"),("helped","参与"),("decide","决定"),("who could sell it.","谁能卖它。")],
     "（whose puzzle…：定语从句，修饰 The man；\nfor nothing：免费；\nwho could sell it：宾语从句）\n"
     "（简述：1984年6月，29岁的莫斯科程序员帕基特诺夫，\n"
     "在一台只能显示文字的 Elektronika 60 上编出俄罗斯方块，方块由字符拼成，\n"
     "名字由 tetra- 和 tennis 合成。游戏归国家所有，他没有任何权利，\n"
     "软盘拷贝在东欧集团免费流传。1986年，英国软件商斯坦因在匈牙利碰到这个游戏，\n"
     "不知道有 Elorg，就先卖起了版权，版权随后在西方公司之间层层转卖。\n"
     "1989年2月，罗杰斯持旅游签证到莫斯科找到 Elorg，斯坦因和凯文·马克斯韦尔\n"
     "同一周也在争夺版权；任天堂拿下掌机版权，又拿下全球主机版权。\n"
     "Game Boy 版出货超过3,500万份，帕基特诺夫多年分文未得，约1995年协议到期后才有收入。\n"
     "1996年，他和罗杰斯成立俄罗斯方块公司管理版权。）"]]),
]
CONF={"合组":{
 "S2 was assembled from characters":"对齐不了：被动 be assembled from A 中文“用 A 拼出来”，材料 from characters 必须放到动词前",
 "S4 a fusion of the Greek tetra- and tennis":"对齐不了：a fusion of A and B 中文“A 和 B 的融合”，of 结构语序必须倒过来；tetra-、tennis 两个词保留英文原形",
 "S8 rights he did not yet legitimately hold":"对齐不了：he did not yet legitimately hold 是省略关系代词的定语从句，修饰 rights，中文“他尚未合法拥有的版权”从句必须提前",
 "S9 among Western firms":"对齐不了：among A 中文“在 A 之间”，“之间”必须放到名词后面",
 "S10 reached Moscow on a tourist visa":"对齐不了：on a tourist visa 是方式状语，中文“持旅游签证来到莫斯科”必须放到动词前",
 "S10 and found his way to Elorg":"对齐不了：find one's way to 是固定说法“设法找到”，拆开不通",
 "S15 His earnings began only after his arrangement's expiry around 1995":"对齐不了：only after A, B 中文“直到 A 之后，才 B”，时间状语必须提前，“才开始有收入”放到最后",
 "S17 spread for nothing":"对齐不了：for nothing 是方式状语，中文“免费四处流传”必须放到动词前"},
"对齐":{
 "S1-2 a diversion he had built.":"he had built 是省略关系代词的定语从句，修饰 diversion，中文“自己编写的一个消遣”从句必须提前",
 "S4-2 a fusion of the Greek tetra- a":"a fusion of A and B 中文“A 和 B 的融合”，of 结构语序必须倒过来",
 "S5-2 was the proprietor of this int":"the proprietor of A 中文“A 的所有者”，of 结构语序必须倒过来",
 "S5-3 held no entitlement to it.":"entitlement to it 中文“对它没有任何权利”，to 引出的对象必须放到动词前",
 "S7-2 stumbled upon Tetris in Hungar":"in Hungary 是地点状语，中文“在匈牙利偶然碰到了俄罗斯方块”地点必须放到动词前",
 "S8-1 In his ignorance of Elorg,":"ignorance of A 中文“对 A 毫不知情”，of 引出的对象必须提前",
 "S8-2 rights he did not yet legitima":"省略关系代词的定语从句修饰 rights，中文“他尚未合法拥有的版权”从句必须提前",
 "S10-2 reached Moscow on a tourist vi":"on a tourist visa 是方式状语，中文“持旅游签证来到莫斯科”必须放到动词前",
 "S10-2 and found his way to Elorg.":"find one's way to 是固定说法“设法找到”，拆开不通",
 "S12-1 felt a fondness for Rogers,":"feel a fondness for A 中文“对 A 颇有好感”，for 引出的对象必须放到动词前",
 "S13-1 bundled Tetris with its pocket":"bundle A with B 中文“把 A 和 B 捆绑销售”，动词必须放到后面",
 "S15-1 His earnings began only after ":"only after A, B 中文“直到 A 之后，才 B”，时间状语必须提前"},
"短语":{"S4 fusion … of":"不是搭配：of 引出融合的两部分（tetra- 和 tennis），fusion 单独就是“融合”，同速查表 a fusion of styles",
 "S5 proprietor … of":"不是搭配：of 引出所有的东西（this intellectual property），proprietor 单独就是“所有者”",
 "S5 entitlement … to":"不是搭配：to 引出权利指向的对象（it），entitlement 单独就是“权利”",
 "S6 mushroomed … on":"不是搭配：on floppy disks 是方式状语（靠软盘），和 mushroomed 无关",
 "S8 ignorance … of":"不是搭配：of 引出不知道的对象（Elorg），ignorance 单独就是“不知情”",
 "S9 shuffled … of":"不是搭配：of 属于 a chaotic muddle of overlapping deals，和 shuffled 无关",
 "S9 muddle … of":"不是搭配：of 引出乱麻的内容（overlapping deals），muddle 单独就是“乱麻，混乱”",
 "S12 fondness … for":"不是搭配：for 引出好感的对象（Rogers），fondness 单独就是“好感”，同速查表 a fondness for sweets",
 "S13 bundled … with":"不是搭配：bundle A with B 里 with 引出捆绑的另一方（Game Boy），bundle 单独就是“捆绑”",
 "S14 reaped … for":"不是搭配：for years 是时间状语（长达多年），和 reaped 无关",
 "S14 reaped … of":"不是搭配：of 属于 none of the spoils（好处中一点也没有），reap 的宾语是 none"}}
CONF["停顿位置"]={"S11 Maxwell, / the @1.670":"2026-10-29 逐段看声音实测（S11 w）：Maxwell 的 /l/ 不断开直接连到 the 的 /ð/：1.625–1.675 是 /l/ 浊音（-23～-27 dB，周期 0.48，低频 -1 dB 占优，重心 0.8–2 kHz），1.6775 起 /ð/ 摩擦（重心 3.2–4.2 kHz），1.6925 起 ə 升到 -17 dB；1.6700 是两词交界最低处 -30.2 dB（过零 1.67075），插在这里不切前后词（A42）"}
# S3 句子增益 -1.0 dB：2026-10-29 出片后响度一致性实测 S3（成片 24.1–25.6s）比全片响 2.6 LU、与 S2 相差 2.5 LU，调轻 1 dB（先例 19 S5 -0.3、20 S10 -0.6）
# S9 第2块高亮开始 72.665：2026-10-29 逐段看声音 S9 w 1.75 onward 的 /d/ 浊音结束（低频 -1 dB、重心 0.4 kHz），w 1.76 起 through 的 /θ/（重心 4.6–8.2 kHz、低频 -16～-43 dB），段 1 成片 70.91 + 1.755；乙 72.65、甲 72.71
# S17 去掉自动切点的 [2.726625, 2.771125]：w 2.705–2.81 是连续送气（-40～-44 dB、重心 2.1–2.4 kHz、低频 -10～-29 dB，一路升到 helped 的元音），中间没有低谷，是 helped 的 /h/，切了就切进词头（独立复核 onset 35 ms）
# 非人声区间新加 S2/S13/S16 的实测依据（2026-10-29）：{"S2 2.134333–2.3425（左头紧贴 sixty 词尾，落在过零点 2.134333；右头外侧 5 ms -56.7 dB）":"逐 10 ms 实测：sixty 的 i 在 w 2.12 收尾（-31 dB，低频 0），2.13 降到 -41 dB；2.15–2.33 平稳 -39～-41 dB、重心 2.5–3.1 kHz、低频 -9～-17 dB、周期 0.2–0.3，是气声；2.34–2.35 降到 -50/-48 dB 和 had 的 /h/（2.36 起）隔开；中间无标点，不是词",
#  "S13 4.04–4.257625（右头紧贴 and 起音前浊音，落在过零点 4.257625；左头外侧 5 ms -57.0 dB）":"逐 10 ms 实测：Game Boy, 的停顿后 w 4.06–4.25 从 -52 升到 -39 dB、重心 2.2–2.7 kHz、低频 -10～-18 dB、周期 0.2–0.4，是吸气声（A19）；4.26–4.29 低频转为 -0.2～-1.6 dB 占优，是 and 起音前的浊音，保留；and 4.30 起 -24.7 dB",
#  "S16 1.515–1.735":"逐 10 ms 实测：ninety-six 的末尾 /s/ 在 w 1.46–1.47 结束（重心 4.3 kHz），1.50–1.51 降到 -56～-57 dB；1.52–1.72 平稳 -50～-53 dB、重心 2.1–2.5 kHz、低频 -6～-16 dB、周期 0.2–0.3，是气声；1.73–1.78 降到 -56～-62 dB 和 he 隔开；中间无标点，不是词"}
CONF["非人声"]={"10.17–10.20s": {"配音指纹": "80c111d1ff5d", "依据": "2026-10-29 34 逐 10 ms 看实际声音：S1 w 6.66–6.685：grew 的 /g/ 除阻前的浊音杠（-32 dB、重心 0.5–0.8 kHz、周期 0.42–0.47、低频 -1 dB 占优），w 6.68 起 /g/ 除阻（重心 2.8 kHz），属于 grew", "实测": {"最响dB": -33.6, "重心Hz": 586, "周期": 0.42, "低频dB": -1.2}}, "22.88–22.96s": {"配音指纹": "80c111d1ff5d", "依据": "2026-10-29 34 逐 10 ms 看实际声音：S2 w 9.215–9.30：characters 的 ɚ 浊音（周期 0.3–0.43、低频 -1～-7 dB、重心 1.1–1.5 kHz），w 9.29 起接 /z/（重心 3.5–5.4 kHz），属于 characters", "实测": {"最响dB": -35.6, "重心Hz": 1522, "周期": 0.31, "低频dB": -2.1}}, "16.32–16.34s": {"配音指纹": "80c111d1ff5d", "依据": "2026-10-29 34 逐 10 ms 看实际声音：S2 w 2.615–2.635：a 的元音衰减到 /p/ 闭塞（-50～-52 dB，低频 0～-1 dB），w 2.65 起 purely 的 /p/ 除阻（-25 dB、重心 3.1 kHz），属于 a/purely 的交界", "实测": {"最响dB": -51.9, "重心Hz": 2261, "周期": 0.34, "低频dB": -0.3}}, "18.45–18.46s": {"配音指纹": "80c111d1ff5d", "依据": "2026-10-29 34 逐 10 ms 看实际声音：S2 w 4.785–4.80：so 的 /s/ 起始，从 -47 升到 -39 dB、重心 2.6→4.0 kHz，w 4.80 起 -24 dB、重心 5 kHz 的 /s/，属于 so", "实测": {"最响dB": -44.4, "重心Hz": 3033, "周期": 0.0, "低频dB": -0.5}}, "22.92–22.93s": {"配音指纹": "80c111d1ff5d", "依据": "2026-10-29 34 逐 10 ms 看实际声音：S2 w 9.255–9.27：characters 的 ɚ 浊音中段（-34～-37 dB、周期 0.42、低频 -1 dB），属于 characters", "实测": {"最响dB": -36.0, "重心Hz": 1028, "周期": 0.0, "低频dB": -2.3}}, "41.81–41.83s": {"配音指纹": "80c111d1ff5d", "依据": "2026-10-29 34 逐 10 ms 看实际声音：S5 w 7.845–7.86：and 的起音浊音（-42～-43 dB、周期 0.42、低频 0 dB），前面的吸气已删到 7.8436，w 7.87 起 -32、7.88 -17 dB 是 and 的元音，属于 and", "实测": {"最响dB": -43.4, "重心Hz": 2063, "周期": 0.0, "低频dB": -0.4}}, "47.31–47.34s": {"配音指纹": "80c111d1ff5d", "依据": "2026-10-29 34 逐 10 ms 看实际声音：S6 w 1.825–1.845：on 的起音（-42～-46 dB、低频 0～-1 dB），w 1.85 起 -30、1.86 -14 dB 是 on 的元音，属于 on", "实测": {"最响dB": -44.5, "重心Hz": 1883, "周期": 0.25, "低频dB": -0.2}}, "54.10–54.13s": {"配音指纹": "80c111d1ff5d", "依据": "2026-10-29 34 逐 10 ms 看实际声音：S7 w 2.91–2.94：an 的起音（-46～-51 dB、低频 -1 dB），w 2.95 起 -28 dB、周期 0.52 是 an 的元音，属于 an", "实测": {"最响dB": -47.3, "重心Hz": 3785, "周期": 0.38, "低频dB": -0.9}}, "69.75–69.84s": {"配音指纹": "80c111d1ff5d", "依据": "2026-10-29 34 逐 10 ms 看实际声音：S8 w 9.71–9.795：hold 的 /l/、/d/ 浊音闭塞（周期 0.3–0.45、低频 -1～-5 dB、重心 1–1.8 kHz），w 9.80 -50 dB 闭塞、9.81 -27 dB /d/ 除阻，属于 hold", "实测": {"最响dB": -35.3, "重心Hz": 1323, "周期": 0.33, "低频dB": -2.8}}, "76.50–76.60s": {"配音指纹": "80c111d1ff5d", "依据": "2026-10-29 34 逐 10 ms 看实际声音：S9 w 5.62–5.715：firms 的 /m/ 鼻音（-34～-38 dB、周期 0.3–0.48、低频 -2～-5 dB），w 5.75 起接 /z/（重心 5.5 kHz），属于 firms", "实测": {"最响dB": -35.2, "重心Hz": 1439, "周期": 0.32, "低频dB": -4.2}}, "77.17–77.18s": {"配音指纹": "80c111d1ff5d", "依据": "2026-10-29 34 逐 10 ms 看实际声音：S9 w 6.31–6.325：one 的起音（-44～-47 dB、低频 0～-2 dB），w 6.33 起 -23、6.34 -16 dB 是 one 的 /w/，属于 one", "实测": {"最响dB": -49.2, "重心Hz": 2871, "周期": 0.0, "低频dB": -1.3}}, "77.78–77.79s": {"配音指纹": "80c111d1ff5d", "依据": "2026-10-29 34 逐 10 ms 看实际声音：S9 w 6.92–6.935：by 的 /b/ 浊音杠（w 6.93 -37 dB），w 6.94 /b/ 除阻 -8 dB，属于 by", "实测": {"最响dB": -51.9, "重心Hz": 2545, "周期": 0.0, "低频dB": -1.2}}, "83.85–83.94s": {"配音指纹": "80c111d1ff5d", "依据": "2026-10-29 34 逐 10 ms 看实际声音：S10 w 2.95–3.045：Rogers 的 ɚ 浊音（周期 0.3–0.4、低频 -1～-6 dB、重心 1–1.7 kHz），w 3.04 起接 /z/（重心 4.5–5.8 kHz），属于 Rogers", "实测": {"最响dB": -35.4, "重心Hz": 1793, "周期": 0.26, "低频dB": -2.4}}, "90.87–90.97s": {"配音指纹": "80c111d1ff5d", "依据": "2026-10-29 34 逐 10 ms 看实际声音：S10 w 10.00–10.105：Elorg 的 /g/ 浊音闭塞（-37～-50 dB、周期 0.15–0.48、低频 0～-6 dB），w 10.11 /g/ 除阻（-28 dB、重心 3.5 kHz），属于 Elorg", "实测": {"最响dB": -37.5, "重心Hz": 1391, "周期": 0.21, "低频dB": -2.1}}, "85.75–85.80s": {"配音指纹": "80c111d1ff5d", "依据": "2026-10-29 34 逐 10 ms 看实际声音：S10 w 4.87–4.91：Dutch 的 /d/ 浊音杠（-47→-33 dB、周期 0.29→0.55、低频 0～-2 dB、重心 1.6→0.56 kHz），w 4.91 /d/ 除阻（重心 2.5 kHz），属于 Dutch", "实测": {"最响dB": -33.5, "重心Hz": 777, "周期": 0.55, "低频dB": -0.2}}, "90.91–90.92s": {"配音指纹": "80c111d1ff5d", "依据": "2026-10-29 34 逐 10 ms 看实际声音：S10 w 10.04–10.055：Elorg 的 /g/ 浊音闭塞中段（-37～-40 dB、低频 -1 dB），属于 Elorg", "实测": {"最响dB": -41.4, "重心Hz": 1067, "周期": 0.0, "低频dB": -1.9}}, "90.94–90.97s": {"配音指纹": "80c111d1ff5d", "依据": "2026-10-29 34 逐 10 ms 看实际声音：S10 w 10.065–10.105：Elorg 的 /g/ 闭塞到除阻（w 10.11 -28 dB、重心 3.5 kHz），属于 Elorg", "实测": {"最响dB": -43.6, "重心Hz": 1845, "周期": 0.38, "低频dB": -1.1}}, "100.19–100.28s": {"配音指纹": "80c111d1ff5d", "依据": "2026-10-29 34 逐 10 ms 看实际声音：S11 w 7.725–7.81：bidder. 句末 ɚ 的自然衰减（-34～-39 dB，连续降到 7.86 的 -99 dB，中间不断），属于 bidder", "实测": {"最响dB": -35.2, "重心Hz": 1498, "周期": 0.25, "低频dB": -3.8}}, "95.53–95.56s": {"配音指纹": "80c111d1ff5d", "依据": "2026-10-29 34 逐 10 ms 看实际声音：S11 w 3.075–3.115：were 的 /w/ 起音（-42～-49 dB、周期 0.47、低频 0 dB），w 3.12 起 -33、3.125 -16 dB，属于 were", "实测": {"最响dB": -43.2, "重心Hz": 2030, "周期": 0.39, "低频dB": -0.1}}, "97.36–97.38s": {"配音指纹": "80c111d1ff5d", "依据": "2026-10-29 34 逐 10 ms 看实际声音：S11 w 4.905–4.925：hectic 中 /k/ 和 /t/ 之间的闭塞里的除阻余音（-48～-51 dB），w 4.97 起 /t/ 除阻 -30 dB，属于 hectic", "实测": {"最响dB": -49.2, "重心Hz": 2198, "周期": 0.22, "低频dB": -9.5}}, "108.63–108.64s": {"配音指纹": "80c111d1ff5d", "依据": "2026-10-29 34 逐 10 ms 看实际声音：S12 w 7.28–7.295：rights 的元音收尾进 /t/ 闭塞（-36 dB、低频 0 dB），w 7.29–7.33 闭塞、7.34 /ts/ 除阻（重心 3.9–5 kHz），属于 rights", "实测": {"最响dB": -38.0, "重心Hz": 1660, "周期": 0.0, "低频dB": -0.5}}, "114.28–114.30s": {"配音指纹": "80c111d1ff5d", "依据": "2026-10-29 34 逐 10 ms 看实际声音：S13 w 4.265–4.29：and 起音前的浊音（低频 -0.2～-1.6 dB），前面的吸气已删到 4.257625，w 4.30 起 and -24.7 dB，属于 and", "实测": {"最响dB": -43.7, "重心Hz": 2692, "周期": 0.34, "低频dB": -0.2}}, "115.39–115.39s": {"配音指纹": "80c111d1ff5d", "依据": "2026-10-29 34 逐 10 ms 看实际声音：S13 w 5.375–5.385：shipped 的 /p/ 除阻（-38 dB、重心 3.4 kHz、单帧），前后是 /p/、/t/ 闭塞，属于 shipped", "实测": {"最响dB": -38.1, "重心Hz": 3721, "周期": 0.0, "低频dB": -15.2}}, "123.08–123.11s": {"配音指纹": "80c111d1ff5d", "依据": "2026-10-29 34 逐 10 ms 看实际声音：S15 w 0.785–0.81：began 的 /b/ 浊音杠（-42～-50 dB、周期 0.5、低频 0 dB），w 0.81 /b/ 除阻，属于 began", "实测": {"最响dB": -43.3, "重心Hz": 1586, "周期": 0.5, "低频dB": -0.2}}, "126.08–126.10s": {"配音指纹": "80c111d1ff5d", "依据": "2026-10-29 34 逐 10 ms 看实际声音：S15 w 3.78–3.80：around 的起音（-41～-42 dB、周期 0.42、低频 0 dB），前面的吸气已删到 3.7834，w 3.80 起 -22 dB，属于 around", "实测": {"最响dB": -41.4, "重心Hz": 1865, "周期": 0.3, "低频dB": -0.2}}, "138.53–138.56s": {"配音指纹": "80c111d1ff5d", "依据": "2026-10-29 34 逐 10 ms 看实际声音：S17 w 3.00–3.025：helped 的 /p/ 除阻（-36～-37 dB、重心 3.2–3.3 kHz），前后是 /p/、/t/ 闭塞，属于 helped", "实测": {"最响dB": -38.6, "重心Hz": 3688, "周期": 0.32, "低频dB": -19.2}}}
CONF["删除段"]={"S1 raw 6.3200-6.6600": "2026-10-29 配音指纹 80c111d1ff5d 实际声音：删除段对应 非人声区间 S1 [6.31, 6.645] 和 coder, 的停顿；w 6.29 coder 收尾降到 -51 dB，6.32–6.57 是 -41～-49 dB 的吸气（删掉的部分重心 2–3.5 kHz、低频 -10～-27 dB、周期 ≤0.33，是吸气声，不是词）；6.58–6.64 降到 -55 dB，6.66 起是 grew 的 /g/，没删；复核报 lost 是吸气本身偏响", "S8 raw 5.7400-6.1250": "2026-10-29 配音指纹 80c111d1ff5d 实际声音：删除段对应 非人声区间 S8 [5.75, 6.095] 和 exports, 的停顿；w 5.70 /s/ 结束，5.71–5.91 -50～-57 dB，5.92–6.08 是 -40～-48 dB 的吸气（删掉的部分重心 2–3.5 kHz、低频 -10～-27 dB、周期 ≤0.33，是吸气声，不是词）；6.10–6.11 降到 -57/-65 dB，没碰 the；复核报 lost 是吸气本身偏响", "S2 raw 2.1544-2.3625": {"类型": "紧贴词尾的非人声", "配音指纹": "80c111d1ff5d", "依据": "2026-10-29 实际声音：非人声区间 S2 [2.134333, 2.3425, 紧贴词尾]；sixty 的 i 在 w 2.12–2.13 降到 -43/-54.6 dB，左头切在过零点 2.134333；2.15–2.33 是 -39～-41 dB 的气声（删掉的部分重心 2–3.5 kHz、低频 -10～-27 dB、周期 ≤0.33，是吸气声，不是词）；右头 2.3425 外侧 5 ms -56.7 dB，had 的 /h/ 从 2.36 起，没碰"}, "S5 raw 7.5250-7.9436": {"类型": "紧贴词头的非人声", "配音指纹": "80c111d1ff5d", "依据": "2026-10-29 实际声音：非人声区间 S5 [7.6, 7.843625, 紧贴词头] 和 property, 的停顿；w 7.55–7.63 -55～-61 dB，7.64–7.83 是 -36～-51 dB 的吸气（删掉的部分重心 2–3.5 kHz、低频 -10～-27 dB、周期 ≤0.33，是吸气声，不是词）；切点后 7.84–7.86 低频 -1 dB 的浊音是 and 的起音，保留，and 的元音 7.88 起完整"}, "S6 raw 1.6667-1.8460": {"类型": "紧贴两头的非人声", "配音指纹": "80c111d1ff5d", "依据": "2026-10-29 实际声音：非人声区间 S6 [1.646708, 1.826083, 紧贴两头]；freely 的 i 收尾后 1.68–1.80 是 -44～-47 dB 的吸气（删掉的部分重心 2–3.5 kHz、低频 -10～-27 dB、周期 ≤0.33，是吸气声，不是词）；两头切在过零点，切点后 1.83–1.84 低频 -1 dB 是 on 的起音，保留，on 的元音 1.85 起完整"}, "S7 raw 2.6150-2.9161": {"类型": "紧贴词头的非人声", "配音指纹": "80c111d1ff5d", "依据": "2026-10-29 实际声音：非人声区间 S7 [2.67, 2.906125, 紧贴词头] 和 Stein, 的停顿；w 2.62–2.71 -55～-66 dB，2.72–2.89 是 -40～-52 dB 的吸气（删掉的部分重心 2–3.5 kHz、低频 -10～-27 dB、周期 ≤0.33，是吸气声，不是词）；切点后 2.91–2.94 低频 -1 dB 是 an 的起音，保留，an 的元音 2.95 起完整"}, "S12 raw 2.4400-2.7500": {"类型": "紧贴词头的非人声", "配音指纹": "80c111d1ff5d", "依据": "2026-10-29 实际声音：Rogers, 的停顿删除；/z/ 在 w 2.41 结束，2.42–2.44 降到 -54～-59 dB，2.45–2.71 是 -42～-52 dB 的吸气（删掉的部分重心 2–3.5 kHz、低频 -10～-27 dB、周期 ≤0.33，是吸气声，不是词）；2.73–2.745 低频 0～-2 dB 的浊音是 and 的声门起音，经 2.755 的 -57 dB 后 2.775 起 and 的元音 -24 dB，完整"}, "S13 raw 3.8450-4.2676": {"类型": "紧贴词头的非人声", "配音指纹": "80c111d1ff5d", "依据": "2026-10-29 实际声音：非人声区间 S13 [4.04, 4.257625, 紧贴词头] 和 Boy, 的停顿；w 3.98–4.05 -54～-61 dB，4.06–4.25 从 -52 升到 -39 dB 的吸气（重心 2.2–2.7 kHz、低频 -10～-18 dB、周期 0.2–0.4）；右头切在过零点 4.257625，4.26–4.29 低频 -0.2～-1.6 dB 的浊音是 and 的起音，保留，and 4.30 起 -24.7 dB 完整"}, "S15 raw 3.5913-3.8034": {"类型": "紧贴两头的非人声", "配音指纹": "80c111d1ff5d", "依据": "2026-10-29 实际声音：非人声区间 S15 [3.571292, 3.783375, 紧贴两头]；expiry 的 i 在 w 3.56 收尾（-33 dB），3.57–3.76 是 -39～-53 dB 的吸气（删掉的部分重心 2–3.5 kHz、低频 -10～-27 dB、周期 ≤0.33，是吸气声，不是词）；切点后 3.78–3.79 低频 -1 dB 是 around 的起音，保留，3.80 起 -22 dB 完整"}}
out={"no":"34","title_en":"The Game That Escaped the Soviet Union","title_zh":"越过铁幕的俄罗斯方块","title_fx":{"hl":["Escaped","Soviet"],"ghost":[]},"sentences":[],"核对确认":CONF,"结尾解说":"简述",
     "说明放宽特批":{"S17":{"倍数":"整屏","依据":"用户 2026-10-25 看 25 简述截图：“以后以后一定要合理的安排，不要压缩成这个样子……这个地方特批一下”（用户同意记录：原话适用以后各篇，26 起沿用）"}},
     "非人声区间":{"S1": [[6.31, 6.645]], "S2": [[2.134333, 2.3425, "紧贴词尾"]], "S4": [[3.595, 3.815]], "S5": [[2.83, 2.865], [7.6, 7.843625, "紧贴词头"]], "S6": [[1.646708, 1.826083, "紧贴两头"]], "S7": [[2.67, 2.906125, "紧贴词头"]], "S8": [[5.75, 6.095]], "S9": [[6.065, 6.307833, "紧贴词头"]], "S13": [[4.04, 4.257625, "紧贴词头"]], "S15": [[3.571292, 3.783375, "紧贴两头"]], "S16": [[1.515, 1.735]]},
     "句子增益dB":{"S3":-1.0},
     "高亮开始":{"S9 第2块":72.665},
     "高亮按实际开口":True,"高亮开口门槛":40,
     "术语":{"Tetris":"俄罗斯方块","Eastern bloc":"东欧集团","Alexey Pajitnov":"阿列克谢·帕基特诺夫","Pajitnov":"帕基特诺夫","Moscow":"莫斯科","Greek":"希腊语","Robert Stein":"罗伯特·斯坦因","Stein":"斯坦因","British":"英国","Hungary":"匈牙利","Soviet":"苏联","Western":"西方","Robert Maxwell":"罗伯特·马克斯韦尔","Henk Rogers":"亨克·罗杰斯","Rogers":"罗杰斯","Dutch-born":"荷兰裔","Kevin Maxwell":"凯文·马克斯韦尔","Nintendo":"任天堂","The Tetris Company":"俄罗斯方块公司"}}
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 核对 import 生成并核对
生成并核对(S, out)
