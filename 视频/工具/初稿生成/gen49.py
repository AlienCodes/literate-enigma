import json,re,glob,os
# 第49篇初稿（逐词对照）：S = [(段, [chunk, ...])]，chunk = ([(英文组, 中文组), ...], 可选 note)
# 2026-11-04 重点词中文沿用文章定稿（铁律），只按《翻译风格》调格式；形容词重点词“的”一起标；不用破折号（T36）。
S=[
(1,[[[("Marie Curie","玛丽·居里"),("was born Maria Skłodowska","原名玛丽亚·斯克沃多夫斯卡，")]],
    [[("on 7 November 1867","1867年11月7日"),("in Warsaw,","生于华沙。")]],
    [[("then","当时华沙"),("under Russian **dominion**,","处于俄国的**统治**(dominion)之下，")],
     "（then under Russian dominion：插入语，补充说明华沙当时的处境）"],
    [[("where","在那里，"),("women","女性"),("**were denied**","**被剥夺了**(were denied)"),("university **admission**.","大学的**入学资格**(admission)。")],
     "（be denied = 被拒绝给予/被剥夺）"]]),
(1,[[[("**Eager** to","**渴望**(Eager)"),("**pursue**","**追求**(pursue)"),("**formal** study,","**正规的**(formal)学习，")],
     "（eager to do：渴望做……，形容词短语作状语）"],
    [[("she","她"),("**emigrated** to Paris in 1891,","于1891年**移居**(emigrated)巴黎，"),("**enrolling** at the Sorbonne.","**注册入读**(enrolling)索邦大学。")],
     "（enrolling at…：现在分词短语作状语，\n表接着发生的动作）"]]),
(1,[[[("On 26 July 1895","1895年7月26日，"),("she","她"),("**wed** the physicist Pierre Curie,","与物理学家皮埃尔·居里**成婚**(wed)，")]],
    [[("**forging**","两人**建立起**(forging)"),("a research **partnership**.","研究上的**合作关系**(partnership)。")],
     "（forging…：现在分词短语作状语，表结果；\nforge 常用来表示“打造、建立”。\n比如 forge a friendship 就是建立友谊，forge an alliance 是结盟；\n如果是 forge a path，意思就是硬生生“开辟/闯出一条路”。）"]]),
(2,[[[("Henri Becquerel","亨利·贝克勒尔"),("found that","发现，"),("uranium","铀"),("emitted","会发出"),("**rays**;","**射线**(rays)；")],
     "（that 引导宾语从句）"],
    [[("she","她"),("named this **property** of certain **elements**","把某些**元素**(elements)的这种**性质/属性**(property)"),("**radioactivity**.","命名为**放射性**(radioactivity)。")],
     "（name A B：把 A 命名为 B；\nof certain elements：后置定语，修饰 property）"]]),
(2,[[[("In July 1898","1898年7月，"),("the Curies","居里夫妇"),("announced","宣布发现了"),("polonium,","钋，")]],
    [[("a **tribute to**","以此**致敬**(tribute to)"),("her **motherland**,","她的**祖国**(motherland)；")],
     "（a tribute to…：对……的致敬，同位语，补充说明 polonium）"],
    [[("and on 26 December,","12月26日，他们又宣布发现了"),("**radium**.","**镭**(radium)。")],
     "（on 26 December, radium：省略句，省去了 the Curies announced）"]]),
(2,[[[("In a **leaky**","在一间**漏雨的**(leaky)"),("shed","棚屋里，"),("they","他们"),("**painstakingly**","**费尽心力地**(painstakingly)"),("processed","处理了"),("**tonnes** of pitchblende,","成**吨**(tonnes)的沥青铀矿，")],
     "（tonnes of…：成吨的……）"],
    [[("a uranium **ore**;","这是一种铀**矿石**(ore)。")],
     "（a uranium ore：同位语，补充说明 pitchblende）"],
    [[("by 1902","到1902年，"),("she","她"),("had **recovered**","已**提取**(recovered)出"),("about","约"),("a tenth of a **gram**","十分之一**克**(gram)的"),("of radium **chloride**.","**氯化**(chloride)镭。")],
     "（had recovered：过去完成时，到1902年为止已完成；\na tenth of a gram：十分之一克）"]]),
(3,[[[("On 10 December 1903","1903年12月10日，"),("she","她"),("**jointly** won the physics Nobel with Pierre and Becquerel,","与皮埃尔和贝克勒尔**共同**(jointly)获得诺贝尔物理学奖，")]],
    [[("the first woman","第一位"),("so **recognised**.","**获此认可的**(recognised)女性。")],
     "（the first woman so recognised：同位语，\n补充说明 she；\nso：指获得诺贝尔奖这件事）"]]),
(3,[[[("The nomination","提名"),("had **initially**","**最初**(initially)"),("**left** her **out**;","把她**排除在外了**(left out)；")],
     "（leave sb out：把某人排除在外）"],
    [[("at Pierre's **insistence**,","在皮埃尔的**坚持**(insistence)下，"),("the **omission**","这一**疏漏**(omission)"),("was **rectified**.","得到了**纠正**(rectified)。")],
     "（at one's insistence：在某人的坚持下）"]]),
(3,[[[("On 19 April 1906","1906年4月19日，"),("a horse-drawn **wagon**","一辆马拉的**货车**(wagon)"),("**fatally**","**致命地**(fatally)"),("struck","撞上了"),("Pierre.","皮埃尔。")],
     "（horse-drawn：马拉的）"]]),
(3,[[[("On 5 November","11月5日，"),("she","她"),("gave her **inaugural** lecture as his **successor**,","作为他的**继任者**(successor)发表了**就职**(inaugural)演讲，")],
     "（as his successor：as 表身份，作为他的继任者）"],
    [[("the Sorbonne's","成为索邦大学"),("first","第一位"),("woman","女"),("professor.","教授。")],
     "（同位语，补充说明 she）"]]),
(4,[[[("In November 1911","1911年11月，"),("a press **scandal** about her private life","一场关于她私生活的媒体**丑闻**(scandal)"),("**erupted**;","**爆发**(erupted)，")],
     "（about her private life：后置定语，修饰 scandal）"],
    [[("she was urged","有人劝她"),("to stay away.","不要前往。")],
     "（be urged to do：被劝做……；stay away：不去，不到场）"]]),
(4,[[[("**Undeterred**,","她并**没有被吓住**(Undeterred)，")],
     "（Undeterred：形容词作状语，说明 she 的状态）"],
    [[("she collected the chemistry Nobel, won **outright**, on 10 December.","于12月10日，领取了**完全**(outright)属于她的诺贝尔化学奖。")],
     "（won outright：过去分词短语作插入语，修饰 Nobel；\nwin outright：独得，完胜）"]]),
(4,[[[("Her **distinction** in two sciences","她在两门科学中双双获得诺贝尔奖，这份**荣誉**(distinction)"),("remains **unmatched**.","至今仍**无人企及**(unmatched)。")],
     "（in two sciences：后置定语，修饰 distinction）"]]),
(4,[[[("In the First World War","第一次世界大战期间，"),("she","她"),("**mobilised**","**动员/调用了**(mobilised)"),("X-ray **vans**","X光**面包车**(vans)"),("and **stationary** posts","和**固定**(stationary)站点，")],
     "（vans：医疗式面包车，载有X光设备，类似于医院的救护车）"],
    [[("that examined","这些设施检查了"),("over a million","超过一百万"),("**casualties**.","**伤亡人员**(casualties)。")],
     "（that 引导定语从句，修饰 vans and stationary posts）"]]),
(5,[[[("She died on 4 July 1934","1934年7月4日，她死于"),("of a blood **disorder**,","一种血液**疾病**(disorder)，")],
     "（die of…：死于……）"],
    [[("probably caused by","这很可能是由"),("**prolonged**","**长期**(prolonged)"),("exposure to radiation.","暴露于辐射所导致的。")],
     "（probably caused by…：过去分词短语作后置定语，修饰 disorder；\nexposure to…：暴露于……）"]]),
(5,[[[("Her notebooks,","她的笔记本"),("still","至今仍"),("**radioactive**,","**有放射性**(radioactive)，")],
     "（still radioactive：形容词短语作插入语，补充说明 notebooks）"],
    [[("are **preserved**","**保存**(preserved)在"),("in **lead**-lined boxes at the National Library of France;","法国国家图书馆的**铅**(lead)衬的盒子里；")],
     "（at the National Library of France：后置定语，修饰 boxes；\n铅衬的盒子目的是为了防止辐射，封印这本笔记）"],
    [[("readers","读者"),("sign","须签署"),("a **liability waiver**","**免责协议**(liability waiver)，"),("and **don**","并**穿上**(don)"),("**protective**","**防护**(protective)"),("**garments**.","**服装**(garments)。")]]]),
(5,[[[("The pages","这些书页"),("**retain**","**留存**(retain)着"),("her **handwriting**","她的**笔迹**(handwriting)，"),("and her radium.","同样也留存着她所发现的镭。")],
     "（简述：玛丽·居里1867年生于华沙，当时那里的女性上不了大学，\n"
     "她1891年移居巴黎，入读索邦大学，1895年与皮埃尔·居里结婚。\n"
     "她把某些元素发出射线的性质命名为放射性，\n"
     "居里夫妇1898年宣布发现钋和镭，又在漏雨的棚屋里处理成吨矿石提取镭。\n"
     "1903年她与皮埃尔和贝克勒尔共同获得诺贝尔物理学奖；\n"
     "1906年皮埃尔被马车撞死，她接任成为索邦大学第一位女教授。\n"
     "1911年她不顾丑闻领取独得的诺贝尔化学奖，一战中又调集X光车为伤员做检查。\n"
     "1934年她死于很可能由辐射引起的血液疾病，她的笔记本至今仍有放射性。）"]]),
]
G={
 "S4 named this property of certain elements":"对齐不了：name A B 中文“把 A 命名为 B”（沿用文章定稿），named 化成“把……命名为”；of certain elements 是后置定语，中文“某些元素的这种性质”定语必须提前",
 "S7 jointly won the physics Nobel with Pierre and Becquerel":"对齐不了：with Pierre and Becquerel 是伴随状语，中文“与皮埃尔和贝克勒尔共同获得”必须放到动词前，夹在 jointly 前面，拆开不通",
 "S8 left her out":"对齐不了：left her out 中文“把她排除在外了”（用户原话），her 化成“把她”放到动词前",
 "S10 gave her inaugural lecture as his successor":"对齐不了：as his successor 表身份，中文“作为他的继任者发表了就职演讲”必须放到动词前",
 "S11 a press scandal about her private life":"对齐不了：about her private life 是后置定语，修饰 scandal，中文“关于她私生活的媒体丑闻”定语必须提前",
 "S12 she collected the chemistry Nobel, won outright, on 10 December":"对齐不了：on 10 December 是时间状语，中文“于12月10日”必须放到动词前；won outright 是插入的后置修饰，中文“她独得的”必须放到“诺贝尔化学奖”前",
 "S15 probably caused by":"对齐不了：caused by 中文“是由……所导致的”（用户原话）包住后面的“长期暴露于辐射”，“所导致的”只能放最后",
 "S15 exposure to radiation":"对齐不了：exposure to radiation 中文“暴露于辐射”，“所导致的”属于前面的 caused by，拆开不通",
}
CONF={"合组":G,"对齐":{
 "S2-2 emigrated to Paris in 1891,":"in 1891 是时间状语，中文“于1891年移居巴黎”时间必须放到动词前",
 "S3-1 wed the physicist Pierre Curie":"wed sb 中文“与某人成婚”，对象必须放到动词前",
 "S4-2 named this property of certain":"name A B 中文“把 A 命名为 B”；of certain elements 是后置定语，中文定语必须提前",
 "S6-3 a tenth of a gram":"a tenth of a gram 是分数读法，中文“十分之一克”，拆开数字不通",
 "S7-1 jointly won the physics Nobel ":"with Pierre and Becquerel 是伴随状语，中文必须放到动词前",
 "S10-1 gave her inaugural lecture as ":"as his successor 表身份，中文必须放到动词前",
 "S11-1 a press scandal about her priv":"about her private life 是后置定语，中文定语必须提前",
 "S12-2 she collected the chemistry No":"on 10 December 是时间状语，中文必须放到动词前；won outright 中文“独得的”作定语提前",
 "S13-1 Her distinction in two science":"in two sciences 是后置定语，修饰 distinction，中文沿用文章定稿“她在两门科学中双双获得诺贝尔奖，这份荣誉”，必须提前",
 "S14-1 In the First World War":"the First World War 是专名“第一次世界大战”，in 化成“期间”放最后，拆开不通",
 "S15-1 She died on 4 July 1934":"on 4 July 1934 是时间状语，中文“1934年7月4日，她死于”时间必须放到句首",
 "S16-2 in lead-lined boxes at the Nat":"at the National Library of France 是后置定语，修饰 boxes，中文“法国国家图书馆的铅衬盒子里”定语必须提前"},
"短语":{
 "S2 Eager … to":"不是搭配：to 是不定式符号，引出 pursue formal study 作 eager 的补足语，eager 单独就是“渴望的”",
 "S2 pursue … to":"不是搭配：to 属于 emigrated to Paris，和 pursue 无关",
 "S2 emigrated … to":"不是搭配：emigrate 本身就是“移居国外”，to 只引出目的地（巴黎），中文“移居巴黎”已译出",
 "S2 enrolling … at":"不是搭配：enrol 本身就是“注册入学”，at 只引出学校（索邦大学），中文“注册入读索邦大学”已译出",
 "S6 tonnes … of":"不是搭配：of pitchblende 说明是什么东西的吨数，tonne 单独就是“吨”",
 "S6 recovered … of":"不是搭配：of 属于 a tenth of a gram，和 recovered 无关",
 "S6 gram … of":"不是搭配：of radium chloride 说明是什么东西的克数，gram 单独就是“克”",
 "S16 preserved … of":"不是搭配：of 属于 the National Library of France，和 preserved 无关"}}
