import json,re,glob,os
# 第53篇初稿（逐词对照）：S = [(段, [chunk, ...])]，chunk = ([(英文组, 中文组), ...], 可选 note)
# 2026-11-05 重点词中文沿用文章定稿（铁律），只按《翻译风格》调格式；三项并列加牛津逗号（T18）；不用破折号（T36）；“了”进粗体；英文没有引号中文不加。
S=[
(1,[[[("On the morning of 7 November 1940,","1940年11月7日上午，"),("a **sustained** wind of about 40 miles an hour","一股时速约40英里的**持续**(sustained)大风"),("set","使"),("the Tacoma Narrows Bridge","塔科马海峡大桥"),("**twisting**.","**扭动**(twisting)起来。")],
     "（of about 40 miles an hour：后置定语，修饰 wind；\nset sth doing：使……（不停地）做某事）"]]),
(1,[[[("Its **deck**","它的**桥面**(deck)"),("**tilted** from side to side","左右**倾侧**(tilted)，"),("in ever more **violent** **oscillations**","**振荡**(oscillations)愈发**剧烈**(violent)，")],
     "（ever more＋形容词：越来越……）"],
    [[("until","直到"),("most of the main span","主跨大部分"),("**tore apart**","**断裂**(tore apart)、"),("and **tumbled** into the water.","**跌落**(tumbled)水中。")],
     "（until…：时间状语从句，直到……）"]]),
(1,[[[("No one died.","无人丧生。")]]]),
(1,[[[("**Footage** of the **spectacle**","这一**奇观**(spectacle)的**影像**(Footage)"),("would later","后来"),("**fascinate**","**吸引了**(fascinate)"),("students worldwide.","世界各地的学生。")],
     "（would later do：过去将来，后来会……）"]]),
(2,[[[("The bridge","这座桥"),("had opened in July 1940","于1940年7月通车，")],
     "（had opened：过去完成时，通车早于坍塌）"],
    [[("as","其主跨是"),("the third-longest","当时世界上第三长的"),("**suspension**","**悬索**(suspension)桥"),("**span** in the world at the time,","**跨径**(span)，")],
     "（as…：作为……；at the time：在当时）"],
    [[("its roadway","路面"),("hung from","悬挂在"),("steel","钢"),("cables.","缆上。")],
     "（its roadway hung from…：独立主格结构，\n补充说明桥的结构）"]]),
(2,[[[("Girders only eight feet deep stiffened the deck,","加劲桥面的钢梁只有8英尺高，")],
     "（only eight feet deep：后置定语，修饰 Girders）"],
    [[("making it","使桥身"),("**slender**,","**纤细**(slender)、"),("**elegant**,","**优雅**(elegant)"),("and **economical**,","而又**省钱**(economical)，"),("but far from **rigid**.","却远谈不上**刚硬**(rigid)。")],
     "（making it…：现在分词短语作结果状语；\nfar from：远非）"]]),
(2,[[[("Even **faint**","哪怕**轻微的**(faint)"),("**breezes**","**微风**(breezes)"),("made it **heave**,","也会让它**起伏**(heave)，")],
     "（make sth do：使……做）"],
    [[("earning the **nickname**","由此得了个**绰号**(nickname)："),("Galloping Gertie.","舞动的格蒂。")],
     "（earning…：现在分词短语作结果状语）"]]),
(3,[[[("**Textbooks**","**教科书**(Textbooks)"),("have long","长期以来一直"),("**invoked**","**援引**(invoked)"),("**resonance**:","**共振**(resonance)来解释：")],
     "（have long done：现在完成时，长期以来一直……）"],
    [[("{{=}}a **periodic** push that matches an object's natural **frequency**","与物体固有**频率**(frequency)相合的**周期性的**(periodic)推力"),("can **amplify**","能**放大**(amplify)"),("its motion,","其运动，")],
     "（that matches…：定语从句，修饰 push）"],
    [[("as when","就像"),("well-timed","合拍的"),("shoves","一次次推送"),("**propel**","**推动**(propel)"),("a child on a swing.","秋千上的孩子越荡越高。")],
     "（as when…：就像……的时候那样）"]]),
(3,[[[("The **analogy**","这个**类比**(analogy)"),("is **intuitive**","**直观**(intuitive)"),("but **deceptive**.","却**具有迷惑性**(deceptive)。")]]]),
(3,[[[("That morning's","那天上午的"),("wind","风"),("did not **pulse** in time with the bridge;","并没有合着大桥的节拍**一阵阵涌动**(pulse)；")],
     "（in time with：合着……的节拍）"],
    [[("it blew","它吹得"),("fairly **steadily**.","还算**平稳**(steadily)。")]]]),
(4,[[[("The **mechanism**","其**机理**(mechanism)"),("was **subtler**.","要**更为微妙**(subtler)。")]]]),
(4,[[[("Each twist","每一次扭动都"),("**altered**","**改变了**(altered)"),("the passing","掠过的"),("airflow,","气流，")]],
    [[("which","而气流又"),("**reinforced**","**加强了**(reinforced)"),("the next","下一次"),("twist:","扭动：")],
     "（which…：非限制性定语从句，指代 the passing airflow）"],
    [[("a **feedback** loop that kept **tapping** the wind for energy.","这是一个不断从风中**汲取**(tapping)能量的**反馈**(feedback)回路。")],
     "（a feedback loop：同位语，概括前面的过程；\nkeep doing：不断做；tap A for B：从 A 汲取 B）"]]),
(4,[[[("In March 1941","1941年3月，"),("a federal **panel**","一个联邦**调查委员会**(panel)"),("blamed","把原因归于"),("the deck's **flexibility**","桥面的**柔性**(flexibility)"),("and","和"),("wing-like","类似机翼的"),("lift.","升力。")],
     "（blame…：把（事故）归咎于……）"]]),
(4,[[[("Later analysis","后来的分析"),("called the mechanism flutter;","把这一机理称为颤振；")],
     "（call A B：把 A 称为 B）"],
    [[("in February 1991","1991年2月，"),("two engineers","两位工程师"),("**asserted** in a physics journal","在一份物理学期刊上**断言**(asserted)，"),("that textbooks had **erred**.","教科书**说错了**(erred)。")],
     "（that…：宾语从句，作 asserted 的宾语；\nhad erred：过去完成时）"]]),
(5,[[[("The panel","该委员会"),("urged","力主进行"),("**wind-tunnel** tests,","**风洞**(wind-tunnel)试验，")]],
    [[("and trials on","而用"),("**scaled-down**","**按比例缩小的**(scaled-down)"),("**replicas**","**模型**(replicas)做试验"),("**gradually**","也**逐渐**(gradually)"),("became","成为"),("**customary** for suspension bridges.","悬索桥的**惯例**(customary)。")],
     "（trials on…：用……做的试验；\nbecome customary：成为惯例）"]]),
(5,[[[("A **sturdier**","一座**更坚固的**(sturdier)"),("**replacement**","**替代**(replacement)桥"),("opened in October 1950.","于1950年10月通车。")]]]),
(5,[[[("Gertie's fall","格蒂的倒塌"),("may still **instruct** engineers,","或许至今仍能给工程师以**教益**(instruct)，"),("if read **accurately**:","只要解读得**准确**(accurately)：")],
     "（if read accurately：省略形式，= if it is read accurately）"],
    [[("the wind","风"),("never kept time with the bridge,","从未合着大桥的节拍，"),("the bridge's","是大桥"),("own","自身的"),("motion","运动"),("turned","让"),("a sustained","持续不断的"),("wind","风"),("destructive.","变得具有破坏力。")],
     "（keep time with：合着……的节拍；\nturn A＋形容词：使 A 变得……）\n"
     "（简述：1940年11月7日，一股持续的大风让塔科马海峡大桥扭动起来，振荡越来越剧烈，主跨断裂坠入水中，无人丧生。\n"
     "这座悬索桥当年7月才通车，桥身纤细、省钱却不够刚硬，微风就能让它起伏，人称舞动的格蒂。\n"
     "教科书常用共振来解释，但那天的风吹得平稳，并没有合着大桥的节拍涌动。\n"
     "真正的机理是扭动改变气流、气流又加强扭动的反馈回路，后来称为颤振，1991年两位工程师指出教科书错了。\n"
     "此后风洞模型试验成为惯例，1950年更坚固的新桥通车。）"]]),
]
G={
 "S1 a sustained wind of about 40 miles an hour":"对齐不了：of about 40 miles an hour 是后置定语，修饰 wind，中文“时速约40英里的”必须提前",
 "S2 tilted from side to side":"对齐不了：from side to side 是方式状语，中文“左右”必须放到动词“倾侧”前",
 "S2 most of the main span":"对齐不了：most of… 是 of 结构，中文“主跨大部分”语序必须倒过来",
 "S4 students worldwide":"对齐不了：worldwide 后置修饰 students，中文“世界各地的”必须提前",
 "S5 span in the world at the time":"对齐不了：in the world at the time 是后置的地点、时间限定，中文“当时世界上”必须提到“第三长的”前面",
 "S6 Girders only eight feet deep stiffened the deck":"对齐不了：only eight feet deep 是后置定语，中文把 stiffened the deck 化成定语“加劲桥面的”、把 only eight feet deep 化成谓语“只有8英尺高”，整句结构倒过来",
 "S8 a periodic push that matches an object's natural frequency":"对齐不了：that matches… 是定语从句，修饰 push，中文“与物体固有频率相合的”必须提前",
 "S8 a child on a swing":"对齐不了：on a swing 是后置定语，修饰 child，中文“秋千上的”必须提前",
 "S10 did not pulse in time with the bridge":"对齐不了：in time with the bridge 是方式状语，中文“合着大桥的节拍”必须放到动词前",
 "S12 a feedback loop that kept tapping the wind for energy":"对齐不了：that kept tapping… 是定语从句，修饰 loop，中文“不断从风中汲取能量的”必须提前",
 "S14 called the mechanism flutter":"对齐不了：call A B 中文“把 A 称为 B”，语序必须变",
 "S14 asserted in a physics journal":"对齐不了：in a physics journal 是地点状语，中文“在一份物理学期刊上”必须放到动词前",
 "S15 customary for suspension bridges":"对齐不了：for suspension bridges 中文“悬索桥的”必须提到“惯例”前",
 "S17 never kept time with the bridge":"对齐不了：keep time with 是固定说法“合着……的节拍”，the bridge 夹在中间，拆开中文不通",
}
CONF={"合组":G}
CONF["非人声"]={
 "S13 1.920708–2.280042":"2026-11-05 逐 10 ms 实测（S13 w）：1941 的 /n/ 1.86 后衰减，1.87–1.96 静音（-58～-66 dB）；1.97–2.22 是 -42～-55 dB、重心 2.0–2.6 kHz、低频 -8～-28 dB 的吸气（1941 与 a 之间无标点）；2.23–2.27 -44～-58 dB 低频 0～-3 dB 的零碎声门声，2.27–2.28 回到 -56～-60 dB，2.2825 起 a 的 ɐ（-38→-2 dB）。原自动区间 2.0–2.27 两头留着吸气尾和声门声，把静音隔断，无标点停顿压不下去（0.28 s）；改成 1.920708–2.280042 整段（两头过零点），紧贴 ɐ 词头",
 "S17 7.24525–7.605667":"2026-11-05 逐 10 ms 实测（S17 w）：bridge 的 /dʒ/ 擦音 7.13–7.21（重心 4.3–5.3 kHz）衰减到 7.24 -55.5 dB；7.25–7.545 是 -41～-49 dB、重心 2.2–3.1 kHz、低频 -9～-26 dB 的吸气（bridge, 后停顿，A19）；7.55–7.595 -44～-50 dB 低频 0 dB 的零碎浊杂声，7.60–7.62 静音（-56～-65 dB）把它和 the 隔开，不是 ð 的一部分；7.625 起 ð。删 7.24525–7.605667（两头过零点），紧贴 /dʒ/ 衰减末端"}
