import json,re,glob,os
# 第56篇初稿（逐词对照）：S = [(段, [chunk, ...])]，chunk = ([(英文组, 中文组), ...], 可选 note)
# 2026-11-07 重点词中文沿用文章定稿（铁律），只按《翻译风格》调格式；不用破折号（T36）；形容词的“的”进粗体（T38）。
S=[
(1,[[[("Charles Darwin **disembarked** from HMS Beagle in October 1836.","1836年10月，查尔斯·达尔文从小猎犬号上**登岸**(disembarked)。")],
     "（disembark from…：从（船、飞机）上下来；\nHMS Beagle：英国皇家海军舰船小猎犬号）"]]),
(1,[[[("In September 1838","1838年9月，"),("he","他"),("began","开始"),("**formulating**","**构想并明确表述**(formulating)"),("the **principle** of natural **selection**:","自然**选择**(selection)的**原理**(principle)：")],
     "（began formulating：begin doing，开始做某事；\nthe principle of natural selection：of 结构，自然选择的原理）"],
    [[("individuals better **adapted to** their **surroundings**","**对**(adapted to)**周围环境**(surroundings)**适应**(adapted to)得更好的个体"),("survive","存活下来，"),("and","并"),("**pass on**","将**传递**(pass on)"),("their","他们自身"),("**hereditary**","**遗传的**(hereditary)"),("**traits**.","**性状**(traits)（给后代）。")],
     "（better adapted to…：过去分词短语作后置定语，\n修饰 individuals；be adapted to…：适应……；\npass on：传递）"]]),
(1,[[[("By 1844","到1844年，"),("he","他"),("had **composed**","已**撰写了**(composed)"),("a 230-page","一份230页的"),("**manuscript**,","**手稿**(manuscript)，")],
     "（By 1844：到1844年为止；\nhad composed：过去完成时，表示到那时已经完成）"],
    [[("yet","却"),("kept it","一直"),("**unpublished**,","**未予发表**(unpublished)，"),("**cautiously**","**谨慎地**(cautiously)"),("**amassing**","**积累着**(amassing)"),("evidence.","证据。")],
     "（keep it unpublished：keep + 宾语 + 补语，使它保持未发表；\ncautiously amassing evidence：现在分词短语作伴随状语）"]]),
(2,[[[("In February 1858,","1858年2月，"),("two decades after Darwin's first insight,","达尔文最初的洞察出现后的二十年，")],
     "（two decades after…：插入的时间说明，\n补充这时离达尔文最初的洞察已有多久）"],
    [[("Alfred Russel Wallace, a **naturalist**","**博物学家**(naturalist)阿尔弗雷德·拉塞尔·华莱士"),("**afflicted by** fever in the Malay Archipelago,","在马来群岛**饱受**(afflicted by)热病**的折磨**(afflicted by)，")],
     "（a naturalist…：同位语，说明 Wallace；\nafflicted by…：过去分词短语作后置定语，\nbe afflicted by：饱受……的折磨）"],
    [[("**independently**","**独自一人**(independently)"),("**conceived**","**构想出**(conceived)了"),("the same","同一个"),("idea.","想法。")]]]),
(2,[[[("His","华莱士这篇"),("**concise**","**简明的**(concise)"),("essay","文章"),("reached Darwin on 18 June 1858.","于1858年6月18日到达了达尔文的手里。")],
     "（His：指华莱士；reach sb：送到某人手中）"]]),
(2,[[[("Its","文中的"),("argument","论证"),("**paralleled** Darwin's own almost **precisely**;","**与**(paralleled)达尔文自己的几乎**完全**(precisely)**一样**(paralleled)；")],
     "（Its：指华莱士的文章；paralleled：与……极其相似；\nDarwin's own：达尔文自己的论证，own 后面省略了 argument）"],
    [[("he told","达尔文告诉"),("Charles Lyell","查尔斯·莱尔，"),("he","自己"),("had never","从未"),("seen","见过"),("a more","比这更"),("**remarkable**","**惊人的**(remarkable)"),("**coincidence**.","**巧合**(coincidence)。")],
     "（he had never seen…：宾语从句，省略了 that；\nhad never seen：过去完成时）"]]),
(2,[[[("His claim to **priority**","他对**优先权**(priority)的主张"),("seemed","似乎"),("**threatened**.","**受到了威胁**(threatened)。")],
     "（claim to…：对……的主张、要求；\nseem + 过去分词：似乎被……）"]]),
(3,[[[("Lyell","莱尔"),("and","和"),("the **botanist**","**植物学家**(botanist)"),("Joseph Hooker","约瑟夫·胡克"),("**arranged for**","**安排**(arranged for)"),("both","这两篇"),("papers","论文，")],
     "（arrange for sth to be done：安排、促成某事被做）"],
    [[("to be read **simultaneously** at the Linnean Society, a scientific **institution** in London, on 1 July 1858.","于1858年7月1日在伦敦的科学**机构**(institution)林奈学会上被**同时**(simultaneously)宣读。")],
     "（to be read：不定式的被动式；\na scientific institution in London：同位语，\n说明 the Linnean Society）"]]),
(3,[[[("Neither author","两位作者都没有"),("attended","出席"),("the **proceedings**.","这场**会议**(proceedings)。")],
     "（Neither…：两者都不；\nproceedings：在学术语境下，\n特指学会的会议、活动议程或会议记录）"]]),
(3,[[[("Wallace","华莱士"),("was abroad,","身在海外，"),("and Darwin","达尔文则"),("was **grieving**:","处于**哀痛**(grieving)之中：")],
     "（was grieving：过去进行时，当时正处于悲痛中；\ngrieve 指因失去某人（尤指亲人离世）而承受极度的悲伤与痛苦（即哀悼））"],
    [[("**scarlet**","**猩红**(scarlet)"),("fever","热"),("had killed his **infant** son on 28 June.","在6月28日夺去了他**幼子**(infant)的生命。")],
     "（scarlet fever：猩红热；\nhad killed：过去完成时，发生在会议之前）"]]),
(3,[[[("The **compromise**,","这一**折中办法**(compromise)"),("struck without Wallace,","在华莱士未参与的情况下达成，")],
     "（struck without Wallace：过去分词短语作后置定语，\n修饰 compromise；strike a compromise：达成折中办法）"],
    [[("may have kept **rivalry** over **precedence** at bay.","或许避免了围绕**先后次序**(precedence)的**竞争**(rivalry)。")],
     "（may have done：对过去的推测；\nkeep sth at bay：使……无法逼近，避免……；\nrivalry over…：围绕……的竞争）"]]),
(4,[[[("The papers'","这些论文"),("**publication** on 20 August 1858","于1858年8月20日的**发表**(publication)，"),("met","遭遇了"),("a **muted**","一个**很不热烈的**(muted)"),("**reception**.","**反响**(reception)。")],
     "（The papers' publication：名词化结构，\n相当于 the papers were published；\nmeet a … reception：遭遇……的反响）"]]),
(4,[[[("In May 1859","1859年5月，"),("the Society's","学会"),("president","会长"),("**remarked** in his **yearly** address","在**年度**(yearly)致辞中**评论**(remarked)说，")],
     "（the Society：指林奈学会；\nremark that…：说到、评论……）"],
    [[("that the year","这一年"),("had been","一直"),("**barren of**","**毫无**(barren of)"),("**revolutionary**","**革命性的**(revolutionary)"),("discoveries.","发现。")],
     "（that…：宾语从句，作 remarked 的宾语；\nbe barren of…：缺乏……，毫无……）"]]),
(4,[[[("The **sensation**","这场**轰动**(sensation)"),("came on 24 November 1859","于1859年11月24日"),("with Darwin's","随着达尔文的"),("**treatise**,","**专著**(treatise)"),("**On the Origin of Species**:","**《物种起源》**(On the Origin of Species)到来：")],
     "（The sensation came with…：轰动随着……到来；\nOn the Origin of Species：同位语，说明 treatise，\n即书名《物种起源》）"],
    [[("booksellers","书商们"),("had","已"),("**subscribed for**","**订购了**(subscribed for)"),("every copy of its first **impression**,","该书首**次印刷**(impression)的每一册，"),("1,250 in all.","总计1,250册。")],
     "（subscribe for…：订购……；\nits first impression：该书的首次印刷；in all：总计）"]]),
(5,[[[("Wallace","华莱士"),("had **readily**","早已**欣然**(readily)"),("**signified**","**表明了**(signified)"),("his **acceptance**","**接受**(acceptance)的态度，"),("in October 1858,","那是在1858年10月；")],
     "（had signified：过去完成时，表示早在那之前；\nsignify one's acceptance：表示接受）"],
    [[("**assuring** Hooker in a **cordial** letter","他在一封**亲切的**(cordial)信中**向**(assuring)胡克**保证**(assuring)，"),("of his","自己"),("**satisfaction** with the **arrangement**.","对这一**安排**(arrangement)感到**满意**(satisfaction)。")],
     "（assuring…：现在分词短语作伴随状语；\nassure sb of sth：向某人保证某事；\nsatisfaction with…：对……满意）"]]),
(5,[[[("In 1889","1889年，"),("he","他"),("published","出版了"),("a **lengthy**","一部**长篇的**(lengthy)"),("**exposition**","**阐述**(exposition)"),("of the idea","解释这一思想，"),("and","并"),("**entitled** it","**将**(entitled)其**命名为**(entitled)"),("Darwinism.","《达尔文主义》。")],
     "（an exposition of…：对……的阐述；\nentitle A B：将 A 命名为 B）"]]),
(5,[[[("Wallace","华莱士"),("never","从未"),("**named** the theory **after** himself.","**用**(named after)自己的名字**为**(named after)这一理论**命名**(named after)。")],
     "（name A after B：以 B 的名字给 A 命名）\n"
     "（简述：1836年10月，达尔文从小猎犬号上登岸；1838年9月开始提出自然选择的原理，\n"
     "1844年写成230页的手稿，却一直未予发表。1858年2月，华莱士在马来群岛独立构想出同一个想法，\n"
     "他的文章6月18日寄到达尔文手中，论证与达尔文的几乎完全相合，达尔文的优先权似乎受到威胁。\n"
     "7月1日，莱尔和胡克促成两篇论文在林奈学会同时宣读，两位作者都没有出席：\n"
     "华莱士身在海外，达尔文的幼子6月28日死于猩红热。论文8月刊出，反响平淡；\n"
     "1859年11月24日《物种起源》问世，引起轰动，第一次印刷的1,250册被书商全部认购。\n"
     "华莱士1858年10月就欣然表示接受这一安排，1889年把阐述这一思想的著作定名为《达尔文主义》，\n"
     "从未用自己的名字为这一理论命名。）"]]),
]
G={
 "S1 Charles Darwin disembarked from HMS Beagle in October 1836":"对齐不了：in October 1836 是时间状语，中文“1836年10月”必须放到句首；disembark from… 中文“从……上登岸”，“登岸”必须放到船名后面",
 "S2 the principle of natural selection":"对齐不了：the principle of… 是 of 结构，中文“自然选择的原理”，“原理”必须放到最后",
 "S2 individuals better adapted to their surroundings":"对齐不了：better adapted to… 是过去分词短语作后置定语，修饰 individuals，中文“对环境适应得更好的个体”定语必须提前",
 "S2 and pass on their hereditary traits":"对齐不了：pass on… 中文“把……传递下去”，“传递下去”必须放到宾语后面",
 "S4 Alfred Russel Wallace, a naturalist":"对齐不了：a naturalist 是同位语，中文“博物学家阿尔弗雷德·拉塞尔·华莱士”身份必须放到人名前",
 "S4 afflicted by fever in the Malay Archipelago":"对齐不了：in the Malay Archipelago 是地点状语，中文“在马来群岛饱受热病的折磨”地点必须放到动词前，热病又夹在“饱受……的折磨”中间",
 "S5 reached Darwin on 18 June 1858":"对齐不了：on 18 June 1858 是时间状语，中文“于1858年6月18日到达了达尔文的手里”时间必须放到动词前",
 "S6 paralleled Darwin's own almost precisely":"对齐不了：paralleled… almost precisely 中文“与达尔文本人的论证几乎完全相合”，比较对象和程度必须放到动词“相合”前",
 "S6 a more remarkable coincidence":"对齐不了：a more remarkable coincidence 中文“比这更惊人的巧合”，“比这”是 more 的比较对象，必须一起放在前面",
 "S7 His claim to priority":"对齐不了：claim to priority 中文“对优先权的主张”，介词短语必须提前",
 "S8 to be read simultaneously at the Linnean Society, a scientific institution in London, on 1 July 1858":"对齐不了：时间状语 on 1 July 1858、地点状语 at the Linnean Society 和同位语 a scientific institution in London，中文“于1858年7月1日在伦敦的科学机构林奈学会同时宣读”都必须放到动词“宣读”前，整组语序倒过来",
 "S10 had killed his infant son on 28 June":"对齐不了：on 28 June 是时间状语，中文“在6月28日”必须放到动词前；kill his son 中文“夺去了他幼子的生命”，“生命”必须放到最后",
 "S4 two decades after Darwin's first insight":"对齐不了：two decades after… 中文“达尔文最初的洞察出现后的二十年”，after 引出的起算点必须放到“二十年”前，整组语序倒过来",
 "S11 struck without Wallace":"对齐不了：without Wallace 中文“在华莱士未参与的情况下”必须放到动词“达成”前",
 "S14 On the Origin of Species":"对齐不了：书名《物种起源》，不能拆",
 "S17 named the theory after himself":"对齐不了：name A after B 中文“用 B 的名字为 A 命名”，after himself 必须放到动词前，the theory 化成“为这一理论”也在动词前",
 "S11 may have kept rivalry over precedence at bay":"对齐不了：keep A at bay 中文“避免了 A”，at bay 不能单独成组；rivalry over precedence 中文“围绕先后次序的竞争”定语必须提前",
 "S12 publication on 20 August 1858":"对齐不了：on 20 August 1858 是后置的时间说明，中文“于1858年8月20日的发表”时间必须放到“发表”前",
 "S12 met a muted reception":"对齐不了：met a muted reception 中文“得到的反响却很平淡”，muted 必须改成谓语放到最后",
 "S13 remarked in his yearly address":"对齐不了：in his yearly address 是地点状语，中文“在年度致辞中谈到”必须放到动词前",
 "S14 The sensation came on 24 November 1859 with Darwin's treatise, On the Origin of Species":"对齐不了：时间状语 on 24 November 1859 和 with Darwin's treatise… 中文“1859年11月24日，达尔文的专著《物种起源》问世，引起轰动”都必须放到 sensation 前，整组语序倒过来",
 "S14 every copy of its first impression":"对齐不了：every copy of… 是 of 结构，中文“该书第一次印刷的每一册”，“每一册”必须放到最后",
 "S15 Wallace had readily signified his acceptance in October 1858":"对齐不了：in October 1858 是时间状语，中文“1858年10月”必须放到句首",
 "S15 assuring Hooker in a cordial letter":"对齐不了：in a cordial letter 是方式状语，中文“在一封亲切的信中向胡克保证”必须放到动词前",
 "S15 of his satisfaction with the arrangement":"对齐不了：satisfaction with… 中文“对这一安排感到满意”，“满意”必须放到最后",
 "S16 a lengthy exposition of the idea":"对齐不了：an exposition of… 中文“一部长篇论述阐释这一思想”，of the idea 必须化成后面的“阐释这一思想”",
 "S16 and entitled it Darwinism":"对齐不了：entitle A B 中文“将 A 定名为 B”，“为”必须放到书名前，不能拆",
 "S17 never named the theory after himself":"对齐不了：name A after B 中文“用 B 的名字为 A 命名”，after himself 必须放到动词前",
}
CONF={"合组":G,
"数字写法":{"S4-1 two":"two decades 中文“二十年”，数值相同（two decades = 20年）"},
"方向":{},
"对齐":{},
"短语":{"S1 disembarked … from":"不是搭配：from 只引出从哪条船上下来，disembarked 单独就是“登岸”",
 "S2 formulating … of":"不是搭配：of 属于 the principle of natural selection（of 结构），和 formulating 无关",
 "S2 principle … of":"不是搭配：of natural selection 是 of 结构的后置修饰（自然选择的原理），principle 单独就是“原理”",
 "S2 adapted … to":"不是搭配：to 引出适应的对象（对环境），adapted 单独就是“适应”，沿用文章定稿只标 adapted",
 "S8 arranged … to":"不是搭配：短语已整体标 arranged for（促成）；to be read 是 for 后面引出的不定式，不属于短语本身",
 "S8 for … to":"不是搭配：to be read 是 arranged for 后面的不定式宾补，for 已随 arranged for 整体标",
 "S8 institution … in":"不是搭配：in London 只说明机构在哪里，institution 单独就是“机构”",
 "S11 rivalry … over":"不是搭配：over precedence 引出竞争的内容（围绕先后次序），rivalry 单独就是“竞争”",
 "S14 treatise … on":"不是搭配：On the Origin of Species 是书名（同位语），和 treatise 无关",
 "S14 subscribed … of":"不是搭配：短语已整体标 subscribed for（认购）；of 属于 every copy of its first impression（of 结构）",
 "S15 acceptance … of":"不是搭配：of 属于后面的 assuring Hooker … of his satisfaction，和 acceptance 无关",
 "S15 assuring … of":"不是搭配：assure sb of sth 的 of 只引出保证的内容（自己对安排满意），assure 单独就是“保证”；意思“向……保证”被“胡克”隔开，“向”和“保证”两处都标 assuring（T23）",
 "S15 assuring … with":"不是搭配：with 属于 satisfaction with the arrangement（对安排满意），和 assuring 无关",
 "S15 satisfaction … with":"不是搭配：with 引出满意的对象（对这一安排），satisfaction 单独就是“满意”",
 "S16 exposition … of":"不是搭配：of the idea 是 of 结构，说明阐述的内容，exposition 单独就是“论述”"},
"同词异译":{"assuring：向/保证":"不是两种译法：assure sb 的意思“向……保证”被“胡克”隔开，“向”和“保证”是同一个意思的两部分（T23）","assuring：保证/向":"不是两种译法：assure sb 的意思“向……保证”被“胡克”隔开，“向”和“保证”是同一个意思的两部分（T23）"}}
# 对齐、方向：按组自动生成键（与核查程序同一取法），原因取 G
def _en(x): return re.sub(r"\*\*","",x).strip()
for si,(pa,chunks) in enumerate(S,1):
    for ci,ch in enumerate(chunks,1):
        for en,zh in ch[0]:
            e=_en(en); k=f"S{si} "+e.rstrip(",.;:")
            if len(e.split())>=5 and k in G: CONF["对齐"][f"S{si}-{ci} {e[:30]}"]=G[k].replace("对齐不了：","")
            z=re.sub(r"\*\*|\([^)]*\)","",zh)
            if re.search(r"\bafter\b",e):
                CONF["方向"][f"S{si}-{ci} after→{z[:12]}"]={"S4":"two decades after… 的 after 表示“在……之后”，中文“……出现后的二十年”的“后”就是从那之后算起，方向一致","S17":"name A after B 的 after 是“以……命名”的固定用法（按照），不是时间先后，中文“用自己的名字为……命名”意思一致"}[f"S{si}"]
