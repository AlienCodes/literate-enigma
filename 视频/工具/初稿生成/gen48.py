import json,re,glob,os
# 第48篇初稿（逐词对照）：S = [(段, [chunk, ...])]，chunk = ([(英文组, 中文组), ...], 可选 note)
# 2026-11-04 重点词中文沿用文章定稿（铁律），只按《翻译风格》调格式；形容词的“的”标进粗体；三项并列加牛津逗号（T18）；不用破折号（T36）。
S=[
(1,[[[("In July 1964,","1964年7月，")]],
    [[("**inspecting** rice ear by ear","逐穗**察看**(inspecting)水稻时，")],
     "（inspecting…：现在分词短语作伴随状语；\near by ear：一穗一穗地）"],
    [[("{{=}}in a **paddy** at Anjiang Agricultural School in Hunan province,","在湖南省安江农校的一块**稻田**(paddy)里，")]],
    [[("the **instructor**","**教员**(instructor)"),("Yuan Longping","袁隆平"),("spotted","发现了"),("a **peculiar**","一株**奇特的**(peculiar)"),("plant.","稻子。")],
     "（the instructor Yuan Longping：同位语，说明袁隆平的身份）"]]),
(1,[[[("It was","它是"),("male-**sterile**,","雄性**不育**(sterile)株，"),("**shedding** no","**散**(shedding)不出"),("**viable**","**有活力的**(viable)"),("**pollen**.","**花粉**(pollen)。")],
     "（shedding no viable pollen：现在分词短语作伴随状语，\n补充说明 male-sterile）"]]),
(1,[[[("Rice","水稻"),("pollinates itself,","是自花授粉的，")]],
    [[("so","所以，"),("breeding **hybrid** seed **in bulk**","要**大批地**(in bulk)培育**杂交**(hybrid)种子，"),("depends on","就得靠"),("such plants.","这样的植株。")],
     "（breeding… in bulk：动名词短语作主语；\nin bulk：大批，大量地）"]]),
(1,[[[("In February 1966","1966年2月，"),("he","他"),("**detailed**","**详细描述了**(detailed)"),("the **anomaly**","这一**反常现象**(anomaly)，"),("in the **journal**","文章发表在**期刊**(journal)"),("Chinese Science Bulletin.","《科学通报》上。")],
     "（Chinese Science Bulletin：《科学通报》，\n中国的学术期刊）"]]),
(2,[[[("The **specimen**","这株**标本**(specimen)"),("**launched**","**开启了**(launched)"),("a six-year **hunt**:","一场长达六年的**搜寻**(hunt)：")]],
    [[("Yuan and his **colleagues**","袁隆平和**同事们**(colleagues)"),("could not **breed**","始终**培育**(breed)不出"),("a sterile line","一个不育系，")]],
    [[("whose **offspring**","能让**后代**(offspring)"),("**reliably**","**稳定地**(reliably)"),("**inherited**","**遗传**(inherited)"),("the **trait**.","这一**性状**(trait)。")],
     "（whose…：定语从句，修饰 a sterile line）"]]),
(2,[[[("The **breakthrough**","**突破**(breakthrough)"),("came","出现在"),("on 23 November 1970,","1970年11月23日，")]],
    [[("in a **marsh**","地点是一片**沼泽**(marsh)，"),("near Nanhong Farm in Sanya, Hainan.","在海南三亚南红农场附近。")]]]),
(2,[[[("Yuan's assistant, Li Bihu,","袁隆平的助手李必湖"),("and Feng Keshan, a farm **technician**,","和农场**技术员**(technician)冯克珊")],
     "（a farm technician：同位语，补充说明 Feng Keshan）"],
    [[("found","找到了"),("wild rice","一种野生稻，"),("whose pollen","它的花粉"),("was **abortive**.","**败育**(abortive)。")],
     "（whose…：定语从句，修饰 wild rice）"]]),
(3,[[[("Then came","随后，"),("Yuan's","袁隆平迈出了"),("**decisive**","**决定性的**(decisive)"),("move:","一步：")],
     "（Then came…：倒装句，主语是 Yuan's decisive move）"],
    [[("rather than **withhold** the **strain**,","他没有把这个**品系**(strain)**扣在**(withhold)自己手里，")],
     "（rather than…：而不是……）"],
    [[("he","而是"),("**distributed** it **to**","把它**分给了**(distributed to)"),("**collaborators** **nationwide**.","**全国各地的**(nationwide)**协作者**(collaborators)。")],
     "（distribute A to B：把 A 分给 B）"]]),
(3,[[[("Hybrids","杂交稻"),("need","需要"),("three","三个"),("**distinct**","**各不相同的**(distinct)"),("lines:","系：")]],
    [[("a sterile line,","不育系，"),("one to **maintain**","**保持**(maintain)"),("its sterility,","其不育性的保持系，"),("and one","以及使杂交种"),("to **restore**","**恢复**(restore)"),("**fertility** in the hybrids.","**育性**(fertility)的恢复系。")],
     "（one to…：不定式作后置定语，修饰 one（= line））"]]),
(3,[[[("Yan Longan's team","颜龙安的团队"),("in Jiangxi","在江西"),("bred","育成了"),("sterile lines","不育系，")]],
    [[("and Zhang Xiancheng","张先程"),("in Guangxi","在广西"),("first **identified**","率先**找出了**(identified)"),("a restorer line.","恢复系。")]]]),
(3,[[[("In October 1973,","1973年10月，"),("at a national conference in Suzhou,","在苏州召开的全国性会议上，")]],
    [[("Yuan","袁隆平"),("declared","宣布"),("the three-line system","三系"),("complete.","已经配套。")],
     "（declare＋宾语＋形容词：宣布……已经……）"]]),
(4,[[[("By 1976","到1976年，"),("hybrids","杂交稻的"),("were **under cultivation**","**种植**(under cultivation)面积"),("on about 140,000","已达约14万"),("**hectares**.","**公顷**(hectares)。")],
     "（under cultivation：在耕种中，正被种植）"]]),
(4,[[[("The World Food Prize Foundation","据世界粮食奖基金会"),("**estimates**","**估计**(estimates)，")],
     "（estimate that…：估计……）"],
    [[("that hybrid rice","杂交稻"),("can **yield** up to a fifth more **grain** than **conventional** **varieties**.","比**常规**(conventional)**品种**(varieties)最多可多**产**(yield)五分之一的**稻谷**(grain)。")],
     "（up to a fifth more…than…：比……最多多五分之一）"]]),
(4,[[[("By the early 2000s","到21世纪初，"),("it","杂交稻"),("covered","已覆盖"),("almost half","近一半的"),("of China's rice fields.","中国稻田。")]]]),
(5,[[[("Yuan,","袁隆平"),("who shared the 2004 World Food Prize with Sierra Leone's Monty Jones,","曾与塞拉利昂的蒙蒂·琼斯共获2004年世界粮食奖，")],
     "（who…：非限制性定语从句，补充说明 Yuan）"],
    [[("died in Changsha on 22 May 2021,","2021年5月22日在长沙逝世，"),("aged 91.","享年91岁。")]]]),
(5,[[[("Yet","然而，"),("popular **myth**","一种流传甚广的**误解**(myth)"),("**portrays** him **as**","把他**描绘成**(portrays as)"),("a **solitary**","一个**单枪匹马的**(solitary)"),("**genius**.","**天才**(genius)。")],
     "（portray A as B：把 A 描绘成 B）"]]),
(5,[[[("His eye","他的慧眼"),("began","开启了"),("the search;","这场搜寻；")]],
    [[("his **generosity**","他的**慷慨**(generosity)，"),("let","让"),("many hands","许多双手"),("**bring in the harvest**.","一起**迎来了丰收**(bring in the harvest)。")],
     "（bring in the harvest：收庄稼，这里指迎来丰收）\n"
     "（简述：1964年7月，袁隆平在安江农校的稻田里发现一株雄性不育的稻子。\n"
     "此后六年，他和同事们始终培育不出后代能稳定遗传不育性的不育系。\n"
     "1970年11月，李必湖和冯克珊在海南三亚找到花粉败育的野生稻。\n"
     "袁隆平把这个品系分给全国各地的协作者，\n"
     "颜龙安的团队育成不育系，张先程率先找出恢复系，1973年三系配套。\n"
     "杂交稻最多可比常规品种多产五分之一的稻谷，\n"
     "到21世纪初已覆盖中国近一半的稻田。\n"
     "他不是单枪匹马的天才，丰收靠的是许多双手。）"]]),
]
G={
 "S1 inspecting rice ear by ear":"对齐不了：ear by ear 是方式状语，中文“逐穗察看水稻时”（沿用文章定稿“逐穗察看”）“逐穗”必须放到动词前",
 "S3 breeding hybrid seed in bulk":"对齐不了：in bulk 是方式状语，中文“大批地”必须放到动词“培育”前，拆开 breeding、seed 中文不通",
 "S5 a sterile line":"对齐不了：sterile line 是育种术语“不育系”，拆开不通",
 "S7 wild rice":"对齐不了：wild rice 是术语“野生稻”，拆开不通",
 "S9 a sterile line":"对齐不了：sterile line 是育种术语“不育系”，拆开不通",
 "S10 sterile lines":"对齐不了：sterile line 是育种术语“不育系”，拆开不通",
 "S10 a restorer line":"对齐不了：restorer line 是育种术语“恢复系”，拆开不通",
 "S11 at a national conference in Suzhou":"对齐不了：in Suzhou 是后置定语，修饰 conference，中文“在苏州召开的全国性会议上”定语必须提前",
 "S11 the three-line system":"对齐不了：three-line system 是育种术语“三系”，拆开不通",
 "S13 that hybrid rice":"对齐不了：hybrid rice 是术语“杂交稻”，拆开不通",
 "S14 of China's rice fields":"对齐不了：rice fields 中文“稻田”是一个词，拆开不通",
}
CONF={"合组":G,"对齐":{
 "S1-2 inspecting rice ear by ear":"ear by ear 是方式状语，中文“逐穗察看”（沿用文章定稿）必须放到动词前",
 "S1-3 in a paddy at Anjiang Agricult":"at Anjiang Agricultural School in Hunan province 是后置定语，修饰 paddy，中文“在湖南省安江农校的一块稻田里”（沿用文章定稿）定语必须提前；in Hunan province 也要提到校名前，修饰 Anjiang Agricultural School，中文“湖南省安江农校”省名必须提前；专名不能拆",
 "S7-1 and Feng Keshan, a farm techni":"a farm technician 是同位语，补充说明 Feng Keshan，中文“农场技术员冯克珊”（沿用文章定稿）身份必须放到人名前",
 "S3-2 breeding hybrid seed in bulk":"in bulk 是方式状语，中文“要大批地培育杂交种子”必须放到动词前",
 "S6-2 near Nanhong Farm in Sanya, Ha":"地点由小到大 near Nanhong Farm in Sanya, Hainan，中文“海南三亚南红农场附近”必须由大到小倒过来，“附近”放最后",
 "S8-2 rather than withhold the strai":"withhold the strain 中文沿用文章定稿“把这个品系扣在自己手里”，宾语必须提到动词前",
 "S11-1 at a national conference in Su":"in Suzhou 是后置定语，修饰 conference，中文“在苏州召开的全国性会议上”定语必须提前",
 "S13-1 The World Food Prize Foundatio":"专名 World Food Prize Foundation 不能拆，中文“据世界粮食奖基金会”",
 "S13-2 can yield up to a fifth more g":"than conventional varieties 是比较状语，中文“比常规品种最多可多产五分之一的稻谷”（沿用文章定稿）比较对象必须放到动词前",
 "S15-1 who shared the 2004 World Food":"非限制性定语从句，with Sierra Leone's Monty Jones 中文“曾与塞拉利昂的蒙蒂·琼斯共获”必须放到动词前，年份也要提到奖名前",
 "S15-2 died in Changsha on 22 May 202":"时间、地点状语 in Changsha on 22 May 2021，中文“2021年5月22日在长沙逝世”必须放到动词前，时间在地点前",
},
 "们":{"S5-2 **同事们**":"colleagues 是复数，沿用文章定稿“同事们”，们在加粗内"},
 "数字":{"S12-1 140,000":"about 140,000 中文按文章定稿写作“约14万”，数值相同（140,000 = 14万）；英文读 one hundred and forty thousand","S14-1 2000":"the early 2000s 中文按文章定稿写作“21世纪初”（2000年代初 = 21世纪初）；英文读 the early two thousands"},
 "短语":{"S6 breakthrough … in":"不是搭配：in a marsh 是地点状语，不是 breakthrough in 搭配（文中没有“在……方面的突破”）",
  "S8 withhold … to":"不是搭配：to 属于后面的 distributed it to，withhold 后面只有宾语 the strain",
  "S9 maintain … to":"不是搭配：to 是下一项 one to restore 的不定式符号，不是 maintain 的搭配",
  "S13 estimates … to":"不是搭配：to 属于 up to a fifth，estimates 只接 that 从句",
  "S13 yield … to":"不是搭配：up to 修饰 a fifth more grain（最多……），不是 yield 的搭配",
  "S8 collaborators nationwide":"不是搭配：nationwide 是后置修饰语（全国各地的），collaborators 用的就是本义“协作者”（速查表 collaborator n. 合作者，协作者），不是习语"},
}
# 非人声区间（2026-11-04 逐 2.5 ms 实测，配音指纹 df5a646c744c 的 dossier_48）：
# S4 2.2875–2.5725（左头外侧 2.2825–2.2875 -60～-63 dB）：1966 的 /s/ 到 2.27 衰减到 -58 dB，2.33–2.555 是 -50～-55 dB、重心 2.0–2.5 kHz、低频 -10～-20 dB、周期 ≤0.3 的吸气（1966 和 he 之间无标点），2.62 起 he 的 /h/；两头 -59.5/-60.8 dB
# S10 6.155–6.168042（紧贴 /f/ 起擦 6.168 重心 3.8 kHz，过零点）：Guangxi 尾音后 6.12–6.16 静音（-56～-61），6.1625–6.1725 是 -47～-50 dB、低频占 -0.3～-3.6 dB 的低频噗，紧贴 first 的 /f/（6.175 起重心 4.5–7 kHz）；/f/ 是清音，前面不该有浊起音，切
# S12 4.503–4.635（紧贴 about 尾，过零点 4.503）：about 的 aʊ 到 4.49，4.50–4.632 是 -40～-56 dB、重心 1.5–2.3 kHz、低频 -3～-20 dB 的吸气（about 和 one 之间无标点），4.635–4.69 是 one 的起音（低频 -1.5～-5 dB）留着
# S13 5.595542–5.800208（两头过零点）：fifth 的 θ（重心 6–7.5 kHz）到 5.5925 衰减完，5.61–5.80 是 -42～-51 dB、重心 2.0–2.6 kHz、低频 -10～-26 dB、周期 ≤0.35 的吸气（fifth 和 more 之间无标点），5.80–5.84 是 more 的 /m/ 预浊音（低频 -0.2～-1.8 dB、周期 0.3–0.52）留着
# S14 1.53025–1.70575（两头过零点）：thousands 的 /z/ 到 1.51 衰减，1.535–1.70 是 -46～-55 dB、重心 2.0–2.6 kHz、低频 -5～-24 dB 的吸气（thousands 和 it 之间无标点），1.705 起 it 的声门起音（低频 -0.5～-2 dB）
# S13 2.950292–3.1（原程序切点 2.939042 把 that 的 /t/ 除阻切掉了：2.9425–2.9475 是 -32～-40 dB、重心 1.5–2.7 kHz 的除阻，2.95 降到 -49.6 dB；改从除阻后的过零点 2.950292 开切，2.95–3.10 是 -42～-51 dB、重心 2.0–2.5 kHz 的吸气）
# S16 1.935208–2.090458（两头过零点）：him 的 /m/ 到 1.915 衰减，1.94–2.08 是 -44～-51 dB、重心 1.8–2.4 kHz、低频 -4～-26 dB 的吸气（him 和 as 之间无标点），2.0925 起 as 的声门起音（低频 -0.4～-4 dB）
CONF["停顿位置"]={
 "S7 Bihu, / and @2.117":"2026-11-04 逐 2.5 ms 实测（S7 w）：Bihu 的 uː 浊音到 2.09（-17～-25 dB、周期 0.45–0.55）；2.0925–2.115 是 uː 的衰减尾（-25～-30 dB、周期 0.18–0.35）；2.1175 是两词之间最低一帧（-34.7 dB）；2.12 起 and 的 æ 起音（-17 dB、重心 1.8–2.5 kHz、周期 0.2→0.5）。程序原插 2.115 在衰减尾末端，改插交界过零点 2.117292，衰减尾整段留给 Bihu，不切 and 的起音",
 "S15 Yuan, / who @0.635":"2026-11-04 逐 2.5 ms 实测（S15 w）：Yuan 的 /n/ 浊音（周期 0.65–0.72、重心 0.4–0.8 kHz）到 0.60 衰减到 -47.9 dB；0.6075–0.665 是 -48～-58 dB 的静音段（最低 0.6375 -58.3 dB）；0.6675–0.70 是 who 的 /h/ 送气（-35～-44 dB、重心 2.2–3.0 kHz、低频 -17～-35 dB、周期 ≤0.5），0.705 起 uː 浊音。插入点 0.635 落在静音段中间，前后词都不切，位置正确"}
