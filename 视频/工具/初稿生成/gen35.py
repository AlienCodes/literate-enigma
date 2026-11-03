import json,re,glob,os
# 第35篇初稿（逐词对照）：S = [(段, [chunk, ...])]，chunk = ([(英文组, 中文组), ...], 可选 note)
# 2026-10-29 重点词中文沿用文章定稿（铁律），只按《翻译风格》调格式；短语型用法整体标（T22）；不用破折号（T36）。
S=[
(1,[[[("On 3 June 1952","1952年6月3日，"),("Rosario Mazzeo","罗萨里奥·马泽奥"),("**released** a Manx shearwater in Boston.","在波士顿**放飞了**(released)一只大西洋鹱。")],
     "（Manx shearwater：大西洋鹱，一种海鸟；\nin Boston：地点状语）"]]),
(1,[[[("It","它"),("came by **rail**","乘**火车**(rail)"),("and **airliner**","和**客机**(airliner)，"),("from its **burrow** on Skokholm,","从斯科克霍姆岛上的**洞穴**(burrow)来到这里——"),("an **isle** off Wales,","那是威尔士外海的一座**小岛**(isle)；")],
     "（come by rail and airliner：乘火车和客机来，by 表示交通方式；\nan isle off Wales：同位语，补充说明 Skokholm；off：在……外海）"],
    [[("and Mazzeo","而马泽奥"),("**posted a letter** **at once**.","**随即**(at once)**寄出了一封信**(posted a letter)。")],
     "（at once：立刻，马上）"]]),
(1,[[[("After a roughly","经过约"),("3,200-mile","三千二百英里的"),("**odyssey**","**远征**(odyssey)，"),("across","飞越"),("the **unbroken** Atlantic,","**连绵不断的**(unbroken)大西洋之后，")],
     "（After…：时间状语；\nacross the unbroken Atlantic：后置定语，修饰 odyssey）"],
    [[("the **feathered**","这位**披着羽毛的**(feathered)"),("**traveller**","**旅行者**(traveller)"),("was back on its **doorstep** twelve and a half days later.","十二天半后回到了自家**门口**(doorstep)。")],
     "（the feathered traveller：披着羽毛的旅行者，指这只鹱；\nbe back on its doorstep：回到自家门口）"]]),
(1,[[[("The letter","那封信"),("arrived **afterwards**.","是**随后**(afterwards)才到的。")],
     "（afterwards：之后，随后，\n这里指鸟回到洞巢之后）"]]),
(2,[[[("The first **hints** of a compass","关于这种罗盘的最初**迹象**(hints)，"),("were **celestial**.","是**和天体有关的**(celestial)。")],
     "（hints of a compass：关于鸟的罗盘的线索；\ncelestial：天上的，这里指太阳和星星）\n（科学家为了搞清楚这只鸟跨越3200英里不迷路的原因，发现最早的线索指向了“天体”——也就是说，这只鸟很可能是在靠白天看太阳、晚上看星星来导航认路的。）"]]),
(2,[[[("In the 1950s","20世纪50年代，"),("Kramer","克雷默"),("kept starlings","把椋鸟"),("**cooped**","**关进**(cooped)"),("in cages","笼子里，")],
     "（keep A cooped in…：把 A 关在……里；\ncooped：过去分词作宾语补足语）"],
    [[("and","再"),("moved the **apparent sun** with mirrors.","用镜子挪动**太阳的视位置**(apparent sun)。")],
     "（the apparent sun：太阳的视位置，\n即从地面看到的太阳位置）"]]),
(2,[[[("The **duped** birds","**受骗的**(duped)鸟儿"),("**swivelled** to match,","随之**转动**(swivelled)以与之匹配，")],
     "（swivel to match：转身与之对应；\nto match：不定式作结果状语）"],
    [[("**allowing for**","并且还会**考虑到**(allowing for)"),("the sun's","太阳"),("daily","每天运行的"),("**arc**.","**弧线**(arc)。")],
     "（allowing for…：现在分词短语作伴随状语；\nallow for：考虑到，顾及）"]]),
(2,[[[("In the 1960s","20世纪60年代，"),("Emlen","埃姆伦"),("**curtained off** stars in a planetarium's **vault**.","在天文馆的**穹顶**(vault)内，**用帘子遮挡住了**(curtained off)星星。")],
     "（curtain off：用帘子遮挡；\nin a planetarium's vault：地点状语）\n（科学家在天文馆里把星星遮住，\n就是想看看这只鸟在“瞎了”的情况下，还能不能认路。）"]]),
(2,[[[("His buntings","他的靛蓝彩鹀"),("**steered** by stars around the **pole-star**,","依靠**北极星**(pole-star)周围的星星**控制方向**(steered)，")],
     "（buntings：这里指靛蓝彩鹀；steer by…：依靠……辨向；\naround the pole-star：后置定语，修饰 stars）"],
    [[("the **axis** of the **nightly** **whirl**.","北极星正是星空**每夜**(nightly)都绕着**旋转**(whirl)的**轴心**(axis)。")],
     "（the axis of the nightly whirl：同位语，补充说明 the pole-star；\nwhirl：旋转，这里指星空整夜绕北极星转动）"]]),
(3,[[[("In 1972","1972年，"),("the Wiltschkos","维尔奇科夫妇"),("showed that","证明，")],
     "（the Wiltschkos：维尔奇科夫妇；\nthat 引导宾语从句）"],
    [[("**robins**","**知更鸟**(robins)"),("read","读取"),("Earth's","地球"),("**magnetic** field","**磁场**(magnetic)时，"),("by **inclination**,","看的是**倾角**(inclination)，"),("not **polarity**,","而不是**极性**(polarity)，")],
     "（by inclination：靠倾角，by 表示方式；\ninclination：倾角，磁力线与地面的夹角）"],
    [[("unlike","这一点和"),("a **sailor**'s","**水手**(sailor)的"),("**needle**.","罗盘**指针**(needle)不同。")],
     "（unlike…：介词短语，和……不同）"]]),
(3,[[[("In 1978","1978年，"),("Schulten","舒尔滕"),("proposed","提出了"),("a **light-triggered**","一种**由光触发**(light-triggered)、"),("reaction to **decode** the field.","用于**解码**(decode)地球磁场的反应。")],
     "（to decode the field：不定式作后置定语，修饰 reaction；\nthe field：指地球磁场）"]]),
(3,[[[("Proposed in 2000,","2000年被提出的"),("cryptochrome,","隐花色素，"),("a protein in the **retina**,","是**视网膜**(retina)中的一种蛋白质，")],
     "（Proposed in 2000：过去分词短语作状语；\na protein in the retina：同位语，\n补充说明 cryptochrome）"],
    [[("is now","如今它是"),("the **foremost**","**头号**(foremost)"),("**suspect**.","**嫌疑对象**(suspect)。")],
     "（the foremost suspect：头号嫌疑对象，\n指最可能负责感知磁场的分子）"]]),
(3,[[[("In 2021","2021年，"),("robin","知更鸟的"),("cryptochrome","隐花色素"),("proved more **finely** **tuned** in the laboratory","在实验室里被证明**调校**(tuned)得更**精细**(finely)，"),("than that of chickens or **pigeons**.","胜过鸡和**鸽子**(pigeons)的。")],
     "（proved more finely tuned…than…：比较结构，\n证明比……调校得更精细；\nthat of chickens or pigeons：that 指 cryptochrome）"]]),
(3,[[[("Proof in a living bird","在活鸟身上的证据，"),("is **awaited**.","仍**有待**(awaited)获取。")],
     "（in a living bird：后置定语，修饰 proof；\nbe awaited：被动，有待……）"]]),
(4,[[[("In 2014","2014年，"),("came","事情出现了"),("an **eerie**,","一个**诡异的**(eerie)、"),("**man-made**","**人为的**(man-made)"),("**twist**.","**转折**(twist)。")],
     "（In 2014 came…：倒装句，\n主语是 an eerie, man-made twist）"]]),
(4,[[[("At Oldenburg University,","在奥尔登堡大学，"),("robins in campus **huts**","校园**小木屋**(huts)里的知更鸟"),("lost","失去了"),("that **sense**.","这种**感知/感官**(sense)。")],
     "（in campus huts：后置定语，修饰 robins；\nthat sense：指读取磁场的能力）"]]),
(4,[[[("In huts **clad in** grounded aluminium,","在**覆有**(clad in)接地铝板**的**(clad in)小屋里，")],
     "（clad in 覆盖着……的：\n指建筑物或物体表面用某种材料覆盖或作饰面；\ngrounded：接地的）"],
    [[("they","它们"),("**reclaimed**","**找回了**(reclaimed)"),("their **bearings**.","它们的**方向**(bearings)。")],
     "（reclaim one's bearings：找回方向感；\nbearings：方位，方向感）"]]),
(4,[[[("Removing the grounding,","无论是拆掉接地，"),("or **piping** radio noise **in**,","还是**灌入**(piping in)无线电噪声，")],
     "（Removing…, or piping…：两个动名词短语作主语；\npipe in：用管道输入，这里指把噪声输进屋里）"],
    [[("**bewildered** them again in double-blind tests.","在双盲实验中都再次让它们**不知所措**(bewildered)。")],
     "（bewilder：使……困惑，使……不知所措；\nin double-blind tests：在双盲实验中）"]]),
(4,[[[("The **interference**,","这种**干扰**(interference)"),("a **murmur** from everyday **appliances**,","只是日常**电器**(appliances)发出的一阵电磁**低语**(murmur)，")],
     "（a murmur from everyday appliances：同位语，补充说明 interference；\nmurmur：低语，这里比喻微弱的电磁噪声）"],
    [[("sat far below","强度远低于"),("WHO","世卫组织的"),("**safety limits**.","**安全限值**(safety limits)。")],
     "（sit far below…：远低于……；\nWHO：世界卫生组织）"]]),
(5,[[[("How a **wanderer** knows where it is","一位**漫游者**(wanderer)如何知道自己身在何处，"),("remains **unanswered**.","至今仍**没有答案**(unanswered)。")],
     "（How a wanderer knows…：主语从句；\nwhere it is：宾语从句，作 knows 的宾语）\n（这只鸟到底是怎么在大脑里\n算出自己在地球上的确切位置的？\n科学家至今也没完全搞懂。）"]]),
(5,[[[("The compass","罗盘的"),("code","密码"),("is partly **cracked**,","已**破解了**(cracked)一部分，")],
     "（is partly cracked：被动，已被部分破解）"],
    [[("but","但"),("the **atlas** that steered the shearwater","指引那只大西洋鹱的那张**地图**(atlas)，"),("has yet to be read.","还没有人读懂。")],
     "（that steered the shearwater：定语从句，修饰 atlas；\nhas yet to do：“尚未……” / “还有待……”\n（表示某件事到现在为止还没发生，或者还没做完））\n"
     "（简述：1952年6月3日，马泽奥在波士顿放飞了一只来自威尔士外海斯科克霍姆岛的大西洋鹱，\n"
     "它飞越约三千二百英里的大西洋，十二天半后回到洞巢，比他随即寄出的信还早。\n"
     "20世纪50年代，克雷默用镜子挪动太阳的视位置，椋鸟随之转身；\n"
     "20世纪60年代，埃姆伦在天文馆遮住星星，发现靛蓝彩鹀依靠北极星周围的星星辨向。\n"
     "1972年，维尔奇科夫妇证明知更鸟读取磁场看的是倾角而不是极性；\n"
     "1978年舒尔滕提出由光触发的化学反应，2000年视网膜中的隐花色素被提出，如今是头号嫌疑对象，\n"
     "但在活鸟身上的证据仍有待取得。2014年，奥尔登堡大学发现，日常电器发出的微弱电磁干扰\n"
     "会让知更鸟失去方向感，接地铝板屏蔽后它们又找回了方向感。\n"
     "鸟如何知道自己身在何处，至今仍没有答案。）"]]),
]
CONF={"合组":{
 "S1 released a Manx shearwater in Boston":"对齐不了：in Boston 是地点状语，中文“在波士顿放飞了一只大西洋鹱”地点必须放到动词前；Manx shearwater 是一个鸟名“大西洋鹱”",
 "S2 posted a letter at once":"对齐不了：at once 是时间状语，中文“随即寄出了一封信”，“随即”必须放到动词前（用户 2026-11-03 定的译法）",
 "S2 from its burrow on Skokholm":"对齐不了：on Skokholm 是后置定语，修饰 burrow，中文“从斯科克霍姆岛上的洞穴来到这里”定语必须提前；came 的“来到这里”放在最后（用户 2026-11-03 定的译法）",
 "S3 was back on its doorstep twelve and a half days later":"对齐不了：twelve and a half days later 是时间状语，中文“十二天半后回到了自家门口”，时间必须放到动词前",
 "S6 kept starlings":"对齐不了：keep A cooped in B 中文是“把”字句“把 A 关进 B”，kept 不单独译，化进“把”和“关进”",
 "S6 moved the apparent sun with mirrors":"对齐不了：with mirrors 是方式状语，中文“用镜子挪动太阳的视位置”必须放到动词前；the apparent sun 中文“太阳的视位置”是一个词组",
 "S8 curtained off stars in a planetarium's vault":"对齐不了：in a planetarium's vault 是地点状语，中文“在天文馆的穹顶内，用帘子遮挡住了星星”地点必须放到动词前（用户 2026-11-03 定的译法）",
 "S9 steered by stars around the pole-star":"对齐不了：steer by A 中文“依靠 A 控制方向”，动词“控制方向”必须放到最后（用户 2026-11-03 定的译法）；around the pole-star 是后置定语，修饰 stars，中文“北极星周围的星星”必须提前",
 "S11 reaction to decode the field":"对齐不了：to decode the field 是不定式作后置定语，修饰 reaction，中文“用于解码地球磁场的反应”定语必须提前，“反应”放最后（用户 2026-11-03 定的译法）",
 "S13 proved more finely tuned in the laboratory":"对齐不了：in the laboratory 是地点状语，中文“在实验室里被证明……”必须放到动词前；more finely tuned 中文“调校得更精细”，程度补语放到动词后",
 "S14 Proof in a living bird":"对齐不了：in a living bird 是后置定语，修饰 proof，中文“在活鸟身上的证据”定语必须提前",
 "S16 robins in campus huts":"对齐不了：in campus huts 是后置定语，修饰 robins，中文“校园小木屋里的知更鸟”定语必须提前",
 "S17 In huts clad in grounded aluminium":"对齐不了：clad in grounded aluminium 是后置定语，修饰 huts，中文“在覆有接地铝板的小屋里”定语必须提前（用户 2026-11-03 定的译法）",
 "S18 or piping radio noise in":"对齐不了：pipe A in 中文“还是灌入 A”（用户 2026-11-03 定的译法），in 和 piping 合成一个动作，必须放在 A 前面",
 "S18 bewildered them again in double-blind tests":"对齐不了：in double-blind tests 是状语，中文“在双盲实验中都再次让它们不知所措”状语必须放到动词前（用户 2026-11-03 选的语序）",
 "S19 sat far below":"对齐不了：sit far below 是固定说法“远低于”，sat 不单独译；中文补出主语“强度”",
 "S21 the atlas that steered the shearwater":"对齐不了：that steered the shearwater 是定语从句，修饰 atlas，中文“指引那只大西洋鹱的那张地图”从句必须提前"},
"已告诉用户被去掉的重点词":"2026-10-29 已在会话中把 protein（与16 proteins 撞词，用户 2026-10-17 定留在16，35 改回普通词）原样告诉用户"}
CONF["停顿位置"]={"S12 retina, / is @3.995":"2026-10-29 逐段看声音实测（S12 w）：retina 的 ə 在 3.96 收尾（-24 dB），3.97 -31、3.98 -44、3.99 -57 dB，3.995 是两词之间最低处；4.01 起是吸气（-42～-46 dB、重心 2–3.4 kHz、低频 -8～-25 dB，已写进非人声区间 [4.0, 4.2275] 删掉），4.245 起 is 的声门起音；插在 retina 收尾后的静音里，不切词（A42）",
 "S15 eerie, / man-made @2.025":"2026-10-29 逐段看声音实测（S15 w）：eerie 的 i 在 1.995 收尾（-37 dB），2.005 -50、2.025 -61 dB 是两词之间最低处；2.035 起是吸气（-49～-57 dB、重心 1.9–2.4 kHz，已写进非人声区间 [2.04, 2.21] 删掉），2.235 起 man-made 的 /m/（-24 dB、重心 654 Hz）；插在最低处，不切词（A42）"}
