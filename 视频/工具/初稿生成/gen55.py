import json,re,glob,os
# 第55篇初稿（逐词对照）：S = [(段, [chunk, ...])]，chunk = ([(英文组, 中文组), ...], 可选 note)
# 2026-11-05 重点词中文沿用文章定稿（铁律），只按《翻译风格》调格式；短语型用法整体标（T22）；不用破折号（T36）；形容词的“的”进粗体。
S=[
(1,[[[("Nearly 1,900 years after its **completion**, in about AD 125–128,","万神殿约于公元125至128年**竣工**(completion)，近1,900年后的今天，")],
     "（its completion：its 指 the Pantheon；\nin about AD 125–128：插入语，补充竣工的年代）"],
    [[("the Pantheon's **dome**","它的**穹顶**(dome)"),("still","依然"),("**crowns**","**高踞**(crowns)于"),("the **vast**","下方**宏大的**(vast)"),("**chamber** below.","**殿堂**(chamber)之上。")],
     "（crown：位于……顶部，高踞……之上；\nbelow：副词作后置定语，修饰 chamber）"]]),
(1,[[[("About 43 metres in **diameter**,","穹顶**直径**(diameter)约43米，"),("it remains","至今仍是"),("the world's","世界上"),("largest","最大的"),("unreinforced","无钢筋"),("concrete","混凝土"),("dome.","穹顶。")],
     "（About 43 metres in diameter：形容词短语作状语，说明穹顶的大小；\nunreinforced：没有用钢筋加固的）"]]),
(1,[[[("It is","它是"),("an **astonishing** **feat** of **architecture**,","**建筑**(architecture)史上**令人惊叹的**(astonishing)**壮举**(feat)，"),("and a **stubborn**","也是一道**久解不开的**(stubborn)"),("**puzzle**.","**谜题**(puzzle)。")],
     "（a feat of architecture：建筑上的壮举）"]]),
(2,[[[("Modern","现代"),("concrete","混凝土"),("is usually","通常"),("reinforced with **embedded** steel bars,","靠**嵌入**(embedded)其中的钢筋加固，")],
     "（be reinforced with…：用……加固）"],
    [[("which","而钢筋"),("are **prone** to","**容易**(prone)发生"),("**corrosion**.","**锈蚀**(corrosion)。")],
     "（which…：非限制性定语从句，修饰 steel bars；\nbe prone to…：容易……）"]]),
(2,[[[("As the steel **rusts**,","钢筋**生锈**(rusts)时"),("it **swells**","会**膨胀**(swells)，"),("and **fractures** the concrete around it,","把周围的混凝土**撑裂**(fractures)；")],
     "（As…：时间状语从句，当……时；\naround it：后置定语，修饰 concrete，it 指 the steel）"],
    [[("and many structures","许多建筑的"),("are designed for","设计"),("a **lifespan**","**使用寿命**(lifespan)"),("of around 50 years.","约为50年。")],
     "（be designed for…：按……设计）"]]),
(2,[[[("Roman concrete","罗马混凝土"),("is not stronger than its modern **counterpart**;","并不比现代的**同类材料**(counterpart)更坚固，")],
     "（its modern counterpart：现代的同类材料，即现代混凝土）"],
    [[("its **merit**","它的**长处**(merit)"),("lies in **durability**.","在于**耐久性**(durability)。")],
     "（lie in…：在于……）"]]),
(3,[[[("Yet","然而，"),("the ancient","这种古代"),("material","材料"),("seemed to have","似乎有个"),("a **shortcoming**.","**缺点**(shortcoming)。")]]]),
(3,[[[("It","它的内部"),("is **dotted** with","**散布**(dotted)着"),("white","白色的"),("**chunks** of lime,","石灰**小块**(chunks)，")],
     "（be dotted with…：散布着……，布满……）"],
    [[("known as","称为"),("lime","石灰"),("clasts.","团块。")],
     "（known as…：过去分词短语作后置定语，修饰 chunks）"]]),
(3,[[[("Experts long","长期以来，专家"),("**ascribed** these **lumps** **to**","**把**(ascribed to)这些**块状物**(lumps)**归因于**(ascribed to)"),("**sloppy** mixing","搅拌**马虎**(sloppy)"),("or **inferior** raw **ingredients**,","或原料**成分**(ingredients)**低劣**(inferior)。")],
     "（ascribe A to B：把 A 归因于 B）"],
    [[("a **defect** that, they assumed, a more **conscientious** builder would have avoided.","他们认为，换一个更**认真负责的**(conscientious)工匠，就不会出这种**瑕疵**(defect)。")],
     "（a defect that…：同位语，补充说明前面说的情况；\nthey assumed：插入语，他们认为；\nwould have avoided：虚拟语气，本可以避免）"]]),
(4,[[[("A study published in Science Advances in January 2023","2023年1月发表于《科学进展》（Science Advances）的一项研究"),("offered","提出了"),("a different **interpretation**.","不同的**解释**(interpretation)。")],
     "（published in…：过去分词短语作后置定语，\n修饰 study）"]]),
(4,[[[("The clasts, it suggested,","该研究认为，这些团块"),("were","是"),("a **by-product** of \"hot mixing\" with quicklime,","用生石灰“热混合”留下的**副产品**(by-product)；")],
     "（it suggested：插入语，it 指这项研究；\na by-product of…：……的副产品）"],
    [[("a **reactive** lime that heats up in water.","生石灰是一种遇水会发热、**活性强的**(reactive)石灰。")],
     "（a reactive lime…：同位语，补充说明 quicklime；\nthat heats up in water：定语从句，修饰 lime）"]]),
(4,[[[("When water","水"),("**seeps** into a crack,","**渗入**(seeps)裂缝时，")],
     "（When…：时间状语从句）"],
    [[("the clasts","团块"),("**dissolve**","会**溶解**(dissolve)，"),("and their **calcium**","其中的**钙**(calcium)"),("recrystallises as","重新结晶为"),("calcium carbonate,","碳酸钙，"),("**plugging** the gap.","**堵住**(plugging)缝隙。")],
     "（recrystallise as…：重新结晶为……；\nplugging the gap：现在分词短语作状语，表示结果）"]]),
(4,[[[("In tests,","试验中，"),("water","水"),("**ceased** to","**不再**(ceased)"),("**trickle**","**细细流过**(trickle)"),("through cracked","开裂的"),("hot-mixed","热混合"),("samples","样本，"),("within","只用了"),("weeks,","几周；")],
     "（cease to do：不再做……；\nwithin weeks：几周之内）"],
    [[("but","而"),("kept","水一直"),("flowing through samples without quicklime.","从不含生石灰的样本中流过。")],
     "（keep doing：一直做……；\nwithout quicklime：介词短语作后置定语，修饰 samples）"]]),
(5,[[[("The **implications**","这项发现的**意义**(implications)"),("**extend** beyond","**超出了**(extend)"),("**archaeology**.","**考古学**(archaeology)的范围。")],
     "（extend beyond…：超出……的范围）"]]),
(5,[[[("Cement **manufacture**","水泥**生产**(manufacture)"),("accounts for","约占"),("about 8 per cent of global carbon dioxide **emissions**,","全球二氧化碳**排放**(emissions)的8%，")],
     "（account for…：（在数量上）占……）"],
    [[("the think-tank Chatham House","智库查塔姆研究所（Chatham House）"),("reported in June 2018.","2018年6月报告称。")]]]),
(5,[[[("Concrete that mends its cracks","能自行修补裂缝的混凝土"),("could","可能"),("last longer,","更经久耐用，")],
     "（that mends its cracks：定语从句，修饰 Concrete）"],
    [[("making","从而使"),("**demolition**","**拆除**(demolition)"),("and rebuilding","与重建"),("rarer","减少，"),("and **trimming**","并**削减**(trimming)"),("emissions.","排放。")],
     "（making… and trimming…：两个现在分词短语作状语，表示结果；\nmake A rarer：使 A 更少见）"]]),
(5,[[[("The white","这些白色"),("lumps","块状物"),("once **scorned** as","曾被**轻视**(scorned)为"),("signs of **clumsy** workmanship","手艺**拙劣的**(clumsy)痕迹，")],
     "（once scorned as…：过去分词短语作后置定语，修饰 lumps；\nscorn A as B：把 A 轻视为 B）"],
    [[("have **prompted**","如今却**促使**(prompted)人们"),("a **rethink** of construction.","**重新思考**(rethink)建造之道。")],
     "（a rethink of…：对……的重新思考）\n"
     "（简述：万神殿穹顶建成近1,900年依然屹立，是世界上最大的无钢筋混凝土穹顶。\n"
     "现代混凝土里的钢筋会生锈膨胀、撑裂混凝土，许多建筑设计寿命约50年；\n"
     "罗马混凝土并不更坚固，长处在于耐久。它里面的白色石灰团块，\n"
     "过去被专家当作搅拌马虎或原料低劣的瑕疵。2023年《科学进展》的研究认为，\n"
     "团块是生石灰热混合的副产品：水渗入裂缝时团块溶解，钙重新结晶为碳酸钙，堵住缝隙。\n"
     "水泥生产约占全球二氧化碳排放的8%，能自行修补裂缝的混凝土可能减少拆建和排放，\n"
     "这些曾被轻视的团块因此促使人们重新思考建造之道。）"]]),
]
G={
 "S1 Nearly 1,900 years after its completion, in about AD 125–128":"对齐不了：after its completion 是时间状语，中文要先说“竣工”再说“近1,900年后”；in about AD 125–128 是插入语，中文“约于公元125至128年竣工”年代必须放到动词前，整组语序倒过来",
 "S4 reinforced with embedded steel bars":"对齐不了：be reinforced with… 中文“靠……加固”，“加固”必须放到“钢筋”后面；embedded 是前置定语，中文“嵌入其中的钢筋”",
 "S6 is not stronger than its modern counterpart":"对齐不了：not stronger than… 是比较句，中文“并不比……更坚固”，“更坚固”必须放到比较对象后面",
 "S9 a defect that, they assumed, a more conscientious builder would have avoided":"对齐不了：a defect that… 是同位语带定语从句，they assumed 是插入语，中文“他们认为，换一个更认真负责的工匠，就不会出这种瑕疵”整句语序倒过来",
 "S10 A study published in Science Advances in January 2023":"对齐不了：published in… 是过去分词短语作后置定语，修饰 study，中文“2023年1月发表于《科学进展》的一项研究”定语必须提前",
 "S11 The clasts, it suggested":"对齐不了：it suggested 是插入语，中文“该研究认为”必须放到句首",
 "S11 a by-product of \"hot mixing\" with quicklime":"对齐不了：a by-product of… 是 of 结构，中文“用生石灰“热混合”留下的副产品”定语必须提前",
 "S11 a reactive lime that heats up in water":"对齐不了：that heats up in water 是定语从句，修饰 lime，中文“遇水会发热、活性强的石灰”定语必须提前；同位语里补出主语“生石灰是”",
 "S12 calcium carbonate":"对齐不了：calcium carbonate 是化学名“碳酸钙”，一个词，不能拆",
 "S13 flowing through samples without quicklime":"对齐不了：without quicklime 是后置定语，修饰 samples，中文“从不含生石灰的样本中流过”，“流过”必须放到最后",
 "S15 about 8 per cent of global carbon dioxide emissions":"对齐不了：8 per cent of… 是 of 结构，中文“全球二氧化碳排放的8%”百分数必须放到后面",
 "S16 Concrete that mends its cracks":"对齐不了：that mends its cracks 是定语从句，修饰 Concrete，中文“能自行修补裂缝的混凝土”定语必须提前",
 "S16 last longer":"对齐不了：last longer 中文“更经久耐用”是一个说法，拆开不通",
 "S17 signs of clumsy workmanship":"对齐不了：signs of… 是 of 结构，中文“手艺拙劣的痕迹”，“痕迹”必须放到最后",
}
CONF={"合组":G,
"非人声":{"7.42–7.50s":{"配音指纹":"ed59953f5c3d","依据":"2026-11-05 逐 2.5 ms 实测（dossier_55，配音指纹 ed59953f5c3d）：S1 w 3.775–3.855：completion, 的 ən 尾，3.73 -28 dB 起逐渐衰减到 3.855 -56 dB，低频占 -3～-11 dB、重心 1.1–2.2 kHz，连续无低谷，是词尾 /n/ 的浊音衰减（词的一部分）"},"12.11–12.12s":{"配音指纹":"ed59953f5c3d","依据":"2026-11-05 逐 2.5 ms 实测（dossier_55，配音指纹 ed59953f5c3d）：S1 w 8.49–8.505：the 的 ə 8.445 -25 dB 起衰减（低频 -0.5～-3 dB 浊音），8.505 起 Pantheon's 的 /p/ 除阻（-11 dB、重心 3.5 kHz），中间连续无低谷，是 ə 进 /p/ 闭塞的浊音尾（词的一部分）"},"23.19–23.25s":{"配音指纹":"ed59953f5c3d","依据":"2026-11-05 逐 2.5 ms 实测（dossier_55，配音指纹 ed59953f5c3d）：S2 w 6.50–6.56：concrete 的 /t/ 之后、dome 的 /d/ 除阻（6.56 -29→-16 dB、重心 3.2 kHz）之前，6.505–6.555 -38～-44 dB、低频占 -1～-3 dB、重心 0.5–0.8 kHz，是 /d/ 的浊音预发声（词的一部分）"},"34.79–34.83s":{"配音指纹":"ed59953f5c3d","依据":"2026-11-05 逐 2.5 ms 实测（dossier_55，配音指纹 ed59953f5c3d）：S4 w 4.825–4.865：bars, 停顿之后、which 开口前，-46～-58 dB、低频占 -0.4～-5 dB，4.875 起 /w/（-33→-6 dB、重心 0.7–2 kHz），连续无低谷，是 /w/ 的浊音预发声（词的一部分）"},"46.38–46.48s":{"配音指纹":"ed59953f5c3d","依据":"2026-11-05 逐 2.5 ms 实测（dossier_55，配音指纹 ed59953f5c3d）：S5 w 8.92–9.02：years. 内部，ɚ 浊音 8.875–9.00（-30～-50 dB、低频 -3～-10 dB、重心 0.9–2 kHz）衰减，9.005 起 /z/ 擦音（重心 2.7→5 kHz、低频 -20～-46 dB），连续无低谷，是 ɚ 到词尾 /z/ 的过渡（词的一部分）"},"71.19–71.22s":{"配音指纹":"ed59953f5c3d","依据":"2026-11-05 逐 2.5 ms 实测（dossier_55，配音指纹 ed59953f5c3d）：S9 w 6.92–6.945：that, 停顿之后（6.875–6.915 -61～-71 dB 静音），6.92 起电平 -53→-28 dB 渐升、低频占 -1～-2 dB、重心 0.8–1.9 kHz，一路连到 they 的 /ð/（6.98 -15 dB），是 /ð/ 的浊音起始（词的一部分）"},"86.45–86.47s":{"配音指纹":"ed59953f5c3d","依据":"2026-11-05 逐 2.5 ms 实测（dossier_55，配音指纹 ed59953f5c3d）：S11 w 1.92–1.94：suggested, 停顿之后、were 开口前，-44～-56 dB、低频占 -0.3～-2.5 dB，1.945 起渐升到 1.97 -14 dB（重心 0.5–0.6 kHz），连续无低谷，是 /w/ 的浊音预发声（词的一部分）"},"94.94–95.00s":{"配音指纹":"ed59953f5c3d","依据":"2026-11-05 逐 2.5 ms 实测（dossier_55，配音指纹 ed59953f5c3d）：S12 w 1.81–1.865：crack, 的 /k/ 闭塞 1.77–1.805（-61～-71 dB）之后，1.81–1.86 -31～-50 dB、重心 3.3–4.5 kHz、低频 -10～-22 dB 的爆破送气，衰减到 1.87 -64 dB，是词尾 /k/ 的除阻（词的一部分）"},"96.06–96.07s":{"配音指纹":"ed59953f5c3d","依据":"2026-11-05 逐 2.5 ms 实测（dossier_55，配音指纹 ed59953f5c3d）：S12 w 2.855–2.87：clasts 的 /s/ 到 2.83（重心 5.4–6 kHz），2.85–2.865 -43～-57 dB、低频占 -1～-3 dB、重心 0.8–2.8 kHz，2.875 起 dissolve 的 /d/ 除阻（重心 2.8–4.2 kHz），是 /d/ 的浊音预发声（词的一部分）"},"103.71–103.73s":{"配音指纹":"ed59953f5c3d","依据":"2026-11-05 逐 2.5 ms 实测（dossier_55，配音指纹 ed59953f5c3d）：S13 w 0.875–0.895：tests, 停顿之后、water 开口前，-42～-51 dB 渐升、低频占 -1.4～-3 dB、重心 0.9–2.3 kHz，0.895 起 /w/（-27→-14 dB、重心 0.35–0.5 kHz），连续无低谷，是 /w/ 的浊音预发声（词的一部分）"},"105.65–105.67s":{"配音指纹":"ed59953f5c3d","依据":"2026-11-05 逐 2.5 ms 实测（dossier_55，配音指纹 ed59953f5c3d）：S13 w 2.815–2.835：cracked 内部（带时长模型 2.524–2.922），æ 2.77 -30 dB 之后 2.775–2.84 -41～-59 dB、低频占 -1～-4 dB 的浊音闭塞，2.85 起 /t/ 除阻（-21 dB、重心 2.7 kHz），是 /k/→/t/ 闭塞里的浊音尾（词的一部分）"},"108.17–108.19s":{"配音指纹":"ed59953f5c3d","依据":"2026-11-05 逐 2.5 ms 实测（dossier_55，配音指纹 ed59953f5c3d）：S13 w 5.31–5.33：weeks, 停顿之后、but 的 /b/ 除阻（5.345 -24 dB、重心 3.5 kHz）之前，-50～-58 dB、低频占 -0.3～-3.8 dB，连续无低谷，是 /b/ 的浊音预发声（词的一部分）"},"122.08–122.16s":{"配音指纹":"ed59953f5c3d","依据":"2026-11-05 逐 2.5 ms 实测（dossier_55，配音指纹 ed59953f5c3d）：S15 w 5.80–5.88：emissions, 的 ən 尾，5.755–5.795 -24～-28 dB（低频 -2～-3 dB）衰减成 5.80–5.875 -34～-45 dB、低频占 -1.4～-8 dB、重心 0.8–2.5 kHz 的浊音，是词尾 /nz/ 的浊音（词的一部分）"},"122.14–122.16s":{"配音指纹":"ed59953f5c3d","依据":"2026-11-05 逐 2.5 ms 实测（dossier_55，配音指纹 ed59953f5c3d）：S15 w 5.865–5.88：同上 emissions, 的 /nz/ 浊音尾（-36～-54 dB、低频占 -1.4～-5 dB），连续衰减（词的一部分）"},"122.17–122.18s":{"配音指纹":"ed59953f5c3d","依据":"2026-11-05 逐 2.5 ms 实测（dossier_55，配音指纹 ed59953f5c3d）：S15 w 5.89–5.905：emissions, 的 /z/ 浊音尾最后一下（-40～-43 dB、低频占 -2～-4 dB、重心 1.0–1.4 kHz），之后衰减到 -50 dB，是词的一部分"},"126.60–126.69s":{"配音指纹":"ed59953f5c3d","依据":"2026-11-05 逐 2.5 ms 实测（dossier_55，配音指纹 ed59953f5c3d）：S15 w 10.375–10.46：eighteen. 的 n 尾，10.33 -28 dB 起衰减到 10.505 -86 dB，低频占 -1.5～-10 dB、重心 0.9–2.5 kHz，连续无低谷，是词尾 /n/ 的浊音衰减（词的一部分）"},"135.81–135.82s":{"配音指纹":"ed59953f5c3d","依据":"2026-11-05 逐 2.5 ms 实测（dossier_55，配音指纹 ed59953f5c3d）：S17 w 0.03–0.045：句首 The 之前，0.025 -43 dB、0.03 -31.7 dB 低频占 -2～-3 dB 渐升，0.045 起 /ð/ 擦音（重心 3.9–4.5 kHz、-27→-16 dB），连续无低谷，是 /ð/ 的浊音起始（词的一部分）"},"137.52–137.53s":{"配音指纹":"ed59953f5c3d","依据":"2026-11-05 逐 2.5 ms 实测（dossier_55，配音指纹 ed59953f5c3d）：S17 w 1.745–1.76：scorned 内部（带时长模型 1.166–1.886），n 1.705 -35 dB（低频 -2.7 dB）之后 1.72–1.80 -48～-61 dB、低频占 -0.5～-4 dB 的浊音，是 /n/→/d/ 的浊音闭塞（词的一部分），1.985 起 as"},"139.57–139.59s":{"配音指纹":"ed59953f5c3d","依据":"2026-11-05 逐 2.5 ms 实测（dossier_55，配音指纹 ed59953f5c3d）：S17 w 3.80–3.815：workmanship 的 ɪ 3.755 -23 dB 衰减，3.795–3.815 -51～-55 dB、低频占 -1.7～-2.5 dB 的浊音，进 /p/ 闭塞（3.82 -66 dB），是 ɪ→/p/ 闭塞的浊音尾（词的一部分）"},"141.86–141.94s":{"配音指纹":"ed59953f5c3d","依据":"2026-11-05 逐 2.5 ms 实测（dossier_55，配音指纹 ed59953f5c3d）：S17 w 6.18–6.26：construction. 的 ən 尾，6.17–6.235 -30～-52 dB、低频占 -1.5～-6 dB、重心 0.7–2.2 kHz，衰减到 6.30 -115 dB，连续无低谷，是词尾 /n/ 的浊音衰减（词的一部分）"},"141.90–141.91s":{"配音指纹":"ed59953f5c3d","依据":"2026-11-05 逐 2.5 ms 实测（dossier_55，配音指纹 ed59953f5c3d）：S17 w 6.215–6.23：同上 construction. 的 /n/ 尾里一下回升（-36～-48 dB、低频占 -1.5～-3.4 dB、重心 1.1–2.0 kHz），是 /n/ 浊音的一部分"}},
"删除段":{"S1 raw 3.9000-4.2950": "2026-11-05 逐 2.5/10 ms 实测（S# w，配音指纹 ed59953f5c3d）：completion, 后停顿：n 尾衰减到 3.88 -63 dB，3.89–3.96 -52～-61 dB 底噪，3.96–4.20 渐升到 -39 dB、平稳不衰减的吸气（非人声区间 3.925–4.245 即此，删掉最响 -39.3 dB 就是它），4.20–4.26 回落到 -63 dB，4.27 起 in 的起音；两侧 -62.2/-59.2 dB 干净，没有词的声音", "S9 raw 5.6750-6.1000": "2026-11-05 逐 2.5/10 ms 实测（S# w，配音指纹 ed59953f5c3d）：ingredients, 后停顿：s 尾之后 5.67–5.77 -53～-58 dB 底噪，5.78–5.93 渐升到 -40.5 dB 的吸气，5.94–5.99 回落到 -62 dB，6.00 起 a 的起音（-7 dB）；删掉最响 -39.4 dB 是吸气，两侧 -59.8/-60.0 dB 干净", "S9 raw 7.9400-8.3050": "2026-11-05 逐 2.5/10 ms 实测（S# w，配音指纹 ed59953f5c3d）：assumed, 后停顿：d 尾之后 7.92–7.97 -54～-57 dB，7.97–8.16 -41～-52 dB 的吸气，8.17–8.20 回落到 -64 dB，8.21 起 a 的起音（-19→-3 dB）；删掉最响 -39.9 dB 是吸气，两侧 -62.4/-62.9 dB 干净", "S13 raw 4.9350-5.3080": "2026-11-05 逐 2.5/10 ms 实测（S# w，配音指纹 ed59953f5c3d）：weeks, 后停顿：s 尾之后 4.92–5.12 -54～-60 dB 底噪，5.12–5.26 渐升到 -43.6 dB 的吸气，5.27–5.30 -37～-41 dB 一下声门噗声（与 but 的 /b/ 除阻 5.345 之间隔着 5.30–5.34 的 -50～-58 dB），删到 5.308（非人声区间 5.08–5.307958 紧贴词头），留下 5.308 起紧贴 /b/ 的弱预发声；两侧 -62.6/-56.1 dB", "S5 raw 4.5700-4.9385": {"类型": "紧贴词头的非人声", "配音指纹": "ed59953f5c3d", "依据": "2026-11-05 逐 2.5/10 ms 实测（S# w，配音指纹 ed59953f5c3d）：it, 后停顿：4.47–4.66 -56～-69 dB 底噪，4.67–4.90 -41～-54 dB、重心 2.0–2.9 kHz、低频 -11～-22 dB 的吸气，4.91–4.935 -42～-45 dB 是吸气接 and 声门起音的过渡，没有 -55 dB 低谷；切点 4.9385 紧贴 and 词头，4.94 起 -34 dB、4.95 起 æ（-18 dB）完整保留"}, "S11 raw 1.6050-1.9287": {"类型": "紧贴词头的非人声", "配音指纹": "ed59953f5c3d", "依据": "2026-11-05 逐 2.5/10 ms 实测（S# w，配音指纹 ed59953f5c3d）：suggested, 后停顿：1.60–1.89 -44～-49 dB、低频 -10～-18 dB 的吸气，1.895–1.915 -55 dB，1.92 起 were 的 /w/ 浊音预发声（-44.7 dB、低频 -0.3 dB），吸气与 /w/ 预发声之间低谷只到 -55 dB；切点 1.9287 紧贴词头，1.945 起 /w/ 渐升到 1.97 -14 dB 完整保留"}},
"机器复听":{"S7":{"配音指纹":"ed59953f5c3d","依据":"2026-11-05 S7 Yet the ancient material seemed to have a shortcoming.：parakeet 整句听对；同一段声音单独切出（55.145–57.845s）给 small.en 也听成 material seemed，只有放在整篇流程里 small.en 听成 materials seem；material 的 /l/ 直接连 seemed 的 /s/（同一个 s，不是复数 s），seemed 的 /d/ 在 to 的 /t/ 前不完全除阻（自然连读），读音没错；识别器听不准，进疑点表"}},
"读音":{"rethink":{"标准读音":"ɹˈiːθˌɪŋk","可接受读音":[],"判定":"正确","依据":"2026-11-05 55 S17 a rethink of construction：名词，Merriam-Webster 名词 ˈrē-ˌthiŋk（动词 (ˌ)rē-ˈthiŋk），misaki NOUN ɹˈiθˌɪŋk；CMU 只收动词重音，配音经按语境读音改成名词读法","来源":["https://www.merriam-webster.com/dictionary/rethink"]}},
"停顿位置":{"S11 clasts, / it @0.736":"2026-11-05 逐 2.5 ms 实测（S11 w）：机器复听两路在插入点 0.730 时都听成 clasts, as it（0.730–0.735 还带 clasts 的 /s/ 余音，重心 4.8→2.6 kHz，被拼到停顿后面），插入点后移到 0.736125（0.7375 起 ɪ 浊音）；clasts 的 /s t s/ 擦音 0.60–0.7275（重心 5.7–6.9 kHz、低频 -18～-54 dB），0.730 起低频占比升到 -8 dB、重心降到 4.8 kHz 是 it 的 ɪ 起音，0.7375 起 ɪ 浊音（-9.5 dB、周期 0.41、重心 1.8 kHz）到 0.82，0.83 起 it 的 /t/ 闭塞，0.847 起 suggested 的 /s/；原插入点 0.730042 落在 clasts 词尾和 it 词头的交界，带时长模型给的 it 开头 0.800 偏后。原来自动插在 0.835 是 it 与 suggested 之间，错","S5 it, / and @4.555":"2026-11-05 逐 2.5 ms 实测（S5 w，配音指纹 2a450ed79690）：it 的 /t/ 4.40–4.43（重心 3.1 kHz）后 4.4625 -40.7 dB 衰减，4.47–4.66 是 -56～-69 dB 底噪，4.67–4.92 是 -41～-54 dB、重心 2.0–2.9 kHz、低频 -11～-22 dB 的吸气（非人声区间已清掉），4.93 起 and 的起音（-34→-18 dB）；停顿 4.555–4.905 整段落在 it 词尾之后、and 词头之前，带时长模型给的 it 末音素 4.776 偏后（±0.05 秒以上），停顿位置正确"}}
out={"no":"55","title_en":"The Secret of Rome's Undying Concrete","title_zh":"罗马混凝土的千年之谜","title_fx":{"hl":["Secret","Undying"],"ghost":[]},"sentences":[],"核对确认":CONF,"结尾解说":"简述",
     "停顿插入点":{"S11":{"1":[0.736125,"交界"]}},
     "词尾除阻":{"S6":{"1":[3.779,"t"]}},
     "高亮按实际开口":True,"高亮开口门槛":40,
     "术语":{"Pantheon":"万神殿","Roman":"罗马","Science Advances":"《科学进展》","Chatham House":"查塔姆研究所","AD":"公元"}}
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 核对 import 生成并核对
生成并核对(S, out)