CONF["非人声"]={"4.82–4.85s": {"配音指纹": "8253a58195c8", "依据": "2026-11-04 逐 2.5 ms 实测（dossier_48）：S1 w 2.295–2.33：前面吸气已按 非人声区间 切到 2.29625；这一段 -44～-57 dB、低频占 -0.4～-3.6 dB、周期 0.12–0.41，2.3325 起 -38→-20 dB 进入 inspecting 的 ɪ；是 inspecting 开口前的声门起音"}, "14.96–15.01s": {"配音指纹": "8253a58195c8", "依据": "2026-11-04 逐 2.5 ms 实测（dossier_48）：S1 w 12.52–12.565：plant 的 /n/ 之后 12.47–12.5175 闭塞（-55～-70 dB），12.525 突起 -29.7 dB、重心 2.8–3.4 kHz、周期 0.12–0.16、低频 -10～-30 dB，再衰减到 12.565 的 -58 dB；是句末 plant 的 /t/ 除阻"}, "24.22–24.24s": {"配音指纹": "8253a58195c8", "依据": "2026-11-04 逐 2.5 ms 实测（dossier_48）：S3 w 4.005–4.025：bulk 的 /l/ 到 3.98 衰减（-47～-58 dB），4.01 突起 -33.8 dB、重心 2.2 kHz、周期 0.15、低频 -18 dB，4.025 回到 -56 dB；是 bulk 的 /k/ 除阻（4.09 起 depends 的 /d/）"}, "40.54–40.55s": {"配音指纹": "8253a58195c8", "依据": "2026-11-04 逐 2.5 ms 实测（dossier_48）：S5 w 6.265–6.28：line 后的吸气已按 非人声区间 切到 6.25；这一段 -42～-57 dB、低频占 -1.1～-3.7 dB，6.28–6.30 周期升到 0.4–0.48，6.31 起 whose 的 /h/→uː；是 whose 的声门起音"}, "61.53–61.55s": {"配音指纹": "8253a58195c8", "依据": "2026-11-04 逐 2.5 ms 实测（dossier_48）：S7 w 7.805–7.82：abortive 的 ɪ→v 浊音 7.76–7.80（-31～-40 dB、周期 0.3–0.39、低频 -3～-10 dB），这一段 -39～-48 dB、低频 -1.5～-4.8 dB 是同一段 /v/ 浊音的延续，7.83 起 /v/ 擦音（重心 4.2–5 kHz）；是 abortive 词尾 /v/"}, "65.08–65.17s": {"配音指纹": "8253a58195c8", "依据": "2026-11-04 逐 2.5 ms 实测（dossier_48）：S8 w 2.24–2.33：move 的 uː 到 2.21（-25～-37 dB），2.24–2.28 衰减的浊音（周期 0.15–0.44），2.285–2.38 是重心 3–5.5 kHz、低频 -16～-35 dB 的擦音，冒号停顿从 2.405 起；是 move 词尾 /v/ 的擦音，不是吸气（吸气重心在 2–2.5 kHz）"}, "73.92–74.03s": {"配音指纹": "8253a58195c8", "依据": "2026-11-04 逐 2.5 ms 实测（dossier_48）：S9 w 2.27–2.38：lines 的 /n/ 浊音段，-35～-56 dB、低频占 -1～-9 dB、周期 0.2–0.59、重心 1.1–2.9 kHz，2.38 起 /z/（重心 5.5 kHz、-19～-26 dB）；是 lines 的 n→z 过渡"}, "75.84–75.88s": {"配音指纹": "8253a58195c8", "依据": "2026-11-04 逐 2.5 ms 实测（dossier_48）：S9 w 4.30–4.33：line, 后的吸气已按 非人声区间 切到 4.30125；这一段 -44～-55 dB、低频占 -0.4～-2.9 dB，4.33 起 one 的 /w/（-33.7 dB、重心 1.2 kHz→0.5 kHz）；是 one 的声门起音"}, "77.87–77.89s": {"配音指纹": "8253a58195c8", "依据": "2026-11-04 逐 2.5 ms 实测（dossier_48）：S9 w 6.305–6.325：sterility, 后的吸气已按 非人声区间 切到 6.306208；这一段 -39～-49 dB、低频占 -0.4～-1.7 dB、周期 0.2–0.4，6.3425 起 and 的 æ（-19.9 dB）；是 and 的声门起音"}, "107.16–107.25s": {"配音指纹": "8253a58195c8", "依据": "2026-11-04 逐 2.5 ms 实测（dossier_48）：S12 w 6.845–6.94：hectares 的 ɛɹ 浊音 6.785–6.84（-23～-45 dB），这一段 -38～-55 dB、低频占 -2～-9 dB、重心 1–2.5 kHz，6.9225 起重心升到 2.4→5.6 kHz 进入 /z/；是 hectares 的 ɹ→z 过渡"}, "110.27–110.35s": {"配音指纹": "8253a58195c8", "依据": "2026-11-04 逐 2.5 ms 实测（dossier_48）：S13 w 1.915–1.995：Foundation 的 /n/（-20～-37 dB、重心 0.7–1 kHz、低频 -0.6～-5 dB）衰减，这一段 -42～-57 dB、低频 -1～-14 dB，1.995 起 -53～-65 dB；是 Foundation 的 /n/ 衰减尾"}, "116.64–116.73s": {"配音指纹": "8253a58195c8", "依据": "2026-11-04 逐 2.5 ms 实测（dossier_48）：S13 w 8.28–8.375：varieties 的 i 到 /z/ 之间，-35～-54 dB、低频占 -0.9～-4 dB、周期 0.1–0.43、重心 1.6–3 kHz，8.365 起重心升到 4.7–5.7 kHz 是 /z/；是 varieties 的 i→z 浊音过渡"}, "116.67–116.69s": {"配音指纹": "8253a58195c8", "依据": "2026-11-04 逐 2.5 ms 实测（dossier_48）：S13 w 8.315–8.33：同 116.64–116.73s（varieties 的 i→z 浊音过渡），低频占 -2～-3 dB，是嗓音"}, "114.16–114.19s": {"配音指纹": "8253a58195c8", "依据": "2026-11-04 逐 2.5 ms 实测（dossier_48）：S13 w 5.80–5.84：fifth 后的吸气已按 非人声区间 切到 5.800208；这一段 -45～-56 dB、低频占 -0.2～-1.8 dB、周期 0.3–0.52，5.875 起 more 的 /m/（-36→-12 dB、重心 0.4–0.8 kHz）；是 /m/ 的预浊音"}, "113.23–113.25s": {"配音指纹": "8253a58195c8", "依据": "2026-11-04 逐 2.5 ms 实测（dossier_48）：S13 w 4.88–4.89：up 的 ʌ 到 4.84 衰减，4.845–4.875 闭塞（-55～-66 dB），4.88 突起 -32 dB、重心 3.5 kHz、周期 0.13，4.89 回到 -56 dB；是 up 的 /p/ 除阻（4.92 起 to 的 /t/）"}, "119.55–119.58s": {"配音指纹": "8253a58195c8", "依据": "2026-11-04 逐 2.5 ms 实测（dossier_48）：S14 w 1.705–1.73：thousands 后的吸气已按 非人声区间 切到 1.70575；这一段 -47～-63 dB、低频占 -0.5～-2 dB，1.755 起 it 的 ɪ（-33 dB）；是 it 的声门起音"}, "130.59–130.60s": {"配音指纹": "8253a58195c8", "依据": "2026-11-04 逐 2.5 ms 实测（dossier_48）：S15 w 6.525–6.54：Jones, 后的停顿已按 非人声区间 切到 6.5；这一段 -50→-33 dB 上升、重心 0.57–1.8 kHz、低频 -1～-2.4 dB，6.5425 起重心 340–600 Hz 的浊音杠，6.58 /d/ 除阻（重心 4.2 kHz）；是 died 的 /d/ 浊音杠"}, "139.50–139.53s": {"配音指纹": "8253a58195c8", "依据": "2026-11-04 逐 2.5 ms 实测（dossier_48）：S16 w 2.09–2.11：him 后的吸气已按 非人声区间 切到 2.090458；这一段 -45～-63 dB、低频占 -0.4～-4 dB，2.135 起 as 的 æ（-37→-22 dB）；是 as 的声门起音"}, "148.46–148.51s": {"配音指纹": "8253a58195c8", "依据": "2026-11-04 逐 2.5 ms 实测（dossier_48）：S17 w 6.155–6.21：harvest 的 /s/ 到 6.12 衰减，6.12–6.155 闭塞（-56～-70 dB），6.1575 突起 -38 dB、重心 2.9–3.9 kHz、周期 0.17–0.31，6.21 衰减到 -60 dB；是句末 harvest 的 /t/ 除阻"}}
CONF["高亮"]={"S10 第2块": {"开始读": 85.3, "配音指纹": "8253a58195c8", "依据": "2026-11-04 直接读 work_48/a.wav 逐 10 ms：85.13–85.28 是 lines, 后的数字静音（-180 dB），85.29 -69、85.30 -49 dB（声门起音），85.32 起 and 的 æ（-22→-11 dB、重心 1.8–2.6 kHz）；and 在 85.30 开始读，高亮 85.30 对；甲法 85.13 落在静音开头"}, "S13 第2块": {"开始读": 111.1625, "配音指纹": "8253a58195c8", "依据": "2026-11-04 直接读 work_48/a.wav 逐 10 ms：estimates 的 /s/ 111.10–111.13（重心 7.3–7.9 kHz），111.14–111.15 衰减到 -47～-49 dB，111.16 起 that 的 ð（-39 dB、重心 4.3 kHz），111.18 起 æ（-11 dB）；逐 2.5 ms 开口判定 111.1625（前 30 ms 最响 -36.5 dB，之后 -3 dB）；that 在 111.1625 开始读，已写 高亮开始 111.16；乙法 111.49 落在 hybrid 上"}}
CONF["机器复听"]={"S10": {"配音指纹": "8253a58195c8", "依据": "2026-11-04 实测（S10 w）：restorer 配音音标 ɹᵻstˈɔːɹɚ，读音核对 0；/s/ 7.84–7.90（重心 5.8–6.1 kHz），/t/ 闭塞 7.91–7.95、除阻 7.96，ɔː 7.98–8.07（-4.5～-12 dB、重心 0.5–1.3 kHz），ɹ 8.08–8.22（-11～-18 dB），8.23–8.24 电平回升到 -10.4 dB 是第二个音节 ɚ 的音节核，ɚ 到 8.33，8.34 起 line 的 /l/；-er 音节在，只有 small.en 一路把 restorer line 听成 restore，交用户听"}}
out={"no":"48","title_en":"Rice for the World","title_zh":"稻济天下","title_fx":{"hl":["Rice","World"],"ghost":[]},"sentences":[],"核对确认":CONF,"结尾解说":"简述",
     "非人声区间":{"S4":[[2.2875,2.5725]],"S10":[[3.57,3.86],[5.91,6.125],[6.155,6.168042,"紧贴词头"]],"S12":[[1.785,2.01],[4.503,4.635,"紧贴词尾"]],"S13":[[2.950292,3.1,"紧贴词尾"],[5.595542,5.800208,"紧贴两头"]],"S14":[[1.53025,1.70575,"紧贴两头"]],"S16":[[1.935208,2.090458,"紧贴两头"]]},
     "高亮开始":{"S13 第2块":111.16},
     "停顿插入点":{"S7":{"2":[2.117292,"交界"]}},
     "高亮按实际开口":True,"高亮开口门槛":40,
     "术语":{"Yuan Longping":"袁隆平","Yuan":"袁隆平","Anjiang Agricultural School":"安江农校","Hunan":"湖南","Chinese Science Bulletin":"《科学通报》","Li Bihu":"李必湖","Feng Keshan":"冯克珊","Nanhong Farm":"南红农场","Sanya":"三亚","Hainan":"海南","Yan Longan":"颜龙安","Jiangxi":"江西","Zhang Xiancheng":"张先程","Guangxi":"广西","Suzhou":"苏州","World Food Prize Foundation":"世界粮食奖基金会","World Food Prize":"世界粮食奖","China":"中国","Sierra Leone":"塞拉利昂","Monty Jones":"蒙蒂·琼斯","Changsha":"长沙"}}
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 核对 import 生成并核对
生成并核对(S, out)