# 非人声区间新加（2026-10-29 逐 10 ms 实测）：S3 [8.935,9.025] doorstep 的 /p/ 除阻 8.9175（-42 dB、重心 2.9 kHz）保留，之后 8.93–9.02 平稳 -51～-55 dB、重心 1.8–2.4 kHz、低频 -3～-16 dB、周期 0.1–0.2 的气声，9.03 起降到 -60 dB 以下，twelve 9.14 起；
#  （S3 doorstep 后 8.93–9.02 不切：紧接 /p/ 除阻、中间没有 -55 dB 的缝，是 /p/ 的送气尾）S6 [1.2525,1.34] fifties 的 /z/ 在 1.2375 结束（重心 3.8 kHz），1.2475–1.33 -53～-57 dB、重心 2–3.3 kHz 的气声，1.34 起 -58 dB 以下，kept 1.547 起；S8 [1.325,1.655] sixties 的 /z/ 在 1.325 结束（重心 5.3 kHz），1.335–1.53 -46～-55 dB、重心 2–2.8 kHz、低频 -8～-22 dB 的吸气，1.535–1.655 -52～-68 dB 的残余气声（重心 2.8–5 kHz），Emlen 1.665 起；
#  S12 [4.0,4.2275]、S15 [2.04,2.21] 见 停顿位置；S19 [3.4875,3.69] appliances 的 /z/ 在 3.4575 结束（重心 4.9 kHz），3.4675–3.68 -41～-53 dB、重心 2.4–3.4 kHz、低频 -7～-24 dB 的吸气，3.70 -52 dB 低频 -2 dB 起是 sat 前的起音，保留；S21 [2.198,2.245] the 收尾后 2.20–2.25 -53～-62 dB 里 2.21 一下 -43 dB、重心 5.8 kHz、低频 -28 dB 的咔声，atlas 2.26 起
CONF["非人声"]={"5.62–5.63s": {"配音指纹": "88dfc3dbe8d5", "依据": "2026-10-29 35 逐 10 ms 看实际声音：S1 w 2.68–2.78：fifty-two 收尾后 -51～-63 dB 的低处，低频 -1～-5 dB 占优（浊音），w 2.79 起 -35 dB、重心 889 Hz 是 Rosario 的 /ɹ/，属于 Rosario 起音前的浊音", "实测": {"最响dB": -50.4, "重心Hz": 2344, "周期": 0.0, "低频dB": -0.5}}, "14.16–14.20s": {"配音指纹": "88dfc3dbe8d5", "依据": "2026-10-29 35 逐 10 ms 看实际声音：S2 w 4.04–4.08：前面的吸气删到 4.043792（低频转为占优之前的过零点），4.045–4.075 低频 -0.6～-1.6 dB、周期 0.3–0.4 的浊音，4.09 -33、4.10 -13 dB 是 an 的元音，属于 an 的起音", "实测": {"最响dB": -43.7, "重心Hz": 3479, "周期": 0.42, "低频dB": -0.5}}, "16.52–16.55s": {"配音指纹": "88dfc3dbe8d5", "依据": "2026-10-29 35 逐 10 ms 看实际声音：S2 w 6.555–6.595：Mazzeo 的 o 收尾后 -52～-56 dB、低频 -1～-2 dB 的浊音闭塞，6.605 -19 dB、重心 2.2 kHz 是 posted 的 /p/ 除阻，属于 posted 的 /p/ 闭塞", "实测": {"最响dB": -51.3, "重心Hz": 2748, "周期": 0.37, "低频dB": -0.4}}, "27.89–27.97s": {"配音指纹": "88dfc3dbe8d5", "依据": "2026-10-29 35 逐 10 ms 看实际声音：S3 w 8.915–9.02：doorstep 的 /p/ 除阻 8.9175（-42 dB、重心 2.9 kHz），紧接 -51～-55 dB、重心 1.8–2.4 kHz 的送气尾，中间没有 -55 dB 的缝（试切 [8.935, 9.025] 外侧不够安静被出片程序拦下），属于 doorstep 的 /p/", "实测": {"最响dB": -44.4, "重心Hz": 2109, "周期": 0.09, "低频dB": -6.7}}, "40.09–40.10s": {"配音指纹": "88dfc3dbe8d5", "依据": "2026-10-29 35 逐 10 ms 看实际声音：S6 w 3.175–3.245：cooped 的 /p/ 闭塞（-49～-68 dB），3.215 一帧 -52 dB 在闭塞里，3.255 -22 dB、重心 3.5 kHz 是 /p/ 除阻，属于 cooped", "实测": {"最响dB": -35.5, "重心Hz": 2882, "周期": 0.0, "低频dB": -23.8}}, "48.73–48.79s": {"词尾": "k", "配音指纹": "88dfc3dbe8d5", "依据": "2026-10-29 35 逐 10 ms 看实际声音：S7 w 4.18–4.23：arc. 的 /k/ 除阻（-38～-47 dB、重心 3–4 kHz），之前 4.09–4.17 是 -54～-70 dB 的闭塞，属于 arc", "实测": {"最响dB": -31.0, "重心Hz": 3686, "周期": 0.2, "低频dB": -15.6}}, "54.28–54.33s": {"配音指纹": "88dfc3dbe8d5", "依据": "2026-10-29 35 逐 10 ms 看实际声音：S8 w 4.68–4.71：vault. 的 /t/ 除阻（-31～-44 dB、重心 2.2–3.7 kHz），之前 4.60–4.67 是 -52～-66 dB 的闭塞，属于 vault", "实测": {"最响dB": -30.9, "重心Hz": 3369, "周期": 0.34, "低频dB": -12.4}}, "78.03–78.05s": {"配音指纹": "88dfc3dbe8d5", "依据": "2026-10-29 35 逐 10 ms 看实际声音：S11 w 5.36–5.49：field. 的 /d/ 收尾（5.43–5.44 低频 -1～-2 dB 浊音、5.47 -27 dB 重心 2.5 kHz 除阻），属于 field", "实测": {"最响dB": -39.7, "重心Hz": 2324, "周期": 0.35, "低频dB": -2.1}}, "84.04–84.06s": {"配音指纹": "88dfc3dbe8d5", "依据": "2026-10-29 35 逐 10 ms 看实际声音：S12 w 4.225–4.255：前面吸气已删到 4.2275，4.245 -48 dB、低频 -0 dB、周期 0.48 的声门起音，4.265 起 -29 dB 是 is 的元音，属于 is 的起音", "实测": {"最响dB": -48.3, "重心Hz": 2491, "周期": 0.37, "低频dB": -0.2}}, "86.00–86.06s": {"配音指纹": "88dfc3dbe8d5", "依据": "2026-10-29 35 逐 10 ms 看实际声音：S12 w 6.20–6.25：suspect. 的 /t/ 除阻（6.21 -32 dB、重心 3.1 kHz），之前 6.12–6.19 -53～-69 dB 闭塞，属于 suspect", "实测": {"最响dB": -31.1, "重心Hz": 3265, "周期": 0.32, "低频dB": -13.8}}, "89.78–89.80s": {"配音指纹": "88dfc3dbe8d5", "依据": "2026-10-29 35 逐 10 ms 看实际声音：S13 w 2.805–2.865：robin 的 /n/ 收尾后 cryptochrome 的 /k/ 闭塞，2.825 一帧 -44 dB、重心 4 kHz，2.865 -14 dB 是 /k/ 除阻，属于 cryptochrome 的 /k/", "实测": {"最响dB": -41.1, "重心Hz": 3943, "周期": 0.0, "低频dB": -16.0}}, "113.62–113.76s": {"配音指纹": "88dfc3dbe8d5", "依据": "2026-10-29 35 逐 10 ms 看实际声音：S17 w 2.665–2.705：they 的 /ð/ 摩擦起音（2.665 -37、2.675 -29、2.685 -21 dB，重心 3.1–5.2 kHz），2.705 -5 dB 周期 0.59 是元音，属于 they", "实测": {"最响dB": -35.7, "重心Hz": 2090, "周期": 0.21, "低频dB": -4.1}}, "112.28–112.30s": {"配音指纹": "88dfc3dbe8d5", "依据": "2026-10-29 35 逐 10 ms 看实际声音：S17 w 3.93–4.12：bearings 的 /ŋ/（-20～-53 dB、低频 -1～-6 dB、周期 0.2–0.46），4.15 起是 /z/（重心 5.1–5.8 kHz、低频 -48～-69 dB），属于 bearings", "实测": {"最响dB": -30.0, "重心Hz": 3687, "周期": 0.0, "低频dB": -1.3}}, "133.48–133.58s": {"配音指纹": "88dfc3dbe8d5", "依据": "2026-10-29 35 逐 10 ms 看实际声音：S20 w 2.69–2.87：unanswered 的 ɚ 收尾到 /d/ 浊音闭塞（-37～-51 dB、低频 -1～-10 dB、重心 0.9–2.7 kHz），2.89 -33 dB 是 /d/ 除阻，属于 unanswered", "实测": {"最响dB": -39.4, "重心Hz": 2017, "周期": 0.24, "低频dB": -3.8}}, "131.99–132.00s": {"配音指纹": "88dfc3dbe8d5", "依据": "2026-10-29 35 逐 10 ms 看实际声音：S20 w 1.275–1.29：knows 的 /z/ 在 1.255 结束，1.285 -30 dB、重心 788 Hz、低频 -1 dB 是 where 的 /w/ 浊音起音，属于 where", "实测": {"最响dB": -30.1, "重心Hz": 1008, "周期": 0.0, "低频dB": -1.8}}, "133.54–133.56s": {"配音指纹": "88dfc3dbe8d5", "依据": "2026-10-29 35 逐 10 ms 看实际声音：S20 w 2.835–2.85：unanswered 的 /d/ 浊音闭塞中段（-41～-45 dB、低频 -1～-2 dB），属于 unanswered", "实测": {"最响dB": -40.1, "重心Hz": 1001, "周期": 0.0, "低频dB": -1.4}}, "133.56–133.58s": {"配音指纹": "88dfc3dbe8d5", "依据": "2026-10-29 35 逐 10 ms 看实际声音：S20 w 2.855–2.87：unanswered 的 /d/ 浊音闭塞末段（-44～-51 dB、低频 -2 dB），属于 unanswered", "实测": {"最响dB": -46.7, "重心Hz": 1731, "周期": 0.0, "低频dB": -1.5}}, "133.59–133.62s": {"配音指纹": "88dfc3dbe8d5", "依据": "2026-10-29 35 逐 10 ms 看实际声音：S20 w 2.885–2.915：unanswered. 的 /d/ 除阻（2.89 -33 dB、重心 2.1 kHz、低频 -27 dB），之后连续衰减到 -88 dB，属于 unanswered", "实测": {"最响dB": -32.5, "重心Hz": 1935, "周期": 0.11, "低频dB": -12.2}}, "136.67–136.70s": {"配音指纹": "88dfc3dbe8d5", "依据": "2026-10-29 35 逐 10 ms 看实际声音：S21 w 2.065–2.095：cracked 的 /k/（模型 k 2.073），-37 dB、重心 1.6 kHz，之后 2.1425 起 /t/ 除阻，属于 cracked", "实测": {"最响dB": -36.7, "重心Hz": 1640, "周期": 0.18, "低频dB": -5.8}}}
CONF["停顿位置"]["S21 cracked, / but @2.257"]="2026-10-29 逐段看声音实测（S21 w）：cracked 的 /t/ 除阻 2.1425–2.1675（-30～-45 dB、重心 2.7–4.2 kHz），2.175 降到 -51 dB，2.18–2.278 是 -58～-67 dB 的静音（结尾句接点也在这段里），2.2825 起 but 的 /b/；2.257 在静音里，不切词（A42）"
CONF["机器复听"]={"S2": {"配音指纹": "88dfc3dbe8d5", "依据": "2026-10-29 实测（配音指纹 88dfc3dbe8d5）：burrow 配音音标 bˈɜːɹoʊ，读音核对 0；parakeet 听成 borough：美音 burrow 与 borough 同音（Merriam-Webster burrow ˈbər-(ˌ)ō、borough ˈbər-(ˌ)ō），small.en 听对，不是读错"}, "S9": {"配音指纹": "88dfc3dbe8d5", "依据": "2026-10-29 实测（配音指纹 88dfc3dbe8d5）：buntings steered 同音连读：S9 w /ŋ/ 到 0.665，0.675–0.795 是 120 ms 连续咝音（-13～-22 dB、重心 4.1–6.1 kHz、低频 -10～-53 dB），复数 -s 和 steered 的 /s/ 连成一段（单个 /s/ 的约两倍长），0.81–0.865 /t/ 闭塞、0.87 除阻；两路都听成 bunting 是复数尾音被并进下一个 /s/，不是缺音（同 34 magnate's son）"}, "S16": {"配音指纹": "88dfc3dbe8d5", "依据": "2026-10-29 实测（配音指纹 88dfc3dbe8d5）：robins in campus：S16 w /z/ 2.52–2.55，in 的元音 2.56–2.64（约 80 ms 短元音、周期 0.45–0.61），/n/ 2.65–2.70（低频 -0.7～-1.1 dB 鼻音），2.72 /k/ 闭塞、2.73 除阻；parakeet 听对 in，只有 small.en 一路听成 and"}, "S17": {"配音指纹": "88dfc3dbe8d5", "依据": "2026-10-29 实测（配音指纹 88dfc3dbe8d5）：huts clad in grounded：S17 w clad 的 /d/ 连进 in，元音 0.96–1.08（周期 0.45–0.56），/n/ 1.08–1.11（低频 -0.5～-1.2 dB 鼻音），1.12 起 grounded 的 /g/；parakeet 听对 huts clad in，只有 small.en 一路连成 hutzklad and"}}
CONF.setdefault("对齐",{}).update({"S1-1 released a Manx shearwater in ": "in Boston 是地点状语，中文“在波士顿放飞了一只大西洋鹱”地点必须放到动词前", "S2-2 posted a letter at once.": "at once 是时间状语，中文“随即寄出一封信”，“随即”必须放到动词前", "S3-2 was back on its doorstep twelv": "twelve and a half days later 是时间状语，中文“十二天半后回到了自家门口”时间必须放到动词前", "S5-1 The first hints of a compass": "hints of a compass 是 of 结构，中文“最初的罗盘线索”，of 引出的“罗盘”必须提前", "S6-2 moved the apparent sun with mi": "with mirrors 是方式状语，中文“用镜子挪动太阳的视位置”必须放到动词前", "S8-1 curtained off stars in a plane": "in a planetarium's vault 是地点状语，中文“在天文馆的穹顶内，用帘子遮挡住了星星”地点必须放到动词前（用户 2026-11-03 定的译法）", "S9-1 steered by stars around the po": "steer by A 中文“依靠 A 控制方向”，动词放最后；around the pole-star 是后置定语，中文“北极星周围的星星”必须提前", "S9-2 the axis of the nightly whirl.": "the axis of A 是 of 结构，中文“星空每夜都绕着旋转的轴心”，of 引出的部分必须提前", "S12-1 a protein in the retina,": "in the retina 是后置定语，修饰 protein，中文“视网膜中的一种蛋白质”定语必须提前", "S13-1 proved more finely tuned in th": "in the laboratory 是地点状语，中文“在实验室里被证明调校得更精细”必须放到动词前", "S13-1 than that of chickens or pigeo": "that of A or B 是 of 结构，中文“鸡和鸽子的”，of 引出的部分必须提前", "S14-1 Proof in a living bird": "in a living bird 是后置定语，修饰 proof，中文“在活鸟身上的证据”定语必须提前", "S17-1 In huts clad in grounded alumi": "clad in grounded aluminium 是后置定语，修饰 huts，中文“在覆有接地铝板的小屋里”定语必须提前（用户 2026-11-03 定的译法）", "S18-1 or piping radio noise in,": "pipe A in 中文“还是灌入 A”（用户 2026-11-03 定的译法），in 和 piping 合成一个动作，必须放在 A 前面", "S19-1 a murmur from everyday applian": "from everyday appliances 是后置定语，修饰 murmur，中文“日常电器发出的一阵电磁低语”定语必须提前", "S20-1 How a wanderer knows where it ": "How a wanderer knows… 是主语从句，中文“一位漫游者如何知道自己身在何处”，疑问词 how 放到主语后面", "S21-2 the atlas that steered the she": "that steered the shearwater 是定语从句，修饰 atlas，中文“指引那只大西洋鹱的那张地图”从句必须提前", "S21-2 has yet to be read.": "被动 has yet to be read 中文“还没有人读懂”，被动换成主动说法，“还”“没有人”“读懂”拆开对不上英文"})
CONF.setdefault("短语",{}).update({"S2 by … rail": "不是搭配：by 是普通介词，表示交通方式（同 by car、by air），同时管 rail 和 airliner；rail 单独就是“铁路”，中文“坐火车”", "S2 isle … off": "不是搭配：off 引出方位（off Wales，在威尔士外海），isle 单独就是“小岛”", "S5 hints … of": "不是搭配：of 引出线索的内容（a compass），hints 单独就是“线索”", "S6 cooped … in": "不是搭配：速查表搭配是 coop up；这里 in cages 是地点（关在笼子里），in 是普通介词", "S6 cooped … with": "不是搭配：with mirrors 属于后面的 moved（用镜子挪动），和 cooped 无关", "S7 duped … for": "不是搭配：for 属于 allowing for（顾及），和 duped 无关", "S7 duped … to": "不是搭配：to 属于 swivelled to match（不定式），和 duped 无关", "S7 swivelled … for": "不是搭配：for 属于 allowing for（顾及），和 swivelled 无关", "S7 swivelled … to": "不是搭配：to match 是不定式作结果状语（随之转身），swivel 单独就是“转身”", "S9 axis … of": "不是搭配：of 引出轴心所属的旋转（the nightly whirl），axis 单独就是“轴心”，同速查表 the earth's axis", "S10 by … inclination": "不是搭配：by 是普通介词表示方式（靠倾角），inclination 单独就是“倾角”，同 by polarity", "S19 murmur … from": "不是搭配：from 引出来源（everyday appliances），murmur 单独就是“低语”"})
CONF.setdefault("方向",{}).update({"S3-1 after→经过约": "After a … odyssey 中文“经过约三千二百英里的远征”，“经过”表示经历完这段远征之后，与 after 同方向（远征在前、回家在后）"})
CONF.setdefault("数字",{}).update({"S3-1 3,200": "3,200-mile 中文按文章定稿写作“三千二百英里”，数值相同（配音读 three thousand two hundred）", "S6-1 1950": "the 1950s 中文“20世纪50年代”，同一个年代（配音读 nineteen fifties）", "S8-1 1960": "the 1960s 中文“20世纪60年代”，同一个年代（配音读 nineteen sixties）"})
CONF.setdefault("即",{}).update({"S2-2 即": "“随即”是现代汉语常用词（立刻、马上，对应 at once），不是文言的“即”"})
CONF.setdefault("对齐",{}).update({"S2-1 from its burrow on Skokholm,": "on Skokholm 是后置定语，修饰 burrow，中文“从斯科克霍姆岛上的洞穴来到这里”定语必须提前（用户 2026-11-03 定的译法）", "S11-1 reaction to decode the field.": "to decode the field 是不定式作后置定语，修饰 reaction，中文“用于解码地球磁场的反应”定语必须提前（用户 2026-11-03 定的译法）", "S18-2 bewildered them again in doubl": "in double-blind tests 是状语，中文“在双盲实验中都再次让它们不知所措”状语必须放到动词前（用户 2026-11-03 选的语序）"})
CONF.setdefault("短语",{}).update({"S9 steered … by": "不是搭配：用户 2026-11-03 只要 steered 标为“控制方向”；by stars 是方式状语（依靠星星），中文“依靠……”已译出", "S9 steered … of": "不是搭配：of 属于 the axis of the nightly whirl，和 steered 无关"})
CONF.setdefault("同词异译",{}).update({"clad in：的/覆有": "被隔开的同一个意思“覆有……的”两部分（T22/T23，用户 2026-11-03 原话“所对应中文意思为 覆有......的”），不是两种译法"})
CONF.setdefault("口述",{}).update({"S5-1 就是说": "用户 2026-11-03 原话要加的小字里就是“也就是说”（“发现最早的线索指向了“天体”——也就是说，……”），是用户本意，不是口述多出来的词"})
CONF.setdefault("是的",{}).update({"S5-1 是**和天体有关的**": "用户 2026-11-03 原话定的译文“关于这种罗盘的最初迹象，是和天体有关的”，celestial 对应“和天体有关的”，照用户原话"})
out={"no":"35","title_en":"The Bird That Beat the Letter Home","title_zh":"比信先到家的鸟","title_fx":{"hl":["Bird","Letter"],"ghost":[]},"sentences":[],"核对确认":CONF,"结尾解说":"简述",
     "说明放宽特批":{"S21":{"倍数":"整屏","依据":"用户 2026-10-25 看 25 简述截图：“以后以后一定要合理的安排，不要压缩成这个样子……这个地方特批一下”（用户同意记录：原话适用以后各篇，26 起沿用）"}},
     "非人声区间":{"S1":[[2.45,2.725]],"S2":[[3.755,4.043792,"紧贴词头"]],"S6":[[1.2525,1.34],[4.13,4.443708,"紧贴词头"]],"S8":[[1.325,1.655]],"S10":[[6.61,6.97]],"S11":[[1.45,1.645]],"S12":[[4.0,4.2275]],"S13":[[1.855,2.075],[6.225,6.585]],"S15":[[2.04,2.21]],"S18":[[3.39,3.685]],"S19":[[3.4875,3.69]],"S21":[[2.565,2.585]]},
     "allow_clash":["released","steered","suspect"],"换行变更已获同意":{"S11":"用户 2026-11-03 原话：“同意换行变”（问的是：S11 按用户新译文，reaction to decode the field 放一组，英文换行跟上一版不同，同意吗）","S2":"用户 2026-11-03 原话：“同意换行变”（问的是：S2 按用户新译文，on Skokholm 和 from its burrow 放一组，英文换行跟上一版不同，同意吗）"},"高亮按实际开口":True,"高亮开口门槛":40,
     "术语":{"Rosario Mazzeo":"罗萨里奥·马泽奥","Mazzeo":"马泽奥","Manx shearwater":"大西洋鹱","shearwater":"大西洋鹱","Boston":"波士顿","Skokholm":"斯科克霍姆","Wales":"威尔士","Atlantic":"大西洋","Kramer":"克雷默","Emlen":"埃姆伦","buntings":"靛蓝彩鹀","Wiltschkos":"维尔奇科夫妇","Schulten":"舒尔滕","cryptochrome":"隐花色素","Oldenburg University":"奥尔登堡大学","WHO":"世卫组织"}}
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 核对 import 生成并核对
生成并核对(S, out)
