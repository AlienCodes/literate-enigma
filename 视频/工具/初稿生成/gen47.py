import json,re,glob,os
# 第47篇初稿（逐词对照）：S = [(段, [chunk, ...])]，chunk = ([(英文组, 中文组), ...], 可选 note)
# 2026-11-04 重点词中文沿用文章定稿（铁律），只按《翻译风格》调格式；形容词重点词“的”进粗体；短语型用法整体标（T22）；三项并列加牛津逗号（T18）；不用破折号（T36）。
S=[
(1,[[[("Yellowstone's","黄石公园那些"),("**iconic**","**标志性的**(iconic)"),("grey","灰"),("wolves","狼，"),("had been **exterminated** by 1926.","到1926年已遭**赶尽杀绝**(exterminated)。")],
     "（had been exterminated：过去完成时被动语态，\n到过去某时已经被……）"]]),
(1,[[[("On 12 January 1995","1995年1月12日，"),("eight","八只"),("wolves **captured** in Alberta, Canada,","在加拿大艾伯塔省**捕获**(captured)的狼")],
     "（captured in Alberta, Canada：过去分词短语作后置定语，修饰 wolves）"],
    [[("were **hauled** to the park in **crates**;","装在**板条箱**(crates)里，一路**拖运**(hauled)进了公园；"),("six more followed.","随后又来了六只。")],
     "（in crates：方式状语；\nsix more：又六只）"]]),
(1,[[[("Released from **enclosures** in late March,","3月下旬，它们被放出**围栏**(enclosures)，")],
     "（Released from enclosures：过去分词短语作状语，\n逻辑主语是 they）"],
    [[("they **roamed** the **wilderness**.","得以在**荒野**(wilderness)中**四处游荡**(roamed)。")]]]),
(2,[[[("In February 2014","2014年2月，"),("a **viral video**","一段**火了的视频**(viral video)，"),("**narrated by** writer George Monbiot","**由**(narrated by)作家乔治·蒙比奥特**解说**(narrated by)，")],
     "（Viral videos 指代的是那些在互联网上火了的视频。）"],
    [[("**spun**","**编织**(spun)出"),("a","一个"),("**compelling**","**引人入胜的**(compelling)"),("**narrative**:","**故事**(narrative)。")],
     "（spin a narrative：编织出一个故事）"],
    [[("elk,","片中说，麋鹿"),("thinned by wolves","被狼捕杀得数量变少，"),("and","又"),("**wary of** them,","处处**提防**(wary of)着狼，"),("**retreated from** valleys,","便**撤离了**(retreated from)河谷，")],
     "（thinned by wolves and wary of them：插入语，补充说明 elk；\nbe wary of：提防）"],
    [[("letting","这让"),("**willows**","**柳树**(willows)"),("**flourish**","**繁茂**(flourish)起来，"),("and riverbanks","河岸也"),("**stabilise**.","**稳固**(stabilise)下来。")],
     "（因为狼群的回归（威慑力） -> 逼得麋鹿不敢在河边吃草（行为改变） -> 柳树得以疯狂生长（植被恢复） -> 最终固定了河岸的泥土（地貌重塑））"]]),
(2,[[[("Ecologists","生态学家"),("call this","把这称为"),("a **trophic cascade**:","**营养级联**(trophic cascade)：")],
     "（call A B：把 A 称为 B）"],
    [[("**predators**","**捕食者**(predators)"),("eat","吃掉"),("or","或"),("**deter**","**吓阻**(deter)"),("plant-eaters,","食草动物，"),("and","然后"),("**vegetation**","**植被**(vegetation)"),("**rebounds**.","得以**恢复生长**(rebounds)。")]]]),
(3,[[[("Yet","然而，"),("the **census**","**普查**(census)结果首先就"),("**undermined**","**动摇了**(undermined)"),("the thinning claim:","鹿被狼吃少了这一说法。")],
     "（the thinning claim：狼让麋鹿变少的说法）"],
    [[("elk on the park's northern range","黄石北部草场的麋鹿"),("**peaked at** about 19,000 in January 1994","在1994年1月**达到**(peaked at)约19,000头**的峰值**(peaked at)，")],
     "（on the park's northern range：后置定语，修饰 elk；\npeak at：达到……的峰值）"],
    [[("and were **dwindling** before wolves arrived,","狼还没来就已**日渐减少**(dwindling)；")]],
    [[("**depleted** by **hunters**, **drought**, and bears.","鹿群被**猎人**(hunters)、**干旱**(drought)和熊不断地**消耗**(depleted)着。")],
     "（depleted by…：过去分词短语作状语，补充说明减少的原因）"]]),
(3,[[[("Fear","恐惧一说"),("looked weak too:","看来也站不住。")]],
    [[("in June 2013","2013年6月，"),("Arthur Middleton's","阿瑟·米德尔顿领导的"),("University of Wyoming team","怀俄明大学团队"),("found that","发现，")]],
    [[("**collared** elk east of the park","园区东侧**戴项圈的**(collared)麋鹿"),("kept","照样"),("**grazing**","**吃草**(grazing)，")],
     "（项圈是科学家给麋鹿戴的GPS追踪器，用来获取它们真实的活动数据，从而用铁证戳破了“狼一靠近鹿就吓得不敢吃草”的传说。）"],
    [[("unless","除非"),("wolves","狼"),("**ventured** within half a mile.","**胆敢踏入**(ventured)进半英里以内。")],
     "（unless：除非）"]]),
(4,[[[("Trees","树木方面的证据也"),("**fared no better**:","**好不到哪里去**(fared no better)：")],
     "（fare no better：也好不到哪里去）"],
    [[("in November 2021","2021年11月，"),("Utah State University's","犹他州立大学的"),("Elaine Brice","伊莱恩·布赖斯"),("showed that","指出，")]],
    [[("**sampling** only","只**抽样测量**(sampling)"),("the tallest","最高的"),("**aspens**","**山杨**(aspens)，"),("**overstated** **regrowth**","会**把**(overstated)它们的**再生**(regrowth)程度**夸大**(overstated)"),("four- to sevenfold.","四到七倍。")],
     "（sampling only the tallest aspens：动名词短语作主语；\nfour- to sevenfold：四到七倍）"]]),
(4,[[[("The deeper","更根本的"),("**flaw**","**缺陷**(flaw)"),("was water.","出在水上。")]]]),
(4,[[[("Colorado State University's","科罗拉多州立大学的"),("Tom Hobbs","汤姆·霍布斯"),("and","和"),("David Cooper","戴维·库珀")]],
    [[("had **excluded** elk with fences","用围栏**把**(excluded)麋鹿**挡在外面**(excluded)，"),("and built","并修建"),("**artificial**","**人工**(artificial)"),("beaver","海狸"),("**dams**.","**坝**(dams)。")],
     "（with fences：方式状语，用围栏）"]]),
(4,[[[("In January 2024","2024年1月，"),("they reported:","他们报告说，")]],
    [[("**eroding**","**不断冲蚀**(eroding)河床的"),("streams","溪流"),("had cut","下切"),("so deep that","太深，"),("**stunted**","那些**矮小的**(stunted)"),("willows","柳树"),("no longer reached","已经够不着"),("water.","水了。")],
     "（eroding：现在分词作前置定语，修饰 streams；\nso…that…：如此……以至于……）"]]),
(5,[[[("In January 2025","2025年1月，"),("Oregon State University's William Ripple, an **advocate** of the **hypothesis**,","这一**假说**(hypothesis)的**倡导者**(advocate)、俄勒冈州立大学的威廉·里普尔")],
     "（an advocate of the hypothesis：同位语，补充说明 William Ripple）"],
    [[("reported","发文称，"),("one of the world's strongest cascades;","黄石的级联效应位居世界最强之列；")],
     "（one of the＋最高级＋复数名词：最……之一）"],
    [[("critics","批评者则"),("**disputed** his methods.","**对**(disputed)他的方法提出**质疑**(disputed)。")]]]),
(5,[[[("The question","问题"),("is **unresolved**,","仍**悬而未决**(unresolved)，")]],
    [[("but","但"),("the wolves'","狼投下的"),("shadow","影子"),("looks **fainter** than the **fable** suggested,","比**谣传**(fable)所暗示的**更加无力**(fainter)，")],
     "（than the fable suggested：比较状语从句）"],
    [[("and the science","相关研究也要"),("**messier**.","**复杂纠结**(messier)得多。")],
     "（the science messier：省略了 looks）"]]),
(5,[[[("A **discipline** willing to **revise** its **cherished** example","一门**学科**(discipline)如果愿意去**修正**(revise)（甚至推翻）自己最**珍视的**(cherished)完美案例，")],
     "（willing to revise its cherished example：\n形容词短语作后置定语，修饰 discipline）"],
    [[("may deserve more trust than the fable ever did.","那么这门学科，比那个完美的谣传本身更值得信任。")],
     "（than the fable ever did：比较状语从句，did 代替 deserved trust）\n"
     "（简述：黄石公园的狼在1926年就灭绝了，直到1995年才从加拿大重新引进。\n"
     "2014年，网上爆火了一个动人的“生态神话”：\n"
     "说狼来了以后，吓得麋鹿不敢吃树，结果柳树长出来了，河岸也稳固了。\n"
     "但真实情况却被科学数据无情打脸：其实在狼来之前，麋鹿就已经开始减少了；\n"
     "科学家给麋鹿戴上追踪项圈后发现，只要狼没凑到跟前，麋鹿照样该吃吃该喝喝；\n"
     "而且所谓“树木重新繁茂”的数据，被查出严重夸大了4到7倍；\n"
     "柳树长不出来，其实是因为河水水位下降，树根根本喝不到水，跟鹿吃不吃没关系。\n"
     "直到2025年，依然有专家坚称黄石公园的“狼群连锁效应”是世界上最强的，\n"
     "但也遭到了同行的质疑。这事至今没个定论。\n"
     "不过，一个敢于推翻自己完美案例的学科，比那个编出来的童话，更值得信任。）"]]),
]
G={
 "S4 thinned by wolves":"对齐不了：被动 thinned by wolves 中文“被狼捕杀得数量变少”，by wolves 化成“被狼”必须放到动词前",
 "S6 the thinning claim":"对齐不了：thinning claim 中文沿用文章定稿“鹿被狼吃少了这一说法”，thinning 化成一整句说法的内容放在“说法”前",
 "S6 elk on the park's northern range":"对齐不了：on the park's northern range 是后置定语，修饰 elk，中文“黄石北部草场的麋鹿”定语必须提前",
 "S6 and were dwindling before wolves arrived":"对齐不了：before wolves arrived 是时间状语从句，中文“狼还没来就已日渐减少”时间必须放到动词前",
 "S7 looked weak too":"对齐不了：look weak 中文沿用文章定稿“看来也站不住”，weak 化成“站不住”，too 化成“也”放到中间，拆开不通",
 "S7 collared elk east of the park":"对齐不了：east of the park 是后置定语，修饰 elk，中文“园区东侧戴项圈的麋鹿”地点必须提前",
 "S7 ventured within half a mile":"对齐不了：within half a mile 中文“进半英里以内”，within 化成“进……以内”包住数量，拆开不通",
 "S8 four- to sevenfold":"对齐不了：four- to sevenfold 是倍数“四到七倍”，four- 省去 fold，拆开数字不通",
 "S10 had excluded elk with fences":"对齐不了：with fences 是方式状语，中文“用围栏把麋鹿挡在外面”方式必须放到动词前，exclude 化成“把……挡在外面”包住宾语",
 "S11 no longer reached":"对齐不了：no longer reached 中文“已经够不着”，否定 no 化进“不”里，拆开不通",
 "S12 one of the world's strongest cascades":"对齐不了：one of the＋最高级 中文沿用文章定稿“级联效应位居世界最强之列”，one of 化成“之列”放到最后",
 "S13 looks fainter than the fable suggested":"对齐不了：比较级 fainter than A 中文“比 A 所说的要淡”，than 引出的对象必须放到形容词前",
 "S14 A discipline willing to revise its cherished example":"对齐不了：willing to revise its cherished example 是形容词短语作后置定语，修饰 discipline，中文“一门肯修正自己珍视的案例的学科”定语必须提前",
 "S14 deserve more trust than the fable ever did":"对齐不了：比较级 more trust than A 中文“比 A 更值得信赖”，than 引出的对象必须放到动词前",
}
CONF={"合组":G,"对齐":{
 "S1-1 had been exterminated by 1926.":"by 1926 是时间状语，中文“到1926年已遭赶尽杀绝”时间必须放到动词前",
 "S2-1 wolves captured in Alberta, Ca":"captured in Alberta, Canada 是过去分词短语作后置定语，修饰 wolves，中文“在加拿大艾伯塔省捕获的狼”定语必须提前",
 "S2-2 were hauled to the park in cra":"in crates 是方式状语，中文“装在板条箱里，一路拖运进了公园”（沿用文章定稿）方式必须放到动词前",
 "S3-1 Released from enclosures in la":"in late March 是时间状语，中文“3月下旬，它们被放出围栏”时间必须提到句首，主语 they 也要提前",
 "S6-2 elk on the park's northern ran":"on the park's northern range 是后置定语，修饰 elk，中文“黄石北部草场的麋鹿”定语必须提前",
 "S6-2 peaked at about 19,000 in Janu":"in January 1994 是时间状语，中文“在1994年1月达到约19,000头的峰值”时间必须放到动词前，peak at 化成“达到……的峰值”包住数量",
 "S6-3 and were dwindling before wolv":"before wolves arrived 是时间状语从句，中文“狼还没来就已日渐减少”时间必须放到动词前",
 "S6-4 depleted by hunters, drought, ":"被动 depleted by A 中文沿用文章定稿“A 不断削减着鹿群”，by 引出的施动者必须放到动词前",
 "S7-3 collared elk east of the park":"east of the park 是后置定语，修饰 elk，中文“园区东侧戴项圈的麋鹿”地点必须提前",
 "S7-4 ventured within half a mile.":"within half a mile 中文“进半英里以内”，within 化成“进……以内”包住数量，拆开不通",
 "S10-2 had excluded elk with fences":"with fences 是方式状语，中文“用围栏把麋鹿挡在外面”方式必须放到动词前",
 "S12-1 Oregon State University's Will":"an advocate of the hypothesis 是同位语，中文沿用文章定稿“这一假说的倡导者、俄勒冈州立大学的威廉·里普尔”同位语提到人名前，of 结构语序倒过来",
 "S12-2 one of the world's strongest c":"one of the＋最高级 中文“位居世界最强之列”，one of 化成“之列”放到最后",
 "S13-2 looks fainter than the fable s":"比较级 fainter than A 中文“比 A 所说的要淡”，than 引出的对象必须放到形容词前",
 "S14-1 A discipline willing to revise":"willing to revise its cherished example 是后置定语，修饰 discipline，中文定语必须提前",
 "S14-2 deserve more trust than the fa":"比较级 more trust than A 中文“比 A 更值得信赖”，than 引出的对象必须放到动词前"},
"短语":{
 "S2 captured … in":"不是搭配：in Alberta, Canada 是地点状语（在艾伯塔省），capture 单独就是“捕获”",
 "S2 captured … to":"不是搭配：to 属于 were hauled to the park，和 captured 无关",
 "S2 hauled … to":"不是搭配：haul 本身就是“拖运”，to the park 只引出目的地，中文“进了公园”已译出",
 "S2 in … crates":"不是搭配：in crates 是普通介词短语“装在板条箱里”，in 表示容器里，不是 in flocks 那类固定用法",
 "S6 depleted … by":"不是搭配：by 引出被动的施动者（猎人、干旱和熊），deplete 单独就是“削减”",
 "S6 by … hunters":"不是搭配：by 是被动句引出施动者的普通介词，和 hunters 不成固定用法",
 "S7 collared … of":"不是搭配：of 属于 east of the park（园区东侧），和 collared 无关",
 "S7 ventured within":"不是搭配：ventured 用的就是速查表第一个意思“冒险去（某处），斗胆前往”，中文“闯”；within half a mile 是普通介词短语，引出闯入的范围（半英里以内）",
 "S8 overstated … to":"不是搭配：to 属于 four- to sevenfold（四到七倍），和 overstated 无关",
 "S10 excluded … with":"不是搭配：with fences 是方式状语（用围栏），exclude 单独就是“挡在外面”",
 "S12 advocate … of":"不是搭配：of 引出倡导的对象（the hypothesis），advocate 单独就是“倡导者”，同 gen34 proprietor of"},
"牛津逗号":{"S4 elk, thinned by wolves and":"不是三项并列：thinned by wolves and wary of them 只有两项，作插入语修饰 elk",
 "S4 retreated from valleys, letting willows flourish and":"不是三项并列：willows flourish and riverbanks stabilise 只有两项，都是 letting 的宾语"},
"方向":{"S2-2 more→随后又来了六只。":"six more 中文“又……六只”，“又”就是 more（再多），方向一致",
 "S6-3 before→狼还没来就已日渐减少；":"before wolves arrived 中文“狼还没来”，“还没来”就是在狼来之前，方向一致"}}