CONF["停顿位置"]={
 "S12 airflow, / which @2.443":"2026-11-05 逐 2.5 ms 实测（S12 w）：airflow 的 oʊ 2.38–2.40（重心 440–660 Hz、周期 0.5）衰减到 2.405–2.45 最弱（-37～-40 dB、周期 0.2–0.4），2.455–2.50 电平回升、重心 440–630 Hz 是 which 的 /w/，2.505–2.55 ɪ（重心 1.0–2.0 kHz），2.555–2.58 /tʃ/ 闭塞，2.585–2.66 /ʃ/（重心 3.3–5.2 kHz）。程序原选 2.575 落在 which 的 /tʃ/ 闭塞里（会把 which 切开）；两词交界取最弱处的过零点 2.443375，按交界插入",
 "S17 bridge, / the @7.612":"2026-11-05 逐 10 ms 实测（S17 w）：bridge 的 /dʒ/ 到 7.24 衰减完，7.25–7.605 吸气和零碎杂声已写进非人声区间，7.60–7.62 静音，7.625 起 the 的 ð（重心 4.4 kHz）、7.655 起 ə，7.81 起 bridge's 的 /b/；7.612 正在 bridge 与 the 之间。对齐程序把 the 的开头算到 7.942（其实是 bridge's 的 ɹɪ），是对齐偏差"}
