import json,re,glob,os
# 第37篇初稿（逐词对照）：S = [(段, [chunk, ...])]，chunk = ([(英文组, 中文组), ...], 可选 note)
# 重点词中文沿用文章定稿（铁律），只按《翻译风格》调格式；短语型用法整体标（T22）；不用破折号（T36）；三项并列加牛津逗号（T18）。
S=[
(1,[[[("Around 1847","1847年前后，"),("the Italian","意大利"),("chemist","化学家"),("Sobrero","索布雷罗"),("first","首次"),("made","制得"),("nitroglycerin,","硝酸甘油，")]],
    [[("a **colourless**,","这是一种**无色**(colourless)、"),("**oily**","**油状的**(oily)"),("**liquid**","**液体**(liquid)，"),("of","具有"),("**acute**","**极度的**(acute)"),("**instability**.","**不稳定性**(instability)。")],
     "（“acute”的核心意思就是“尖锐而强烈”，\n既可指角度小于90度的锐角，\n也可形容感官极度敏锐、问题严峻紧迫或疾病发作急骤。）"]]),
(1,[[[("A **mere**","**仅仅**(mere)一"),("**droplet**","**小滴**(droplet)"),("on the tongue,","放在舌头上，"),("he","他"),("reported,","报告说，")],
     "（he reported：插入语，表示这是他自己的说法）"],
    [[("left","就让"),("his head","他头部"),("**throbbing** **violently**","**剧烈地**(violently)**抽痛了**(throbbing)"),("for hours.","好几个小时。")],
     "（leave sb/sth doing：使……处于某种状态；\nthrobbing violently：现在分词短语作宾语补足语）"]]),
(1,[[[("On 3 September 1864","1864年9月3日，"),("a","一间"),("**nitroglycerin**","**硝酸甘油**(nitroglycerin)"),("**shed**","**棚屋**(shed)"),("in Stockholm","在斯德哥尔摩"),("exploded.","发生爆炸。")],
     "（shed：简易房，棚（用于贮藏物品））"]]),
(1,[[[("The","这场"),("**tragic**","**悲惨的**(tragic)"),("blast","爆炸"),("killed","炸死了"),("five,","五个人，"),("including","其中包括"),("Alfred Nobel's","阿尔弗雷德·诺贝尔的"),("younger brother","弟弟"),("Emil.","埃米尔。")],
     "（including…：介词短语，补充说明死者中有谁）"]]),
(2,[[[("Nobel","诺贝尔"),("**tamed**","**驯服了**(tamed)"),("the liquid","这种液体，")]],
    [[("by **blending** it with kieselguhr, a **porous** earth,","方法是把它与硅藻土这种**多孔的**(porous)土**混合**(blending)，"),("into a **paste**","制成**糊状物**(paste)，"),("shaped into **rods**.","再塑造成**棒条**(rods)状。")],
     "（blend A with B into C：把 A 与 B 混合成 C；\na porous earth：同位语，补充说明 kieselguhr；\nshaped into rods：过去分词短语作后置定语，修饰 paste）"]]),
(2,[[[("Patented in 1867 as dynamite,","1867年作为炸药获得专利后，")],
     "（Patented…：过去分词短语作状语，表被动）"],
    [[("it","它"),("was **harnessed**","被**用于**(harnessed)"),("for mining,","采矿、"),("**quarrying**,","**采石**(quarrying)"),("and demolition,","和拆除工程，")],
     "（be harnessed for…：被用于……）"],
    [[("**enriching** him","让他**获利**(enriching)"),("**immensely**.","十分**丰厚**(immensely)。")],
     "（enriching…：现在分词短语作结果状语）"]]),
(2,[[[("His","他"),("1895","在1895年立下的"),("**testament**","**遗嘱**(testament)"),("made","使"),("the fortune","这笔财产"),("an **endowment**","成为一笔**基金**(endowment)，"),("for prizes,","用来设立奖项，")],
     "（make A B：使 A 成为 B）"],
    [[("first","奖项首次"),("awarded","颁发"),("in 1901.","于1901年。")],
     "（first awarded…：过去分词短语作后置定语，修饰 prizes）"]]),
(3,[[[("Nitroglycerin","硝酸甘油"),("had","有"),("**side-effects**.","**副作用**(side-effects)。")]]]),
(3,[[[("**Factory operatives**","**工厂工人**(Factory operatives)"),("suffered","饱受"),("**racking**","**折磨人的**(racking)"),("headaches,","头痛，")]],
    [[("and their","他们的"),("**tolerance**,","**耐受性**(tolerance)"),("built over the week,","在一周中逐渐建立，"),("**ebbed** at weekends.","到周末又**减退**(ebbed)。")],
     "（built over the week：过去分词短语作插入语，修饰 tolerance）"]]),
(3,[[[("Mondays","每逢星期一，"),("brought a **recurrence**,","头痛便**复发**(recurrence)，"),("with","还伴有"),("**dizziness**","**眩晕**(dizziness)"),("and **palpitations**,","和**心悸**(palpitations)，")],
     "（with…：介词短语作伴随状语）"],
    [[("**hence**","**因此**(hence)"),("the name","得名"),("Monday disease.","星期一病。")],
     "（hence＋名词：因此有了……，省略了谓语）"]]),
(3,[[[("In 1879","1879年，"),("William Murrell","威廉·默雷尔"),("reported in The Lancet","在《柳叶刀》上报告了"),("on its **therapeutic** use against angina pectoris,","它对心绞痛的**治疗**(therapeutic)用途，")],
     "（report on…：报告关于……的情况；\nagainst angina pectoris：后置定语，修饰 use）"],
    [[("attacks","也就是阵发性的"),("of chest pain.","胸痛。")],
     "（attacks of chest pain：同位语，补充说明 angina pectoris）"]]),
(4,[[[("On 25 October 1896","1896年10月25日，"),("Nobel, who had angina,","患有心绞痛的诺贝尔")],
     "（who had angina：非限制性定语从句，补充说明 Nobel）"],
    [[("wrote","写信"),("to his **aide**","给他的**助手**(aide)，"),("that","说"),("by an irony of fate","命运真是讽刺，")],
     "（that…：宾语从句，说明信的内容；\nby an irony of fate：说来讽刺，命运弄人）"],
    [[("doctors","医生"),("had prescribed him","竟给他开了"),("nitroglycerin","硝酸甘油"),("to take **internally**.","让他**内服**(internally)。")],
     "（prescribe sb sth：给某人开某药；\nto take internally：不定式表目的）"]]),
(4,[[[("Its **alias**,","这种药的**别名**(alias)"),("Trinitrin,","Trinitrin"),("was chosen,","是特意选的，"),("he explained,","他解释说，")],
     "（Trinitrin：同位语，补充说明 alias；\nhe explained：插入语）"],
    [[("to avoid","为的是避免"),("**frightening**","**吓到**(frightening)"),("**pharmacists**","那些**药剂师**(pharmacists)"),("or the public.","和公众。")],
     "（avoid doing：避免做某事）"]]),
(4,[[[("He","他"),("did not","没有"),("**comply**.","**遵从**(comply)医嘱。")]]]),
(4,[[[("**Partly**","身体**部分**(Partly)"),("**paralysed**","**瘫痪**(paralysed)，"),("by a **cerebral haemorrhage**,","是由**脑部出血**(cerebral haemorrhage)造成的，")],
     "（Partly paralysed by…：过去分词短语作状语，\n说明他去世前的状况）"],
    [[("he","他"),("died at his San Remo **villa** on 10 December 1896.","于1896年12月10日在圣雷莫的**别墅**(villa)中去世。")],
     "（at his San Remo villa：地点状语；\non 10 December 1896：时间状语）"]]),
(5,[[[("In 1977","1977年，"),("Murad","穆拉德"),("**ascertained**","**查明**(ascertained)"),("that nitroglycerin","硝酸甘油"),("releases","会释放"),("nitric oxide,","一氧化氮，")],
     "（that…：宾语从句）"],
    [[("which **widens**","它会**扩张**(widens)"),("blood vessels.","血管。")],
     "（which…：非限制性定语从句，修饰 nitric oxide）"]]),
(5,[[[("Furchgott","弗奇戈特"),("found","发现了"),("an **unidentified**","一种**未经鉴定的**(unidentified)"),("relaxing **factor**","舒张**因子**(factor)，"),("in **vascular**","存在于**血管的**(vascular)"),("**linings**","**内壁**(linings)里，"),("in 1980,","这是1980年的事；")],
     "（relaxing factor：舒张因子，能让血管放松的物质；\nin vascular linings：地点状语）"],
    [[("and Ignarro","伊格纳罗"),("recognised it","认定它"),("as nitric oxide","就是一氧化氮，"),("in 1986.","这是1986年的事。")],
     "（recognise A as B：认定 A 是 B）"]]),
(5,[[[("The **trio**","这个**三人组**(trio)"),("shared","分享了"),("the 1998","1998年"),("Nobel Prize","诺贝尔"),("in Physiology or Medicine.","生理学或医学奖。")]]]),
(5,[[[("Its","这个奖的"),("**presentation**","**颁奖**(presentation)"),("speech,","致辞"),("on 10 December,","在12月10日，"),("the anniversary of Nobel's death,","也就是诺贝尔的忌日，")],
     "（on 10 December：时间状语；\nthe anniversary of Nobel's death：同位语，补充说明 10 December）"],
    [[("**quoted**","**引述了**(quoted)"),("his","他那封"),("**ironic**","感叹命运**讽刺**(ironic)的"),("letter.","信。")],
     "（quote：引用，引述）\n"
     "（简述：1847年前后，索布雷罗制得极不稳定的硝酸甘油，一小滴就让他头痛数小时。\n"
     "1864年，斯德哥尔摩的一场爆炸夺走了诺贝尔弟弟的生命。\n"
     "诺贝尔把它与硅藻土混合制成炸药，1867年获专利，靠采矿、采石和拆除发了大财，\n"
     "1895年又立遗嘱用这笔财产设立奖项。制炸药的工人饱受头痛之苦，星期一最重，\n"
     "1879年默雷尔报告它能治心绞痛。晚年患心绞痛的诺贝尔也被医生开了硝酸甘油，\n"
     "他在信里说这是命运的讽刺，却没有遵从医嘱，1896年12月10日在圣雷莫去世。\n"
     "后来三位科学家查明它释放一氧化氮、使血管扩张，分享了1998年诺贝尔奖，\n"
     "颁奖致辞正是在他的忌日引述了那封信。）"]]),
]
CONF={
"合组": {
"S4 younger brother": "对齐不了：younger brother 中文就是一个词“弟弟”",
"S5 by blending it with kieselguhr, a porous earth": "对齐不了：blend A with B 中文“把 A 与 B 混合”，动词“混合”必须放到最后；a porous earth 是同位语，中文“硅藻土这种多孔的土”，拆开不通",
"S9 built over the week": "对齐不了：over the week 是时间状语，中文“在一周中逐渐建立”时间必须放到动词前",
"S11 on its therapeutic use against angina pectoris": "对齐不了：against angina pectoris 是后置定语，修饰 use，中文“它对心绞痛的治疗用途”必须提前；angina pectoris 是一个病名“心绞痛”",
"S11 of chest pain": "对齐不了：chest pain 中文就是一个词“胸痛”",
"S12 by an irony of fate": "对齐不了：by an irony of fate 是固定说法“说来讽刺，命运弄人”，拆开不通",
"S16 nitric oxide": "对齐不了：nitric oxide 是化学名，中文就是一个词“一氧化氮”",
"S16 blood vessels": "对齐不了：blood vessels 中文就是一个词“血管”",
"S17 as nitric oxide": "对齐不了：nitric oxide 是化学名，中文就是一个词“一氧化氮”",
"S19 the anniversary of Nobel's death": "对齐不了：the anniversary of A's death 中文就是“A 的忌日”，of 结构必须倒过来，anniversary of death 合成一个词“忌日”"
},
"对齐": {
"S5-2 by blending it with kieselguhr": "blend A with B 中文“把 A 与 B 混合”，动词必须放到最后；a porous earth 是同位语，补充说明 kieselguhr",
"S6-1 Patented in 1867 as dynamite,": "过去分词短语作状语，中文“1867年作为炸药获得专利后”时间、方式状语必须放到动词前",
"S11-1 on its therapeutic use against": "against angina pectoris 是后置定语，修饰 use，中文“对心绞痛的治疗用途”必须提前",
"S12-2 by an irony of fate": "by an irony of fate 是固定说法，拆开不通",
"S15-2 died at his San Remo villa on ": "at his San Remo villa 地点状语、on 10 December 1896 时间状语，中文“于……在……中去世”时间、地点必须放到动词前",
"S19-1 the anniversary of Nobel's dea": "the anniversary of A's death 中文“A 的忌日”，of 结构必须倒过来"
},
"短语": {
"S2 throbbing … for": "不是搭配：for hours 是时间状语（好几个小时），和 throbbing 无关",
"S5 tamed … with": "不是搭配：with 属于 blending it with kieselguhr，和 tamed 无关",
"S5 blending … with": "不是搭配：blend A with B 里 with 引出混合的另一方（kieselguhr），blend 单独就是“混合”，同 34 篇 bundle A with B 先例",
"S5 blending … into": "不是搭配：into a paste 引出混合的结果（制成糊状物），blend 单独就是“混合”",
"S6 harnessed … for": "不是搭配：for 引出用途（采矿、采石和拆除），harness 单独就是“利用，用于”",
"S10 with … dizziness": "不是搭配：with 是普通介词，引出伴随的症状 dizziness and palpitations（还伴有眩晕和心悸）",
"S15 paralysed … by": "不是搭配：by 是被动句引出原因的普通介词（由脑部出血造成），paralyse 单独就是“瘫痪”",
"S19 presentation … of": "不是搭配：of 属于 the anniversary of Nobel's death，和 presentation 无关"
},
"牛津逗号": {
"S10 Mondays brought a recurrence, with dizziness and": "不是三项并列：逗号隔开的是伴随状语 with dizziness and palpitations，只有 dizziness、palpitations 两项",
"S13 he explained, to avoid frightening pharmacists or": "不是三项并列：逗号隔开的是插入语 he explained，pharmacists or the public 只有两项"
}
}
CONF["停顿位置"]={
 "S2 tongue, / he @1.685":"2026-11-03 逐 2.5 ms 看声音（S2 w，配音指纹 6e54939824ed）：tongue 的 /ŋ/ 浊音到 1.6775 收尾（周期 0.37→0.18、重心 0.8→2.3 kHz），1.6825–1.6925 降到 -38～-42 dB 低谷；1.6875 起 he 的 /h/ 送气（重心 3.5–5 kHz、低频 -7～-22 dB）慢慢升到 1.7325 的 -34 dB，1.7525 起 i 元音（-20 dB）；1.685 落在 /ŋ/ 结束、/h/ 起来之前的低谷（-38 dB），插在这里不切前后词（A42）",
 "S6 quarrying, / and @5.735":"2026-11-03 逐 2.5 ms 看声音（S6 w）：quarrying 的 /ŋ/ 浊音到 5.7075（-15.8 dB），5.7125–5.7175 降到 -27 dB，5.7275 一下残余脉冲 -20 dB，5.7325–5.7375 是两词之间最低处 -33.8/-34.4 dB（过零 5.732833、5.737958），5.7425 起 and 的元音 -15.6 dB；5.735 正在这个低谷里，不切前后词（A42）",
 "S9 tolerance, / built @3.935":"2026-11-03 逐 2.5 ms 看声音（S9 w）：tolerance 的 /s/ 3.86–3.915（重心 5–6.2 kHz、低频 -22～-52 dB），3.92–3.925 降到 -32/-36 dB，3.93–3.94 是最低处 -45～-47 dB，3.945 起 built 的 /b/ 浊音杠（低频 -0.5～-1.8 dB、重心 0.24–0.83 kHz），4.035 /b/ 除阻；3.935 落在 /s/ 结束、/b/ 浊音杠开始之前的低谷（-45.1 dB），不切前后词（A42）",
 "S10 recurrence, / with @1.595":"2026-11-03 逐 2.5 ms 看声音（S10 w）：recurrence 的 /s/ 1.50–1.56（重心 3.7–6 kHz），1.5675 -42、1.5775 -55、1.5925 降到最低 -63.6 dB，1.6075 -47.5、1.6125 起 with 的 /w/（-24 dB、重心 0.5 kHz）；1.595 落在两词之间的静音（-58.8～-63.6 dB），不切前后词（A42）",
 "S13 Trinitrin, / was @1.703":"2026-11-03 逐 2.5 ms 看声音（S13 w）：Trinitrin 的 /n/ 直接连 was 的 /w/，中间没有低谷：1.56–1.70 是一段平稳鼻音（-19～-30 dB、周期 0.5–0.6、重心 0.4–0.65 kHz、低频 -1～-4 dB），1.7075 起包络升到 -16.6 dB、1.7175 -12.2、1.7225 起重心升到 1 kHz，是 /w/ 进 ə 的过渡；程序原点 1.630 落在 /n/ 正中间，改用停顿插入点交界 1.702625（过零点，/n/ 结束、/w/ 起升之前）",
 "S13 chosen, / he @2.467":"2026-11-03 逐 2.5 ms 看声音（S13 w）：chosen 的 /n/ 直接连 he，中间没有低谷：2.44–2.4625 是 /n/（-18～-24 dB、重心 0.5–0.9 kHz、低频 -1～-3 dB），2.465 起重心一路升（1.26→1.5→1.8→2.2 kHz），是浊化的 /h/ 进 iː；程序原点 2.510 落在 he 里面（重心已到 2.06 kHz），改用停顿插入点交界 2.46725（过零点，/n/ 结束、重心开始升之前）",
 "S19 December, / the @3.289":"2026-11-03 逐 2.5 ms 看声音（S19 w）：December 的 ɚ 一直到 3.29（-26～-37 dB、周期 0.45–0.56、重心 0.5–1.0 kHz、低频 -1～-3 dB），3.2925 起重心跳到 3.0–3.4 kHz，是 the 的 /ð/，3.3125 起 ə 元音；程序原点 3.240 落在 ɚ 尾巴中间（切了会把 50 ms ɚ 甩到停顿后面），改用停顿插入点交界 3.28925（过零点，ɚ 结束、/ð/ 开始之前）"}