CONF.setdefault("同词异译",{})["disputed：对/质疑"]="S12 dispute A“对 A 提出质疑”被“他的方法提出”隔开，“对”和“质疑”是同一个意思的两部分（T23，用户 2026-11-05 原话“对  质疑 这三个字都要标色。 对应dispute”），不是两种译法"
CONF.setdefault("同词异译",{})["overstated：把/夸大"]="S8 overstate A“把 A 夸大”被“它们的再生程度”隔开，“把”和“夸大”是同一个意思的两部分（T23，用户 2026-11-05 原话“把....夸大 都要标色 对应 overstate”），不是两种译法"
CONF.setdefault("同词异译",{})["narrated by：由/解说"]="S4 narrated by A“由 A 解说”被“作家乔治·蒙比奥特”隔开，“由”和“解说”是同一个意思的两部分（T22/T23，用户 2026-11-04 原话“narrated by 也标注为重点词汇……对应的意思: 由..... 解说”），不是两种译法"
CONF.setdefault("同词异译",{})["excluded：把/挡在外面"]="S10 exclude A“把 A 挡在外面”被“麋鹿”隔开，“把”和“挡在外面”是同一个意思的两部分（T22/T23），不是两种译法"
CONF["对齐"]["S4-1 narrated by writer George Monb"]="narrated by A 中文“由 A 解说”（用户 2026-11-04 原话），A 夹在“由”和“解说”中间，拆开不通"
CONF["停顿位置"]={
 "S2 Alberta, / Canada, @5.260":"2026-11-04 逐 2.5 ms 实测（S2 w）：Alberta 的 ə 浊音到 5.20（-22 dB、周期 0.3、低频 -1 dB），5.215 -40、5.24 -51～-57 dB 衰减，5.255–5.2625 降到 -67～-68.5 dB，是两词之间最低处（过零 5.260292）；5.265 起回升，5.2675–5.27 是 Canada 的 /k/ 除阻（-22～-14 dB、重心 3.9 kHz、低频 -33 dB）。插在 5.260 前后两词都没切到",
 "S5 plant-eaters, / and @5.590":"2026-11-04 逐 2.5 ms 实测（S5 w）：eaters 的 /z/ 5.54–5.58（-17～-22 dB、重心 5.1–5.7 kHz），5.5825 -26、5.585 -28、5.5875 -30 dB 是 /z/ 的尾巴；5.590 -34.2 dB 是两词交界最低处（过零 5.590125）；5.5925 起 -18 dB、重心 1.6 kHz、5.595 周期 0.41，是 and 的起音。程序原插 5.585 落在 /z/ 尾巴上，改插 5.590125，/z/ 整段留给 eaters"}
