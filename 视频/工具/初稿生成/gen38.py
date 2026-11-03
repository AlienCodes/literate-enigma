import json,re,glob,os
# 第38篇初稿（逐词对照）：S = [(段, [chunk, ...])]，chunk = ([(英文组, 中文组), ...], 可选 note)
# 2026-11-03 重点词中文沿用文章定稿（铁律），只按《翻译风格》调格式；三项并列加牛津逗号（T18）；不用破折号（T36）。
S=[
(1,[[[("One of **ecology**'s","**生态学**(ecology)中"),("most **romantic**","最**浪漫的**(romantic)"),("ideas","观念之一，"),("**grew out of**","**萌生于**(grew out of)"),("plastic","塑料"),("bags.","袋之中。")],
     "（One of…：……之一；\ngrow out of…：从……中产生）"]]),
(1,[[[("In a Canadian forest,","在加拿大的一片森林里，"),("researchers","研究人员"),("**enclosed**","**把**(enclosed in)"),("paper birch","纸桦"),("and","和"),("Douglas fir","花旗松的"),("**seedlings**","**幼苗**(seedlings)"),("**in** them,","**罩进**(enclosed in)袋**里**(enclosed in)，")],
     "（enclose A in B：把 A 罩进 B 里；\nthem：指上句的 plastic bags）"],
    [[("then","再"),("**bathed** each species","让两种幼苗分别**沐浴**(bathed)"),("in carbon dioxide **laced with**","在**掺有**(laced with)"),("a different","不同"),("**tracer**.","**示踪物**(tracer)的二氧化碳中。")],
     "（each species：指纸桦和花旗松两种幼苗；\nlaced with…：过去分词短语作后置定语，修饰 carbon dioxide；\n科学家给两棵树吸了加了不同“追踪器”的二氧化碳，\n就是为了看清楚它们有没有在地下互相交换碳元素）"]]),
(1,[[[("Carbon","碳"),("**shuttled** both ways,","在两种树之间双向**穿梭**(shuttled)，")],
     "（both ways：双向，来回）"],
    [[("**apparently**","**似乎**(apparently)是"),("via","经由"),("**fungi** **linking** the trees' roots,","**连接**(linking)两者根系的**真菌**(fungi)；")],
     "（linking the trees' roots：现在分词短语作后置定语，修饰 fungi）"],
    [[("yet","不过，"),("the firs","花旗松"),("ran a","最终出现了碳的"),("**slight**","**小幅**(slight)"),("**surplus**,","**盈余**(surplus)，")],
     "（run a surplus：出现盈余）"],
    [[("larger in deeper **shade**.","在更深的**遮荫**(shade)下盈余更大。")],
     "（larger in deeper shade：省略结构，\n即 the surplus was larger in deeper shade）"]]),
(2,[[[("Most","大多数"),("**terrestrial**","**陆生**(terrestrial)"),("plants","植物身上都"),("**harbour**","**包含/携带着**(harbour)"),("such **fungi**,","这类**真菌**(fungi)，")],
     "（harbour：英式拼写，美式 harbor）"],
    [[("whose **filaments**","它们的**菌丝**(filaments)"),("**forage for**","四处**搜寻/寻找**(forage for)"),("water","水分"),("and","和"),("**nutrients** including **nitrogen**,","**氮**(nitrogen)等**养分**(nutrients)，")],
     "（whose…：非限制性定语从句，修饰 such fungi；\nincluding nitrogen：介词短语，修饰 nutrients）"],
    [[("**swapping** them for","再拿去**换取**(swapping)"),("plant","植物的"),("sugars.","糖分。")],
     "（swapping…：现在分词短语作伴随状语；\nswap A for B：用 A 换 B）"]]),
(2,[[[("One fungus","单个真菌"),("can","就能"),("**knit**","**把**(knit into)"),("plants","多株植物"),("**into**","**编织进**(knit into)"),("a","同一张"),("**shared network**.","**共享网络**(shared network)。")],
     "（knit A into B：把 A 编织进 B）"]]),
(2,[[[("The journal Nature","《自然》杂志"),("**unveiled** the study on 7 August 1997,","于1997年8月7日**公布/发表了**(unveiled)这项研究，")],
     "（The journal Nature：杂志名 Nature，即《自然》）"],
    [[("its cover","当期封面还"),("offering a","送上一个"),("**catchy**","**响亮好记的**(catchy)"),("**coinage**:","**新造词**(coinage)："),("the \"wood-wide web\".","“林木万维网”（wood-wide web）。")],
     "（its cover offering…：独立主格结构，补充说明当期封面；\nwood-wide web：仿 world wide web（万维网）造的词；\ncatchy：非常吸引人，并且容易让人记住。\n比如说我们平时说的洗脑音乐就是 catchy music。\n换句话来说就是容易洗脑的，\n这里的洗脑说的是容易让人们记住，并且在大脑里面会不断循环）"]]),
(3,[[[("The **metaphor**","结果，这个**比喻**(metaphor)"),("proved **irresistible**.","**令人难以抗拒**(irresistible)。")],
     "（prove＋形容词：结果是……，事实证明……）"]]),
(3,[[[("Between 2015 and 2021,","2015年至2021年间，"),("a forester's **bestseller**,","一位护林人的**畅销书**(bestseller)、"),("an **acclaimed** novel,","一部**广受赞誉的**(acclaimed)小说"),("and an ecologist's **memoir**","和一位生态学家的**回忆录**(memoir)")],
     "（a forester's bestseller, an acclaimed novel, and an ecologist's memoir：\n三个名词短语并列作主语）"],
    [[("told readers that","都向读者讲述，"),("trees","树木会"),("**converse**,","**交谈**(converse)，"),("**warn one another**,","会**互相示警**(warn one another)，"),("and,","还会"),("as \"mother trees\",","作为“母树”"),("**nurture**","**哺育/养育**(nurture)"),("their","自己的"),("**kin**.","**亲族**(kin)。")],
     "（that 引导宾语从句；converse, warn, and nurture：三个谓语动词并列；\nas \"mother trees\"：作为“母树”，插入语）"]]),
(3,[[[("Yet","然而，"),("the 1997 trees","1997年实验里的树"),("were seedlings,","都还是幼苗，"),("not **elderly** mothers.","并非**年迈的**(elderly)母亲。")],
     "（the 1997 trees：指1997年那项实验里的树）"]]),
(4,[[[("In February 2023,","2023年2月，"),("three researchers","三位研究者"),("**combed through**","**梳理了**(combed through)"),("the field","野外"),("evidence.","证据。")],
     "（comb through…：仔细梳理，逐一查看）"]]),
(4,[[[("They judged it","他们认为，这些证据"),("too **sparse**,","或过于**稀少**(sparse)，"),("**inconsistent**,","或**互不一致**(inconsistent)，"),("or **ambiguous**","或**含糊不清**(ambiguous)，")],
     "（judge A (to be) B：认为 A 是 B；it：指 the field evidence）"],
    [[("to **demonstrate**","不足以**证明**(demonstrate)"),("that shared","共享"),("networks","网络"),("are **widespread**.","**普遍存在**(widespread)。")],
     "（too…to…：太……而不能……；that 引导宾语从句）"]]),
(4,[[[("In 26","在26项"),("field","野外"),("studies,","研究中，"),("networks","网络"),("helped","帮助"),("and","和"),("**hindered**","**阻碍**(hindered)"),("seedlings","幼苗的"),("about equally often,","频率大致相同，")],
     "（about equally often：次数大致一样多）"],
    [[("with","并且"),("**neutral**","**中性的**(neutral)"),("effects","效应"),("**predominating**.","**占据大多数**(predominating)。")],
     "（with＋名词＋现在分词：with 复合结构作伴随状语）"]]),
(4,[[[("No","没有任何一项经"),("**peer-reviewed**","**同行评审的**(peer-reviewed)"),("field","野外"),("study","研究"),("showed","表明，"),("**mature** trees","**成年**(mature)树木"),("**favouring**","会**偏爱**(favouring)"),("their own","自己的"),("**offspring**.","**后代**(offspring)。")],
     "（show A doing：表明 A 在做某事；\nfavouring：英式拼写，美式 favoring）"]]),
(4,[[[("**Unsupported**","在后来的论文中，**缺乏依据的**(Unsupported)"),("**assertions** in later papers","**论断/断言**(assertions)"),("had **doubled** over 25 years,","在25年间**增加了一倍/翻了一倍**(doubled)，")],
     "（in later papers：介词短语作后置定语，修饰 assertions；\nhad doubled：过去完成时）"],
    [[("with **citations**","**引用**(citations)也"),("**skewed**","**偏向**(skewed towards)"),("**towards**","**于**(skewed towards)"),("**positive results**.","**正面结果**(positive results)。")],
     "（with＋名词＋过去分词：with 复合结构作伴随状语；\nskewed towards…：偏向……）"]]),
(5,[[[("None of this","这一切都不能"),("**disproves**","**否定**(disproves)"),("the networks'","这些网络的"),("**existence**.","**存在**(existence)。")],
     "（None of this…：这一切都不……，全部否定）"]]),
(5,[[[("In January 2025,","2025年1月，"),("**defenders**","共享网络说的**拥护者**(defenders)"),("faulted","挑出了"),("the **critique**'s","这篇**批评文章**(critique)"),("methods.","方法上的问题。")],
     "（defenders：指为共享网络之说辩护的研究者；\nfault：挑出……的问题；\nthe critique：指2023年的那篇批评文章）"]]),
(5,[[[("The **critics**","**批评者**(critics)也"),("**concede** that","**承认**(concede)，"),("carbon","碳"),("and","和"),("nutrients","养分"),("can","可以"),("**migrate** between trees underground.","经由地下在树与树之间**迁移**(migrate)。")],
     "（that 引导宾语从句；underground：副词，在地下）"]]),
(5,[[[("It is","必须由"),("evidence **unearthed** in real forests,","在真实森林中**发掘**(unearthed)出的证据，"),("not","而不能凭"),("the **allure** of a family **saga**,","一部家族**传奇**(saga)的**魅力**(allure)，")],
     "（It is…that…：强调句，强调 evidence…；\nunearthed in real forests：过去分词短语作后置定语）"],
    [[("that must settle","来裁定"),("how much the networks **convey**,","网络究竟**输送了**(convey)多少、"),("and whether it","这又是否"),("matters.","要紧。")],
     "（how much… 和 whether…：两个宾语从句并列，作 settle 的宾语）\n"
     "（简述：1997年，研究人员在加拿大的森林里把纸桦和花旗松的幼苗罩进塑料袋，\n"
     "用不同示踪物追踪碳，发现碳似乎经由真菌在两种树之间双向穿梭。\n"
     "《自然》封面称之为“林木万维网”。2015年至2021年间，\n"
     "畅销书、小说和回忆录把树木讲成会交谈、会照料亲族的“母树”。\n"
     "2023年2月，三位研究者梳理野外证据，认为证据不足以证明共享网络普遍存在。\n"
     "2025年1月，拥护者指摘其方法；批评者也承认碳和养分能在树间迁移。\n"
     "网络输送多少、是否要紧，要靠真实森林里的证据来裁定。）"]]),
]
CONF={
"合组":{
 "S12 about equally often":"对齐不了：about equally often 中文“频率大致相同”（用户 2026-11-03 原话），about 化成“大致”放在中间，拆开语序就乱",
 "S2 paper birch":"对齐不了：paper birch 是一种树的名字“纸桦”，拆开 paper 就成了“纸”",
 "S2 bathed each species":"对齐不了：bathe A in B 中文“让 A 沐浴在 B 中”，使役句宾语“两种幼苗”必须放到“沐浴”前面；each 化成“分别”",
 "S2 in carbon dioxide laced with":"对齐不了：laced with… 是后置定语修饰 carbon dioxide，中文“在掺有不同示踪物的二氧化碳中”定语必须提前，“二氧化碳”落在最后一组",
 "S3 shuttled both ways":"对齐不了：both ways 是方式状语，中文“在两种树之间双向穿梭”必须放到动词前",
 "S3 fungi linking the trees' roots":"对齐不了：linking the trees' roots 是现在分词作后置定语修饰 fungi，中文“连接两者根系的真菌”定语必须提前",
 "S3 larger in deeper shade":"对齐不了：省略结构（the surplus was larger in deeper shade），中文“在更深的遮荫下盈余更大”（用户 2026-11-03 原话“在更深的遮荫下盈余更大”），地点状语 in deeper shade 必须放到“盈余更大”前面",
 "S4 nutrients including nitrogen":"对齐不了：including nitrogen 后置修饰 nutrients，中文“氮等养分”必须提前",
 "S6 the \"wood-wide web\"":"对齐不了：wood-wide web 是一个新造术语，整体译“林木万维网”，括号保留英文（文章定稿），拆开没意思",
 "S8 told readers that":"对齐不了：tell sb that… 中文“向读者讲述”，间接宾语必须放到动词前",
 "S8 as \"mother trees\"":"对齐不了：mother trees 是一个带引号的说法，整体译“母树”（文章定稿），拆开引号就断",
 "S14 assertions in later papers":"对齐不了：in later papers 后置定语修饰 assertions，中文“在后来的论文中”提到句首（放在前一组），这一组只剩“论断”",
 "S14 had doubled over 25 years":"对齐不了：over 25 years 是时间状语，中文“在25年间增加了一倍”时间必须放到动词前",
 "S17 migrate between trees underground":"对齐不了：between trees、underground 都是地点状语，中文“经由地下在树与树之间迁移”必须放到动词前",
 "S18 evidence unearthed in real forests":"对齐不了：unearthed in real forests 是过去分词作后置定语修饰 evidence，中文“在真实森林中发掘出的证据”定语必须提前"},
"对齐":{
 "S2-2 in carbon dioxide laced with":"laced with… 后置定语修饰 carbon dioxide，中文定语必须提前",
 "S3-2 fungi linking the trees' roots":"linking… 现在分词后置定语，中文“连接两者根系的真菌”定语必须提前",
 "S6-1 unveiled the study on 7 August":"on 7 August 1997 是时间状语，中文“于1997年8月7日推出了这项研究”时间必须放到动词前",
 "S14-1 had doubled over 25 years,":"over 25 years 是时间状语，中文“在25年间增加了一倍”时间必须放到动词前",
 "S18-1 evidence unearthed in real for":"unearthed… 过去分词后置定语，中文“在真实森林中发掘出的证据”定语必须提前",
 "S18-1 the allure of a family saga,":"the allure of A 中文“A 的魅力”，of 结构语序必须倒过来",
 "S18-2 how much the networks convey,":"how much 宾语从句，中文“网络究竟输送了多少”疑问词按中文习惯放到动词后"},
"牛津逗号":{"S2 In a Canadian forest, researchers enclosed paper birch and":"不是三项并列：and 只连接 paper birch 和 Douglas fir 两种树",
 "S12 In 26 field studies, networks helped and":"不是三项并列：and 只连接 helped 和 hindered 两个动词"},
"方向":{"S14-1 later→论断/断言":"later 在 in later papers 里，中文“在后来的论文中”因后置定语倒序提到前一组句首，“后来”方向一致"},
"中文意思":{
 "S4 swapping":"swap A for B 本文中文“拿去换取”，“换取”一处就是全部意思，没有被隔开",},
"短语":{
 "S14 doubled … over":"不是搭配：over 25 years 是时间状语（在25年间），double 单独就是“增加一倍”",
 "S14 doubled … with":"不是搭配：with 属于后面的 with 复合结构（with citations skewed…），和 doubled 无关",
 "S2 bathed … in":"不是搭配：in carbon dioxide 引出沐浴的介质，bathe 单独就是“使沐浴、使笼罩”",
 "S2 bathed … with":"不是搭配：with 属于 laced with（已整体标），和 bathed 无关",
 "S4 harbour … for":"不是搭配：for 属于 forage for water，和 harbour 无关",
 "S4 swapping … for":"不是搭配：swap A for B 里 for 引出换来的东西（植物的糖分），swap 单独就是“交换”（同 34 bundled … with 的判法）",
 "S6 unveiled … on":"不是搭配：on 7 August 1997 是时间状语，和 unveiled 无关",
 "S12 hindered … with":"不是搭配：with 属于后面的 with 复合结构（with neutral effects predominating），和 hindered 无关",
 "S14 with … citations":"不是搭配：with citations skewed… 是 with 复合结构（with＋名词＋过去分词），不是 with＋名词的习语",
 "S17 concede that":"不是搭配：concede 本文就是速查表第一个意思“（勉强）承认”，that 只引导宾语从句",
 "S18 unearthed … in":"不是搭配：in real forests 是地点状语（在真实森林中），unearth 单独就是“发掘”",
 "S18 unearthed … of":"不是搭配：of 属于 the allure of a family saga，和 unearthed 无关",
 "S18 allure … of":"不是搭配：the allure of A 里 of 只引出魅力的来源，allure 单独就是“魅力”（同 36 advent … of 的判法）"},
"停顿位置":{
 "S3 ways, / apparently @1.840":"2026-11-03 逐 2.5 ms 看声音实测（S3 w）：ways 的 /z/ 到 1.8325 收尾（-55 dB、重心 4.2 kHz），1.835–1.845 降到 -57～-61 dB，1.840 是两词之间最低处 -61.2 dB，1.8475 起 apparently 的 ɐ（-28.6→-13.5 dB）；插在这里不切前后词（A42）",
 "S8 another, / and, @11.950":"2026-11-03 逐 2.5 ms 看声音实测（S8 w）：another 的 ɚ 到 11.93 收尾（-49 dB），11.94 降到 -57.6 dB，11.95–12.28 是 -60～-74 dB 的静音，12.29 起 and 的元音（-40.8→-11 dB）；删静音 11.950–12.275 全在静音里，不切前后词（A42）",
 "S8 and, / as @12.510":"2026-11-03 逐 2.5 ms 看声音实测（S8 w）：and 的 /d/ 在 12.495–12.5075 衰减（-26→-49 dB），12.51–12.5175 是 -50～-52.5 dB 的低谷，12.5125 最低 -52.5 dB，12.52 起 as 的 /æ/（-29→-17.8 dB）；12.510 在低谷里，插在这里不切前后词（A42）",
 "S8 trees\", / nurture @13.600":"2026-11-03 逐 2.5 ms 看声音实测（S8 w）：trees 的 /z/ 到 13.5775 收尾（-38.8 dB、重心 4.4 kHz），13.5875–13.6075 是 -54～-55 dB 的低谷，13.6475 起 nurture 的 /n/（-18.9 dB、重心 0.56 kHz、周期 0.41）；13.600 在低谷里，插在这里不切前后词（A42）",
 "S18 convey, / and @8.355":"2026-11-03 逐 2.5 ms 看声音实测（S18 w）：convey 的 eɪ 到 8.325 收尾（-37.4 dB），8.33–8.3575 降到 -51～-60 dB，8.355 是 -57.4 dB 的低谷，在后面那段吸气（8.37–8.55，已写进非人声区间）之前；插在这里不切 convey（A42）"},
"非人声":{"9.78–9.82s": {"配音指纹": "e7c1c5358cb3", "依据": "2026-11-03 38 逐 2.5 ms 看实际声音（dossier_38，配音指纹 e7c1c5358cb3）：S2 w 1.45–1.495：forest 的 /s/ 在 1.42 收尾，1.43–1.45 是 /t/ 闭塞（-54～-61 dB），1.46–1.48 是 /t/ 除阻（-30～-36 dB、重心 2.5–3.5 kHz），属于 forest"}, "21.95–21.96s": {"配音指纹": "e7c1c5358cb3", "依据": "2026-11-03 38 逐 2.5 ms 看实际声音（dossier_38，配音指纹 e7c1c5358cb3）：S3 w 1.29–1.305：both 的 /θ/ 在 1.28 收尾，1.30 起 ways 的 /w/ 起音（低频 -1.9 dB、重心 631→351 Hz，1.31 起周期 0.43 一路升到 -8 dB），属于 ways"}, "22.99–23.01s": {"配音指纹": "e7c1c5358cb3", "依据": "2026-11-03 38 逐 2.5 ms 看实际声音（dossier_38，配音指纹 e7c1c5358cb3）：S3 w 1.945–1.965：apparently 的 ɐ 在 1.85–1.92 后，1.925–1.955 是 /p/ 闭塞里的浊音杠（-47～-52 dB、低频 -0.3～-1.3 dB），1.965 /p/ 除阻（重心 3.7 kHz），1.975 起 æ，属于 apparently"}, "57.66–57.67s": {"配音指纹": "e7c1c5358cb3", "依据": "2026-11-03 38 逐 2.5 ms 看实际声音（dossier_38，配音指纹 e7c1c5358cb3）：S7 w 0.665–0.685：metaphor 的 ɚ 衰减到 0.655（-57 dB），0.665–0.675 是 proved 的 /p/ 闭塞（-48～-53 dB、低频 -1 dB），0.685 /p/ 除阻（重心 4.1 kHz），0.695 起 /ɹ/，属于 proved"}, "81.03–81.12s": {"配音指纹": "e7c1c5358cb3", "依据": "2026-11-03 38 逐 2.5 ms 看实际声音（dossier_38，配音指纹 e7c1c5358cb3）：S9 w 4.445–4.54：mothers 的 ɚ 弱浊音（4.365–4.485，-24～-42 dB、低频 -2～-11 dB、重心 0.9–1.8 kHz），4.495 -53 dB 后 4.505–4.525 过渡，4.535 起句末 /z/（重心 4.4–5.7 kHz），属于 mothers", "词尾": "z"}, "87.75–87.83s": {"配音指纹": "e7c1c5358cb3", "依据": "2026-11-03 38 逐 2.5 ms 看实际声音（dossier_38，配音指纹 e7c1c5358cb3）：S10 w 5.28–5.36：evidence 的 /n/ 鼻音衰减（5.26–5.33，-33～-50 dB、低频 -3～-8 dB），5.39 起句末 /s/（重心 3.1 kHz、低频 -31 dB），属于 evidence", "词尾": "s"}, "92.02–92.05s": {"配音指纹": "e7c1c5358cb3", "依据": "2026-11-03 38 逐 2.5 ms 看实际声音（dossier_38，配音指纹 e7c1c5358cb3）：S11 w 2.99–3.02：or 的浊音起音（低频 -0.4～-2.7 dB、周期 0.27–0.48），中间没有 -55 dB 低谷，3.03 起 or 的元音 -16 dB，属于 or（非人声区间 [2.767958, 2.990125] 故意留着）"}, "100.05–100.07s": {"配音指纹": "e7c1c5358cb3", "依据": "2026-11-03 38 逐 2.5 ms 看实际声音（dossier_38，配音指纹 e7c1c5358cb3）：S12 w 2.90–2.92：helped 的 /p/ 闭塞 2.87–2.90（-54～-56 dB），2.91 /p/ 除阻（-42.9 dB、重心 2.6 kHz），2.93–2.94 /t/ 闭塞 -61～-63 dB，2.95 /t/ 除阻连进 and，属于 helped"}, "129.94–129.96s": {"配音指纹": "e7c1c5358cb3", "依据": "2026-11-03 38 逐 2.5 ms 看实际声音（dossier_38，配音指纹 e7c1c5358cb3）：S16 w 4.77–4.79：methods 的 ə（4.69–4.76，-34～-42 dB、低频 -1～-7 dB）后，4.78 是 /d/（-40 dB、低频 -1.6 dB），4.80 起句末 /z/（重心 3.4–5.9 kHz），属于 methods"}, "136.30–136.32s": {"配音指纹": "e7c1c5358cb3", "依据": "2026-11-03 38 逐 2.5 ms 看实际声音（dossier_38，配音指纹 e7c1c5358cb3）：S17 w 5.205–5.23：underground 的 /n/ 衰减到 5.175，5.185–5.205 /d/ 闭塞 -63～-64 dB，5.215 /d/ 除阻（-42 dB、重心 1.8 kHz），之后衰减到 -116 dB 句末，属于 underground"}, "140.60–140.62s": {"配音指纹": "e7c1c5358cb3", "依据": "2026-11-03 38 逐 2.5 ms 看实际声音（dossier_38，配音指纹 e7c1c5358cb3）：S18 w 3.29–3.305：forests, 的停顿后，3.3025 起 not 的 /n/（-32.7 dB、重心 939→524 Hz、低频 -3 dB），3.31 起 -10 dB，属于 not"}, "146.12–146.16s": {"配音指纹": "e7c1c5358cb3", "依据": "2026-11-03 38 逐 2.5 ms 看实际声音（dossier_38，配音指纹 e7c1c5358cb3）：S18 w 8.555–8.59：非人声区间 [8.357667, 8.556167] 之后，8.5625–8.5825 是 and 的浊音起音（-44～-49 dB、低频 -0.9～-1.9 dB），没有 -55 dB 低谷，8.5925 起 -35.7、8.6025 -28 dB 进 and，属于 and"}, "147.10–147.19s": {"配音指纹": "e7c1c5358cb3", "依据": "2026-11-03 38 逐 2.5 ms 看实际声音（dossier_38，配音指纹 e7c1c5358cb3）：S18 w 9.535–9.625：matters 的 ɚ 弱浊音（9.4575–9.58，-24～-42 dB、低频 -1～-5 dB、重心 1.0–1.6 kHz、周期 0.25–0.36），9.5875 -53.9 dB 后 9.5975–9.6175 过渡，9.6275 起句末 /z/（重心 4.2–5.4 kHz），属于 matters", "词尾": "z"}, "147.13–147.15s": {"配音指纹": "e7c1c5358cb3", "依据": "2026-11-03 38 逐 2.5 ms 看实际声音（dossier_38，配音指纹 e7c1c5358cb3）：S18 w 9.565–9.585：matters 的 ɚ 弱浊音中段（-40～-42 dB、低频 -0.9～-1.7 dB、周期 0.30–0.36），属于 matters"}},
"机器复听":{"S11": {"配音指纹": "e7c1c5358cb3", "依据": "2026-11-03 实测（配音指纹 e7c1c5358cb3，S11 w）：ambiguous 配音音标 æmbˈɪɡjuːəs，读音核对 0；m 3.48–3.55（浊音、重心 250–300 Hz），/b/ 除阻 3.5625（重心 2.2 kHz），ɪ 3.57–3.64，/g/ 浊音闭塞 3.67–3.72（-18～-21 dB、重心 290–460 Hz、低频 -2～-3 dB）、除阻 3.7225–3.7525（重心 2.7–3.2 kHz），/j/+uː 3.77–3.85（重心 1.2–1.6 kHz），ə 3.88–3.97，/s/ 3.99–4.10（重心 5.5–6.1 kHz）；音节、辅音都在，只有 parakeet 一路把 ɪɡ 漏听成 ambuous，交用户听"}},
"高亮":{"S3 第2块": {"开始读": 22.88, "配音指纹": "e7c1c5358cb3", "依据": "2026-11-03 直接读 work_38/a.wav 逐 10 ms：ways 的 /z/ 到 22.49 收尾（-60.8 dB），22.50–22.87 是插入的全静音（-229 dB），22.88 起 apparently 开口（-59.8→22.89 -15.8 dB、重心 2.3 kHz）；乙（22.88）对，高亮 22.87 比开口早 0.01 秒，甲（22.51）落在静音开头偏早"}},
"中文重复":{"把":"“把”是把字句的标记，enclosed in（把……罩进……里）和 knit into（把……编织进）都按用户 2026-11-03 原话“把.....罩进....里 都要标色”“knit into 就重点词汇。 把...编织进”标色，各自和后面的动词连成一个意思（罩进/编织进），学生看动词就分得清"},
"同词异译":{"skewed towards：于/偏向":"S14 skewed towards“偏向于”，“偏向”放在 skewed 下、“于”放在 towards 下（用户 2026-11-03 原话“改为偏向于 于 要在 towards 的正下方”），是同一个意思的两部分，不是两种译法","knit into：把/编织进":"S5 knit A into B“把 A 编织进 B”被“多株植物”隔开，“把”“编织进”是同一个意思的两部分（T22/T23，用户 2026-11-03 原话“knit into 就重点词汇。 把...编织进”），不是两种译法","enclosed in：把/罩进/里":"S2 enclose A in B“把 A 罩进 B 里”被“纸桦和花旗松的幼苗”和“袋”隔开，“把”“罩进”“里”是同一个意思的三部分（T22/T23，用户 2026-11-03 原话“刚需要标注的是把in也标注进去。 把.....罩进....里 都要标色”），不是三种译法"},
"已告诉用户被去掉的重点词":"已在会话中把 nitrogen（与16撞词，用户 2026-10-17 定留在16，38 改回普通词）告诉用户（2026-11-03 在“38 文本过了”的消息里原样报主会话转告）"
}
# 非人声区间的实测依据（2026-11-03 逐 2.5 ms 看 S11/S18 w）：
#  S11 [2.767958, 2.990125, 紧贴两头]：inconsistent 的 /t/ 除阻 2.745–2.75（-38 dB、重心 2.6–3.2 kHz），之后 2.7575–2.765 还有 -49～-51 dB 的除阻余音（外侧 5 ms 不到 -55 dB，所以算紧贴词尾），左头切在 2.7675 那个 -62 dB 低谷的过零点 2.767958，余音保留；2.77–2.98 是 -36～-52 dB 的吸气（重心 1.9–2.3 kHz、低频 -6～-27 dB），中间无词；2.985 降到 -51 dB，2.99 起低频 -0.4～-2.8 dB 是 or 的浊音起音（保留），3.025 起 or 的元音
#  S11 停顿处除阻 [2.76, 2.990125, t]：程序自动写的是 [2.76, 2.765]（连读，供体放不进停顿之前），停顿后先出除阻、再是被换成静音的吸气，A19 量到 0.25 s；照 36 S2 gadget [1.67, 1.915] 的做法把范围扩到吸气末尾 2.990125，除阻留在停顿前、吸气不进停顿后
#  S12 [1.737542, 2.0475, 紧贴词尾]（纯人声报 呼吸声/收尾过长 98.79–99.04s）：studies 的 /z/ 到 1.7375 收尾（-58.2 dB 低谷，左头切在过零点 1.737542，/z/ 尾 -50 dB 保留）；1.74–1.98 是 -42～-55 dB 的吸气（重心 2.0–4.6 kHz、低频 -10～-24 dB、周期 ≤0.25）；1.9975–2.0025 低谷 -59～-60 dB；2.0075–2.035 是 -47～-54 dB 的低频残声，和 networks 的 /n/ 之间隔着 2.0475 的 -60.3 dB 低谷，不连着词；右头 2.0475 外侧 5 ms -58～-60 dB，networks 的 /n/ 2.0625 起（-42.7→-11 dB）完整保留
#  S13 [3.18, 3.355792, 紧贴词头]（原自动切点 [3.18, 3.32]，纯人声报 噗声 109.65–109.67s）：3.325–3.3525 是 -49～-57 dB 的低频残声（低频 -0.3～-2.5 dB），是 trees 后吸气的尾巴；favouring 的 /f/ 3.355 起（重心 4.2→6.2 kHz），右头切在过零点 3.355792，/f/ 完整保留
#  S18 [5.432792, 5.751125, 紧贴词头]：saga 的 ə 到 5.39 收尾（-39 dB），5.40–5.43 静音 -57～-63 dB（左头 5.432792 过零点，外侧 5 ms -56～-60 dB）；5.44–5.68 是 -44～-52 dB 的吸气（重心 2.0–2.7 kHz、低频 -5～-24 dB），5.69–5.74 是 -45～-53 dB 的低频残声，和 that 之间隔着 5.745–5.75 的 -58～-60 dB 低谷，不连着词；右头切在 5.751125 过零点，之后 5.755 起一路升进 that 的 /ð/（5.77 -32.8、5.80 -8.6 dB），保留
#  S18 [8.357667, 8.556167, 紧贴词头]：convey 的 eɪ 到 8.325 收尾，8.3575 低谷 -57.5 dB（左头）；8.37–8.55 是 -40～-50 dB 的吸气（重心 2.5–3.0 kHz、低频 -5～-26 dB）；8.555 低谷 -54.6 dB（右头），8.5575–8.59 低频 -1 dB 是 and 的浊音起音（保留），8.595 起 and 的元音
out={"no":"38","title_en":"The Web Beneath the Woods","title_zh":"林下之网","title_fx":{"hl":["Web","Woods"],"ghost":[]},"sentences":[],"核对确认":CONF,"结尾解说":"简述","allow_clash":["linking","nitrogen","offspring","doubled","critics"],
     "说明放宽特批":{"S18":{"倍数":"整屏","依据":"用户 2026-10-25 看 25 简述截图：“以后以后一定要合理的安排，不要压缩成这个样子……这个地方特批一下”（用户同意记录：原话适用以后各篇，26 起沿用）"}},
     "非人声区间":{"S11":[[2.767958,2.990125,"紧贴两头"]],"S12":[[1.737542,2.0475,"紧贴词尾"],[5.505,5.774917,"紧贴词头"]],"S13":[[3.18,3.355792,"紧贴词头"]],"S18":[[5.432792,5.751125,"紧贴词头"],[8.357667,8.556167,"紧贴词头"]]},
     "停顿处除阻":{"S11":{"2":[2.76,2.990125,"t"]}},
     "换行变更已获同意":{"S14":"用户原话“改为偏向于 于 要在 towards 的正下方。”“Positive results作为一个重点词汇。”（2026-11-03，S14 拆组标色，换行随之变）","S12":"用户原话“在26项野外研究中，网络帮助和阻碍幼苗的频率大致相同，”（2026-11-03，S12 第1块中文改写，按新语序拆组，换行随之变）","S5":"用户原话“knit into 就重点词汇。 把...编织进”（2026-11-03，S5 knit … into 拆组标色，换行随之变）","S2":"用户原话“刚需要标注的是把in也标注进去。 把.....罩进....里 都要标色”“这个要标注重点词汇，幼苗”（2026-11-03，S2 enclosed … in、seedlings 拆组标色，换行随之变）"},
     "高亮按实际开口":True,"高亮开口门槛":40,
     "术语":{"Canadian":"加拿大的","paper birch":"纸桦","Douglas fir":"花旗松","Nature":"《自然》","wood-wide web":"林木万维网"}}
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 核对 import 生成并核对
生成并核对(S, out)