CONF["非人声"].update({'0.41–0.42s': {'配音指纹': 'ab5df9ef8e09', '依据': '2026-11-05 逐 5 ms 实测（dossier_53，配音指纹 e9029306192c）：标题 w 0.025–0.04：-57→-42→-30 dB 连续升高、低频占 -2～-3 dB，0.045 起 The 的 ð，是 ð 的浊音起始（词的一部分）'}, '1.17–1.19s': {'配音指纹': 'ab5df9ef8e09', '依据': '2026-11-05 逐 5 ms 实测（dossier_53，配音指纹 e9029306192c）：标题 w 0.79–0.805：Wind 的 /d/ 闭塞 0.75–0.785（-55～-66 dB）之后一下除阻（-34 dB、重心 2.5–3.3 kHz），0.82 起 That 的 ð，是 Wind 词尾 /d/ 的除阻（词的一部分）'}, '14.23–14.25s': {'配音指纹': 'ab5df9ef8e09', '依据': '2026-11-05 逐 5 ms 实测（dossier_53，配音指纹 e9029306192c）：S1 w 9.45–9.47：twisting. 的 ŋ 尾，9.40–9.50 -37～-57 dB、低频占 -1～-5 dB、重心 1.0–2.0 kHz，连续衰减到 9.51 -67 dB，是词尾 ŋ 的鼻音（词的一部分）'}, '15.73–15.76s': {'配音指纹': 'ab5df9ef8e09', '依据': '2026-11-05 逐 5 ms 实测（dossier_53，配音指纹 e9029306192c）：S2 w 0.47–0.495：deck 的 /k/ 闭塞 0.435–0.47（-63～-69 dB）后 0.475 除阻（-37 dB、低频 -19 dB、重心 3.0 kHz），0.50–0.56 是 tilted 的 /t/ 闭塞，是 deck 的 /k/ 除阻（词的一部分）'}, '19.65–19.66s': {'配音指纹': 'ab5df9ef8e09', '依据': '2026-11-05 逐 5 ms 实测（dossier_53，配音指纹 e9029306192c）：S2 w 4.385–4.40：oscillations 内部，ʃən 的 n 4.305–4.44（-33～-61 dB、低频 -1～-10 dB、重心 0.7–3 kHz）起伏衰减，4.445 起 /z/（重心 3.5–5.6 kHz），连续无静音，是 n→z 的过渡（词的一部分）'}, '19.99–20.00s': {'配音指纹': 'ab5df9ef8e09', '依据': '2026-11-05 逐 5 ms 实测（dossier_53，配音指纹 e9029306192c）：S2 w 4.94–4.955：吸气（已按非人声区间删到 4.940542）之后，-44～-53 dB、低频占 0～-1 dB，4.96 起 until 的 ʌ（-30→-12 dB），是 until 元音前的声门起音（词的一部分）'}, '23.93–24.01s': {'配音指纹': 'ab5df9ef8e09', '依据': '2026-11-05 逐 5 ms 实测（dossier_53，配音指纹 e9029306192c）：S2 w 8.875–8.96：句末 water. 的 ɚ，8.795–8.96 由 -18 dB 连续衰减到 -52 dB、低频 -4～-20 dB、重心 1.2–2.1 kHz（ɚ 的 F3 低），8.96 起 -65 dB 以下淡出，中间没有低谷，是词尾 ɚ 的气声收尾（词的一部分）'}, '28.61–28.63s': {'配音指纹': 'ab5df9ef8e09', '依据': '2026-11-05 逐 5 ms 实测（dossier_53，配音指纹 e9029306192c）：S4 w 1.635–1.66：spectacle 后的吸气已按非人声区间删到 1.62；1.62–1.66 -45～-59 dB、低频占 0～-4 dB，1.665 起电平升到 would 的 /w/（1.69 -11 dB），是 /w/ 的浊音预发声（词的一部分）'}, '41.30–41.40s': {'配音指纹': 'ab5df9ef8e09', '依据': '2026-11-05 逐 5 ms 实测（dossier_53，配音指纹 e9029306192c）：S5 w 9.265–9.365：句末 cables. 的 əl 9.185–9.31（-17～-45 dB、低频 -4～-14 dB、重心 0.7–1.9 kHz）起伏衰减，9.325–9.345 浊音过渡，9.35 起 /z/（重心 4–5.7 kHz），连续无低谷，是 l→z 的过渡（词的一部分）'}, '42.53–42.55s': {'配音指纹': 'ab5df9ef8e09', '依据': '2026-11-05 逐 10 ms 实测（dossier_53，配音指纹 ab5df9ef8e09）：S6 w 0.015–0.03：句首 Girders 之前，电平连续升高、低频占 -1～-4 dB，接着 /ɡ/ 浊音闭塞和除阻，是 /ɡ/ 的浊音预发声（词的一部分）'}, '45.58–45.63s': {'配音指纹': 'ab5df9ef8e09', '依据': '2026-11-05 逐 10 ms 实测（dossier_53，配音指纹 ab5df9ef8e09）：S6 w 3.095–3.15（按 stˈɪfənddd 重合成后）：deck, 后吸气已按非人声区间删到 3.090542；3.09–3.15 -43～-53 dB、低频占 0～-2 dB，3.16 起 making 的 /m/（-26→-8 dB），连续升起，是 /m/ 的浊音预发声（词的一部分）'}, '55.03–55.05s': {'配音指纹': 'ab5df9ef8e09', '依据': '2026-11-05 逐 5 ms 实测（dossier_53，配音指纹 e9029306192c）：S7 w 3.685–3.70：Galloping 的 ŋ 3.60–3.67 衰减到 3.68 -58 dB，3.685–3.695 -48～-52 dB、低频占 0 dB，3.705 /ɡ/ 除阻（-14 dB、重心 3.6 kHz），是 Gertie 的 /ɡ/ 浊音闭塞（词的一部分）'}, '64.07–64.16s': {'配音指纹': 'ab5df9ef8e09', '依据': '2026-11-05 逐 5 ms 实测（dossier_53，配音指纹 e9029306192c）：S8 w 7.18–7.27：frequency 的词尾 i，7.10–7.18 -22～-33 dB（低频 -1～-2 dB），7.19–7.26 -39～-54 dB、重心 2.5–3.5 kHz（i 的 F2 高）连续衰减，7.27–7.33 是 can 的 /k/ 闭塞，7.335 /k/ 除阻，是词尾 /i/ 的气声收尾（词的一部分）'}, '72.99–73.01s': {'配音指纹': 'ab5df9ef8e09', '依据': '2026-11-05 逐 5 ms 实测（dossier_53，配音指纹 e9029306192c）：S9 w 2.255–2.275：deceptive 的 ɛ 2.175–2.22 衰减，2.225–2.255 /p/ 闭塞（-56～-64 dB），2.26 /p/ 除阻（-29 dB、低频 -26 dB、重心 2.7 kHz），2.275–2.30 /t/ 闭塞，2.305 /t/ 除阻，是 deceptive 的 /p/ 除阻（词的一部分）'}, '85.83–85.85s': {'配音指纹': 'ab5df9ef8e09', '依据': '2026-11-05 逐 5 ms 实测（dossier_53，配音指纹 e9029306192c）：S12 w 2.445–2.465：airflow 与 which 的交界（停顿按交界插在 2.443375 过零点），之后 -28～-40 dB、低频占 -1～-3 dB、重心 0.4–0.8 kHz 连续浊音升到 2.515 -8 dB，是 which 的 /w/（词的一部分）'}, '87.86–87.92s': {'词尾': 't', '实测': {'最响dB': -31.7, '重心Hz': 3429, '周期': 0.22, '低频dB': -11.6}, '配音指纹': 'ab5df9ef8e09', '依据': '2026-11-05 逐 5 ms 实测（dossier_53，配音指纹 e9029306192c）：S12 w 4.475–4.535：twist: 的 /s/ 4.395–4.44（重心 5.1–5.9 kHz），4.455–4.47 /t/ 闭塞（-56～-64 dB），4.475 /t/ 除阻、4.48–4.53 送气（-31～-52 dB、低频 -13～-26 dB、重心 2.0–3.8 kHz）衰减到 -61 dB，是 twist 的 /t/ 除阻（词的一部分，A21）'}, '89.30–89.31s': {'配音指纹': 'ab5df9ef8e09', '依据': '2026-11-05 逐 5 ms 实测（dossier_53，配音指纹 e9029306192c）：S12 w 6.015–6.03：loop 的 uː 5.935–6.005 衰减（低频 -1～-2 dB），6.015–6.03 -50～-54 dB 浊音进 /p/ 闭塞，6.035–6.06 /p/ 除阻（重心 2.3–4.7 kHz），6.065 起 that 的 ð，是 loop 的一部分'}, '108.78–108.88s': {'配音指纹': 'ab5df9ef8e09', '依据': '2026-11-05 逐 5 ms 实测（dossier_53，配音指纹 e9029306192c）：S14 w 9.22–9.32：句末 erred. 的 ɜ 9.14–9.315（-17～-51 dB、低频 -2～-10 dB、重心 0.8–2.3 kHz）衰减，9.32–9.33 /d/ 闭塞（-57 dB），9.335 /d/ 除阻（-27 dB、低频 -18 dB），是 erred 的 ɜ 与 /d/（词的一部分）'}, '108.86–108.88s': {'配音指纹': 'ab5df9ef8e09', '依据': '2026-11-05 逐 5 ms 实测（dossier_53，配音指纹 e9029306192c）：S14 w 9.22–9.32：句末 erred. 的 ɜ 9.14–9.315（-17～-51 dB、低频 -2～-10 dB、重心 0.8–2.3 kHz）衰减，9.32–9.33 /d/ 闭塞（-57 dB），9.335 /d/ 除阻（-27 dB、低频 -18 dB），是 erred 的 ɜ 与 /d/（词的一部分）'}, '136.91–136.94s': {'配音指纹': 'ab5df9ef8e09', '依据': '2026-11-05 逐 5 ms 实测（dossier_53，配音指纹 e9029306192c）：S17 w 12.16–12.195：destructive 的 ʌ 12.08–12.12 衰减，12.125–12.155 /k/ 闭塞（-59～-67 dB），12.16–12.19 /k/ 除阻（-41～-54 dB、重心 1.7–2.6 kHz，软腭音），12.20–12.255 /t/ 闭塞，12.26 /t/ 除阻，是 kt 里 /k/ 的除阻（词的一部分）'}})
CONF["非人声"].update({
 "标题 1.6–1.78":"2026-11-05 逐 5 ms 实测（标题 w）：Time: 后停顿，1.56–1.60 -60～-67 dB 底噪，1.605–1.775 -51～-57 dB、低频 -7～-22 dB、重心 2.1–2.5 kHz 平稳的吸气，1.78 起回到 -58～-61 dB；两头外侧都 < -55 dB，删 1.6–1.78",
 "S2 4.555–4.940542":"2026-11-05 逐 10 ms 实测（S2 w）：oscillations 的 /z/ 4.45–4.54（重心 4.4–5.6 kHz）衰减，4.55 -62 dB 低谷；4.56–4.92 是 -46～-60 dB、重心 2.1–2.6 kHz、低频 -10～-30 dB 的吸气（oscillations 与 until 之间无标点）；原自动区间从 4.725 起，留着前半段吸气（成片 20.03 报孤立杂音）；起点提前到 4.555（外侧 -62 dB），终点照旧紧贴 until 的声门起音",
 "S15 5.21975–5.3975":"2026-11-05 逐 5 ms 实测（S15 w）：replicas 的 /z/ 5.14–5.19（重心 4.6–5.9 kHz）衰减到 5.215 -46 dB；5.22–5.34 是 -36～-53 dB、重心 2.0–4.7 kHz、低频 -10～-22 dB 的吸气（replicas 与 gradually 之间无标点）；5.345–5.39 -44～-52 dB 低频 0 dB 的浊杂声，后面 5.395–5.425 有 30 ms 静音（-57～-63 dB）才到 5.43 /ɡ/ 除阻，不连着词；删 5.21975（过零点，紧贴 /z/ 衰减末端）–5.3975（外侧 -57 dB）",
 "S17 5.925–5.97":"2026-11-05 逐 5 ms 实测（S17 w）：never 的 ɚ 5.865–5.915 连续衰减到 5.92 -58 dB；5.945–5.955 一下孤立爆破（-33 dB、低频 -22 dB、重心 3.2 kHz），前后都是 -56～-68 dB 静音，6.015 才是 kept 的 /k/ 除阻；never 以元音结尾，这一下不属于任何词；删 5.925–5.97（两头外侧 -57/-67 dB）"})