CONF["非人声"]={"17.08–17.09s": {"配音指纹": "3f09f415a035", "实测": {"最响dB": -40.4, "重心Hz": 3467, "周期": 0.0, "低频dB": -15.8}, "词尾": "d", "依据": "2026-11-07 逐 2.5 ms 实测（dossier_56，配音指纹 3f09f415a035）：S2 w 8.095：adapted 的 -ted，/d/ 闭塞 8.07–8.09（-62～-68 dB）后一下除阻（-38 dB、重心 3.8 kHz、5 ms），8.10–8.13 又静音，8.135 起 to 的 /t/；是 adapted 词尾 /d/ 的除阻（词的一部分）"}, "22.57–22.59s": {"配音指纹": "3f09f415a035", "实测": {"最响dB": -31.0, "重心Hz": 586, "周期": 0.0, "低频dB": -2.7}, "词头": "b", "依据": "2026-11-07 逐 2.5 ms 实测（dossier_56，配音指纹 3f09f415a035）：S3 w 0.02–0.035：-52→-45→-31→-28 dB 连续升高、重心 0.4–0.9 kHz、低频占 -2 dB，0.05 起 By 的元音（-8 dB）；是 By 的 /b/ 浊音起始（词的一部分）"}, "27.43–27.45s": {"配音指纹": "3f09f415a035", "实测": {"最响dB": -37.5, "重心Hz": 2675, "周期": 0.0, "低频dB": -21.2}, "依据": "2026-11-07 逐 2.5 ms 实测（dossier_56，配音指纹 3f09f415a035）：S3 w 4.8875：manuscript 的 -script，/p/ 闭塞 4.86–4.885（-59～-71 dB）后一下除阻（-36 dB、重心 2.8 kHz），4.90–4.92 /t/ 闭塞，4.9275 /t/ 除阻（-28 dB、重心 2.7–4.2 kHz）；是 script 中 /p/ 的除阻（词的一部分）"}, "28.45–28.45s": {"配音指纹": "3f09f415a035", "实测": {"最响dB": -43.9, "重心Hz": 2839, "周期": 0.0, "低频dB": -15.7}, "依据": "2026-11-07 逐 2.5 ms 实测（dossier_56，配音指纹 3f09f415a035）：S3 w 5.905：kept 的 ɛ 衰减到 5.885（-59 dB），/p/ 闭塞 5.89–5.90，5.905 一下除阻（-42 dB、重心 3.6 kHz），5.915–5.94 /t/ 闭塞（-66～-69 dB），5.945 起 /t/ 除阻接 it；是 kept 中 /p/ 的除阻（词的一部分）"}, "29.52–29.57s": {"配音指纹": "3f09f415a035", "实测": {"最响dB": -31.7, "重心Hz": 3444, "周期": 0.12, "低频dB": -13.0}, "词尾": "t", "依据": "2026-11-07 逐 2.5 ms 实测（dossier_56，配音指纹 3f09f415a035）：S3 w 6.985–7.035：unpublished 的 /ʃ/ 6.905–6.955（重心 4.5–5.2 kHz、低频 -40～-57 dB），6.965–6.985 闭塞（-67～-70 dB），6.99 起 /t/ 除阻送气（-34→-59 dB 衰减、重心 2.4–3.5 kHz）；是 unpublished 词尾 /t/ 的除阻（词的一部分）"}, "62.45–62.52s": {"配音指纹": "3f09f415a035", "实测": {"最响dB": -35.8, "重心Hz": 2093, "周期": 0.32, "低频dB": -3.7}, "依据": "2026-11-07 逐 2.5 ms 实测（dossier_56，配音指纹 3f09f415a035）：S6 w 8.375–8.455：coincidence. 的 -dence，/n/ 衰减（-39～-55 dB、低频占 -3～-8 dB 浊音、周期 0.3），8.46–8.475 静音，8.48 起句末 /s/（重心 3.2–6.3 kHz、低频 -28～-54 dB）；是 /n/ 的浊音收尾（词的一部分）"}, "106.02–106.11s": {"配音指纹": "3f09f415a035", "实测": {"最响dB": -35.6, "重心Hz": 1605, "周期": 0.3, "低频dB": -3.0}, "依据": "2026-11-07 逐 2.5 ms 实测（dossier_56，配音指纹 3f09f415a035）：S12 w 5.68–5.77：reception. 句末 -ʃən 的 /n/ 衰减（-30～-59 dB、低频占 -3～-8 dB、重心 0.6–2.5 kHz），5.78 后降到 -67～-108 dB；是 /n/ 的浊音收尾（词的一部分）"}, "113.30–113.40s": {"配音指纹": "3f09f415a035", "实测": {"最响dB": -35.2, "重心Hz": 2159, "周期": 0.19, "低频dB": -13.7}, "词头": "h", "依据": "2026-11-07 逐 2.5 ms 实测（dossier_56，配音指纹 3f09f415a035）：S13 w 6.53–6.63：year 的 ɹ 到 6.53，6.55–6.63 送气（-39～-48 dB、低频 -11～-31 dB、重心 1.6–2.6 kHz）一路升到 6.635 -31、6.65 -22、6.67 起 had 的元音（-16 dB、低频 -5 dB），中间没有 -55 dB 低谷；是 had 的词头 /h/ 送气（词的一部分）"}, "115.89–115.99s": {"配音指纹": "3f09f415a035", "实测": {"最响dB": -36.3, "重心Hz": 2908, "周期": 0.22, "低频dB": -3.1}, "依据": "2026-11-07 逐 2.5 ms 实测（dossier_56，配音指纹 3f09f415a035）：S13 w 9.125–9.22：discoveries. 的 -iz，iː 衰减（-36～-53 dB、低频 -2～-9 dB 浊音），9.21 起重心升到 4.3–5.6 kHz、低频 -30～-53 dB 的句末 /z/ 清化段，连续无低谷；是 iː 到 /z/ 的过渡（词的一部分）"}, "124.78–124.89s": {"配音指纹": "3f09f415a035", "实测": {"最响dB": -36.4, "重心Hz": 2433, "周期": 0.3, "低频dB": -4.4}, "依据": "2026-11-07 逐 2.5 ms 实测（dossier_56，配音指纹 3f09f415a035）：S14 w 7.64–7.75：Species 的 -piːsiːz，iː 衰减（-35～-58 dB、低频 -1～-13 dB、周期 0.3），7.745 起中间那个 /s/（重心 4.4–5.5 kHz、低频 -22～-48 dB）连续无低谷；是 iː 到 /s/ 的过渡（词的一部分）"}, "129.82–129.84s": {"配音指纹": "3f09f415a035", "实测": {"最响dB": -45.8, "重心Hz": 2171, "周期": 0.37, "低频dB": -0.5}, "词头": "w", "依据": "2026-11-07 逐 2.5 ms 实测（dossier_56，配音指纹 3f09f415a035）：S14 w 12.755–12.78：impression, 后的非人声区间到 12.7554 为止，12.755–12.78 低频占 0～-8 dB（浊音）、周期 0.37，12.785 -36、12.79 -26、12.795 -17 连续升高进 one 的 /w/；是 one 的 /w/ 浊音起始（词的一部分）"}, "136.10–136.10s": {"配音指纹": "3f09f415a035", "实测": {"最响dB": -41.9, "重心Hz": 3103, "周期": 0.0, "低频dB": -21.8}, "依据": "2026-11-07 逐 2.5 ms 实测（dossier_56，配音指纹 3f09f415a035）：S15 w 2.695：acceptance 的 -ccept-，/p/ 闭塞 2.655–2.69（-58～-70 dB）后一下除阻（-43 dB、重心 3.1 kHz），2.70–2.735 /t/ 闭塞，2.74 起 /t/ 除阻（-20 dB、重心 3.2–4.1 kHz）；是 accept 中 /p/ 的除阻（词的一部分）"}}
CONF["机器复听"]={"S11": {"配音指纹": "3f09f415a035", "依据": "2026-11-07 逐 2.5 ms 实测（S11 w，配音指纹 3f09f415a035）：precedence 的 /s/ 4.43–4.53（重心 5.5–6.3 kHz），ə-d-ə 4.54–4.68，末尾 /n/ 4.68–4.72（重心 0.4–0.6 kHz、低频 -1 dB），4.7275–4.7375 只降到 -35 dB（低频仍 -1 dB、有周期，还是 /n/ 的浊音），4.74 起重心一路升到 3–6 kHz 进句末 /s/；n 与 s 之间没有闭塞静音、没有爆破，没有多读 /t/。precedence /ˈprɛsɪdəns/ 与 precedents 同音近形，small.en 听成 precedents，parakeet 听成 precedence（没报），读音对"}}
CONF["删除段"]={"S2 raw 0.3700-0.4250": "2026-11-07 逐 2.5 ms 实测（dossier_56 S2 w）：in 的 /n/ 衰减到 0.345（-59 dB），0.345–0.37 -58～-65 dB，0.375 一下 5 ms 孤立咔哒（-36 dB、重心 3.8 kHz、低频 -24 dB、无周期），0.38–0.405 -51～-70 dB，0.41 起 September 的 /s/（重心 3.5–6.2 kHz）；咔哒两边都隔着静音、不连词，手写非人声区间 [0.37, 0.385]；复核报 lost 是删掉的咔哒本身", "S5 raw 2.2163-2.3759": {"类型": "紧贴两头的非人声", "配音指纹": "3f09f415a035", "依据": "2026-10-15 删除段对应 非人声区间 [[2.196292, 2.356083, '紧贴两头']]（w 秒）：自动切点.py 用实际声音按规则判定是吸气声/噗声（听得见的部分七成以上重心 1.8–3.8 kHz、低频 < -10 dB、周期 < 0.35，没有连续 20 ms >4 kHz 的擦音），贴词一侧切在紧挨词 40 ms 内最安静处的过零点；复核报 ['lost', 'post', 'pre'] 是删掉的呼吸声本身偏响（-34～-47 dB），不是词"}, "S8 raw 7.5350-7.9911": {"类型": "紧贴词头的非人声", "配音指纹": "3f09f415a035", "依据": "2026-10-15 删除段对应 非人声区间 [[7.71, 7.981125, '紧贴词头']]（w 秒）：自动切点.py 用实际声音按规则判定是吸气声/噗声（听得见的部分七成以上重心 1.8–3.8 kHz、低频 < -10 dB、周期 < 0.35，没有连续 20 ms >4 kHz 的擦音），贴词一侧切在紧挨词 40 ms 内最安静处的过零点；复核报 ['lost'] 是删掉的呼吸声本身偏响（-34～-47 dB），不是词"}, "S14 raw 5.7150-6.0708": {"类型": "紧贴词头的非人声", "配音指纹": "3f09f415a035", "依据": "2026-10-15 删除段对应 非人声区间 [[5.695, 6.050792, '紧贴词头']]（w 秒）：自动切点.py 用实际声音按规则判定是吸气声/噗声（听得见的部分七成以上重心 1.8–3.8 kHz、低频 < -10 dB、周期 < 0.35，没有连续 20 ms >4 kHz 的擦音），贴词一侧切在紧挨词 40 ms 内最安静处的过零点；复核报 ['lost', 'post'] 是删掉的呼吸声本身偏响（-34～-47 dB），不是词"}, "S14 raw 12.4350-12.7754": {"类型": "紧贴词头的非人声", "配音指纹": "3f09f415a035", "依据": "2026-10-15 删除段对应 非人声区间 [[12.45, 12.755417, '紧贴词头']]（w 秒）：自动切点.py 用实际声音按规则判定是吸气声/噗声（听得见的部分七成以上重心 1.8–3.8 kHz、低频 < -10 dB、周期 < 0.35，没有连续 20 ms >4 kHz 的擦音），贴词一侧切在紧挨词 40 ms 内最安静处的过零点；复核报 ['post'] 是删掉的呼吸声本身偏响（-34～-47 dB），不是词"}, "S15 raw 5.0100-5.4400": "2026-10-15 删除段对应 非人声区间 [[5.18, 5.43]]（w 秒）：自动切点.py 用实际声音按规则判定是吸气声/噗声（听得见的部分七成以上重心 1.8–3.8 kHz、低频 < -10 dB、周期 < 0.35，没有连续 20 ms >4 kHz 的擦音），贴词一侧切在紧挨词 40 ms 内最安静处的过零点；复核报 ['lost'] 是删掉的呼吸声本身偏响（-34～-47 dB），不是词"}
CONF["响度骤降"]={"124.3–124.8s": {"配音指纹": "3f09f415a035", "低": 6.3, "句子": "S14 The sensation came on 24 November 1859 with Darwin's treatise, On the Origin of Species: ...", "依据": "2026-11-07 逐 50 ms 实测（a.wav 对照本句原始合成 w，配音指纹 3f09f415a035）：这一段是 Species 的 -piːsiː（w 7.13–7.68）；a.wav 相对本句有声平均的电平逐格都比原始合成 w 低 1.3 dB，正好是这一段（S14 第2段）的句内调平 -1.5 dB，曲线形状完全一致（124.30 -4.1/-2.9、124.45 -7.0/-5.7、124.60 -7.7/-6.4、124.70 -19.0/-17.8、124.80 -31.4/-30.1）；124.25 一格是 /p/ 闭塞静音，124.55–124.85 是 iː 衰减进中间 /s/ 的清辅音段，原始合成里同样低；不是拼接或调平造成，读音清楚，机器复听两路都听对 Species"}}
CONF["中文重复"]={"安排":"用户 2026-11-07 原话（问 S8 arranged for 与 S15 arrangement 都译“安排”）：“两个都用‘安排’”；两词同根（arrange），S8 是动作“安排两篇论文宣读”，S15 是这件事的结果“这一安排”，意思一脉相承"}
CONF["合组"]["S14 came on 24 November 1859"]="对齐不了：came 的意思“到来”在中文句末（随着……《物种起源》到来），时间“于1859年11月24日”必须放在前面，came 只能和时间合成一组"
CONF["了不并"]={"S4-3":"用户 2026-11-08 原话：“把了加上 但是不要标色”"}
CONF["对齐"]["S14-1 came on 24 November 1859"]="came 的意思“到来”在中文句末（随着……《物种起源》到来），时间“于1859年11月24日”必须放在前面，came 只能和时间合成一组（用户 2026-11-07 给定的译文语序）"
CONF["同词异译"].update({"adapted to：对/适应":"不是两种译法：adapted to 的意思“对……适应”被“周围环境”隔开，“对”和“适应”是同一个意思的两部分（T23，用户 2026-11-07 原话“adapt to 重点词汇 整体”）",
 "afflicted by：的折磨/饱受":"不是两种译法：afflicted by 的意思“饱受……的折磨”被“热病”隔开，“饱受”和“的折磨”是同一个意思的两部分（T23，用户 2026-11-07 原话“中文意思对应：饱受.....的折磨”）",
 "paralleled：一样/与":"不是两种译法：paralleled 的意思“与……一样”被“达尔文自己的几乎完全”隔开，“与”和“一样”是同一个意思的两部分（T23，用户 2026-11-07 原话“与.....一样 对应 paralleled 的中文意思”）",
 "entitled：命名为/将":"不是两种译法：entitle A B 的意思“将……命名为”被“其”隔开，“将”和“命名为”是同一个意思的两部分（T23，用户 2026-11-07 原话“entitle 意思为：将...命名为”）",
 "named after：为/命名/用":"不是三种译法：name A after B 的意思“用……为……命名”被“自己的名字”“这一理论”隔开，“用”“为”“命名”是同一个意思的三部分（T23，用户 2026-11-07 原话“用....为.....命名”）"})