CONF["读音"]={"Sk":{"读音":"skwɔdˈɔfskə","整句读法已核实":True,"依据":"不是单独的词：Skłodowska 里的 ł 不在读音核对的字母范围，被切成 Sk + odowska；整词已写读音改正 skwɔdˈɔfskə（英文维基波兰语原名 [skwɔˈdɔfska]），整句音标里已是 skwɔdˈɔfskə"},
 "odowska":{"读音":"skwɔdˈɔfskə","整句读法已核实":True,"依据":"同 Sk：Skłodowska 被 ł 切开的后半截；整词读音已改正并核实"}}
CONF["停顿位置"]={
 "S5 December, / radium. @7.775":"2026-11-04 逐 1.5 ms 实测（S5 w）：December 的 ɚ 7.57–7.68（400–1k Hz 主导，-22～-30 dB），7.685–7.755 衰减到 -50 dB；7.7685–7.7775 是 -66～-102 dB 的静音低谷（7.773 最低），7.779 起 radium 的 /ɹ/（低频主导，-47→-30 dB），7.865 起 eɪ。插入点 7.775 落在静音低谷里、/ɹ/ 起音前 4 ms，正好在两词之间",
 "S8 insistence, / the @4.415":"2026-11-04 逐 5 ms 实测（S8 w）：insistence 的 /s/ 到 4.215（-26～-38 dB），4.22–4.245 衰减到 -55～-62 dB，4.25–4.35 是 -50～-57 dB 的 /s/ 尾气；4.37–4.435 是 -60～-71 dB 静音（4.41 -71 dB 最低）；4.44 起 the 的 /ð/（低频主导，-46→-23 dB）。插入点 4.415 落在静音里、/ð/ 前 25 ms，在两词之间",
 "S12 Undeterred, / she @0.713":"2026-11-04 逐 2 ms 实测（S12 w）：Undeterred 的 ɚ 到 0.695（低频主导），0.706 /d/ 除阻（重心 2.9 kHz），0.708–0.714 低谷（0.712 -49 dB），0.716 起 she 的 /ʃ/（2.5 kHz 以上占 -0.1～-0.4 dB、重心 3.6–5.1 kHz）。程序原插 0.900 落在 she 和 collected 之间（错），改用停顿插入点插 /d/→/ʃ/ 交界 0.7125（过零点）"}