CONF["高亮"]={"S2 第2块":{"开始读":20.29,"配音指纹":"e9029306192c","依据":"2026-11-05 逐 5 ms 实测（S2 w，成片 = w + 15.33）：吸气已删到 4.940542，4.94–4.955 是声门起音（-44～-53 dB），4.96 起 until 的 ʌ（-30 dB）、4.975 -21 dB 持续升高；until 在 w 4.96 = 成片 20.29 开始读，现高亮 20.27 合格；甲法 20.06 落在被删掉的吸气上"}}
CONF["非人声"]["S6 2.8675–3.090542"]="2026-11-05 逐 10 ms 实测（S6 按 stˈɪfənddd 重合成后 w）：deck 的 /k/ 闭塞 2.74–2.79（-63～-66 dB），2.80–2.85 /k/ 除阻送气（重心 2.5–4.6 kHz），2.86–2.90 静音（-56～-64 dB）；2.91–3.08 是 -43～-49 dB、重心 2.1–2.8 kHz、低频 -8～-29 dB 的吸气（deck, 后停顿，A19）；3.09–3.15 低频占 0～-2 dB 是 making 的 /m/ 预发声，3.16 起 /m/。删 2.8675（外侧 -57/-64 dB）–3.090542（过零点，紧贴 /m/ 预发声），不碰 /k/ 除阻"
CONF["机器复听"]={"S2":{"配音指纹":"ab5df9ef8e09","依据":"2026-11-05 实测（S2 w）：main 配音音标 mˈeɪn，读音核对 0；/m/ 5.71–5.83（重心 0.45–0.7 kHz、周期 0.5–0.6），eɪ 5.84–6.08（重心 1.6–2.3 kHz），/n/ 6.09–6.15（重心 0.65–0.95 kHz、低频 -1 dB），6.17–6.26 是 span 的 /s/（重心 5.3–6.4 kHz、低频只占 -30～-51 dB，清音，不是 /z/），6.27–6.29 /p/ 闭塞；main 读全，small.en 把 main + span 的 /s/ 并听成 manes，parakeet 听对"},
 "S6":{"配音指纹":"ab5df9ef8e09","依据":"2026-11-05 实测（S6 w，按 stˈɪfənddd 重合成后）：girders 配音音标 ɡˈɜːdɚz，读音核对 0；0.015–0.075 /ɡ/ 浊音闭塞（低频 -1～-4 dB、重心 0.3–0.7 kHz），0.08 /ɡ/ 除阻（重心 2.7–3.1 kHz），接 ɜ；首音是硬音 /ɡ/，small.en 写成同音拼法 gerders（不是读错），parakeet 听成 girders；stiffened 两路都听对（/d/ 闭塞 2.32–2.35、除阻 2.36–2.37）"}}
