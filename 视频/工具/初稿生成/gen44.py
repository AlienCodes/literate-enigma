import json,re,glob,os
# 第44篇初稿（逐词对照）：S = [(段, [chunk, ...])]，chunk = ([(英文组, 中文组), ...], 可选 note)
# 2026-11-03 重点词中文沿用文章定稿（铁律），只按《翻译风格》调格式；短语型用法整体标（T22）；不用破折号（T36）。
S=[
(1,[[[("In a 1955","在1955年的一次"),("**referendum**,","**全民公投**(referendum)中，"),("about","约"),("83 per cent","83%的"),("of voters","投票者"),("chose","选择"),("to keep","继续"),("driving on the left,","靠左行驶，")],
     "（keep doing：继续做某事）"],
    [[("an **overwhelmingly**","**压倒性地**(overwhelmingly)"),("clear","明确"),("**rejection**","**否决了**(rejection)"),("of change.","改变。")],
     "（an overwhelmingly clear rejection of change：\n同位语，概括前面的投票结果）"]]),
(1,[[[("On 10 May 1963, however,","然而1963年5月10日，"),("**legislators** in **parliament**","**议会**(parliament)中的**议员**(legislators)"),("**overruled**","**推翻了**(overruled)"),("the **electorate**,","**全体选民**(electorate)的意见，")],
     "（in parliament：后置定语，修饰 legislators）"],
    [[("approving","批准"),("right-hand traffic from 1967","从1967年起改为靠右行驶。")],
     "（approving…：现在分词短语作状语，补充说明结果）"],
    [[("**in defiance of**","他们全然**不顾**(in defiance of)"),("a **populace**","这一计划在**民众**(populace)中"),("among whom the plan was **unpopular**.","**不得人心**(unpopular)。")],
     "（in defiance of：不顾，无视；\namong whom the plan was unpopular：定语从句，修饰 populace）"]]),
(2,[[[("The case","理由"),("rested on","在于与邻国保持"),("**conformity**.","**一致**(conformity)。")],
     "（rest on：基于，取决于）"]]),
(2,[[[("Norway and Finland","挪威和芬兰"),("drove on the right,","都靠右行驶，"),("with about five million border crossings a year,","每年约有500万车次过境，")],
     "（with＋名词：独立结构，补充说明情况）"],
    [[("so","因此"),("a left-hand","靠左的"),("**orientation**","**行车方向**(orientation)"),("meant","意味着"),("**isolation**","**孤立**(isolation)"),("and","和"),("**inconvenient**","**不便**(inconvenient)的"),("journeys.","出行。")]]]),
(2,[[[("Safety","安全方面"),("favoured **alignment** too.","也支持**统一**(alignment)。")]]]),
(2,[[[("About","约"),("90 per cent","90%的"),("of cars","汽车"),("were","是"),("left-hand drive,","左舵车，")],
     "（left-hand drive：左舵，方向盘在车的左侧）"],
    [[("so","于是"),("**motorists**","**驾车者**(motorists)"),("**overtaking** on narrow two-**lane** **highways**","在狭窄的双**车道**(lane)**公路**(highways)上**超车**(overtaking)时，"),("risked **head-on** collisions.","有发生**迎头**(head-on)相撞的危险。")],
     "（overtaking on…：现在分词短语作后置定语，修饰 motorists；\nrisk＋名词：有……的危险）"]]),
(3,[[[("A","一个"),("state","国家"),("body","机构"),("ran the **mammoth** **preparation** under a **logo**, a large H with an arrow.","以一个大写H加箭头作为**标志**(logo)，主持这项**浩大**(mammoth)的**准备工作**(preparation)。")],
     "（under a logo：在……标志下；\na large H with an arrow：同位语，补充说明 logo）"]]),
(3,[[[("Its **propaganda**","它的**宣传**(propaganda)"),("included","包括"),("a song contest on television,","一场电视歌曲比赛，")],
     "（propaganda：这里指政府的宣传活动，不含贬义）"],
    [[("and the winning","获胜的"),("**jingle**,","**广告歌**(jingle)"),("whose **lyrics**","用**歌词**(lyrics)"),("urged","劝"),("people","人们"),("to keep right,","靠右行驶，"),("reached","登上了"),("fifth in the chart.","排行榜第五名。")],
     "（whose lyrics…：非限制性定语从句，修饰 jingle）"]]),
(3,[[[("Some 360,000","约36万"),("items of","件"),("**signage**","**标识**(signage)"),("were changed,","被更换，")],
     "（some＋数字：大约）"],
    [[("and a **massive**","一支由1,000多辆右侧开门的新公交车组成的**庞大**(massive)"),("**fleet** of over 1,000 new buses with right-hand doors","**车队**(fleet)"),("was **procured**.","也已**购置**(procured)到位。")],
     "（a fleet of…：由……组成的车队；\nwith right-hand doors：后置定语，修饰 buses）"]]),
(4,[[[("The **transition**","**转换**(transition)"),("came on Sunday 3 September 1967.","于1967年9月3日星期日进行。")]]]),
(4,[[[("A **curfew**","**宵禁**(curfew)"),("kept","令"),("**non-essential**","**非必要**(non-essential)"),("vehicles","车辆"),("off the **asphalt** from one to six,","在凌晨1点至6点不得驶上**柏油路**(asphalt)，")],
     "（keep A off B：使 A 不进入 B）"],
    [[("with essential","必要"),("traffic","车辆"),("**exempt**.","可以**豁免**(exempt)。")],
     "（with＋名词＋形容词：独立结构，补充说明情况）"]]),
(4,[[[("At ten to five,","4点50分，"),("all","所有"),("traffic","车辆"),("stopped","停下，"),("and **crawled**","**缓缓挪**(crawled)"),("across,","到另一侧，")],
     "（ten to five：差十分五点，即4点50分）"],
    [[("restarting at five,","5点重新出发，"),("before **dawn**,","此时还在**黎明**(dawn)之前，"),("with its direction","行驶方向"),("**flipped**.","已经**翻转**(flipped)。")],
     "（restarting…：现在分词短语作状语；\nwith＋名词＋过去分词：独立结构）"]]),
(4,[[[("Stockholm and Malmö","斯德哥尔摩和马尔默的"),("had a longer **closure**,","**封闭**(closure)时间更长，"),("from Saturday morning","从星期六上午"),("to Sunday afternoon,","持续到星期日下午，")]],
    [[("while crews","工人们在此期间"),("reconfigured","重新调整了"),("**junctions**.","**路口**(junctions)。")],
     "（while：引导时间状语从句，在……期间）"]]),
(5,[[[("On the following Monday,","随后的星期一，"),("125 accidents were reported,","报告的事故有125起，"),("against","而"),("130 to 198 on earlier Mondays,","此前几个星期一为130至198起；")],
     "（against：与……相比）"],
    [[("a **statistical**","这一**统计**(statistical)上的"),("**improvement**","**改善**(improvement)"),("put down to","被归因于"),("the **heightened** care of **hesitant** drivers.","**犹豫**(hesitant)的驾车人**格外**(heightened)小心。")],
     "（a statistical improvement：同位语，概括前面的事故数字；\nput down to：归因于，过去分词短语作后置定语）"]]),
(5,[[[("The **nervousness**","**紧张情绪**(nervousness)"),("apparently","似乎"),("**subsided**","逐渐**平息**(subsided)，"),("and **prudent** habits","**谨慎**(prudent)的习惯"),("**faded**,","也慢慢**消退**(faded)，")]],
    [[("for by 1969","到1969年，"),("accident and fatality rates","事故率和死亡率"),("had **reverted to**","已**回到**(reverted to)"),("their","原来的"),("**baseline**.","**基准**(baseline)水平，便是明证。")],
     "（for：连词，表示推断的依据；\nrevert to：回到原先的状态）\n"
     "（简述：1955年瑞典全民公投，约83%的投票者选择继续靠左行驶。\n"
     "1963年，议会推翻民意，批准从1967年起改为靠右。\n"
     "理由是邻国挪威和芬兰都靠右，过境车辆多；\n"
     "而且大多数汽车是左舵车，超车容易迎头相撞。\n"
     "国家机构以大写H加箭头为标志主持准备，\n"
     "宣传歌曲登上排行榜第五，约36万件标识被更换，\n"
     "还购置了1,000多辆右侧开门的新公交车。\n"
     "1967年9月3日凌晨，所有车辆在4点50分停下换到另一侧，5点重新出发。\n"
     "随后的星期一事故反而减少，因为司机格外小心；\n"
     "但到1969年，事故率和死亡率又回到了原来的水平。）"]]),
]
CONF={"合组":{
 "S1 83 per cent":"对齐不了：per cent 是一个单位“%”，拆开不通",
 "S6 90 per cent":"对齐不了：per cent 是一个单位“%”，拆开不通",
 "S1 driving on the left":"对齐不了：on the left 方式状语，中文“靠左行驶”必须放到动词前",
 "S2 legislators in parliament":"对齐不了：in parliament 后置定语，中文“议会中的议员”必须提前",
 "S2 right-hand traffic from 1967":"对齐不了：from 1967 时间状语，中文“从1967年起改为靠右行驶”必须放到前面",
 "S2 among whom the plan was unpopular":"对齐不了：among whom 定语从句修饰 populace，中文“这一计划在民众中不得人心”改成主谓结构，“这一计划”必须提前",
 "S2 a populace among whom the plan was unpopular":"对齐不了：among whom 定语从句修饰 populace，中文“这一计划在民众中不得人心”改成主谓结构，populace 必须放进从句里",
 "S4 drove on the right":"对齐不了：on the right 方式状语，中文“靠右行驶”必须放到动词前",
 "S4 with about five million border crossings a year":"对齐不了：a year 中文“每年”必须放到最前，border crossings 中文“车次过境”",
 "S5 favoured alignment too":"对齐不了：too 中文“也”必须放到动词前",
 "S6 left-hand drive":"对齐不了：left-hand drive 是一个名词“左舵车”，拆开不通",
 "S6 overtaking on narrow two-lane highways":"对齐不了：overtaking on A 中文“在 A 上超车”，地点状语必须放到动词前",
 "S6 risked head-on collisions":"对齐不了：risk A 中文“有发生 A 的危险”，“的危险”必须放到最后",
 "S7 ran the mammoth preparation under a logo, a large H with an arrow":"对齐不了：under a logo 方式状语，中文“以……作为标志，主持……”必须放到动词前",
 "S8 a song contest on television":"对齐不了：on television 后置定语，中文“电视歌曲比赛”必须把“电视”提前",
 "S8 to keep right":"对齐不了：keep right 是固定说法“靠右行驶”，拆开不通",
 "S8 fifth in the chart":"对齐不了：in the chart 中文“排行榜第五名”必须把“排行榜”提前",
 "S9 and a massive":"对齐不了：a fleet of A 中文“一支由 A 组成的庞大车队”，of 结构和 with 后置定语都必须提到“庞大”前",
 "S9 fleet of over 1,000 new buses with right-hand doors":"对齐不了：of 结构和 with 后置定语中文已提到“庞大”前，这里只剩“车队”",
 "S9 a massive fleet of over 1,000 new buses with right-hand doors":"对齐不了：a fleet of A 中文“一支由 A 组成的车队”，of 结构和 with 后置定语都必须提到“车队”前",
 "S9 and a massive fleet of over 1,000 new buses with right-hand doors":"对齐不了：a fleet of A 中文“一支由 A 组成的车队”，of 结构和 with 后置定语都必须提到“庞大的车队”前",
 "S10 came on Sunday 3 September 1967":"对齐不了：时间状语中文“于1967年9月3日星期日进行”必须放到动词前",
 "S11 off the asphalt from one to six":"对齐不了：from one to six 时间状语，中文“在凌晨1点至6点”必须放到动词前；keep A off B 中文“令 A 不得驶上 B”",
 "S12 crawled across":"对齐不了：crawl across 中文“缓缓挪到另一侧”",
 "S12 restarting at five":"对齐不了：at five 时间状语，中文“5点重新出发”必须放到动词前",
 "S13 had a longer closure":"对齐不了：中文“封闭时间更长”，longer 必须放到后面",
 "S13 while crews":"对齐不了：while 中文“在此期间”放到主语“工人们”后面",
 "S14 125 accidents were reported":"对齐不了：被动 were reported 中文“报告的事故有125起”，数字必须放到后面",
 "S14 130 to 198 on earlier Mondays":"对齐不了：on earlier Mondays 时间状语，中文“此前几个星期一”必须提前",
 "S14 the heightened care of hesitant drivers":"对齐不了：the care of A 中文“A 小心”，of 结构语序必须倒过来",
 "S15 accident and fatality rates":"对齐不了：rates 同时修饰 accident 和 fatality，中文“事故率和死亡率”每个都带“率”"},
"对齐":{
 "S2-3 among whom the plan was unpopu":"among whom 定语从句修饰 populace，中文“这一计划在民众中不得人心”改成主谓结构，“这一计划”提前",
 "S9-2 fleet of over 1,000 new buses ":"of 结构和 with 后置定语中文“由1,000多辆右侧开门的新公交车组成的”已提到“庞大”前",
 "S1-1 chose to keep driving on the l":"on the left 方式状语，中文“靠左行驶”必须放到动词前",
 "S2-1 On 10 May 1963, however,":"however 插入语，中文“然而”放句首；日期中文按“年月日”顺序",
 "S2-2 right-hand traffic from 1967":"from 1967 时间状语，中文“从1967年起”必须提前",
 "S2-3 a populace among whom the plan":"among whom 定语从句修饰 populace，中文“这一计划在民众中不得人心”从句改成主谓结构",
 "S4-1 with about five million border":"a year 中文“每年”必须放到最前",
 "S6-2 overtaking on narrow two-lane ":"地点状语 on narrow two-lane highways 中文必须放到“超车”前",
 "S7-1 ran the mammoth preparation un":"under a logo 方式状语，中文必须放到动词前",
 "S8-1 a song contest on television,":"on television 后置定语，中文“电视歌曲比赛”必须把“电视”提前",
 "S8-2 fifth in the chart.":"in the chart 中文“排行榜第五名”必须把“排行榜”提前",
 "S9-2 and a massive fleet of over 1,":"a fleet of A 中文“由 A 组成的车队”，of 结构和 with 后置定语必须提前",
 "S10-1 came on Sunday 3 September 196":"时间状语中文“于……进行”必须放到动词前",
 "S11-1 off the asphalt from one to si":"from one to six 时间状语，中文必须放到动词前",
 "S13-1 from Saturday morning":"介词短语，中文“从星期六上午”",
 "S14-1 130 to 198 on earlier Mondays,":"on earlier Mondays 时间状语，中文“此前几个星期一”必须提前",
 "S14-2 the heightened care of hesitan":"the care of A 中文“A 小心”，of 结构语序必须倒过来",
 "S15-2 accident and fatality rates":"rates 同时修饰两个名词，中文“事故率和死亡率”"},
"短语":{
 "S1 rejection … of":"不是搭配：of 引出否决的对象（change），rejection 单独就是“否决”，同速查表 the rejection of a proposal",
 "S2 in … parliament":"不是搭配：in parliament 是普通地点后置定语“议会中的”，parliament 单独就是“议会”",
 "S2 overruled … from":"不是搭配：from 1967 属于 approving right-hand traffic，和 overruled 无关",
 "S3 on … conformity":"不是搭配：on 属于 rested on（在于），conformity 单独就是“一致”",
 "S6 overtaking … on":"不是搭配：on narrow two-lane highways 是地点状语（在公路上），overtake 单独就是“超车”",
 "S9 fleet … of":"不是搭配：of 引出车队的组成（over 1,000 new buses），fleet 单独就是“车队”，同速查表 a fleet of taxis",
 "S12 crawled … with":"不是搭配：with its direction flipped 是独立结构，和 crawled 无关",
 "S15 subsided … for":"不是搭配：for 是连词（表示推断的依据），引出后面的分句",
 "S15 faded … for":"不是搭配：for 是连词（表示推断的依据），引出后面的分句"},
"数字":{"S9-1 360,000":"Some 360,000 中文按文章定稿写作“约36万”，数值相同（360,000 = 36万）"},
"数字写法":{"S11-1 one":"from one to six 指钟点，文章定稿中文写“凌晨1点至6点”，数值相同（one = 1）","S11-1 six":"文章定稿中文写“6点”，数值相同（six = 6）","S12-2 five":"restarting at five 指钟点，文章定稿中文写“5点”，数值相同（five = 5）"},
"牛津逗号":{"S12 At ten to five, all traffic stopped and":"不是三项并列：stopped and crawled across 只有两项，restarting 是分词短语作状语","S15 and prudent habits faded, for by 1969 accident and":"不是三项并列：accident and fatality rates 只有两项，for 引出另一个分句"},
"排版指令":{"S2-2 改为":"不是排版指令：“批准从1967年起改为靠右行驶”是译文本身（文章定稿原文），“改为”是“改成”的意思"}}
# S9 非人声区间 [4.24, 4.516042]：2026-11-03 逐段看声音实测（S9 w）：changed 的 /dʒ/ 摩擦 3.89–3.99（重心 4–4.9 kHz），/d/ 除阻 4.035–4.05（-36 dB）保留；4.05–4.25 静音（-58～-68 dB）；4.27–4.475 从 -56 升到 -39 dB 再落到 -48 dB、重心 2.3–2.8 kHz、低频 -10～-22 dB，是吸气声（A19）；4.48–4.51 -45～-52 dB 低频占优的气声尾，经 4.515–4.52 的 -57/-62 dB 低谷和 and 隔开；右头 4.516042 是低谷里的过零点，and 4.525 起音、4.535 元音 -22 dB 完整
# S12 停顿插入点 第3个标点 5.252667：2026-11-03 逐段看声音实测（S12 w）：five, before 配音没停顿，five 的 /v/ 摩擦到 5.25（重心 2.2–3.6 kHz、周期 0.45），5.255–5.31 是 before 的 /b/ 浊音杠（-28～-31 dB、重心 310–850 Hz、低频 -1 dB），5.32 /b/ 除阻（重心 2.6 kHz）；程序选的 5.285 落在 /b/ 浊音杠中间，会把 30 ms 浊音留在 five 后面，改到 /v/ 和 /b/ 交界 5.252667（过零点）
CONF["停顿位置"]={"S12 five, / before @5.253":"2026-11-03 逐段看声音实测（S12 w）：five 的 /v/ 摩擦到 5.25（重心 2.2–3.6 kHz），5.255–5.31 是 before 的 /b/ 浊音杠（重心 310–850 Hz），5.32 /b/ 除阻；插入点 5.252667 是两者交界的过零点（停顿插入点手写），不切前后词（A42）","S12 dawn, / with @6.195":"2026-11-03 逐段看声音实测（S12 w）：dawn 的 /n/ 浊音（-21～-33 dB、重心 0.5–1 kHz、周期 0.5）到 6.17，6.175–6.18 降到 -40/-51 dB，6.19–6.205 是两词之间最低一段（-46～-49 dB），6.21 起 with 的 /w/（-37～-41 dB）、6.23 起元音；6.195 落在最低处（-49.4 dB），不切前后词（A42）","S2 electorate, / approving @6.750":"2026-11-03 逐段看声音实测（S2 w）：electorate 的 ə 到 6.655 落到 -47 dB，6.685 是词尾 /t/ 的弱除阻（-52 dB），6.695–7.155 全是 -63～-73 dB 静音，7.165 起 approving 的 ɐ（-50→-20 dB）；停顿 6.750–7.155 整段落在静音里，不碰前后词（A42）"}
# S14 除阻加强 第1个 [9.425, 9.515, -3.0]（K154 擦音压低，主会话 2026-11-03 定走 (b)）：逐段看声音实测（S14 w）：a 的 ɐ 到 9.42（重心 3.3 kHz 起转擦音），9.425–9.51 是 statistical 第一个 /s/（-5～-12.5 dB、重心 5.6–6.3 kHz、低频 -40～-48 dB），9.515 起降到 -37 dB、9.52–9.54 /t/ 闭塞、9.545 除阻；原版成片 /s/ 5–10 kHz 峰 -11.45 dB（中位数 -19.79），音频体检齿音 8.34/8.06 超 6.43；音标试 12 种最多只降 1.3 dB，过不了线
CONF["非人声"]={"8.91–8.94s": {"配音指纹": "21efe6263229", "依据": "2026-11-03 44 逐 10 ms 看实际声音（疑点清单 dossier_44）：S1 w 5.88–5.92：keep 的 /p/ 除阻后，driving 的 /d/ 浊音杠（-27～-33 dB、周期 0.27–0.47、低频 0～-3 dB、重心 0.3–1.3 kHz），w 5.93 /d/ 除阻（重心 1.9 kHz）、5.94 起 dɹ 摩擦，属于 driving", "实测": {"最响dB": -31.6, "重心Hz": 557, "周期": 0.47, "低频dB": -1.2}}, "22.17–22.18s": {"配音指纹": "21efe6263229", "依据": "2026-11-03 44 逐 10 ms 看实际声音（疑点清单 dossier_44）：S2 w 7.28–7.295：electorate, 后停顿里 approving 的起音（-49～-51 dB、低频 0 dB），w 7.30 起 ɐ -18 dB，属于 approving", "实测": {"最响dB": -48.9, "重心Hz": 1802, "周期": 0.0, "低频dB": -0.2}}, "39.56–39.65s": {"配音指纹": "21efe6263229", "依据": "2026-11-03 44 逐 10 ms 看实际声音（疑点清单 dossier_44）：S4 w 5.585–5.67：year 的 ɹ 收尾衰减（-40～-48 dB、重心 1.4–1.8 kHz、低频 -3～-13 dB、周期 0.16–0.38），w 5.67 起降到 -57/-66 dB 进停顿，属于 year", "实测": {"最响dB": -36.9, "重心Hz": 1674, "周期": 0.2, "低频dB": -7.3}}, "44.61–44.73s": {"配音指纹": "21efe6263229", "依据": "2026-11-03 44 逐 10 ms 看实际声音（疑点清单 dossier_44）：S4 w 10.64–10.74：journeys 的 i 到 /z/ 之间的弱化段（-38～-50 dB、周期 0.2–0.43、低频 -4～-13 dB），w 10.75 起 /z/（重心 4.7–5.8 kHz），在词中间，属于 journeys", "实测": {"最响dB": -36.6, "重心Hz": 3490, "周期": 0.25, "低频dB": -5.3}}, "50.52–50.53s": {"配音指纹": "21efe6263229", "依据": "2026-11-03 44 逐 10 ms 看实际声音（疑点清单 dossier_44）：S6 w 1.85–1.865：cars 的 /z/ 在 1.83 收尾、1.84 低谷 -62 dB，1.85 -55 dB 低频占优是 were 的 /w/ 起音，1.86 起 -37→-16 dB，属于 were", "实测": {"最响dB": -36.4, "重心Hz": 1589, "周期": 0.0, "低频dB": -0.8}}, "51.80–51.96s": {"配音指纹": "21efe6263229", "依据": "2026-11-03 44 逐 10 ms 看实际声音（疑点清单 dossier_44）：S6 w 3.125–3.29：drive 的 aɪ 弱化收尾（-35～-49 dB、重心 1.5–3.5 kHz）接 /v/ 清化摩擦（3.22–3.28，重心 3.6–5.0 kHz、低频 -19～-35 dB），3.29 起降到 -58～-73 dB 进停顿，属于 drive", "实测": {"最响dB": -38.5, "重心Hz": 3727, "周期": 0.18, "低频dB": -4.3}}, "80.06–80.17s": {"配音指纹": "21efe6263229", "依据": "2026-11-03 44 逐 10 ms 看实际声音（疑点清单 dossier_44）：S9 w 3.73–3.835：changed 的 eɪ 到 /n/（-34～-42 dB、周期 0.2–0.59、低频 -2～-9 dB），3.80–3.88 是 dʒ 的 /d/ 闭塞，3.89 起 /ʒ/ 摩擦，在词中间，属于 changed", "实测": {"最响dB": -35.2, "重心Hz": 1970, "周期": 0.33, "低频dB": -6.4}}, "80.37–80.41s": {"配音指纹": "21efe6263229", "依据": "2026-11-03 44 逐 10 ms 看实际声音（疑点清单 dossier_44）：S9 w 4.035–4.07：changed 的词尾 /d/ 除阻：前面 4.01–4.03 闭塞 -65～-69 dB，4.04 除阻 -34 dB（重心 2.4 kHz），4.05–4.07 衰减到 -57 dB，属于 changed", "实测": {"最响dB": -35.4, "重心Hz": 2898, "周期": 0.16, "低频dB": -13.1}}, "85.91–86.00s": {"配音指纹": "21efe6263229", "依据": "2026-11-03 44 逐 10 ms 看实际声音（疑点清单 dossier_44）：S9 w 9.625–9.72：procured 的 ʊɹ 后 /d/ 浊音闭塞（-35～-49 dB、周期 0.15–0.43、重心 0.9–1.6 kHz），9.72–9.73 闭塞 -57/-59 dB，9.74 /d/ 除阻，属于 procured", "实测": {"最响dB": -36.9, "重心Hz": 1482, "周期": 0.27, "低频dB": -5.6}}, "85.98–86.00s": {"配音指纹": "21efe6263229", "依据": "2026-11-03 44 逐 10 ms 看实际声音（疑点清单 dossier_44）：S9 w 9.70–9.72：procured 的 /d/ 浊音闭塞末段（-41～-49 dB、低频 -2 dB），9.74 除阻，属于 procured", "实测": {"最响dB": -40.6, "重心Hz": 881, "周期": 0.32, "低频dB": -1.7}}, "97.64–97.67s": {"配音指纹": "21efe6263229", "依据": "2026-11-03 44 逐 10 ms 看实际声音（疑点清单 dossier_44）：S11 w 4.71–4.74：six, 后停顿里 with 的浊音起音（-48～-52 dB、低频 0～-2 dB、周期 0.27–0.5），4.76 起 /w/ -31→-16 dB，属于 with", "实测": {"最响dB": -45.7, "重心Hz": 1996, "周期": 0.31, "低频dB": -0.1}}, "104.77–104.79s": {"配音指纹": "21efe6263229", "依据": "2026-11-03 44 逐 10 ms 看实际声音（疑点清单 dossier_44）：S12 w 3.89–3.91：across, 后停顿里 restarting 的起音（-47～-61 dB、低频 0 dB），3.92 起 ɹ -45→-22 dB，属于 restarting", "实测": {"最响dB": -49.6, "重心Hz": 2442, "周期": 0.24, "低频dB": -0.2}}, "107.88–107.89s": {"配音指纹": "21efe6263229", "依据": "2026-11-03 44 逐 10 ms 看实际声音（疑点清单 dossier_44）：S12 w 6.195–6.21：dawn 的 /n/ 在 6.18 降到 -51 dB，6.19–6.21 -46～-47 dB 低频占优是 with 的 /w/ 起音，6.23 起 -30→-25 dB，属于 with", "实测": {"最响dB": -45.0, "重心Hz": 1794, "周期": 0.0, "低频dB": -2.0}}, "109.19–109.20s": {"配音指纹": "21efe6263229", "依据": "2026-11-03 44 逐 10 ms 看实际声音（疑点清单 dossier_44）：S12 w 7.505–7.52：flipped 的 /p/ 除阻：前面 7.46–7.50 闭塞 -58～-70 dB，7.51 除阻 -41 dB（低频 -19 dB），7.52–7.54 是 /t/ 闭塞，7.55 /t/ 除阻，属于 flipped", "实测": {"最响dB": -36.3, "重心Hz": 2745, "周期": 0.0, "低频dB": -17.3}}, "116.08–116.09s": {"配音指纹": "21efe6263229", "依据": "2026-11-03 44 逐 10 ms 看实际声音（疑点清单 dossier_44）：S13 w 5.565–5.585：afternoon, 后停顿里 while 的起音（-52～-57 dB、低频 -1 dB），5.61 起 /w/ -43→-15 dB，属于 while", "实测": {"最响dB": -49.0, "重心Hz": 2324, "周期": 0.21, "低频dB": -0.2}}, "118.17–118.19s": {"配音指纹": "21efe6263229", "依据": "2026-11-03 44 逐 10 ms 看实际声音（疑点清单 dossier_44）：S13 w 7.66–7.675：junctions 的 /n/ 到 /z/ 的过渡（7.67 -41 dB、低频 -2 dB、重心 1.1 kHz），在词中间，属于 junctions", "实测": {"最响dB": -41.0, "重心Hz": 1394, "周期": 0.0, "低频dB": -2.2}}, "121.14–121.17s": {"配音指纹": "21efe6263229", "依据": "2026-11-03 44 逐 10 ms 看实际声音（疑点清单 dossier_44）：S14 w 1.515–1.54：Monday, 后停顿里 one 的起音（-50～-61 dB、低频 0～-7 dB），1.56 起 /w/ -31→-20 dB，属于 one", "实测": {"最响dB": -49.9, "重心Hz": 2731, "周期": 0.33, "低频dB": -0.2}}, "133.35–133.44s": {"配音指纹": "21efe6263229", "依据": "2026-11-03 44 逐 10 ms 看实际声音（疑点清单 dossier_44）：S14 w 13.78–13.87：drivers 的 ɚ 弱化段（-37～-49 dB、周期 0.15–0.37、低频 -1～-16 dB、重心 0.8–3.2 kHz），13.87 起 /z/（重心 4.6–5.7 kHz），在词中间，属于 drivers", "实测": {"最响dB": -35.6, "重心Hz": 1993, "周期": 0.26, "低频dB": -1.8}}, "134.60–134.62s": {"配音指纹": "21efe6263229", "依据": "2026-11-03 44 逐 10 ms 看实际声音（疑点清单 dossier_44）：S15 w 0.02–0.035：句首 The 的 /ð/ 起始（-43→-34 dB），0.04–0.05 -26/-22 dB，0.06 起 ə -6 dB，属于 The", "实测": {"最响dB": -35.6, "重心Hz": 4401, "周期": 0.0, "低频dB": -2.4}}, "135.60–135.62s": {"配音指纹": "21efe6263229", "依据": "2026-11-03 44 逐 10 ms 看实际声音（疑点清单 dossier_44）：S15 w 1.02–1.035：nervousness 和 apparently 之间 apparently 的起音（-55～-57 dB、低频 0～-3 dB），1.04 起 ɐ -20 dB，属于 apparently", "实测": {"最响dB": -43.1, "重心Hz": 1609, "周期": 0.0, "低频dB": -1.1}}, "138.60–138.72s": {"配音指纹": "21efe6263229", "依据": "2026-11-03 44 逐 10 ms 看实际声音（疑点清单 dossier_44）：S15 w 4.02–4.135：faded 的词尾 /d/：4.02–4.10 浊音闭塞（-37～-54 dB、周期 0.14–0.44、低频 -1～-8 dB、重心 0.8–2.8 kHz），4.11 除阻 -39 dB，4.12–4.13 衰减，4.14 起 -62～-72 dB 进停顿，属于 faded", "实测": {"最响dB": -35.8, "重心Hz": 1638, "周期": 0.24, "低频dB": -1.9}}, "138.63–138.68s": {"配音指纹": "21efe6263229", "依据": "2026-11-03 44 逐 10 ms 看实际声音（疑点清单 dossier_44）：S15 w 4.05–4.095：faded 的词尾 /d/ 浊音闭塞中段（-42～-54 dB、低频 -1～-3 dB、重心 0.8–1.8 kHz），4.11 除阻，属于 faded", "实测": {"最响dB": -39.4, "重心Hz": 1035, "周期": 0.35, "低频dB": -1.4}}, "142.62–142.66s": {"配音指纹": "21efe6263229", "依据": "2026-11-03 44 逐 10 ms 看实际声音（疑点清单 dossier_44）：S15 w 7.84–7.885：accident 的词尾 /t/ 除阻：7.82–7.84 闭塞 -56～-61 dB，7.85 除阻 -35 dB（重心 2.0 kHz、低频 -11 dB），7.86–7.88 衰减，7.89–7.92 静音，7.93 起 and，属于 accident", "实测": {"最响dB": -31.0, "重心Hz": 2038, "周期": 0.23, "低频dB": -12.9}}, "146.47–146.58s": {"配音指纹": "21efe6263229", "依据": "2026-11-03 44 逐 10 ms 看实际声音（疑点清单 dossier_44）：S15 w 11.69–11.805：baseline 的 aɪ 到 /n/ 的弱化收尾（-35～-53 dB、周期 0.1–0.45、低频 -2～-12 dB），句末自然衰减，属于 baseline", "实测": {"最响dB": -36.3, "重心Hz": 2694, "周期": 0.31, "低频dB": -6.9}}}
CONF["删除段"]={"S4 raw 3.1550-3.2550": {"类型": "紧贴两头的非人声", "配音指纹": "21efe6263229", "依据": "2026-11-03 实际声音（非人声区间 S4 [3.145, 3.245042, 紧贴两头]，w 比 raw 早 0.01 s）：about 的 /t/ 除阻 w 3.13（-39 dB）、3.14–3.15 回落到 -53 dB，左头切在过零点 3.145，紧贴除阻衰减之后；3.16–3.24 是 -44～-51 dB 的气声（重心 2.4–3.6 kHz、低频 -9～-19 dB、周期 ≤0.28），删掉部分最响 -43.6 dB，不是词；右头切在过零点 3.245042，3.25 起 five 的 /f/（重心 4.5→6.3 kHz、低频 -18～-32 dB）完整保留；两边都没有 -55 dB 低谷，只能紧贴切"}, "S10 raw 2.9650-3.0200": "2026-11-03 配音指纹 21efe6263229 实际声音（非人声区间 S10 [2.945, 2.995]）：of 的 /v/ 到 w 2.93 收尾，2.94–2.96 -55～-67 dB，2.97 是 15 ms 孤立杂音（-39 dB、重心 2.7 kHz、低频 -18 dB），2.98–3.00 -61～-69 dB；两侧 -55/-59 dB 干净，3.01 起 September 的 /s/ 没碰；复核报 lost 是这一下杂音本身","S1 raw 2.4100-2.7936": {"类型": "紧贴词头的非人声", "配音指纹": "21efe6263229", "依据": "2026-11-03 实际声音（S1 raw）：referendum, 的停顿；2.41–2.43 -58～-64 dB，2.44–2.74 从 -58 升到 -39 dB 的吸气（重心 1.9–2.8 kHz、低频 -9～-29 dB、周期 ≤0.35，不是词）；2.75–2.79 -45～-46 dB、低频 -1～-9 dB 是 about 的声门起音，和吸气之间没有 -55 dB 低谷，只能紧贴切；about 的元音 2.80 起完整"}, "S2 raw 3.1288-3.5250": {"类型": "紧贴词尾的非人声", "配音指纹": "21efe6263229", "依据": "2026-11-03 实际声音（S2 raw）：however, 的停顿；however 的 ɚ 3.11 -33 dB、3.12 -47 dB 收尾，切点 3.1288 紧贴词尾衰减之后；3.15–3.45 是 -50～-53 dB 的吸气（重心 1.8–2.9 kHz、低频 -8～-23 dB、周期 ≤0.30），删掉部分最响 -48 dB，不是词；3.53 起 legislators，没碰"}, "S2 raw 10.7150-11.0350": "2026-11-03 配音指纹 21efe6263229 实际声音（S2 raw）：1967 和 in defiance 之间块停顿；10.72–11.00 从 -52 升到 -39 dB 的吸气（重心 2.5–3.7 kHz、低频 -13～-25 dB、周期 ≤0.37，是吸气声，不是词），两侧 -57/-60 dB；11.05 起 in，没删；复核报 lost 是吸气本身偏响", "S8 raw 3.6750-4.0736": {"类型": "紧贴词头的非人声", "配音指纹": "21efe6263229", "依据": "2026-11-03 实际声音（S8 raw）：television, 的停顿；3.67–3.70 -58～-61 dB，3.71–4.03 从 -55 升到 -34 dB 的吸气（重心 2.2–3.4 kHz、低频 -13～-31 dB、周期 ≤0.42，不是词）；4.04–4.08 -41～-46 dB、低频 0～-8 dB 是 and 的声门起音，和吸气之间没有 -55 dB 低谷，只能紧贴切；and 的元音 4.09 起完整"}, "S9 raw 4.0851-4.5300": "2026-11-03 配音指纹 21efe6263229 实际声音（S9 raw）：changed, 的停顿（非人声区间 S9 [4.24, 4.516042]）；/d/ 除阻 4.05 -36 dB 保留，4.08–4.26 静音 -59～-68 dB，4.27–4.48 从 -57 升到 -40 dB 的吸气（重心 2.0–2.8 kHz、低频 -10～-22 dB），4.49–4.51 低频占优气声尾，4.52 低谷 -55 dB；4.53 起 and，没删；复核报 lost 是吸气本身偏响", "S14 raw 8.9450-9.3750": "2026-11-03 配音指纹 21efe6263229 实际声音（S14 raw）：Mondays, 的停顿；/z/ 8.90–8.93 收尾，8.94–9.15 静音 -56～-64 dB，9.16–9.33 从 -56 升到 -41 dB 的吸气（重心 2.2–2.8 kHz、低频 -6～-28 dB），9.34–9.35 -52 dB 气声尾，9.36–9.37 低谷 -60/-62 dB；9.38 起 a，没删；复核报 lost 是吸气本身偏响"}
CONF["高亮"]={"S2 第3块":{"开始读":25.785,"配音指纹":"21efe6263229","依据":"2026-11-03 直接读 work_44/a.wav 逐 10 ms：1967 后的块停顿到 25.76 是全静音（-240 dB），25.77 -66、25.78 -57、25.79 -36 dB 是 in 的开口，25.81 起 -23～-20 dB；高亮 25.77 与开始读只差 0.015 s。甲 25.60 是带时长模型算的，没扣掉删掉的吸气段（S2 raw 10.715–11.035），不准"}}
CONF["机器复听"]={"S5":{"配音指纹":"21efe6263229","依据":"2026-11-03 实测（S5 w）：favoured 配音音标 fˈeɪvɚd，读音核对 0；ɚ 0.76–0.80（-10～-13 dB），0.81 降到 -20 dB，0.82–0.83 是 20–30 ms 的 /d/ 浊音闭塞（低频 -1 dB、重心 0.4–0.5 kHz），0.84 起 alignment 的 ɐ；中间没有 /ɪ/ 元音、也没有 /t/ 爆破，favorite 要多一个 ɪt；/d/ 在元音前读成浊闪音，parakeet 一路听成 favorite，交用户听"}}
# S4 非人声区间 [3.145, 3.245042, 紧贴两头]（两头都是过零点；左头紧贴 about 的 /t/ 除阻衰减，右头紧贴 five 的 /f/ 起始，两边都没有 -55 dB 低谷）：2026-11-03 疑点清单 #3 实测（S4 w）：about 的 /t/ 除阻 3.13（-39 dB），3.14–3.15 回落到 -53 dB；3.16–3.25 是 -44～-51 dB 的气声（重心 2.4–4.5 kHz、低频 -9～-19 dB、周期 ≤0.28），不是词；3.26 起 five 的 /f/（重心 6.3–7.4 kHz）
# S10 非人声区间 [2.945, 2.995]：2026-11-03 疑点清单 #12 实测（S10 w）：of 的 /v/ 到 2.93 收尾，2.94–2.96 -55～-67 dB，2.97 是 15 ms 孤立的杂音（-39 dB、重心 2.7 kHz、低频 -18 dB），2.98–3.00 又回到 -61～-69 dB，3.01 起 September 的 /s/；两边都是静音，不是词的声音
out={"no":"44","title_en":"The Night Sweden Switched Sides","title_zh":"一夜之间换边开车","title_fx":{"hl":["Sweden","Switched"],"ghost":[]},"sentences":[],"核对确认":CONF,"结尾解说":"简述",
     "除阻加强":{"S14":{"1":[9.425,9.515,-3.0]}},
     "非人声区间":{"S4":[[3.145,3.245042,"紧贴两头"]],"S9":[[4.24,4.516042]],"S10":[[2.945,2.995]]},
     "停顿插入点":{"S12":{"3":[5.252667,"交界"]}},
     "高亮按实际开口":True,"高亮开口门槛":40,
     "术语":{"Sweden":"瑞典","Norway":"挪威","Finland":"芬兰","Stockholm":"斯德哥尔摩","Malmö":"马尔默"}}
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 核对 import 生成并核对
生成并核对(S, out)