CONF["删除段"]={'S3 raw 2.7300-3.0600': '2026-11-03 实际声音（S3 w = raw - 0.01）：1864 的 /ɹ/ 在 w 2.67 收尾（-47 dB），2.69 降到 -63 dB；w 2.72–3.00 是 -37～-57 dB 的吸气（重心 1.8–2.4 kHz、低频 -7～-30 dB、周期 ≤0.34，是吸气声，不是词，这里没有标点，是配音在 1864 后换气）；3.01–3.03 一小段低频起音后经 3.04–3.05 的 -54～-57 dB 低谷，3.0575 起 a 的元音完整；复核报 lost 是吸气本身偏响', 'S5 raw 3.0450-3.3300': '2026-11-03 实际声音（S5 w = raw - 0.02）：kieselguhr 的 ɚ 在 w 2.99 收尾（-29.8 dB），3.01–3.03 降到 -52～-56 dB；3.04–3.25 是 -36～-48 dB 的吸气（重心 1.8–2.6 kHz、低频 -7～-26 dB、周期 ≤0.37，是吸气声，不是词）；3.26–3.30 低频起音后 3.31 降到 -57.5 dB，3.32 起 a 的元音完整；复核报 lost 是吸气本身偏响', 'S13 raw 3.3700-3.7750': '2026-11-03 实际声音（S13 w = raw - 0.01）：explained 的 /d/ 在 w 3.34 收尾，3.355–3.39 是 -58～-67 dB 静音；3.395–3.67 是 -42～-56 dB 的吸气（重心 2.0–2.5 kHz、低频 -5～-22 dB、周期 ≤0.29，是吸气声，不是词）；3.695–3.725 是 -44～-49 dB 的低频喉音（吸气收尾声门合拢），之后 3.735–3.765 是 -59～-64 dB 的 /t/ 闭塞静音，3.775 起 to 的 /t/ 除阻（重心 3.8–5.5 kHz）完整，没删', 'S15 raw 5.2750-5.4800': '2026-11-03 实际声音（S15 w = raw）：villa 的 ə 在 w 5.255 收尾（-34.7 dB），5.265 降到 -54 dB；5.295–5.445 是 -39～-48 dB 的吸气（重心 1.8–2.6 kHz、低频 -5～-34 dB、周期 ≤0.36，是吸气声，不是词，这里没有标点，是配音在 villa 后换气）；5.455–5.485 低频起音后 5.495 降到 -58 dB，5.505 起 on 的元音完整；复核报 lost 是吸气本身偏响', 'S11 raw 1.6291-1.7800': {'类型': '紧贴词尾的非人声', '配音指纹': '60c9f0945458', '依据': '2026-11-03 实际声音（S11 w = raw - 0.01）：1879 的 nine 的 /n/ 浊音到 w 1.59（-24.6 dB、低频 -0.6 dB、周期 0.27），1.60 降到 -39.7、1.61 -45 dB；1.61–1.75 是 -38～-46 dB 的吸气（重心 2.0–2.9 kHz、低频 -10～-24 dB、周期 ≤0.35，是吸气声，不是词）；左头 1.619 在 /n/ 结束 20 ms 之后，没切到 nine；复核报词尾被切 125 ms 是把吸气算进了词；1.77–1.81 低频起音、1.82 起 William 的 /w/ 完整'}, 'S17 raw 6.0450-6.4902': {'类型': '紧贴词头的非人声', '配音指纹': '60c9f0945458', '依据': '2026-11-03 实际声音（S17 w = raw - 0.02）：1980 的 eighty 的 i 在 w 5.99 收尾，6.03–6.26 是 -58～-66 dB 静音；6.26–6.465 是 -44～-57 dB 的吸气（重心 2.2–3.1 kHz、低频 -9～-24 dB、周期 ≤0.48，是吸气声，不是词）；右头切在过零点 6.470167，之后 6.475–6.50 低频 -0.2～-3 dB 的浊音是 and 的声门起音，保留，经 6.505–6.515 的 -58～-60 dB 后 6.52 起 and 的元音完整；复核报 post 是这段起音本身'}, 'S9 raw 2.6500-2.9475': {'类型': '紧贴词头的非人声', '配音指纹': '60c9f0945458', '依据': '2026-11-03 实际声音（S9 w = raw - 0.02）：headaches 的 /s/ 在 w 2.60 前结束，2.6175–2.65 是 -56～-62 dB 静音；2.655–2.92 是 -41～-55 dB 的吸气（重心 2.0–2.8 kHz、低频 -8～-29 dB、周期 ≤0.29，是吸气声，不是词）；右头切在过零点 2.927583（2.9275 低频 -10 dB 还是吸气），之后 2.9375–2.9675 低频 -0.5～-5 dB 的浊音是 and 的声门起音，整段保留，2.9775 起 and 的元音 -24.5 dB 完整；复核报 onset/post 是把这段起音算成了词头'}, 'S1 raw 7.0650-7.3350': {'类型': '紧贴词尾的非人声', '配音指纹': '60c9f0945458', '依据': '2026-11-03 实际声音（S1 w = raw - 0.05）：colourless 的 /s/ 到 w 6.985 收尾（重心 4–5.8 kHz），6.99–7.01 降到 -49～-59 dB 低谷；7.015–7.12 是 -42～-55 dB 的吸气（重心 1.8–3.8 kHz、低频 -8～-24 dB、周期 ≤0.38，是吸气声，不是词），之后是逗号停顿；切点在 /s/ 结束、-58.8 dB 低谷之后，没切到 colourless；复核报词尾被切 10 ms 是把吸气起头算进了词'}}
CONF["机器复听"]={"S5":{"配音指纹":"60c9f0945458","依据":"2026-11-03 实测（配音指纹 60c9f0945458）：kieselguhr 已按 读音改正 读 kˈiːzəlɡˌʊɹ（kee-zuhl-goor，Dictionary.com/Wiktionary），读音核对 0；small.en 听成 kieselgore、parakeet 听成 kizilgur，两路辅音 k-z-l-g-r 全对，只差弱读元音（ə/ɪ）和尾元音 ʊ/oʊ 的近音，是不常见的德语借词、识别器词表里没有"}}
CONF["非人声"]={'8.29–8.31s': {'配音指纹': '60c9f0945458', '依据': '2026-11-03 37 逐 2.5 ms 看实际声音：S1 w 5.745–5.765：nitroglycerin 词尾 /n/ 的浊音（5.755–5.77 周期 0.45、低频 -1.6～-2.7 dB、重心 0.9–1.1 kHz），前面 5.745 一个小低谷，逗号删除段 5.82 才开始，属于 nitroglycerin'}, '18.89–19.01s': {'配音指纹': '60c9f0945458', '依据': '2026-11-03 37 逐 2.5 ms 看实际声音：S2 w 5.27–5.385：hours 的 ɚ 弱化段（-37～-50 dB、周期 0.15–0.33、低频 -3～-12 dB、重心 1.1–2.5 kHz），一路连到 5.38 起的词尾 /z/（重心 4.3–5.8 kHz），中间没有 -55 dB 低谷，属于 hours'}, '38.84–38.85s': {'配音指纹': '60c9f0945458', '依据': '2026-11-03 37 逐 2.5 ms 看实际声音：S5 w 5.095–5.11：a 的元音衰减进 paste 的 /p/ 闭塞（-53～-57 dB、低频 -0.3～-3 dB），5.115 起 /p/ 除阻（重心 3.3 kHz），属于 a/paste 的交界'}, '65.84–65.88s': {'配音指纹': '60c9f0945458', '依据': '2026-11-03 37 逐 2.5 ms 看实际声音：S9 w 2.9375–2.9675：and 的声门起音（-43～-46 dB、低频 -0.5～-5 dB、周期 0.1–0.32），紧接 2.9775 的 and 元音（-24.5 dB），属于 and'}, '67.25–67.27s': {'配音指纹': '60c9f0945458', '依据': '2026-11-03 37 逐 2.5 ms 看实际声音：S9 w 3.945–3.96：built 的 /b/ 浊音杠（低频 -0.5～-1.8 dB、重心 0.24–0.83 kHz、周期 0.26–0.42），4.035 /b/ 除阻，属于 built'}, '79.97–79.99s': {'配音指纹': '60c9f0945458', '依据': '2026-11-03 37 逐 2.5 ms 看实际声音：S11 w 1.77–1.80：William 起音前的声门浊音（-46～-56 dB、低频 -0.6～-1.3 dB），前面的吸气已删到 1.77，属于 William'}, '80.00–80.01s': {'配音指纹': '60c9f0945458', '依据': '2026-11-03 37 逐 2.5 ms 看实际声音：S11 w 1.805–1.82：William 的 /w/ 起音（-41～-55 dB、低频 -1.2～-2.4 dB），1.82 起 -25 dB、重心 0.6 kHz 的 /w/，属于 William'}, '101.08–101.17s': {'配音指纹': '60c9f0945458', '依据': '2026-11-03 37 逐 2.5 ms 看实际声音：S12 w 12.335–12.42：句末 internally 的 i 气声收尾：从元音连续降下来（-31→-51→-61 dB，重心 2.1–4.5 kHz、低频 -3～-16 dB），中间没有 -55 dB 低谷，一路降到 12.45 的 -86 dB，属于 internally'}, '115.73–115.75s': {'配音指纹': '60c9f0945458', '依据': '2026-11-03 37 逐 2.5 ms 看实际声音：S15 w 2.63–2.645：haemorrhage 中 /dʒ/ 前的浊音（-34～-43 dB、周期 0.26–0.52、低频 -2.4～-9 dB、重心 0.45–2.1 kHz），在词中间，属于 haemorrhage'}, '130.60–130.69s': {'配音指纹': '60c9f0945458', '依据': '2026-11-03 37 逐 2.5 ms 看实际声音：S16 w 8.535–8.625：vessels 的 /l/ 浊音弱化段（-32～-56 dB、周期 0.12–0.44、重心 0.7–2.3 kHz、低频 -5～-14 dB），连到 8.62 起的词尾 /z/（重心 4.2–5.7 kHz），属于 vessels'}, '123.85–123.86s': {'配音指纹': '60c9f0945458', '依据': '2026-11-03 37 逐 2.5 ms 看实际声音：S16 w 1.63–1.645：seventy-seven 词尾 /n/ 的衰减（-44～-56 dB、低频 -0.4～-3 dB），后面 1.65 起是已删掉的吸气，属于 seven'}, '137.78–137.80s': {'配音指纹': '60c9f0945458', '依据': '2026-11-03 37 逐 2.5 ms 看实际声音：S17 w 5.975–5.99：eighty 末尾 i 的衰减（-38～-46 dB、周期 0.22–0.44、低频 -1.3～-3.3 dB、重心 2.8–3.9 kHz，i 的第二共振峰高），逗号删除段 6.03 才开始，属于 eighty'}, '138.24–138.26s': {'配音指纹': '60c9f0945458', '依据': '2026-11-03 37 逐 2.5 ms 看实际声音：S17 w 6.475–6.50：and 的声门起音（-47～-53 dB、低频 -0.2～-3 dB、周期 0.18–0.45），经 6.505–6.515 低谷后 6.52 起 and 的元音，属于 and'}, '147.66–147.67s': {'配音指纹': '60c9f0945458', '依据': '2026-11-03 37 逐 2.5 ms 看实际声音：S18 w 3.52–3.545：in 的声门起音（-52～-57 dB、低频 -0.4～-1.8 dB、周期 0.23–0.41），前面的吸气已删到 3.517583，3.565 起 in 的元音，属于 in'}}
out={"no":"37","title_en":"Dynamite for the Heart","title_zh":"炸药大王的救心药","title_fx":{"hl":["Dynamite","Heart"],"ghost":[]},"sentences":[],"核对确认":CONF,"结尾解说":"简述",
     "说明放宽特批":{"S19":{"倍数":"整屏","依据":"用户 2026-10-25 看 25 简述截图：“以后以后一定要合理的安排，不要压缩成这个样子……这个地方特批一下”（用户同意记录：原话适用以后各篇，26 起沿用）"}},
     "非人声区间":{"S17":[[6.26,6.470167,"紧贴词头"]],"S9":[[2.655,2.927583,"紧贴词头"]],"S18":[[3.371,3.517583,"紧贴两头"]]},
     "句子增益dB":{"S14":-1.0},
     "高亮开始":{"S12 第3块":97.29},
     "停顿插入点":{"S13":{"2":[1.702625,"交界"],"3":[2.46725,"交界"]},"S19":{"2":[3.28925,"交界"]}},
     "高亮按实际开口":True,"高亮开口门槛":40,
     "术语":{"Sobrero":"索布雷罗","Italian":"意大利","Stockholm":"斯德哥尔摩","Alfred Nobel":"阿尔弗雷德·诺贝尔","Nobel":"诺贝尔","Emil":"埃米尔","William Murrell":"威廉·默雷尔","The Lancet":"柳叶刀","San Remo":"圣雷莫","Murad":"穆拉德","Furchgott":"弗奇戈特","Ignarro":"伊格纳罗","Trinitrin":"Trinitrin"}}
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 核对 import 生成并核对
生成并核对(S, out)