CONF["删除段"]={'S7 raw 1.9750-2.3350': '2026-11-05 逐 10 ms 实测（S7 w）：heave 的 /v/ 1.85–1.96（重心 3.7–5.6 kHz）衰减，1.97–2.00 静音（-58～-61 dB）；2.01–2.23 是 -40～-53 dB、重心 1.9–2.4 kHz、低频 -13～-29 dB 的吸气（heave, 后自然停顿）；2.27–2.33 静音（-62～-69 dB），2.34 起 earning 的 ɜ；程序删掉的是这段自然停顿（静音+吸气+静音），两侧 -59.5/-55.7 dB，词的声音一点没碰', 'S13 raw 4.0350-4.0400': {'类型': '紧贴词头的非人声', '配音指纹': 'ab5df9ef8e09', '依据': "2026-11-05 逐 10 ms 实测（S13 w）：deck's 的 ɛ 3.95–4.01 衰减，4.02–4.03 /k/ 闭塞静音（-60～-63 dB），4.04 /k/ 除阻（-22 dB）；删掉的 5 ms 是闭塞里的静音（最响 -64 dB），后侧 -54.4 dB 就是 /k/ 除阻起点，除阻本身完整"}, 'S13 raw 4.3700-4.3750': {'类型': '紧贴词尾的非人声', '配音指纹': 'ab5df9ef8e09', '依据': '2026-11-05 逐 10 ms 实测（S13 w）：flexibility 的 ɛ 4.30–4.34 衰减，4.35–4.37 /k/ 闭塞（-53～-58 dB），4.38 /k/ 除阻；删掉的 5 ms 是闭塞里的静音（最响 -57.4 dB），前侧 -54.2 dB 是 ɛ 衰减末端，除阻完整'}, 'S13 raw 5.0350-5.1000': {'类型': '紧贴词头的非人声', '配音指纹': 'ab5df9ef8e09', '依据': '2026-11-05 逐 10 ms 实测（S13 w）：flexibility 的词尾 i 4.95–5.00 衰减到 5.02 -60 dB，5.02–5.09 静音（-55～-70 dB），5.10 起 and（-28→-13 dB）；flexibility 与 and 之间无标点，删掉的 65 ms 是这段静音（最响 -52 dB），后侧 -54.1 dB 是 and 的起音，and 完整'}}
out={"no":"53","title_en":"The Wind That Kept No Time: The Fall of Galloping Gertie","title_zh":"不合拍的风：塔科马大桥的陨落","title_fx":{"hl":["Wind","Galloping Gertie"],"ghost":[]},"sentences":[],"核对确认":CONF,"结尾解说":"简述",
     "非人声区间":{"标题":[[1.6,1.78]],"S2":[[4.555,4.940542,"紧贴词头"]],"S15":[[2.65,2.83875,"紧贴词头"],[5.21975,5.3975,"紧贴词尾"]],"S6":[[2.8675,3.090542,"紧贴词头"],[5.93,6.251208,"紧贴词头"]],"S13":[[1.920708,2.280042,"紧贴词头"]],"S17":[[5.925,5.97],[7.24525,7.605667,"紧贴词尾"]]},
     "停顿插入点":{"S12":{"1":[2.443375,"交界"]}},
     "高亮按实际开口":True,"高亮开口门槛":40,
     "术语":{"Tacoma Narrows Bridge":"塔科马海峡大桥","Galloping Gertie":"舞动的格蒂","Gertie":"格蒂"}}
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 核对 import 生成并核对
生成并核对(S, out)