CONF["句首突起"]={"第9句":"实测：原始合成句首 25 ms 渐起（前 10 ms 比本句最响低 70 dB），A20 切 -55 dB 以下后剩 /ð/ 本身起音：S9 w 0.020 -53、0.025 -45、0.0275 -25 dB（重心 4.4 kHz 摩擦），没切坏；试过 ðˈə、ði 两种写法，ðˈə 渐起最缓但 The 重读改语气，主会话 2026-11-04 定不改读音、不加淡入"}
# 非人声区间（2026-11-04 逐 2.5 ms 实测 dossier_47，两词之间无标点、模型自己吸的气；自动切点写的原样保留）：
# S1 [2.5125, 2.7825]：wolves 的 /z/ 到 2.505（重心 3.8 kHz）收尾，2.5125 降到 -60.5 dB；2.535–2.76 是 -49～-55 dB、重心 2.1–2.9 kHz、低频 -10～-20 dB、周期 ≤0.33 的吸气；2.7825 外侧 -61.6～-64.9 dB，had 的 /h/ 2.856 起，没碰
# S2 [2.87, 3.245]（原自动切点 [2.87, 3.13] 往后延）：3.135–3.18 是切剩的一团 -47～-57 dB 声音，前后都是数字静音，3.18–3.245 降到 -60～-72 dB；eight 3.2525 起（-47→-4 dB），没碰
# S7 [7.285958, 7.540042, 紧贴两头]（右端外侧 -54～-55 dB 不够 -55，改紧贴 found 起音、落在过零点）：team 的 /m/ 浊音到 7.2825（-29.7 dB、低频 -1 dB、重心 0.7 kHz），7.285 起 -38～-48 dB、重心 1.2–2.9 kHz、低频 -13～-22 dB、周期 ≤0.28 的吸气一直到 7.53（-55 dB）；7.5425 起 found 的唇齿接触低频声和 /f/（7.555 起重心 4.7–7 kHz），没碰
# S8 [7.2875, 7.5425, 紧贴词尾]：Brice 的 /s/ 到 7.28（重心 3.5–4.3 kHz）衰减，7.2875 -52.8 dB；7.29–7.53 是 -45～-55 dB、重心 2.4–2.9 kHz、低频 -8～-22 dB、周期 ≤0.25 的吸气；7.5425 -62 dB 最低，7.5575 起 showed 的 /ʃ/（重心 3.6–4.6 kHz），没碰
# S10 [3.9775, 4.21, 紧贴两头]：Cooper 的 ɚ 浊音到 3.975（-36.8 dB、低频 -0.5 dB）；3.9775–4.2075 是 -40～-53 dB、重心 1.2–3.6 kHz 的吸气；4.21 -55.3 dB 最低，4.2125 起 had 的声门起音和 /h/（4.225 起重心 2.4 kHz，4.27 进元音），没碰
CONF["非人声"]={"5.01–5.08s": {"配音指纹": "1b9156c4758b", "实测": {"最响dB": -32.3, "重心Hz": 526, "周期": 0.77, "低频dB": -0.8}, "依据": "2026-11-04 47 逐 2.5 ms 看实际声音（S1 w 1.5700–1.6400）：S1 iconic / grey：iconic 的 /k/ 除阻后，w 1.57–1.64 是 grey 的 /ɡ/ 浊音杠（周期 0.77、低频 -0.8 dB 占优、重心 0.5 kHz、-32～-49 dB），1.686 起 /ɡ/ 除阻进 ɹ，属于 grey", "词头": "g"}, "19.73–19.82s": {"配音指纹": "1b9156c4758b", "实测": {"最响dB": -35.2, "重心Hz": 1516, "周期": 0.28, "低频dB": -3.5}, "依据": "2026-11-04 47 逐 2.5 ms 看实际声音（S2 w 9.5150–9.6050）：S2 followed.：w 9.515–9.605 是 oʊ 衰减进 /d/ 闭塞的浊音（周期 0.28–0.36、低频 -3.5 dB、重心 1.5 kHz），9.59 处 -53 dB 闭塞后 9.60 /d/ 除阻 -28 dB，再衰减到句末，属于 followed", "词尾": "d"}, "16.21–16.23s": {"配音指纹": "1b9156c4758b", "实测": {"最响dB": -44.8, "重心Hz": 1620, "周期": 0.0, "低频dB": -0.2}, "依据": "2026-11-04 47 逐 2.5 ms 看实际声音（S2 w 6.0350–6.0500）：S2 Canada, / were：逗号停顿后 w 6.035–6.05 从 -58 升到 -45 dB、低频 -0.2 dB，紧接着 6.06 起 -35→-15 dB，是 were 的 /w/ 起音，属于 were", "词头": "w"}, "19.79–19.81s": {"配音指纹": "1b9156c4758b", "实测": {"最响dB": -35.2, "重心Hz": 918, "周期": 0.33, "低频dB": -1.9}, "依据": "2026-11-04 47 逐 2.5 ms 看实际声音（S2 w 9.5650–9.5900）：S2 followed. 的 /d/：w 9.565–9.59 是闭塞里的浊音（周期 0.33、低频 -1.9 dB、重心 0.9 kHz），之后 /d/ 除阻 -28 dB，属于 followed", "词尾": "d"}, "42.11–42.23s": {"配音指纹": "1b9156c4758b", "实测": {"最响dB": -37.2, "重心Hz": 3296, "周期": 0.25, "低频dB": -4.2}, "依据": "2026-11-04 47 逐 2.5 ms 看实际声音（S4 w 15.8000–15.9200）：S4 stabilise：w 15.80–15.92 在 stabilise 词中（音素 l 15.77、aɪ 15.94），-35～-51 dB、重心 3.3 kHz、低频 -4.2 dB 的 /l/→aɪ 过渡，之后升到 -20 dB 的 aɪ，属于 stabilise，不能切"}, "37.31–37.33s": {"配音指纹": "1b9156c4758b", "实测": {"最响dB": -51.4, "重心Hz": 2404, "周期": 0.0, "低频dB": -0.2}, "依据": "2026-11-04 47 逐 2.5 ms 看实际声音（S4 w 11.0900–11.1050）：S4 them, / retreated：逗号停顿后 w 11.09–11.105 -60～-51 dB、低频 -0.4 dB，接着 11.11 起 -35→-13 dB，是 retreated 的 /ɹ/ 起音，属于 retreated", "词头": "ɹ"}, "39.06–39.09s": {"配音指纹": "1b9156c4758b", "实测": {"最响dB": -48.6, "重心Hz": 4539, "周期": 0.16, "低频dB": -2.5}, "依据": "2026-11-04 47 逐 2.5 ms 看实际声音（S4 w 12.7500–12.7750）：S4 valleys, / letting：逗号停顿后 w 12.75–12.775 -54～-64 dB，没有低谷直接升到 12.78 的 -44、-27、-17 dB，是 letting 的 /l/ 起音前段，属于 letting", "词头": "l"}, "66.75–66.89s": {"配音指纹": "1b9156c4758b", "实测": {"最响dB": -36.6, "重心Hz": 1843, "周期": 0.21, "低频dB": -3.6}, "依据": "2026-11-04 47 逐 2.5 ms 看实际声音（S6 w 14.7750–14.9150）：S6 bears.：w 14.775–14.915 在 bears 词中（音素 ɛ 14.72、ɹ 14.84、z 14.99），-37～-51 dB、重心 1.8 kHz 的 ɹ 段，之后升到 -20 dB，属于 bears，不能切"}, "63.45–63.47s": {"配音指纹": "1b9156c4758b", "实测": {"最响dB": -39.4, "重心Hz": 1812, "周期": 0.0, "低频dB": -2.4}, "依据": "2026-11-04 47 逐 2.5 ms 看实际声音（S6 w 11.6550–11.6700）：S6 arrived 的 /v/→/d/：w 11.655–11.67 落在 arrived 词尾衰减段中间（-39～-47 dB、低频 -2.4 dB），属于 arrived", "词尾": "d"}, "65.49–65.50s": {"配音指纹": "1b9156c4758b", "实测": {"最响dB": -31.5, "重心Hz": 559, "周期": 0.0, "低频dB": -2.0}, "依据": "2026-11-04 47 逐 2.5 ms 看实际声音（S6 w 13.7900–13.8050）：S6 hunters, / drought：逗号停顿后 w 13.79–13.805 -59→-38 dB、重心 0.56 kHz、低频 -2 dB，是 drought 的 /d/ 浊音杠，13.82 起 -30 dB，属于 drought", "词头": "d"}, "63.34–63.61s": {"配音指纹": "1b9156c4758b", "实测": {"最响dB": -28.4, "重心Hz": 0, "周期": 0.0, "低频dB": 0.0}, "依据": "2026-11-04 47 逐 2.5 ms 看实际声音（S6 w 11.5500–11.8150）：S6 arrived,：w 11.55–11.815 是 /v/ 擦音衰减（-25～-45 dB）接 /d/：末段 -36 dB 的 /d/ 除阻后衰减到 -59 dB，属于 arrived 词尾（收尾 265 ms 是 vd 两个浊辅音）", "词尾": "d"}, "69.42–69.51s": {"配音指纹": "1b9156c4758b", "实测": {"最响dB": -35.1, "重心Hz": 1505, "周期": 0.32, "低频dB": -1.7}, "依据": "2026-11-04 47 逐 2.5 ms 看实际声音（S7 w 1.3950–1.4800）：S7 too:：w 1.395–1.48 是 uː 的自然衰减（-27→-58 dB、周期 0.32、重心 1.5 kHz、低频 -1.7 dB），连续降到数字静音，中间不断，属于 too", "词尾": "uː"}, "75.18–75.19s": {"配音指纹": "1b9156c4758b", "实测": {"最响dB": -46.0, "重心Hz": 2740, "周期": 0.0, "低频dB": -0.5}, "依据": "2026-11-04 47 逐 2.5 ms 看实际声音（S7 w 7.5400–7.5550）：S7 team / found：吸气已切到 7.540042，w 7.54–7.555 -44～-48 dB、低频 -0.5～-1 dB 是唇齿接触声，7.555 起就是 /f/ 擦音（重心 4.7–7 kHz），属于 found", "词头": "f"}, "86.58–86.61s": {"配音指纹": "1b9156c4758b", "实测": {"最响dB": -50.7, "重心Hz": 3120, "周期": 0.34, "低频dB": -0.4}, "依据": "2026-11-04 47 逐 2.5 ms 看实际声音（S8 w 4.6550–4.6750）：S8 one / Utah：w 4.655–4.675 -51～-56 dB、低频 -0.4 dB，接着升到 -46、-34、-25 dB，是 Utah 的 /j/ 起音，属于 Utah", "词头": "j"}, "94.93–94.96s": {"配音指纹": "1b9156c4758b", "实测": {"最响dB": -41.1, "重心Hz": 2008, "周期": 0.52, "低频dB": -2.4}, "依据": "2026-11-04 47 逐 2.5 ms 看实际声音（S8 w 13.0800–13.1100）：S8 sevenfold.：w 13.08–13.11 是 /d/ 闭塞（-51→-79 dB）后除阻 -29 dB（周期 0.52、重心 2 kHz）再衰减，属于 sevenfold 词尾 /d/", "词尾": "d"}, "106.59–106.69s": {"配音指纹": "1b9156c4758b", "实测": {"最响dB": -38.4, "重心Hz": 1773, "周期": 0.32, "低频dB": -3.8}, "依据": "2026-11-04 47 逐 2.5 ms 看实际声音（S10 w 8.2800–8.3850）：S10 dams：w 8.28–8.385 在 dams 词中（音素 d 8.13、æ 8.33），/d/ 除阻后的送气 -39～-50 dB（周期 0.32、重心 1.8 kHz），8.38 起升到 -32 dB 的 æ，属于 dams，不能切"}, "102.64–102.66s": {"配音指纹": "1b9156c4758b", "实测": {"最响dB": -46.6, "重心Hz": 2467, "周期": 0.0, "低频dB": -0.9}, "依据": "2026-11-04 47 逐 2.5 ms 看实际声音（S10 w 4.2100–4.2250）：S10 Cooper / had：吸气已切到 4.210042，w 4.21–4.225 -46～-55 dB、低频 -0.6～-1.9 dB 是 had 的声门起音，4.225 起 /h/（重心 2.4 kHz）连到 4.27 的元音，没有低谷，属于 had", "词头": "h"}, "116.55–116.63s": {"配音指纹": "1b9156c4758b", "实测": {"最响dB": -36.5, "重心Hz": 1561, "周期": 0.23, "低频dB": -8.1}, "依据": "2026-11-04 47 逐 2.5 ms 看实际声音（S11 w 8.8850–8.9650）：S11 water.：w 8.885–8.965 是 ɚ 的自然衰减（-22→-55 dB、周期 0.23、重心 1.6 kHz、低频 -8 dB），连续降到数字静音，属于 water", "词尾": "ɚ"}, "113.80–113.86s": {"配音指纹": "1b9156c4758b", "实测": {"最响dB": -34.4, "重心Hz": 2802, "周期": 0.15, "低频dB": -8.7}, "依据": "2026-11-04 47 逐 2.5 ms 看实际声音（S11 w 6.1350–6.1950）：S11 deep：w 6.135–6.195 是 deep 的 /p/ 除阻（闭塞 -57 dB 后跳到 -34 dB，再 -46～-61 dB 衰减），前后都是静音，属于 deep 词尾 /p/", "词尾": "p"}, "124.83–124.84s": {"配音指纹": "1b9156c4758b", "实测": {"最响dB": -49.7, "重心Hz": 2425, "周期": 0.47, "低频dB": -0.5}, "依据": "2026-11-04 47 逐 2.5 ms 看实际声音（S12 w 7.0350–7.0550）：S12 hypothesis：w 7.035–7.055 在 hypothesis 词头（音素 h 6.99、aɪ 7.07），-46～-55 dB、低频 -0.5 dB，紧接着 7.06 升到 -17 dB 的 aɪ，属于 hypothesis"}, "126.03–126.05s": {"配音指纹": "1b9156c4758b", "实测": {"最响dB": -46.9, "重心Hz": 2225, "周期": 0.29, "低频dB": -0.4}, "依据": "2026-11-04 47 逐 2.5 ms 看实际声音（S12 w 8.1550–8.1800）：S12 hypothesis, / reported：逗号停顿后 w 8.155–8.18 -46～-56 dB、低频占优，接着 8.185 起 -31、-19、-11 dB，是 reported 的 /ɹ/ 起音，属于 reported", "词头": "ɹ"}, "130.99–131.00s": {"配音指纹": "1b9156c4758b", "实测": {"最响dB": -36.9, "重心Hz": 716, "周期": 0.0, "低频dB": -0.8}, "依据": "2026-11-04 47 逐 2.5 ms 看实际声音（S12 w 13.1500–13.1650）：S12 methods：w 13.15–13.165 在 methods 词中（音素 θ 13.12、ə 13.22），θ→ə 过渡处 -36～-58 dB 的一小段，前后都连着词，属于 methods"}, "146.54–146.67s": {"配音指纹": "1b9156c4758b", "实测": {"最响dB": -36.2, "重心Hz": 1427, "周期": 0.26, "低频dB": -3.6}, "依据": "2026-11-04 47 逐 2.5 ms 看实际声音（S14 w 6.3750–6.5050）：S14 did.：w 6.375–6.505 是 ɪ 衰减进 /d/ 闭塞（-31～-54 dB），/d/ 除阻 -38 dB 后衰减到数字静音，属于 did", "词尾": "d"}, "146.57–146.59s": {"配音指纹": "1b9156c4758b", "实测": {"最响dB": -37.1, "重心Hz": 893, "周期": 0.28, "低频dB": -2.0}, "依据": "2026-11-04 47 逐 2.5 ms 看实际声音（S14 w 6.4100–6.4300）：S14 did. 的 /d/ 闭塞浊音：w 6.41–6.43 -37～-50 dB、低频 -2 dB、重心 0.9 kHz，之后 /d/ 除阻，属于 did", "词尾": "d"}, "145.11–145.16s": {"配音指纹": "1b9156c4758b", "实测": {"最响dB": -40.8, "重心Hz": 3589, "周期": 0.15, "低频dB": -13.7}, "依据": "2026-11-04 47 逐 2.5 ms 看实际声音（S14 w 4.9450–4.9900）：S14 trust：w 4.945–4.99 是 trust 的 /t/ 除阻（闭塞后 -41 dB 起、重心 3.6 kHz，衰减到 -55 dB），前后都是静音，属于 trust 词尾 /t/", "词尾": "t"}}
CONF["机器复听"]={"S5":{"配音指纹":"1b9156c4758b","依据":"2026-11-04 实测（配音指纹 1b9156c4758b）：S5 plant-eaters, 停顿后的 and 完整：w 5.595–5.70 是 æ（周期 0.41–0.55、重心 1.2–2.5 kHz），5.66–5.735 是 /n/（重心 0.45–0.7 kHz、周期 0.5、低频 -1～-3 dB），5.74 处 -21 dB 的 /d/ 闭塞后接 vegetation 的 /v/（5.76 起重心 2.6–4.3 kHz、周期 0.46）；parakeet 听对 and，small.en 听成 then 是停顿后元音起得亮"},
 "S13":{"配音指纹":"1b9156c4758b","依据":"2026-11-04 实测（配音指纹 1b9156c4758b）：S13 the wolves' shadow：w 2.535–2.695 ʊ、2.70–2.725 /l/（周期 0.6），2.73–2.78 是浊音 /v/（周期 0.58–0.65、重心 2.6–4.7 kHz、低频 -3～-4 dB），不是清音 /f/；2.785–2.95 是 170 ms 清化的 /z/（周期 0.13–0.25、重心 5–5.5 kHz）直接连 shadow 的 /ʃ/；配音音标 wˈʊlvz 与 wolves 一致，两路识别把清化的 -z 加 shadow 听成 wolf's，交用户听"}}