CONF["非人声"]={
"19.04–19.05s": {
"配音指纹": "fd08c47cc4a4",
"词头": "p",
"依据": "2026-11-04 逐 2.5 ms 实测（S2 w）：to 的 ə 3.11–3.165 衰减到 -55 dB，3.17–3.185 -58～-59 dB 是 /p/ 闭塞，3.19–3.205 是 -45～-53 dB、低频占 -1 dB、周期 0.03 的闭塞内气流，3.21 起 Paris 的 /p/ 爆破（-22 dB、重心 3.4 kHz）；是 Paris 的 /p/",
"实测": {
"最响dB": -46.4,
"重心Hz": 1853,
"周期": 0.0,
"低频dB": -0.7
}
},
"31.73–31.77s": {
"配音指纹": "fd08c47cc4a4",
"词尾": "p",
"依据": "2026-11-04 逐 2.5 ms 实测（S3 w）：句末 partnership 的 ɪ 到 7.875 衰减，7.89–7.935 是 -58～-69 dB 的 /p/ 闭塞，7.94–7.975 是 -36～-52 dB、重心 1.4–2.4 kHz 的爆破，之后衰减到 -65 dB 以下；是 partnership 的词尾 /p/ 除阻",
"实测": {
"最响dB": -32.0,
"重心Hz": 1915,
"周期": 0.19,
"低频dB": -11.4
}
},
"36.12–36.24s": {
"配音指纹": "fd08c47cc4a4",
"词尾": "z",
"依据": "2026-11-04 逐 2.5 ms 实测（S4 w）：rays 的 eɪ 之后 3.085–3.27 是 -22～-50 dB、低频占 -1～-11 dB、周期 0.1–0.38、重心 2.3–4.6 kHz 的气嗓过渡，紧接 3.275 起词尾 /z/（重心 5–5.8 kHz），中间没有 -55 dB 低谷；在词中间（eɪ 和 z 之间），分号停顿在后面 3.425–3.85，不是吸气",
"实测": {
"最响dB": -35.1,
"重心Hz": 3387,
"周期": 0.25,
"低频dB": -1.7
}
},
"36.16–36.20s": {
"配音指纹": "fd08c47cc4a4",
"词尾": "z",
"依据": "2026-11-04 同 36.12–36.24s（S4 rays 词中 eɪ→z 的气嗓过渡），低频占 -1.4 dB、周期 0.47，是嗓音",
"实测": {
"最响dB": -35.8,
"重心Hz": 2869,
"周期": 0.47,
"低频dB": -1.4
}
},
"40.01–40.02s": {
"配音指纹": "fd08c47cc4a4",
"依据": "2026-11-04 逐 2.5 ms 实测（S4 w）：radioactivity 中 7.07 ɪ 衰减，7.075–7.09 是 /v/ 擦音，7.095–7.105 是 -51～-53 dB、低频占 -1～-3 dB 的浊音条，7.11–7.145 -61～-70 dB 闭塞，7.15 起 /t/ 除阻（重心 5.5–6 kHz）；是 radioactivity 里 /t/ 闭塞前的浊音条，词中",
"实测": {
"最响dB": -49.3,
"重心Hz": 2225,
"周期": 0.0,
"低频dB": -2.6
}
},
"40.43–40.52s": {
"配音指纹": "fd08c47cc4a4",
"依据": "2026-11-04 逐 2.5 ms 实测（S4 w）：句末 radioactivity 的 /i/ 7.435–7.51（-14～-46 dB、周期 0.47–0.5），7.515–7.60 是 -36～-55 dB、周期 0.2–0.49、低频 -2～-15 dB 的元音收尾，平滑衰减到 7.64 -87 dB；是词尾元音 /i/ 的衰减",
"实测": {
"最响dB": -35.6,
"重心Hz": 3451,
"周期": 0.25,
"低频dB": -2.2
}
},
"40.46–40.48s": {
"配音指纹": "fd08c47cc4a4",
"依据": "2026-11-04 同 40.43–40.52s（S4 radioactivity 词尾 /i/ 衰减），周期 0.44，是嗓音",
"实测": {
"最响dB": -36.0,
"重心Hz": 3464,
"周期": 0.44,
"低频dB": -1.7
}
},
"62.06–62.17s": {
"配音指纹": "fd08c47cc4a4",
"词尾": "d",
"依据": "2026-11-04 逐 2.5 ms 实测（S6 w）：句末 chloride 的 aɪ 11.27–11.31（-27～-33 dB），11.32–11.46 是 -36～-48 dB、低频 -1～-17 dB、周期 0.11–0.42 的元音收尾，11.47 -55 dB 进 /d/ 闭塞，11.48 /d/ 除阻（-26 dB、重心 2 kHz），11.54 衰减到 -69 dB；在词中间（aɪ 和 d 之间）",
"实测": {
"最响dB": -36.5,
"重心Hz": 3141,
"周期": 0.2,
"低频dB": -3.6
}
},
"62.12–62.15s": {
"配音指纹": "fd08c47cc4a4",
"词尾": "d",
"依据": "2026-11-04 同 62.06–62.17s（S6 chloride 词中 aɪ→d 的元音收尾），低频占 -1.5 dB、周期 0.40，是嗓音",
"实测": {
"最响dB": -36.5,
"重心Hz": 2875,
"周期": 0.4,
"低频dB": -1.5
}
},
"62.15–62.17s": {
"配音指纹": "fd08c47cc4a4",
"词尾": "d",
"依据": "2026-11-04 同 62.06–62.17s（S6 chloride aɪ 收尾进 /d/ 闭塞），低频占 -2.0 dB、周期 0.36，是嗓音",
"实测": {
"最响dB": -37.7,
"重心Hz": 1417,
"周期": 0.36,
"低频dB": -2.0
}
},
"71.53–71.66s": {
"配音指纹": "fd08c47cc4a4",
"词尾": "z",
"依据": "2026-11-04 逐 2.5 ms 实测（S7 w）：recognised 的 aɪ 8.205–8.235，8.245–8.40 是 -34～-48 dB、低频 -1～-15 dB、重心 1.7–3.7 kHz 的气嗓过渡，紧接 8.405 起词尾 /z/（重心 5 kHz 以上），中间没有 -55 dB 低谷；在词中间（aɪ 和 z 之间）",
"实测": {
"最响dB": -36.1,
"重心Hz": 3095,
"周期": 0.23,
"低频dB": -4.8
}
},
"71.77–71.83s": {
"配音指纹": "fd08c47cc4a4",
"词尾": "d",
"依据": "2026-11-04 逐 2.5 ms 实测（S7 w）：句末 recognised 的 /z/ 到 8.49（重心 5.2–5.5 kHz），8.50–8.52 是 -57～-64 dB 的 /d/ 闭塞，8.53–8.57 是 -33～-54 dB、重心 2.2–3.6 kHz 的 /d/ 爆破，8.58 起衰减到 -65 dB 以下；是 recognised 的词尾 /d/ 除阻（K165）",
"实测": {
"最响dB": -30.9,
"重心Hz": 3277,
"周期": 0.26,
"低频dB": -13.0
}
},
"82.31–82.33s": {
"配音指纹": "fd08c47cc4a4",
"依据": "2026-11-04 逐 2.5 ms 实测（S9 w）：six 的 ɪ 1.98–2.02，2.03–2.08 是 -39～-59 dB、低频占 -0～-2 dB、周期 0.13–0.36 的元音收尾进 /k/ 闭塞，2.09 -63 dB 闭塞，2.10 /k/ 爆破、之后 /s/；是 six 的 ɪ→k，词中",
"实测": {
"最响dB": -50.6,
"重心Hz": 3497,
"周期": 0.0,
"低频dB": -1.0
}
},
"90.83–90.84s": {
"配音指纹": "fd08c47cc4a4",
"依据": "2026-11-04 逐 2.5 ms 实测（S10 w）：successor 的词尾 ɚ 4.285–4.40 是 -27～-50 dB、低频 -2～-19 dB、周期 0.1–0.45、重心 0.8–1.9 kHz 的元音，平滑衰减到 4.415 -61 dB；是 successor 的词尾 ɚ",
"实测": {
"最响dB": -34.9,
"重心Hz": 1370,
"周期": 0.4,
"低频dB": -1.6
}
},
"93.42–93.50s": {
"配音指纹": "fd08c47cc4a4",
"依据": "2026-11-04 逐 2.5 ms 实测（S10 w）：句末 professor 的 ɚ 6.88–7.04 是 -21～-54 dB、低频 -3～-20 dB、周期 0.14–0.41、重心 0.8–1.8 kHz 的元音，平滑衰减到 7.06 -80 dB；是词尾 ɚ 的衰减",
"实测": {
"最响dB": -36.6,
"重心Hz": 1431,
"周期": 0.26,
"低频dB": -2.2
}
},
"93.45–93.47s": {
"配音指纹": "fd08c47cc4a4",
"依据": "2026-11-04 同 93.42–93.50s（S10 professor 词尾 ɚ），低频占 -2.1 dB、周期 0.39，是嗓音",
"实测": {
"最响dB": -36.6,
"重心Hz": 1413,
"周期": 0.39,
"低频dB": -2.1
}
},
"99.02–99.03s": {
"配音指纹": "fd08c47cc4a4",
"依据": "2026-11-04 逐 2.5 ms 实测（S11 w）：erupted 的 ʌ 到 4.30 衰减，4.315–4.335 -64～-68 dB 是 /p/ 闭塞，4.345–4.355 是 -47～-56 dB、重心 2.0–3.8 kHz 的 /p/ 除阻，4.365–4.385 -61～-66 dB 是 /t/ 闭塞，4.395 /t/ 爆破；是 erupted 里 pt 的 /p/ 除阻，词中",
"实测": {
"最响dB": -32.8,
"重心Hz": 3575,
"周期": 0.0,
"低频dB": -22.9
}
},
"101.33–101.42s": {
"配音指纹": "fd08c47cc4a4",
"依据": "2026-11-04 逐 2.5 ms 实测（S11 w）：句末 away 的 eɪ 6.645–6.80 是 -28～-54 dB、低频 -3～-18 dB、周期 0.09–0.41、重心 2.3–4.4 kHz（eɪ 第二共振峰高）的元音，平滑衰减到 6.865 -135 dB；是词尾 eɪ 的衰减",
"实测": {
"最响dB": -35.8,
"重心Hz": 3272,
"周期": 0.26,
"低频dB": -5.2
}
},
"111.29–111.31s": {
"配音指纹": "fd08c47cc4a4",
"依据": "2026-11-04 逐 2.5 ms 实测（S13 w）：sciences 的词尾 /z/ 到 1.73（重心 4.3→2.8 kHz），1.74–1.78 是 -46～-53 dB、低频占 -2～-8 dB、周期 0.16–0.29 的浊音过渡，1.79 起 remains 的 /ɹ/（-30 dB、重心 0.5 kHz）；是 z→ɹ 之间的浊音，连着 remains 的 /ɹ/",
"实测": {
"最响dB": -32.2,
"重心Hz": 1216,
"周期": 0.27,
"低频dB": -2.2
}
},
"143.91–144.00s": {
"配音指纹": "fd08c47cc4a4",
"依据": "2026-11-04 逐 2.5 ms 实测（S16 w）：garments 的 /n/ 11.50–11.57（-24～-30 dB、低频主导），11.58–11.66 是 -38～-57 dB、低频 -3～-21 dB、周期 0.27–0.45 的鼻音收尾，11.67 -65 dB 进 /t/ 闭塞，11.68 /t/ 爆破、11.70 起 /s/；在词中间（n 和 ts 之间）",
"实测": {
"最响dB": -35.5,
"重心Hz": 2306,
"周期": 0.33,
"低频dB": -4.3
}
},
"118.21–118.22s": {
"配音指纹": "fd08c47cc4a4",
"词头": "p",
"依据": "2026-11-04 逐 2.5 ms 实测（S14 w）：stationary 的 /i/ 4.65–4.685 衰减（-16→-35 dB），4.69–4.74 是 -47～-60 dB、低频占 -1～-2 dB 的浊音条进 /p/ 闭塞，4.745 -52 dB，4.75 起 posts 的 /p/ 爆破（-16 dB、重心 2.9 kHz）；是 posts 的 /p/ 闭塞，词头",
"实测": {
"最响dB": -53.3,
"重心Hz": 1962,
"周期": 0.0,
"低频dB": -0.5
}
}
}
CONF["删除段"]={
"S5 raw 5.5950-5.9350": "2026-11-04 逐 10 ms 实测（独立复核原始合成 S5）：motherland, 的 /d/ 到 5.58 衰减到 -58.7 dB；5.59–5.90 由 -74 渐升到 -51 dB、低频只占 -6～-17 dB、重心 1.0–1.8 kHz、周期 ≤0.35，是吸气（删掉最响 -51 dB 即此，re rmsPk -38.8）；5.93 -63 dB，5.94 起 and 的起音，and 不动",
"S6 raw 4.3550-4.7550": "2026-11-04 逐 10 ms 实测（独立复核原始合成 S6）：pitchblende, 的 /d/ 到 4.34 衰减，4.35–4.37 -69～-75 dB；4.38–4.69 由 -66 渐升到 -47 dB、低频 -5～-20 dB、重心 1.2–1.7 kHz、周期 ≤0.33，是吸气；4.70–4.74 是 -55～-65 dB 的声门预发声，4.76 起 a 的元音（-39→-18 dB）不动",
"S7 raw 2.4450-2.7699": "2026-11-04 逐 10 ms 实测（独立复核原始合成 S7）：1903 的 /iː/ 到 2.43 衰减到 -60 dB；2.46–2.75 是 -52～-64 dB、低频 -4～-15 dB、重心 0.8–2.0 kHz 的吸气；2.76 -67 dB，2.79 起 she 的 /ʃ/（重心 4.1 kHz）不动",
"S9 raw 2.3050-2.6150": "2026-11-04 逐 10 ms 实测（独立复核原始合成 S9）：1906 的 /ks/ 到 2.27；2.29–2.55 由 -65 渐升到 -50 dB、低频 -5～-15 dB、重心 0.9–1.3 kHz 的吸气；2.56–2.61 -58～-70 dB，2.62 起 a 的元音（-48→-15 dB）不动",
"S8 raw 4.2522-4.4450": {
"类型": "紧贴词尾的非人声",
"配音指纹": "fd08c47cc4a4",
"依据": "2026-11-04 逐 5 ms 实测（S8 w，非人声区间 4.242208–4.414375 紧贴词尾）：insistence 的 /s/ 到 4.215（重心 5.3→3.6 kHz），4.225–4.235 衰减，4.24 -54 dB 低谷；4.25–4.365 是 -37～-52 dB、低频 -4～-17 dB、重心 1.0–1.9 kHz 的吸气，4.37–4.405 是 -48～-52 dB 低频主导的嘟囔，和 the 之间隔着 4.41–4.44 的 -54～-61 dB 低谷；/s/ 与吸气之间没有 -55 dB 低谷，前头切在 4.242208 过零点，/s/ 本身不动；4.445 起 the 的 /ð/ 不动"
},
"S10 raw 1.2675-1.4300": {
"类型": "紧贴词尾的非人声",
"配音指纹": "fd08c47cc4a4",
"依据": "2026-11-04 逐 5 ms 实测（S10 w，非人声区间 1.2575–1.418042 紧贴词尾）：November 的 ɚ 到 1.255 衰减（低频主导，-41～-52 dB）；1.26–1.40 是 -42～-56 dB、低频 -3～-10 dB、重心 0.9–1.7 kHz 的吸气（无标点处）；1.405–1.42 -56～-59 dB，1.425 起 she 的 /ʃ/ 不动；ɚ 与吸气之间没有 -55 dB 低谷，前头切在 1.2575 过零点"
},
"S11 raw 1.8723-2.0050": {
"类型": "紧贴词尾的非人声",
"配音指纹": "fd08c47cc4a4",
"依据": "2026-11-04 逐 5 ms 实测（S11 门前声音，非人声区间 1.76225–1.889208 紧贴词尾）：eleven 的 /n/ 1.70–1.76 由 -20 衰减到 -52 dB；1.765–1.875 是 -45～-53 dB、低频占 -6 dB、重心 1.2 kHz 的吸气；1.88–1.895 -57～-62 dB，1.90 起 a 的元音不动；/n/ 与吸气之间没有 -55 dB 低谷，前头切在 1.76225 过零点"
},
"S14 raw 5.2190-5.5100": {
"类型": "紧贴词尾的非人声",
"配音指纹": "fd08c47cc4a4",
"依据": "2026-11-04 逐 5 ms 实测（S14 门前声音，非人声区间 5.218958–5.502333 紧贴词尾）：posts 的 /s/ 到 5.21（重心 5.1–5.9 kHz），5.215–5.22 衰减到 -53～-56 dB；5.225–5.435 是 -39～-52 dB、低频 -5～-15 dB、重心 1.2–1.9 kHz 的吸气（无标点处），5.44–5.50 是 -45～-58 dB 低频主导的嘟囔，和 that 之间隔着 5.50–5.51 的 -60～-64 dB 低谷；/s/ 与吸气之间没有 -55 dB 低谷，前头切在 5.218958 过零点，/s/ 本身不动；5.515 起 that 的 /ð/ 不动"
},
"S16 raw 2.2300-2.5412": {
"类型": "紧贴词头的非人声",
"配音指纹": "fd08c47cc4a4",
"依据": "2026-11-04 逐 10 ms 实测（独立复核原始合成 S16）：radioactive, 的 /v/ 到 2.21 衰减，2.22–2.23 -61～-68 dB；2.24–2.50 由 -64 渐升到 -47 dB、低频 -5～-16 dB、重心 1.0–1.7 kHz 的吸气；2.51–2.54 是 -55～-58 dB 的声门预发声，紧接 2.55 起 are 的元音（-47→-13 dB），吸气和 are 之间没有 -55 dB 低谷，后头切在过零点，are 的元音本身不动"
}
}
CONF["响度骤降"]={
"20.4–20.9s": {
"配音指纹": "fd08c47cc4a4",
"低": 6.4,
"句子": "S2 …she emigrated to Paris in 1891,（ninety-one, 逗号前收尾）",
"依据": "2026-11-04 实测 a.wav 逐 50 ms：20.00–20.30 是 -20～-22 dB 的元音，20.40 一下 -30 dB 重心 5.2 kHz 是 /w/ 前的送气，20.45–20.65 -25～-28 dB（one 的 ʌ、/n/），20.70–20.80 平滑降到 -34→-44 dB，20.85 -61 dB，20.90 起逗号停顿静音；是逗号前 one 的自然降调收尾，没有突然掉音、发闷或吞音",
"用户原话": "不要总是请我听，请我定，按照你认为最正确的方式来做，你拥有最高决策权，我跟你说过。你拥有最高决策权，你拥有最高决策权，你是总负责人。所以说你按照你认为最好的方式来定，我可能有时候不在，没有办法迅速决定，所以说你来帮我做最好的决定，但是前提是这个决定他能够是最好的。（主会话按总负责人授权接受，2026-11-04）"
},
"71.1–71.6s": {
"配音指纹": "fd08c47cc4a4",
"低": 6.7,
"句子": "S7 …the first woman so recognised.（句末）",
"依据": "2026-11-04 实测 a.wav 逐 50 ms：70.80–71.00 是 -21～-22 dB 的元音，71.05–71.20 -29～-34 dB 是 /ɡn/ 的闭塞和鼻音，71.25–71.35 -24～-28 dB 是 aɪ，71.40–71.60 平滑降到 -33→-55 dB（aɪ 的气嗓收尾），71.65–71.70 词尾 /z/（-32～-37 dB、重心 4.6 kHz），71.75 /d/ 除阻，71.85 起静音；是句末 recognised 的自然降调，词尾 z、d 都在",
"用户原话": "不要总是请我听，请我定，按照你认为最正确的方式来做，你拥有最高决策权，我跟你说过。你拥有最高决策权，你拥有最高决策权，你是总负责人。所以说你按照你认为最好的方式来定，我可能有时候不在，没有办法迅速决定，所以说你来帮我做最好的决定，但是前提是这个决定他能够是最好的。（主会话按总负责人授权接受，2026-11-04）"
},
"137.0–137.5s": {
"配音指纹": "fd08c47cc4a4",
"低": 6.1,
"句子": "S16 …are preserved in lead-lined boxes…",
"依据": "2026-11-04 实测 a.wav 逐 50 ms：136.75–136.90 是 -18～-22 dB 的元音，137.00–137.10 -26～-32 dB、重心 4.2–5.6 kHz 是 preserved 的 /z/，137.15–137.20 -28～-31 dB 的 ɜː/v，137.25–137.30 -31～-33 dB、重心 3.2 kHz 的 /d/ 除阻和擦音，137.35 -25 dB 的 in，137.45 -43 dB 的 /l/ 前闭合，137.50 起 -24～-25 dB 的 lead；这一段擦音、塞音多，元音少，响度低是语音本身，没有发闷或吞音",
"用户原话": "不要总是请我听，请我定，按照你认为最正确的方式来做，你拥有最高决策权，我跟你说过。你拥有最高决策权，你拥有最高决策权，你是总负责人。所以说你按照你认为最好的方式来定，我可能有时候不在，没有办法迅速决定，所以说你来帮我做最好的决定，但是前提是这个决定他能够是最好的。（主会话按总负责人授权接受，2026-11-04）"
}
}
CONF["们"]={"S6-1 **(leaky)棚屋里，他们**":"们不在加粗里，是代词“他们”（they，指居里夫妇），沿用文章定稿；被报出只因前面 **漏雨的**(leaky) 与“他们”在同一块里"}
G["S7 so recognised"]="对齐不了：the first woman so recognised 中文“第一位获此认可的女性”（用户原话），so recognised 是后置定语，中文“获此认可的”必须提到“女性”前，“女性”随之放最后"
G["S16 in lead-lined boxes at the National Library of France"]="对齐不了：at the National Library of France 是后置定语，修饰 boxes，中文“法国国家图书馆的铅衬的盒子里”定语必须提前；lead-lined 只标 lead（用户原话），lined 化在“衬的”里"
CONF.setdefault("短语",{})["S16 in … lead"]="不是搭配：in 属于 in lead-lined boxes（在……盒子里），lead 只修饰 lined，in lead 不是固定用法"
out={"no":"49","title_en":"The Woman Who Won Two Nobels","title_zh":"两度摘得诺奖的女人","title_fx":{"hl":["Two","Nobels"],"ghost":[]},"sentences":[],"核对确认":CONF,"结尾解说":"简述",
     "停顿插入点":{"S12":{"1":[0.7125,"交界"]}},
     "非人声区间":{"S8":[[4.242208,4.414375,"紧贴词尾"]],"S10":[[1.2575,1.418042,"紧贴词尾"]],"S11":[[1.76225,1.889208,"紧贴词尾"]],"S14":[[1.377208,1.642042],[5.218958,5.502333,"紧贴词尾"]],"S17":[[1.938,2.136042]]},
     "allow_clash":["radioactive"],
     "高亮按实际开口":True,"高亮开口门槛":40,
     "术语":{"Marie Curie":"玛丽·居里","Maria Skłodowska":"玛丽亚·斯克沃多夫斯卡","Warsaw":"华沙","Paris":"巴黎","Sorbonne":"索邦大学","Pierre Curie":"皮埃尔·居里","Pierre":"皮埃尔","Henri Becquerel":"亨利·贝克勒尔","Becquerel":"贝克勒尔","Curies":"居里夫妇","Nobel":"诺贝尔","First World War":"第一次世界大战","National Library of France":"法国国家图书馆"}}
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 核对 import 生成并核对
生成并核对(S, out)
