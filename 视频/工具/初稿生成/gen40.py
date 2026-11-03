import json,re,glob,os
# 第40篇初稿（逐词对照）：S = [(段, [chunk, ...])]，chunk = ([(英文组, 中文组), ...], 可选 note)
# 2026-11-03 重点词中文沿用文章定稿（铁律），只按《翻译风格》调格式；三项并列加牛津逗号（T18）；不用破折号（T36）。
S=[
(1,[[[("In 1968","1968年，"),("Spencer Silver,","斯潘塞·西尔弗，"),("a scientist at 3M,","3M公司的一位科学家，")],
     "（a scientist at 3M：同位语，补充说明 Spencer Silver）"],
    [[("set out to","着手"),("make","研制"),("a super-strong","一种超强"),("**adhesive**.","**黏合剂**(adhesive)。")],
     "（set out to do：着手做……）"]]),
(1,[[[("The **polymer** he produced","然而他制成的**聚合物**(polymer)"),("did something else.","却是另一回事。")],
     "（he produced：定语从句，省略了关系代词，修饰 polymer）"]]),
(1,[[[("Its tiny **spheres**","它的微小**球体**(spheres)"),("formed","形成"),("a layer with little **tack**,","一层**初黏力**(tack)很小的涂层，")],
     "（with little tack：介词短语作后置定语，修饰 layer）"],
    [[("giving","让"),("paper","纸张"),("a **temporary** hold,","获得**暂时的**(temporary)黏着，")],
     "（giving…：现在分词短语作结果状语）"],
    [[("so","因此"),("it would **adhere**,","纸张能**粘附**(adhere)上去，"),("peel off,","揭下后"),("and be **reapplied**.","还能**重新贴上**(reapplied)。")],
     "（peel off：揭下；be reapplied：被重新贴上，被动语态）"]]),
(1,[[[("To an **inventor** chasing strength,","对一个追求强度的**发明者**(inventor)来说，"),("the **formulation**","这种**配方**(formulation)"),("was","是"),("a **setback**.","一次**挫折**(setback)。")],
     "（to sb：对某人来说；\nchasing strength：现在分词短语作后置定语，\n修饰 inventor）"]]),
(2,[[[("For five years","五年间，"),("Silver","西尔弗"),("acted as its **promoter** within 3M's **corporate** ranks,","在3M的**企业**(corporate)上下充当它的**推广者**(promoter)，")],
     "（act as：充当；within…ranks：在……内部上下）"],
    [[("in **informal** chats","在**非正式的**(informal)闲谈中、"),("and at **seminars**.","也在**研讨会**(seminars)上介绍它。")]]]),
(2,[[[("In his own **summary**,","按他自己的**概括**(summary)，"),("it was","这是"),("a solution without a problem.","一个找不到问题的解决方案。")],
     "（without a problem：介词短语作后置定语，\n修饰 solution）"]]),
(2,[[[("His **perseverance**","他的**坚持不懈**(perseverance)"),("met","换来的是"),("**indifference**.","**冷漠**(indifference)。")]]]),
(2,[[[("The **unconventional** material","这种**非常规的**(unconventional)材料"),("found no","找不到"),("use,","用途，")]],
    [[("and the **pursuit**","这番**追求**(pursuit)"),("proved","终究"),("**fruitless**.","**一无所获**(fruitless)。")],
     "（prove＋形容词：结果是……）"]]),
(3,[[[("In 1974","1974年，"),("Art Fry,","阿特·弗莱，"),("a colleague who had heard one of those talks,","一位听过其中一次讲座的同事，")],
     "（a colleague who…：同位语，补充说明 Art Fry；\nwho had heard…：定语从句，修饰 colleague）"],
    [[("faced a small **annoyance** at church.","在教堂里遇到了一件小小的**烦心事**(annoyance)。")]]]),
(3,[[[("The paper **bookmarks** **wedged** in his **choir**'s **hymn** book","他所在**唱诗班**(choir)的**赞美诗**(hymn)集里**夹着的**(wedged)纸**书签**(bookmarks)")],
     "（wedged in…：过去分词短语作后置定语，修饰 bookmarks）"],
    [[("kept","总是"),("getting **dislodged**","**移位**(dislodged)，"),("and falling out.","掉出来。")],
     "（keep doing：一直，总是；get＋过去分词：被……）"]]),
(3,[[[("The **frustration**","这份**懊恼**(frustration)"),("gave Fry","让弗莱"),("an idea.","想到一个主意。")],
     "（give sb an idea：让某人想到一个主意）"]]),
(3,[[[("The **unwanted** adhesive","这种**没人要的**(unwanted)黏合剂"),("could make","可以做成"),("a marker","一种书签，")]],
    [[("that would **cling to**","**附着在**(cling to)"),("a page,","书页上"),("stay put,","不会移动，"),("and leave it","还能让书页"),("**undamaged**.","**完好无损**(undamaged)。")],
     "（that would…：定语从句，修饰 marker；\ncling to：附着在……上；stay put：待在原处不动；\nleave it＋形容词：让它保持……）"]]),
(4,[[[("In 1977","1977年，"),("the notes","这种便条"),("were test-marketed as Press 'n Peel in four American cities,","以 Press 'n Peel 之名在美国四个城市试销，")],
     "（be test-marketed as…：以……之名试销）"],
    [[("where **purchasers**","**购买者**(purchasers)的"),("showed little **enthusiasm**.","**热情**(enthusiasm)不高。")],
     "（where…：非限制性定语从句，修饰 four American cities）"]]),
(4,[[[("In 1978","1978年，"),("3M's **marketers**","3M的**营销人员**(marketers)"),("staged a **blitz** in Boise, Idaho,","在爱达荷州博伊西发起一场**闪电攻势**(blitz)，")],
     "（stage：发起，组织；Boise, Idaho：城市在前、州在后）"],
    [[("{{=}}and **dispensed** **complimentary** **packets** of notes to offices.","向各办公室**分发**(dispensed)一**小包**(packets)一小包的**免费的**(complimentary)便条。")],
     "（dispense A to B：把 A 分发给 B）"]]),
(4,[[[("More than 90 per cent of **respondents** who tried them","试用过的**受访者**(respondents)中，超过90%"),("said","表示"),("they would buy.","会购买。")],
     "（who tried them：定语从句，修饰 respondents）"]]),
(4,[[[("After the **coolness**","**冷遇**(coolness)之后，"),("came","迎来了"),("a **turnaround**.","**转机**(turnaround)。")],
     "（After…came…：倒装句，主语 a turnaround 放在 came 后）"]]),
(5,[[[("On 6 April 1980","1980年4月6日，"),("the **pads**,","这种**便笺本**(pads)"),("**rebranded as**","**更名为**(rebranded as)"),("Post-it Notes,","便利贴，")],
     "（rebranded as…：更名为……，过去分词短语作插入语，补充说明 the pads）"],
    [[("went on sale **nationally** in the US,","在美国**全国**(nationally)上市；")],
     "（go on sale：上市）"],
    [[("and Canada and Europe followed in 1981.","1981年，便利贴又进入加拿大和欧洲。")]]]),
(5,[[[("The stationery **staple**","这款文具**必备品**(staple)"),("owes its","那"),("**signature**","**标志性的**(signature)"),("**canary**","**金丝雀黄**(canary)"),("**tone**","**色调**(tone)，"),("to an **unplanned** twist.","源于一次**计划外的**(unplanned)转折。")],
     "（owe A to B：A 源于 B）"]]),
(5,[[[("The laboratory next door","隔壁实验室"),("had only","手头只有"),("**leftover**","**剩下的**(leftover)"),("yellow","黄"),("paper.","纸。")],
     "（next door：作后置定语，隔壁的）\n"
     "（简述：1968年，3M科学家西尔弗想研制超强黏合剂，\n"
     "却做出一种粘得轻、能揭下再贴的黏合剂。\n"
     "他在公司内部推广了五年，没有人用。\n"
     "1974年，同事弗莱唱诗班的赞美诗集里，纸书签总是掉出来，\n"
     "他想到用这种黏合剂做书签。\n"
     "1977年试销反应冷淡；1978年在博伊西免费分发，\n"
     "超过90%的试用者表示会购买。\n"
     "1980年，它以“便利贴”之名在全美上市，1981年进入加拿大和欧洲。\n"
     "它的黄色，只因隔壁实验室手头只有剩下的黄纸。）"]]),
]
CONF={
"合组":{
 "S1 a scientist at 3M":"对齐不了：at 3M 是后置定语，修饰 scientist，中文“3M公司的一位科学家”定语必须提前",
 "S2 The polymer he produced":"对齐不了：he produced 是省略关系代词的定语从句，修饰 polymer，中文“他制成的聚合物”从句必须提前",
 "S2 did something else":"对齐不了：did something else 是整体说法“结果是另一回事”，拆开 did、something、else 中文不通",
 "S3 a layer with little tack":"对齐不了：with little tack 是后置定语，修饰 layer，中文“一层初黏力很小的涂层”定语必须提前",
 "S4 To an inventor chasing strength":"对齐不了：chasing strength 是现在分词短语作后置定语，修饰 inventor，中文“对一个追求强度的发明者来说”定语必须提前，“来说”放最后",
 "S5 acted as its promoter within 3M's corporate ranks":"对齐不了：within 3M's corporate ranks 是地点状语，中文“在3M的企业上下充当它的推广者”地点必须放到动词前（沿用文章定稿语序）",
 "S6 a solution without a problem":"对齐不了：without a problem 是后置定语，修饰 solution，中文“一个找不到问题的解决方案”定语必须提前",
 "S9 a colleague who had heard one of those talks":"对齐不了：who had heard one of those talks 是定语从句，修饰 colleague，中文“一位听过其中一次讲座的同事”从句必须提前",
 "S9 faced a small annoyance at church":"对齐不了：at church 是地点状语，中文“在教堂里遇到了……”地点必须放到动词前",
 "S10 The paper bookmarks wedged in his choir's hymn book":"对齐不了：wedged in his choir's hymn book 是过去分词短语作后置定语，修饰 bookmarks，中文“他所在唱诗班的赞美诗集里夹着的纸书签”定语必须整体提前",
 "S12 stay put":"对齐不了：stay put 是固定说法“待在原处不动”，拆开 stay、put 都没有这个意思",
 "S13 were test-marketed as Press 'n Peel in four American cities":"对齐不了：as Press 'n Peel、in four American cities 是方式和地点状语，中文“以 Press 'n Peel 之名在美国四个城市试销”都必须放到动词前",
 "S13 showed little enthusiasm":"对齐不了：show little enthusiasm 中文“热情不高”，little 化成“不高”放到名词后，拆开不通",
 "S14 staged a blitz in Boise, Idaho":"对齐不了：in Boise, Idaho 是地点状语，中文“在爱达荷州博伊西发起一场闪电攻势”地点必须放到动词前，美国地名中文州在前、城市在后",
 "S14 and dispensed complimentary packets of notes to offices":"对齐不了：to offices 是对象状语，中文“向各办公室分发……”必须放到动词前；complimentary packets of notes 中文“一小包一小包的免费的便条”，of 结构语序必须倒过来",
 "S14 {{=}}and dispensed complimentary packets of notes to offices":"对齐不了：to offices 是对象状语，中文“向各办公室分发……”必须放到动词前；complimentary packets of notes 中文“一小包一小包的免费的便条”，of 结构语序必须倒过来",
 "S15 More than 90 per cent of respondents who tried them":"对齐不了：A of respondents who tried them 是 of 结构加定语从句，中文“试用过的受访者中，超过90%”语序必须倒过来",
 "S17 went on sale nationally in the US":"对齐不了：nationally in the US 是地点状语，中文“在美国全国上市”必须放到动词前",
 "S17 and Canada and Europe followed in 1981":"对齐不了：follow 在这里指随后上市，中文“1981年，便利贴又进入加拿大和欧洲”时间提前、主语换成便利贴（沿用文章定稿），拆开不通",
 "S19 The laboratory next door":"对齐不了：next door 是后置定语，中文“隔壁实验室”必须提前"},
"对齐":{
 "S3-1 a layer with little tack,":"with little tack 是后置定语，修饰 layer，中文“一层初黏力很小的涂层”定语必须提前",
 "S4-1 To an inventor chasing strengt":"chasing strength 是后置定语，修饰 inventor，中文“对一个追求强度的发明者来说”定语必须提前",
 "S5-1 acted as its promoter within 3":"within 3M's corporate ranks 是提前的地点状语，中文“在3M的企业上下充当它的推广者”地点必须放到动词前",
 "S6-1 a solution without a problem.":"without a problem 是后置定语，修饰 solution，中文“一个找不到问题的解决方案”定语必须提前",
 "S9-1 a colleague who had heard one ":"who had heard… 是定语从句，修饰 colleague，中文从句必须提前",
 "S9-2 faced a small annoyance at chu":"at church 是提前的介词短语（地点状语），中文“在教堂里遇到了”地点必须放到动词前",
 "S10-1 The paper bookmarks wedged in ":"wedged in… 是过去分词短语作后置定语，修饰 bookmarks，中文定语必须整体提前",
 "S13-1 were test-marketed as Press 'n":"as…、in four American cities 是提前的介词短语（方式、地点状语），中文必须放到“试销”前",
 "S14-1 staged a blitz in Boise, Idaho":"in Boise, Idaho 是提前的介词短语（地点状语），中文必须放到“发起”前",
 "S14-2 and dispensed complimentary pa":"to offices 是提前的介词短语（对象），packets of notes 是 of 结构，中文语序必须倒过来",
 "S14-2 {{=}}and dispensed complimenta":"to offices 是提前的介词短语（对象），packets of notes 是 of 结构，中文语序必须倒过来",
 "S15-1 More than 90 per cent of respo":"of 结构加定语从句 who tried them，中文“试用过的受访者中，超过90%”语序必须倒过来",
 "S17-2 went on sale nationally in the":"nationally in the US 是提前的介词短语（地点状语），中文“在美国全国上市”必须放到动词前",
 "S17-3 and Canada and Europe followed":"in 1981 时间状语中文提前；follow 化成“又进入”，主语换成便利贴（沿用文章定稿）"},
"牛津逗号":{
 "S5 within 3M's corporate ranks, in informal chats and":"不是三项并列：within 3M's corporate ranks 是 acted as its promoter 的范围，逗号后 in informal chats and at seminars 是另一个状语，and 只连接两项",
 "S17 nationally in the US, and Canada and":"不是三项并列：逗号后 and 连接的是两个分句（the pads went on sale… 和 Canada and Europe followed…），Canada and Europe 只有两项"},
"方向":{"S15-1 more→试用过的受访者中，超过9":"More than 90 per cent 中文“超过90%”，“超过”就是 more than，方向一致"},
"短语":{
 "S5 at … seminars":"不是搭配：at 只引出场合（在研讨会上），seminars 本身就是“研讨会”（同 36 at … headquarters 的判法）",
 "S10 wedged … in":"不是搭配：in 只引出地点（夹在赞美诗集里），wedged 本身就是“夹着”",
 "S14 dispensed … of":"不是搭配：of 属于 packets of notes，和 dispensed 无关",
 "S14 dispensed … to":"不是搭配：to 只引出接受的对象（向各办公室），dispensed 本身就是“分发”",
 "S14 packets … of":"不是搭配：packets of notes 里 of 只引出所装的东西，packets 本身就是“小包”（同 16 beads … of 的判法）",
 "S17 rebranded … on":"不是搭配：on 属于后面的 went on sale，和 rebranded 无关"},
"已告诉用户被去掉的重点词":"2026-11-03 已在会话中把 stationery（与21 stationery 撞词，用户 2026-10-17 定留在先做的21，40 改回普通词）原样告诉用户（经主会话转告）"}
CONF["停顿位置"]={"S3 off, / and @7.370":"2026-11-03 逐 5 ms 看声音实测（S3 w，配音指纹 67f86bdba50c）：off 的 /f/ 摩擦 7.28–7.365（-24～-29 dB、重心 5.1–7.0 kHz、低频 -22～-40 dB、周期 ≤0.16），7.370 降到全段最低 -36.7 dB（过零 7.370583），7.375 起 and 的声门起音（低频 -5 dB），7.38 起 æ 浊音（周期 0.19→0.45、重心 1.2–2.5 kHz）；两词之间没有静音，7.370 是交界最低处，插在这里不切 /f/ 也不切 and（A42）；程序“后词开头 7.456”是带时长模型估的，实际 and 在 7.375 开口"}
CONF["非人声"]={
 "10.77–10.92s":{"配音指纹":"84fe631d604d","依据":"2026-11-03 40 逐 2.5/10 ms 看实际声音（逐段看声音、dossier_40）：S1 w 7.16–7.31：adhesive. 句末 /v/ 的收尾：7.08–7.13 是 /v/ 浊音（周期 0.4–0.5、低频 -4～-17 dB），7.16–7.21 浊音衰减（-37～-43 dB、周期 0.36–0.41、低频 -2～-4 dB），7.22–7.31 清化成擦音（-42～-50 dB、重心 3–3.9 kHz），一路连续降到 7.32 的 -57 dB、7.37 数字静音，中间没有缝，属于 adhesive"},
 "10.80–10.83s":{"配音指纹":"84fe631d604d","依据":"2026-11-03 40 逐 2.5/10 ms 看实际声音（逐段看声音、dossier_40）：S1 w 7.19–7.22：adhesive. 句末 /v/ 浊音衰减中段（-38～-43 dB、周期 0.37–0.41、低频 -2～-3 dB），前后连续，属于 adhesive"},
 "13.22–13.33s":{"配音指纹":"84fe631d604d","依据":"2026-11-03 40 逐 2.5/10 ms 看实际声音（逐段看声音、dossier_40）：S2 w 1.32–1.43：produced 词尾 /t/ 的除阻加送气：1.24–1.27 /s/（-9 dB、重心 5.6 kHz），1.30–1.31 /t/ 闭塞（-55～-58 dB），1.32 突然爆出 -31 dB（重心 3.3–3.5 kHz），之后连续衰减到 1.42 的 -54 dB，属于 produced"},
 "13.38–13.39s":{"配音指纹":"84fe631d604d","依据":"2026-11-03 40 逐 2.5/10 ms 看实际声音（逐段看声音、dossier_40）：S2 w 1.475–1.495：did 的 /d/ 闭塞里的浊音杠（-52～-57 dB、低频 -1～-5 dB 占优），一直连到 1.555 /d/ 除阻（-24 dB），属于 did"},
 "27.17–27.18s":{"配音指纹":"84fe631d604d","依据":"2026-11-03 40 逐 2.5/10 ms 看实际声音（逐段看声音、dossier_40）：S4 w 2.14–2.155：逗号停顿后 the 的 /ð/ 浊音起音（-38→-28 dB、周期 0.56、低频 -2～-3 dB），2.17 起元音 -12→-1 dB，属于 the"},
 "28.68–28.70s":{"配音指纹":"84fe631d604d","依据":"2026-11-03 40 逐 2.5/10 ms 看实际声音（逐段看声音、dossier_40）：S4 w 3.65–3.67：setback 的 /b/ 浊音杠：3.56–3.585 /t/，3.59–3.645 闭塞（-50～-60 dB），3.65–3.675 浊音杠升起（-33～-47 dB、低频 -0.5～-2 dB 占优），3.68 /b/ 除阻接 æ（-10 dB），属于 setback"},
 "37.63–37.77s":{"配音指纹":"84fe631d604d","依据":"2026-11-03 40 逐 2.5/10 ms 看实际声音（逐段看声音、dossier_40）：S5 w 7.41–7.55：seminars. 的 ɹ 到 /z/ 的过渡：7.33–7.40 ɹ 浊音（-19～-34 dB、重心 1.2–1.4 kHz），7.41–7.52 浊音衰减（-36～-46 dB、周期 0.2–0.4、低频 -2～-17 dB），7.53 起 /z/ 升到 -20 dB（重心 4.4–5.3 kHz），中间没有 -55 dB 的缝，属于 seminars"},
 "37.72–37.74s":{"配音指纹":"84fe631d604d","依据":"2026-11-03 40 逐 2.5/10 ms 看实际声音（逐段看声音、dossier_40）：S5 w 7.495–7.52：seminars. 的 ɹ 到 /z/ 过渡中段（-37～-44 dB、低频 -4 dB），前后连续，属于 seminars"},
 "46.32–46.34s":{"配音指纹":"84fe631d604d","依据":"2026-11-03 40 逐 2.5/10 ms 看实际声音（逐段看声音、dossier_40）：S8 w 0.015–0.03：句首 The 的 /ð/ 起音（-44→-27→-23 dB 连续升起），0.04 起元音 -13→-6 dB，属于 The"},
 "57.55–57.57s":{"配音指纹":"84fe631d604d","依据":"2026-11-03 40 逐 2.5/10 ms 看实际声音（逐段看声音、dossier_40）：S9 w 5.175–5.19：逗号停顿后 faced 的 /f/ 起音（-50→-48→-43 dB 连续升起，5.195 起重心 5.6–6.6 kHz 的 /f/ 摩擦），属于 faced"},
 "64.32–64.34s":{"配音指纹":"84fe631d604d","依据":"2026-11-03 40 直接读 work_40/a.wav 逐 10 ms：S10 kept 的 /k/ 送气 64.14–64.18（-28～-31 dB、重心 3.9–4.7 kHz），ɛ 元音 64.19–64.25（-10～-15 dB），/p/、/t/ 闭塞 64.26–64.31（-27→-68 dB），64.32 /t/ 除阻 -41 dB（重心 3.7 kHz、单帧），64.33–64.34 回到 -55～-71 dB，64.35 起 getting 的 /ɡ/ 除阻 -40 dB；属于 kept 词尾 /t/（S10 w 3.605–3.625）"},
 "70.56–70.58s":{"配音指纹":"84fe631d604d","依据":"2026-11-03 40 逐 2.5/10 ms 看实际声音（逐段看声音、dossier_40）：S12 w 0.02–0.035：句首 The 的 /ð/ 浊音起音（-31 dB、周期 0.46–0.50、低频 -3 dB），连续升到 0.06 的 -8 dB 元音，属于 The"},
 "73.88–73.90s":{"配音指纹":"84fe631d604d","依据":"2026-11-03 40 逐 2.5/10 ms 看实际声音（逐段看声音、dossier_40）：S12 w 3.335–3.355：to a page 里 ɐ 的元音衰减进 /p/ 闭塞（-48～-54 dB、周期 0.40–0.50、低频 -1 dB），3.355 /p/ 除阻 -20 dB（重心 3.3 kHz），属于 a/page 的交界"},
 "77.11–77.16s":{"配音指纹":"84fe631d604d","依据":"2026-11-03 40 逐 2.5/10 ms 看实际声音（逐段看声音、dossier_40）：S12 w 6.80–6.855：undamaged. 句末 /d/ 的除阻：6.72–6.75 /ʒ/（-15 dB、重心 5 kHz），6.77–6.79 /d/ 闭塞（-46～-63 dB），6.80 除阻 -32 dB（重心 3.1–3.5 kHz），连续衰减到 6.86 的 -73 dB、6.89 数字静音，属于 undamaged"},
 "84.99–85.01s":{"配音指纹":"84fe631d604d","依据":"2026-11-03 40 逐 2.5/10 ms 看实际声音（逐段看声音、dossier_40）：S13 w 6.72–6.74：逗号停顿后 where 的 /w/ 浊音起音（-46～-50 dB、低频 -1～-3 dB），6.74 -39、6.75 -14 dB 连续升起，属于 where"},
 "90.25–90.26s":{"配音指纹":"84fe631d604d","依据":"2026-11-03 40 逐 2.5/10 ms 看实际声音（逐段看声音、dossier_40）：S14 w 1.60–1.615：3M 的 three 的 /θ/ 起音（-49→-44 dB，1.61 起重心 5.6→7.9 kHz 一路升到 -24 dB），属于 three"},
 "94.60–94.62s":{"配音指纹":"84fe631d604d","依据":"2026-11-03 40 逐 2.5 ms 看实际声音：S14 w 6.103–6.16：Idaho, 停顿后 and 的声门起音（低频 -0.7～-8 dB 占优、-39～-48 dB），6.16 起 æ 元音 -17→-2 dB；前面 5.86–6.103 的吸气（周期 0.15–0.35、重心 2.5–3.1 kHz、低频 -12～-25 dB）已切掉，切点挪到低频开始占优之前，and 的起音整段保留，属于 and"},
 "113.26–113.28s":{"配音指纹":"84fe631d604d","依据":"2026-11-03 40 逐 2.5/10 ms 看实际声音（逐段看声音、dossier_40）：S17 w 5.325–5.35：逗号停顿后 went 的 /w/ 浊音起音（-41～-44 dB、周期 0.3–0.46、低频 -1～-4 dB），5.355 起 -22→-3 dB，属于 went"},
 "127.45–127.58s":{"配音指纹":"84fe631d604d","依据":"2026-11-03 40 逐 2.5/10 ms 看实际声音（逐段看声音、dossier_40）：S19 w 1.345–1.465：door 的 ɹ 收尾后接 had 的 /h/：1.345–1.455 -36～-43 dB 送气（重心 1.8–2.6 kHz），1.465–1.505 一路升到 -14 dB，1.515 起 æ 元音，中间没有 -55 dB 的低谷（K125：不切 /h/），属于 had","词头":"h"}}