CONF["的不并"]={"S10-2":"主会话 2026-11-07 定：“他**幼子**(infant)的生命”的“的”是所属（幼子的生命），不是形容词 infant 的“的”，标色只标意思本身；T38（修.py 的并进）不并"}
CONF["停顿位置"]={
 "S11 compromise, / struck @1.100":"2026-11-07 逐 2.5 ms 实测（S11 w）：compromise 的 /z/（重心 5.0–5.5 kHz）衰减到 1.09（-57 dB），1.095–1.105 -60 dB 静音，1.108 起 struck 的 /s/（-36.6 dB、重心 2.7 kHz）；对齐器把后词开头标在 1.076（还在 /z/ 里），插入点改到静音里的过零点 1.100208，停顿在两词之间",
 "S15 1858, / assuring @5.005":"2026-11-07 逐 2.5 ms 实测（S15 w）：1858 的 eight 闭塞 4.91–4.94（-63 dB）、/t/ 除阻 4.945–4.97（-43～-49 dB），4.975–5.43 全是 -60～-72 dB 静音，5.435 起 assuring 的 ə（-28 dB、周期 0.55）；对齐器把前词末音素起点标在 5.044（已在静音里），停顿 5.005–5.425 在两词之间"}
out={"no":"56","title_en":"The Letter That Startled Darwin","title_zh":"一封信惊醒了达尔文","title_fx":{"hl":["Letter","Startled"],"ghost":[]},"sentences":[],"核对确认":CONF,"结尾解说":"简述",
     "停顿插入点":{"S11":{"1":1.100208}},
     "非人声区间":{"S1":[[3.24,3.51]],"S2":[[0.37,0.385],[2.06,2.375]],"S5":[[2.196292,2.356083,"紧贴两头"]],"S12":[[3.93,4.29]],"S16":[[4.54,4.905]]},
     "词尾除阻":{"S4":{"1":[1.955,"t"],"2":[4.785,"t"]},"S5":{"句末":[4.805,"t"]},"S8":{"句末":[13.33,"t"]},"S15":{"1":[4.93,"t"],"句末":[9.76,"t"]}},
     "allow_clash":["traits"],
     "高亮按实际开口":True,"高亮开口门槛":40,
     "术语":{"Charles Darwin":"查尔斯·达尔文","HMS Beagle":"小猎犬号","Alfred Russel Wallace":"阿尔弗雷德·拉塞尔·华莱士","Malay Archipelago":"马来群岛","Charles Lyell":"查尔斯·莱尔","Joseph Hooker":"约瑟夫·胡克","Linnean Society":"林奈学会","London":"伦敦","On the Origin of Species":"《物种起源》","Darwinism":"《达尔文主义》"}}
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 核对 import 生成并核对
生成并核对(S, out)
