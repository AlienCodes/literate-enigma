import json,re,glob,os
# 第59篇初稿（逐词对照）：S = [(段, [chunk, ...])]，chunk = ([(英文组, 中文组), ...], 可选 note)
# 2026-11-07 重点词中文沿用文章定稿（铁律），只按《翻译风格》调格式；短语型用法整体标（T22）；被隔开的意思两处都标（T23）；不用破折号（T36）；三项并列加牛津逗号（T18）。
S=[
(1,[[[("A **layer**","一**层**(layer)"),("of **ozone**","**臭氧**(ozone)"),("**shields** Earth **from**","**为**(shields from)地球**遮挡了**(shields from)"),("much of the sun's","太阳的大部分"),("**ultraviolet**","**紫外**(ultraviolet)"),("**radiation**.","**辐射**(radiation)。")],
     "（shield A from B：为 A 遮挡 B，\n保护 A 不受 B 的伤害）"]]),
(1,[[[("In June 1974","1974年6月，"),("Mario Molina and Sherwood Rowland,","马里奥·莫利纳和舍伍德·罗兰，"),("chemists","两位化学家，"),("in California,","在加州工作，")],
     "（chemists in California：同位语，补充说明两人）"],
    [[("warned in Nature","在《自然》杂志上撰文警告，"),("of a **menace**","有一种**威胁**(menace)"),("in fridges","藏在冰箱"),("and **spray** cans.","和**喷雾**(spray)罐里。")],
     "（warn of…：警告……；\nin fridges and spray cans：后置定语，修饰 menace）"]]),
(1,[[[("Chlorofluorocarbons (CFCs)","氯氟烃（CFCs）"),("are so **inert**","**惰性**(inert)极强，"),("that they","它们"),("drift","能飘升到"),("intact","完好无损地"),("into the stratosphere,","进入平流层，")],
     "（so…that…：如此……以至于……；\nintact：形容词作状语，完好无损地）"],
    [[("high in the **atmosphere**,","也就是高层**大气**(atmosphere)中，")],
     "（high in the atmosphere：补充说明平流层的位置）"],
    [[("where they can","在那里，它们可能"),("**liberate**","**释放**(liberate)出"),("**chlorine**,","**氯**(chlorine)，")],
     "（where…：非限制性定语从句，修饰 stratosphere）"],
    [[("a **catalyst**","氯是一种**催化剂**(catalyst)，"),("that destroys ozone **molecule** after molecule.","会把臭氧**分子**(molecule)一个接一个地破坏掉。")],
     "（a catalyst…：同位语，补充说明 chlorine；\nmolecule after molecule：一个接一个的分子）"]]),
(1,[[[("The pair","两人"),("foresaw","预料到的，是"),("**gradual**","一场**缓慢的**(gradual)"),("**erosion**.","**侵蚀**(erosion)。")]]]),
(2,[[[("The **alarm**,","**警报**(alarm)"),("when it sounded,","真的拉响时，"),("was **abrupt**.","却来得十分**突然**(abrupt)。")],
     "（when it sounded：插入的时间状语从句；\nsound：（警报）响起）"]]),
(2,[[[("In May 1985","1985年5月，"),("Joseph Farman","约瑟夫·法曼"),("and colleagues at the British Antarctic Survey","和英国南极调查局的同事"),("reported that","报告称，")],
     "（at the British Antarctic Survey：后置定语，修饰 colleagues）"],
    [[("ozone over Halley Bay,","哈雷湾上空的臭氧，"),("their","那是他们的"),("Antarctic","南极"),("station,","考察站，"),("had **plummeted** each southern spring since the mid-1970s.","自20世纪70年代中期起，每到南半球春季就**骤降**(plummeted)。")],
     "（their Antarctic station：同位语，补充说明 Halley Bay；\nhad plummeted：过去完成时，表示到报告时为止一直在骤降）"]]),
(2,[[[("Their","他们那台"),("**humble**","**不起眼的**(humble)"),("Dobson","多布森"),("spectrophotometer","分光光度计，"),("**gauged** ozone from the ground.","从地面**测量**(gauged)臭氧。")],
     "（spectrophotometer：分光光度计，测量光谱的仪器）"]]),
(2,[[[("The staff","工作人员"),("were **persistent**,","**持之以恒**(persistent)，"),("reading it","读数时遵循"),("in a **painstaking**","一套**一丝不苟的**(painstaking)"),("**routine**","**例行**(routine)规程，"),("of **manual**","全靠**人工**(manual)"),("**observation**.","**观测**(observation)。")],
     "（reading it…：现在分词短语作伴随状语，it 指分光光度计；\na routine of…：……的例行规程）"]]),
(3,[[[("Yet","然而，"),("NASA's","美国国家航空航天局（NASA）的"),("Nimbus-7","雨云7号"),("**satellite**,","**卫星**(satellite)，")]],
    [[("a **sophisticated** eye","这只**精密的**(sophisticated)眼睛"),("**in orbit**,","**在轨道上运行**(in orbit)，")],
     "（a sophisticated eye in orbit：同位语，\n补充说明卫星）"],
    [[("had recorded","也记录到了"),("the same","同样的"),("lows.","低值。")],
     "（lows：名词复数，低值）"]]),
(3,[[[("Its software","它的软件"),("flagged them as **dubious**,","把这些读数标记为**可疑**(dubious)，")],
     "（flag A as B：把 A 标记为 B）"],
    [[("since","因为"),("ozone that low","这么低的臭氧"),("had never been","此前从没有"),("reliably measured.","被可靠地测到过。")],
     "（that low：that 作副词，这么低，\nozone that low 即这么低的臭氧）"]]),
(3,[[[("NASA says","据NASA的说法，"),("it was still","它还在"),("**verifying** them","**核实**(verifying)这些读数，"),("when Farman published.","就在法曼发表论文的时候。")],
     "（NASA says…：注明是 NASA 一方的说法；\nwhen Farman published：时间状语从句）"]]),
(3,[[[("The **sensor**","**传感器**(sensor)"),("had worked;","并没有出问题；"),("**expectation**","**预期**(expectation)"),("had not.","却出了问题。")],
     "（had not：省略了 worked，\n即 expectation had not worked）"]]),
(4,[[[("**Remarkably**,","**令人称奇的是**(Remarkably)，"),("the response","各国的反应"),("was **swift**.","十分**迅速**(swift)。")]]]),
(4,[[[("In September 1987","1987年9月，"),("**diplomats**","**外交官**(diplomats)们"),("signed","签署了"),("the Montreal **Protocol**,","《蒙特利尔**议定书**(Protocol)》，")]],
    [[("a **binding**","这是一项具有**约束力**(binding)的"),("**accord**","**协定**(accord)，"),("to **curb** CFCs.","用来**限制**(curb)CFCs。")],
     "（a binding accord…：同位语，补充说明议定书；\nto curb CFCs：不定式作后置定语，修饰 accord）"]]),
(4,[[[("**Amendments**","此后的**修正案**(Amendments)"),("**tightened** it:","又**收紧了**(tightened)它的管控：")]],
    [[("in June 1990","1990年6月，"),("**affluent** countries","**富裕**(affluent)国家"),("**pledged** to","**承诺**(pledged)"),("**phase out** CFCs by 2000.","在2000年前**逐步淘汰**(phase out)CFCs。")],
     "（pledge to do：承诺做……；\nphase out：逐步淘汰）"]]),
(4,[[[("In September 2009","2009年9月，"),("the Protocol","该议定书"),("and its parent Vienna Convention","与其所依据的《维也纳公约》一道，")],
     "（its parent Vienna Convention：\n议定书所依据的母公约《维也纳公约》）"],
    [[("became","成为"),("the UN's first treaties to win **universal** ratification.","联合国首批获得**普遍**(universal)批准的条约。")],
     "（to win…：不定式作后置定语，修饰 treaties）"]]),
(5,[[[("In January 2023","2023年1月，"),("a UN-backed **assessment**","一份由联合国支持的**评估**(assessment)报告"),("**forecast**","**预测**(forecast)，")],
     "（UN-backed：由联合国支持的；\nforecast：过去式与原形同形）"],
    [[("**recovery**","臭氧层将**恢复**(recovery)"),("to 1980 levels","到1980年的水平：")],
     "（recovery to 1980 levels：恢复到1980年的水平）"],
    [[("around 2066","约2066年"),("over Antarctica,","在南极上空，"),("2045","2045年"),("over the Arctic,","在北极上空，"),("and 2040","其他地区"),("elsewhere.","则在2040年。")]]]),
(5,[[[("**Healing**","臭氧层的**愈合**(Healing)"),("will take","还需要"),("decades.","数十年。")]]]),
(5,[[[("The sky's **rescue**","天空得以**拯救**(rescue)，"),("began with","始于"),("**diligent** observers","一群**勤勉的**(diligent)观测者，")]],
    [[("who trusted that","他们相信，"),("a **baffling** number","一个**令人费解的**(baffling)数字"),("was no **glitch**,","并不是**小故障**(glitch)，"),("and published it.","于是把它发表了出来。")],
     "（who…：定语从句，修饰 observers；\nwas no glitch：并不是小故障；\nand published it：与 trusted 并列，it 指那个数字）\n"
     "（简述：臭氧层为地球遮挡太阳的大部分紫外辐射。1974年，莫利纳和罗兰警告，\n"
     "冰箱和喷雾罐里的氯氟烃会飘到平流层释放氯，慢慢破坏臭氧。\n"
     "1985年，法曼团队用地面仪器发现南极哈雷湾上空的臭氧每年春季骤降；\n"
     "NASA 卫星也记录到了这些低值，却被软件标为可疑。各国随后迅速行动：\n"
     "1987年签署《蒙特利尔议定书》，修正案又要求富裕国家在2000年前淘汰氯氟烃，\n"
     "2009年它和《维也纳公约》成为联合国首批获普遍批准的条约。\n"
     "2023年的评估预测臭氧层将在几十年内恢复。拯救天空，\n"
     "靠的是相信异常数字不是故障、并把它发表出来的观测者。）"]]),
]
G={
 "S1 much of the sun's":"对齐不了：much of the sun's… 是 of 结构，中文“太阳的大部分”语序倒过来",
 "S2 Mario Molina and Sherwood Rowland":"对齐不了：两个人名，中文“马里奥·莫利纳和舍伍德·罗兰”人名不能拆",
 "S2 warned in Nature":"对齐不了：in Nature 是地点状语，中文“在《自然》杂志上撰文警告”地点必须放到动词前",
 "S3 that destroys ozone molecule after molecule":"对齐不了：中文用把字句“会把臭氧分子一个接一个地破坏掉”，destroys 化成“把……破坏掉”，molecule after molecule 化成“一个接一个地”，拆开不通",
 "S3 high in the atmosphere":"对齐不了：high in the atmosphere 中文“高层大气中”，high 化成“高层”，拆开不通",
 "S6 and colleagues at the British Antarctic Survey":"对齐不了：at the British Antarctic Survey 是后置定语，修饰 colleagues，中文“英国南极调查局的同事”定语必须提前，机构名不能拆",
 "S6 ozone over Halley Bay":"对齐不了：over Halley Bay 是后置定语，修饰 ozone，中文“哈雷湾上空的臭氧”定语必须提前",
 "S6 had plummeted each southern spring since the mid-1970s":"对齐不了：since the mid-1970s 和 each southern spring 是时间状语，中文“自20世纪70年代中期起，每到南半球春季就骤降”时间必须放到动词前",
 "S7 gauged ozone from the ground":"对齐不了：from the ground 是方式状语，中文“从地面测量臭氧”必须放到动词前",
 "S10 flagged them as dubious":"对齐不了：flag A as B 中文用把字句“把这些读数标记为可疑”，flagged 化成“把……标记为”，拆开不通",
 "S10 ozone that low":"对齐不了：that low 后置修饰 ozone，中文“这么低的臭氧”必须提前",
 "S10 reliably measured":"对齐不了：被动 had never been reliably measured，中文“被可靠地测到过”，reliably 和 measured 连成一个说法",
 "S15 phase out CFCs by 2000":"对齐不了：by 2000 是时间状语，中文“在2000年前逐步淘汰CFCs”时间必须放到动词前",
 "S16 and its parent Vienna Convention":"对齐不了：its parent 修饰 Vienna Convention，中文“与其所依据的《维也纳公约》一道”，公约名不能拆",
 "S16 the UN's first treaties to win universal ratification":"对齐不了：to win… 是不定式作后置定语，修饰 treaties，中文“联合国首批获得普遍批准的条约”定语必须提前",
 "S17 a UN-backed assessment":"对齐不了：UN-backed 是复合形容词“由联合国支持的”，中文定语整体在前，不能拆",
}
CONF={"合组":G,
"牛津逗号":{},
}
out={"no":"59","title_en":"Saving the Sky","title_zh":"拯救天空","title_fx":{"hl":["Saving","Sky"],"ghost":[]},"sentences":[],"核对确认":CONF,"结尾解说":"简述",
     "高亮按实际开口":True,"高亮开口门槛":40,
     "术语":{"Mario Molina":"马里奥·莫利纳","Sherwood Rowland":"舍伍德·罗兰","California":"加州","Nature":"《自然》","Chlorofluorocarbons":"氯氟烃","CFCs":"CFCs","Joseph Farman":"约瑟夫·法曼","British Antarctic Survey":"英国南极调查局","Halley Bay":"哈雷湾","Dobson":"多布森","NASA":"NASA","Nimbus-7":"雨云7号","Montreal":"蒙特利尔","Protocol":"议定书","Vienna Convention":"《维也纳公约》","UN":"联合国","Antarctica":"南极","Arctic":"北极"}}
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 核对 import 生成并核对
生成并核对(S, out)