CONF["高亮"]={"S10 第2块":{"开始读":64.14,"配音指纹":"84fe631d604d","依据":"2026-11-03 直接读 work_40/a.wav 逐 10 ms：book 的 /k/ 除阻 63.91（-37.6 dB、重心 3.4 kHz）衰减到 63.96，63.97–64.12 是删掉吸气后的数字静音（-180 dB），64.13 -74.6、64.14 起 kept 的 /k/ 送气（-30.6 dB、重心 4.3 kHz），64.19 起 ɛ 元音 -15→-10 dB；kept 在 64.14 开始读，高亮 64.12 提前 0.02 秒；甲法 63.97 落在静音开头"}}
CONF["机器复听"]={"S13":{"配音指纹":"84fe631d604d","依据":"2026-11-03 实测（配音指纹 84fe631d604d）：Press 'n Peel 的 'n 是 and 的缩写，按 按语境读音.json 弱读，配音音标 pɹˈɛs ən pˈiːl，读音核对 0；small.en 听成 and（正是 'n 的意思），parakeet 听成 in（ən/ɪn 弱读近音），两路前后的 Press、Peel 都对；交用户听"}}
out={"no":"40","title_en":"The Glue That Failed Its Way to Success","title_zh":"失败的胶水，成功的便利贴","title_fx":{"hl":["Failed","Success"],"ghost":[]},"sentences":[],"核对确认":CONF,"结尾解说":"简述",
     "高亮按实际开口":True,"高亮开口门槛":40,
     "术语":{"Spencer Silver":"斯潘塞·西尔弗","Silver":"西尔弗","3M":"3M","Art Fry":"阿特·弗莱","Fry":"弗莱","Press 'n Peel":"Press 'n Peel","Boise":"博伊西","Idaho":"爱达荷州","Post-it Notes":"便利贴","US":"美国","American":"美国","Canada":"加拿大","Europe":"欧洲"}}
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 核对 import 生成并核对
生成并核对(S, out)
