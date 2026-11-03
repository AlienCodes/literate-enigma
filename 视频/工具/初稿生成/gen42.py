import json,re,glob,os
# 第42篇初稿（逐词对照）：S = [(段, [chunk, ...])]，chunk = ([(英文组, 中文组), ...], 可选 note)
# 2026-11-03 重点词中文沿用文章定稿（铁律），只按《翻译风格》调格式；短语型用法整体标（T22）；三项并列加牛津逗号（T18）；不用破折号（T36）。
S=[
(1,[[[("On 24 April 1990","1990年4月24日，"),("the space shuttle Discovery","发现号航天飞机"),("**lofted** the Hubble Space Telescope into orbit.","把哈勃空间望远镜**送上**(lofted)轨道。")],
     "（loft A into orbit：把 A 送上轨道）"]]),
(1,[[[("The **observatory** **cradled** in the **payload** bay","这座**安放**(cradled)在**有效载荷**(payload)舱里的**天文台**(observatory)"),("had cost","耗资"),("about","约"),("$1.5 billion,","15亿美元，")],
     "（cradled in…：过去分词短语作后置定语，修饰 observatory）"],
    [[("a **lavish**","是一笔**巨额**(lavish)"),("**investment**","**投资**(investment)，"),("meant to","旨在"),("fix its **gaze** on","把**目光**(gaze)投向"),("the **cosmos**","**宇宙**(cosmos)"),("and its **galaxies**.","及其中的**星系**(galaxies)。")],
     "（a lavish investment…：同位语，补充说明前面这笔钱；\nmeant to…：过去分词短语作后置定语，修饰 investment；\nfix one's gaze on…：把目光投向……）"]]),
(1,[[[("Money, it soon emerged,","人们很快发现，钱"),("could not buy **clarity**.","买不来**清晰**(clarity)。")],
     "（it soon emerged：插入语，人们很快发现）"]]),
(2,[[[("Its first **snapshots**","它最初的**快照**(snapshots)"),("came back","传回来时"),("**blurred**","**模糊**(blurred)不清、"),("and **fuzzy**.","**朦胧**(fuzzy)一片。")],
     "（come back＋形容词：传回来时是……的样子）"]]),
(2,[[[("In June 1990","1990年6月，"),("NASA","美国航天局"),("announced","宣布"),("a flaw in the main mirror:","主镜有缺陷，")],
     "（in the main mirror：介词短语作后置定语，修饰 flaw；\n冒号后面具体说明缺陷）"],
    [[("its outer **rim**","主镜外侧**边缘**(rim)"),("had been **flattened**","被**磨平了**(flattened)"),("by 2.2 micrometres,","2.2微米，")],
     "（by：表示相差的量）"],
    [[("roughly","大约相当于"),("a fiftieth of the **width** of a hair.","头发丝**宽度**(width)的五十分之一。")],
     "（a fiftieth：五十分之一；\nroughly a fiftieth of…：同位语，补充说明 2.2 micrometres）"]]),
(2,[[[("That **deviation**","这一**偏差**(deviation)"),("**marred**","**损害了**(marred)"),("the **optics**,","**光学系统**(optics)，")]],
    [[("leaving","使"),("light","光线"),("without","无法形成"),("a **sharp** focus.","**锐利的**(sharp)焦点。")],
     "（leaving…：现在分词短语作结果状语；\nleave A without B：使 A 没有 B）"]]),
(3,[[[("The trouble","问题"),("began with **calibration**.","始于**校准**(calibration)。")],
     "（begin with…：始于……）"]]),
(3,[[[("A **lens** in the **assembly** that checked the mirror's shape","检测主镜形状的那套**组件**(assembly)中，一块**透镜**(lens)"),("had been **offset**","**错位了**(offset)"),("by about","约"),("1.3 **millimetres**,","1.3**毫米**(millimetres)，")],
     "（in the assembly…：介词短语作后置定语，修饰 lens；\nthat checked…：定语从句，修饰 assembly）"],
    [[("so the mirror","主镜因此"),("was ground to","被磨成了"),("the wrong **curve**.","错误的**曲面**(curve)。")],
     "（ground：grind 的过去分词，研磨；\nbe ground to…：被磨成……）"]]),
(3,[[[("A second, independent test by the contractor, Perkin-Elmer,","承包商珀金-埃尔默公司做的第二次独立测试"),("gave","给出了"),("a **divergent** result,","**不同的**(divergent)结果，")],
     "（by the contractor：介词短语作后置定语，修饰 test；\nPerkin-Elmer：同位语，补充说明 the contractor）"],
    [[("but","但"),("engineers","工程师"),("and","和"),("NASA","美国航天局的"),("managers","管理人员"),("judged","认为"),("it","它"),("less **reliable**","不太**可靠**(reliable)，")],
     "（judge A＋形容词：认为 A……）"],
    [[("and left the **contradictory** reading","这一**相互矛盾的**(contradictory)读数也就"),("**unexplored**.","**无人深究**(unexplored)。")],
     "（leave A＋形容词：使 A 处于某种状态）"]]),
(4,[[[("The mirror","主镜"),("could not be repaired in orbit,","无法在轨道上修复，")],
     "（in orbit：在轨道上）"],
    [[("so","于是"),("engineers","工程师"),("**prescribed**","**开出了**(prescribed)"),("**tailored** glasses.","一副**量身定制的**(tailored)眼镜。")],
     "（prescribe：开（药方），这里把矫正装置比作眼镜）"]]),
(4,[[[("COSTAR,","COSTAR "),("a **corrective**","是一个冰箱大小的**矫正**(corrective)"),("**cabinet**","**箱体**(cabinet)，"),("the size of a refrigerator,","")],
     "（a corrective cabinet…：同位语，补充说明 COSTAR；\nthe size of…：……那么大）"],
    [[("carried small mirrors on **adjustable** arms","**可调节的**(adjustable)机械臂上装着小镜子，")],
     "（on adjustable arms：介词短语作后置定语，修饰 mirrors）"],
    [[("that **intercepted** the light","在光线到达仪器之前将光**截住**(intercepted)，"),("and **compensated for**","**抵消**(compensated for)"),("the **imperfect**","**有缺陷的**(imperfect)"),("mirror's","主镜造成的"),("**distortion** before the light reached the instruments.","**畸变**(distortion)。")],
     "（that intercepted…and compensated for…：定语从句，\n修饰 small mirrors；\ncompensate for…：抵消，弥补……；\nbefore…：时间状语从句）"]]),
(4,[[[("The mirror itself","主镜本身"),("would stay **untouched**,","将保持**原封不动**(untouched)，")],
     "（stay＋形容词：保持某种状态）"],
    [[("and a new","一台新的"),("main","主"),("camera","相机"),("was prepared.","也已准备就绪。")]]]),
(5,[[[("On 2 December 1993","1993年12月2日，"),("Endeavour","奋进号"),("**ascended** with seven astronauts.","载着七名宇航员**升空**(ascended)。")],
     "（with seven astronauts：伴随状语）"]]),
(5,[[[("After a **rendezvous**,","完成**交会**(rendezvous)后，")],
     "（rendezvous：航天器在轨道上会合）"],
    [[("they","他们"),("worked **in tandem**","**协同**(in tandem)进行了"),("across five","五次"),("spacewalks,","太空行走，")],
     "（in tandem：协力，配合；\nacross five spacewalks：在五次太空行走中）"],
    [[("about 35 and a half hours of **exertion**,","**辛苦作业**(exertion)共约35个半小时，")],
     "（about 35 and a half hours of exertion：\n同位语，补充说明五次太空行走的工作量）"],
    [[("**installing**","**安装了**(installing)"),("COSTAR","COSTAR "),("and","和"),("the new","新"),("camera.","相机。")],
     "（installing…：现在分词短语作伴随状语）"]]),
(5,[[[("The **imagery**","**影像**(imagery)"),("turned **crisp**,","变得**清楚分明**(crisp)，")],
     "（turn＋形容词：变得……）"],
    [[("Hubble's **vision**","哈勃的**视力**(vision)"),("**renewed**.","得以**恢复**(renewed)。")],
     "（Hubble's vision renewed：\n独立主格结构，相当于\nand Hubble's vision was renewed）"]]),
(5,[[[("The mirror","主镜"),("still carries","至今仍带着"),("that 2.2-micrometre","那2.2微米的"),("flaw,","缺陷，")]],
    [[("and the light it **gathers**","它**收集**(gathers)的光"),("is corrected only after leaving it.","要离开镜面之后才得到矫正。")],
     "（it gathers：定语从句，省略了关系代词，修饰 light；\nonly after…：只有在……之后才）\n"
     "（简述：1990年，航天飞机把耗资约15亿美元的\n"
     "哈勃空间望远镜送上轨道，传回的照片却模糊不清。\n"
     "原来检测主镜的组件里有一块透镜错位，\n"
     "主镜外缘被磨平了2.2微米。\n"
     "另一次独立测试给出过不同结果，却没人追查。\n"
     "主镜无法在轨道上修复，工程师就给它配了一副眼镜：\n"
     "冰箱大小的矫正装置 COSTAR。\n"
     "1993年，七名宇航员经过五次太空行走，\n"
     "装好了 COSTAR 和新相机，哈勃的视力得以恢复。\n"
     "主镜至今仍带着原有的缺陷。）"]]),
]
CONF={
"合组":{
 "S1 the space shuttle Discovery":"对齐不了：Discovery 是航天飞机的名字，中文“发现号航天飞机”名字必须放在前面",
 "S3 Money, it soon emerged":"对齐不了：it soon emerged 是插入语，中文“人们很快发现”必须提到句首，Money 中文“钱”接在后面（沿用文章定稿）",
 "S5 a flaw in the main mirror":"对齐不了：in the main mirror 是后置定语，修饰 flaw，中文“主镜有缺陷”主镜必须提前",
 "S5 a fiftieth of the width of a hair":"对齐不了：两层 of 结构，中文“头发丝宽度的五十分之一”语序必须整个倒过来",
 "S8 A lens in the assembly that checked the mirror's shape":"对齐不了：in the assembly 是后置定语，that checked the mirror's shape 是定语从句修饰 assembly，中文“检测主镜形状的那套组件中，一块透镜”从句和地点必须提前",
 "S9 A second, independent test by the contractor, Perkin-Elmer":"对齐不了：by the contractor 是后置定语，Perkin-Elmer 是同位语，中文“承包商珀金-埃尔默公司做的第二次独立测试”定语必须整体提前",
 "S9 and left the contradictory reading":"对齐不了：leave A unexplored 中文“A 也就无人深究”，A 必须提到前面，left 化成“也就”（沿用文章定稿）",
 "S10 could not be repaired in orbit":"对齐不了：in orbit 是地点状语，中文“无法在轨道上修复”地点必须放到动词前",
 "S11 carried small mirrors on adjustable arms":"对齐不了：on adjustable arms 是地点（后置定语），中文“可调节的机械臂上装着小镜子”地点必须提前，carried 化成“装着”",
 "S11 the size of a refrigerator":"对齐不了：the size of a refrigerator 是后置定语，修饰 cabinet，中文“冰箱大小的”按文章定稿提到“矫正箱体”前（放在 corrective 那组），这里没有中文",
 "S11 distortion before the light reached the instruments":"对齐不了：before the light reached the instruments 是时间状语从句，中文“在光线到达仪器之前”按文章定稿提到这半句开头（放在 intercepted 那组），这里只剩“畸变”",
 "S16 is corrected only after leaving it":"对齐不了：only after leaving it 是时间状语，中文“要离开镜面之后才得到矫正”时间必须放到“得到矫正”前"},
"对齐":{
 "S1-1 lofted the Hubble Space Telesc":"loft A into orbit，中文“把 A 送上轨道”，把字句宾语必须提前",
 "S2-1 The observatory cradled in the":"cradled in the payload bay 是过去分词短语作后置定语，修饰 observatory，中文“安放在有效载荷舱里的天文台”定语必须提前",
 "S5-1 a flaw in the main mirror:":"in the main mirror 是后置定语，中文“主镜有缺陷”主镜必须提前",
 "S5-3 a fiftieth of the width of a h":"两层 of 结构，中文“头发丝宽度的五十分之一”语序必须整个倒过来",
 "S8-1 A lens in the assembly that ch":"in the assembly 是后置定语、that checked… 是定语从句，中文从句和地点必须提前",
 "S9-1 A second, independent test by ":"by the contractor 是后置定语、Perkin-Elmer 是同位语，中文定语必须整体提前",
 "S9-3 and left the contradictory rea":"leave A unexplored，中文“A 也就无人深究”，A 必须提前",
 "S10-1 could not be repaired in orbit":"in orbit 是地点状语，中文“在轨道上”必须放到“修复”前",
 "S11-1 the size of a refrigerator,":"the size of a refrigerator 是后置定语，中文“冰箱大小的”必须提到“矫正箱体”前（放在 corrective 那组）",
 "S11-2 carried small mirrors on adjus":"on adjustable arms 是地点（后置定语），中文“机械臂上装着小镜子”地点必须提前",
 "S11-3 distortion before the light re":"before… 是时间状语从句，中文“在光线到达仪器之前”按文章定稿提到这半句开头（intercepted 那组），这里只剩“畸变”",
 "S14-3 about 35 and a half hours of e":"同位语里 hours of exertion 是 of 结构，中文“辛苦作业共约35个半小时”语序必须倒过来",
 "S16-2 and the light it gathers":"it gathers 是省略关系代词的定语从句，修饰 light，中文“它收集的光”从句必须提前",
 "S16-2 is corrected only after leavin":"only after leaving it 是时间状语，中文“要离开镜面之后才”必须放到“得到矫正”前"},
"牛津逗号":{
 "S9 gave a divergent result, but engineers and":"不是三项并列：逗号后 but 连接两个分句，engineers and NASA managers 只有两项",
 "S14 tandem across five spacewalks, about 35 and":"不是三项并列：about 35 and a half hours of exertion 是同位语，and a half 是数字读法",
 "S14 half hours of exertion, installing COSTAR and":"不是三项并列：installing… 是现在分词短语，COSTAR and the new camera 只有两项"},
"方向":{"S9-2 less→不太可靠，":"less reliable 中文“不太可靠”，“不太”就是 less，方向一致",
 "S11-3 before→畸变。":"before 引出的从句中文“在光线到达仪器之前”按文章定稿提到这半句开头（intercepted 那组），“之前”与 before 方向一致"},
"短语":{
 "S1 lofted … into":"不是搭配：into 只引出方向（送入轨道），lofted 本身就是“送上”",
 "S2 cradled … in":"不是搭配：in 只引出地点（在有效载荷舱里），cradled 本身就是“安放”",
 "S2 gaze … on":"不是搭配：gaze 在这里是名词“目光”，on 属于动词短语 fix … on（把……投向），中文“把目光投向”整组已对上",
 "S5 rim … of":"不是搭配：of 属于后面的 a fiftieth of the width，和 rim 无关",
 "S5 flattened … of":"不是搭配：of 属于后面的 a fiftieth of the width，和 flattened 无关",
 "S5 width … of":"不是搭配：of 只引出所属（头发丝的宽度），width 本身就是“宽度”（同 16 beads … of 的判法）",
 "S7 with … calibration":"不是搭配：with 属于 began with（始于），calibration 本身就是“校准”",
 "S8 offset … by":"不是搭配：by 表示偏移的量（约1.3毫米），offset 本身就是“错位”",
 "S13 ascended … with":"不是搭配：with 表示伴随（载着七名宇航员），ascended 本身就是“升空”"}}
out={"no":"42","title_en":"The Telescope That Needed Glasses","title_zh":"需要戴眼镜的望远镜","title_fx":{"hl":["Telescope","Glasses"],"ghost":[]},"sentences":[],"核对确认":CONF,"结尾解说":"简述",
     "高亮按实际开口":True,"高亮开口门槛":40,
     "术语":{"Discovery":"发现号","Hubble Space Telescope":"哈勃空间望远镜","Hubble":"哈勃","NASA":"美国航天局","Perkin-Elmer":"珀金-埃尔默公司","COSTAR":"COSTAR","Endeavour":"奋进号"}}
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 核对 import 生成并核对
生成并核对(S, out)