# S4 第2块 高亮开始 31.71：2026-11-04 逐 10 ms 看 a.wav（配音指纹 1b9156c4758b）：31.60–31.70 是 Monbiot 的 oʊ 尾音（-19～-24 dB、重心 0.7–1.4 kHz），31.71 起重心跳到 3.6、5.9 kHz，是 spun 的 /s/（31.73 起 -11～-15 dB）；乙 31.73、甲 31.76
out={"no":"47","title_en":"Shadows of Wolves Over Yellowstone","title_zh":"黄石公园狼影再现","title_fx":{"hl":["Wolves","Yellowstone"],"ghost":[]},"sentences":[],"核对确认":CONF,"结尾解说":"简述",
     "高亮开始":{"S4 第2块":31.71},
     "换行变更已获同意":{"S4":"用户原话“这句话的翻译改成：一段火了的视频，由作家 乔治蒙比奥特解说 narrated by  也标注为重点词汇……viral video 一起标注重点词汇。”（2026-11-04，S4 第1块拆成三组，换行随之变）"},
     "停顿插入点":{"S5":{"2":[5.590125,"交界"]}},
     "非人声区间":{"S1":[[2.5125,2.7825]],"S2":[[2.87,3.245],[5.776417,6.03,"紧贴词尾"]],"S4":[[10.87,11.065],[12.47,12.745]],"S6":[[9.235,9.513667,"紧贴词头"]],"S7":[[3.898792,4.135,"紧贴词尾"],[7.285958,7.540042,"紧贴两头"]],"S8":[[4.31,4.62],[7.287917,7.5425,"紧贴词尾"]],"S10":[[3.978542,4.210042,"紧贴两头"]],"S11":[[2.398417,2.59,"紧贴词尾"]],"S12":[[2.491708,2.735,"紧贴词尾"],[5.475,5.72875,"紧贴词头"]],"S14":[[3.305,3.565]]},
     "高亮按实际开口":True,"高亮开口门槛":40,
     "术语":{"Yellowstone":"黄石公园","Alberta":"艾伯塔省","Canada":"加拿大","George Monbiot":"乔治·蒙比奥特","Arthur Middleton":"阿瑟·米德尔顿","University of Wyoming":"怀俄明大学","Utah State University":"犹他州立大学","Elaine Brice":"伊莱恩·布赖斯","Colorado State University":"科罗拉多州立大学","Tom Hobbs":"汤姆·霍布斯","David Cooper":"戴维·库珀","Oregon State University":"俄勒冈州立大学","William Ripple":"威廉·里普尔"}}
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 核对 import 生成并核对
生成并核对(S, out)
