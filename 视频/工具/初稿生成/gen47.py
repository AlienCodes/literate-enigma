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
(2,[[[("In February 2014","2014年2月，"),("a **viral** video narrated by writer George Monbiot","一段由作家乔治·蒙比奥特解说的视频在网上**疯传**(viral)，")],
     "（narrated by writer George Monbiot：过去分词短语作后置定语，修饰 video）"],
    [[("**spun**","**编织**(spun)出"),("a","一个"),("**compelling**","**引人入胜的**(compelling)"),("**narrative**:","**故事**(narrative)。")],
     "（spin a narrative：编织出一个故事）"],
    [[("elk,","片中说，麋鹿"),("thinned by wolves","被狼捕杀得数量变少，"),("and","又"),("**wary of** them,","处处**提防**(wary of)着狼，"),("**retreated from** valleys,","便**撤离了**(retreated from)河谷，")],
     "（thinned by wolves and wary of them：插入语，补充说明 elk；\nbe wary of：提防）"],
    [[("letting","于是"),("**willows**","**柳树**(willows)"),("**flourish**","**繁茂**(flourish)起来，"),("and riverbanks","河岸也"),("**stabilise**.","**稳固**(stabilise)下来。")],
     "（letting…：现在分词短语作结果状语；\nlet A do：让 A 做）"]]),
(2,[[[("Ecologists","生态学家"),("call this","把这称为"),("a **trophic cascade**:","**营养级联**(trophic cascade)：")],
     "（call A B：把 A 称为 B）"],
    [[("**predators**","**捕食者**(predators)"),("eat","吃掉"),("or","或"),("**deter**","**吓阻**(deter)"),("plant-eaters,","食草动物，"),("and **vegetation**","**植被**(vegetation)"),("**rebounds**.","便**恢复生长**(rebounds)。")]]]),
(3,[[[("Yet","然而，"),("the **census**","**普查**(census)结果首先就"),("**undermined**","**削弱了**(undermined)"),("the thinning claim:","鹿被狼吃少了这一说法。")],
     "（the thinning claim：狼让麋鹿变少的说法）"],
    [[("elk on the park's northern range","黄石北部草场的麋鹿"),("peaked at about 19,000 in January 1994","在1994年1月达到约19,000头的峰值，")],
     "（on the park's northern range：后置定语，修饰 elk；\npeak at：达到……的峰值）"],
    [[("and were **dwindling** before wolves arrived,","狼还没来就已**日渐减少**(dwindling)；")]],
    [[("**depleted** by **hunters**, **drought**, and bears.","**猎人**(hunters)、**干旱**(drought)和熊不断**削减**(depleted)着鹿群。")],
     "（depleted by…：过去分词短语作状语，补充说明减少的原因）"]]),
(3,[[[("Fear","恐惧一说"),("looked weak too:","看来也站不住。")]],
    [[("in June 2013","2013年6月，"),("Arthur Middleton's","阿瑟·米德尔顿领导的"),("University of Wyoming team","怀俄明大学团队"),("found that","发现，")]],
    [[("**collared** elk east of the park","园区东侧**戴项圈的**(collared)麋鹿"),("kept","照样"),("**grazing**","**吃草**(grazing)，")],
     "（east of the park：后置定语，修饰 elk；\nkeep doing：一直做）"],
    [[("unless","除非"),("wolves","狼"),("**ventured** within half a mile.","**闯**(ventured)进半英里以内。")],
     "（unless：除非）"]]),
(4,[[[("Trees","树木方面的证据也"),("**fared no better**:","**好不到哪里去**(fared no better)：")],
     "（fare no better：也好不到哪里去）"],
    [[("in November 2021","2021年11月，"),("Utah State University's","犹他州立大学的"),("Elaine Brice","伊莱恩·布赖斯"),("showed that","指出，")]],
    [[("**sampling** only","只**抽样测量**(sampling)"),("the tallest","最高的"),("**aspens**","**山杨**(aspens)，"),("**overstated** **regrowth**","会把它们的**再生**(regrowth)程度**夸大**(overstated)"),("four- to sevenfold.","四到七倍。")],
     "（sampling only the tallest aspens：动名词短语作主语；\nfour- to sevenfold：四到七倍）"]]),
(4,[[[("The deeper","更根本的"),("**flaw**","**漏洞**(flaw)"),("was water.","出在水上。")]]]),
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
    [[("critics","批评者则"),("**disputed** his methods.","对他的方法提出**质疑**(disputed)。")]]]),
(5,[[[("The question","问题"),("is **unresolved**,","仍**悬而未决**(unresolved)，")]],
    [[("but","但"),("the wolves'","狼投下的"),("shadow","影子"),("looks fainter than the **fable** suggested,","比**寓言**(fable)所说的要淡，")],
     "（than the fable suggested：比较状语从句）"],
    [[("and the science","相关研究也要"),("**messier**.","**复杂纠结**(messier)得多。")],
     "（the science messier：省略了 looks）"]]),
(5,[[[("A **discipline** willing to **revise** its **cherished** example","一门肯**修正**(revise)自己**珍视的**(cherished)案例的**学科**(discipline)，")],
     "（willing to revise its cherished example：\n形容词短语作后置定语，修饰 discipline）"],
    [[("may","或许"),("deserve more trust than the fable ever did.","比那则寓言更值得信赖。")],
     "（than the fable ever did：比较状语从句，did 代替 deserved trust）\n"
     "（简述：黄石的灰狼1926年前已被消灭，\n"
     "1995年从加拿大运来的狼又放归公园。\n"
     "2014年一段走红的视频讲了个动人的故事：\n"
     "狼让麋鹿变少、变得警惕，柳树和河岸随之恢复。\n"
     "可普查显示，麋鹿在狼来之前就已减少；\n"
     "戴项圈的麋鹿只要狼不靠近，照样吃草；\n"
     "只量最高的山杨，会把再生夸大四到七倍；\n"
     "溪流下切太深，柳树够不着水。\n"
     "2025年里普尔称黄石的级联位居世界最强之列，批评者质疑他的方法。\n"
     "问题仍悬而未决，肯修正自己珍视案例的学科更值得信赖。）"]]),
]
G={
 "S4 a viral video narrated by writer George Monbiot":"对齐不了：narrated by writer George Monbiot 是过去分词短语作后置定语，中文“由作家乔治·蒙比奥特解说的视频”定语必须提前；viral 中文沿用文章定稿“在网上疯传”，作谓语放到最后",
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
 "S4-1 a viral video narrated by writ":"narrated by writer George Monbiot 是后置定语，修饰 video，中文定语必须提前，viral 化成谓语“在网上疯传”放到最后",
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
CONF.setdefault("同词异译",{})["excluded：把/挡在外面"]="S10 exclude A“把 A 挡在外面”被“麋鹿”隔开，“把”和“挡在外面”是同一个意思的两部分（T22/T23），不是两种译法"
CONF["停顿位置"]={
 "S2 Alberta, / Canada, @5.260":"2026-11-04 逐 2.5 ms 实测（S2 w）：Alberta 的 ə 浊音到 5.20（-22 dB、周期 0.3、低频 -1 dB），5.215 -40、5.24 -51～-57 dB 衰减，5.255–5.2625 降到 -67～-68.5 dB，是两词之间最低处（过零 5.260292）；5.265 起回升，5.2675–5.27 是 Canada 的 /k/ 除阻（-22～-14 dB、重心 3.9 kHz、低频 -33 dB）。插在 5.260 前后两词都没切到",
 "S5 plant-eaters, / and @5.590":"2026-11-04 逐 2.5 ms 实测（S5 w）：eaters 的 /z/ 5.54–5.58（-17～-22 dB、重心 5.1–5.7 kHz），5.5825 -26、5.585 -28、5.5875 -30 dB 是 /z/ 的尾巴；5.590 -34.2 dB 是两词交界最低处（过零 5.590125）；5.5925 起 -18 dB、重心 1.6 kHz、5.595 周期 0.41，是 and 的起音。程序原插 5.585 落在 /z/ 尾巴上，改插 5.590125，/z/ 整段留给 eaters"}
out={"no":"47","title_en":"Shadows of Wolves Over Yellowstone","title_zh":"黄石公园狼影再现","title_fx":{"hl":["Wolves","Yellowstone"],"ghost":[]},"sentences":[],"核对确认":CONF,"结尾解说":"简述",
     "停顿插入点":{"S5":{"2":[5.590125,"交界"]}},
     "高亮按实际开口":True,"高亮开口门槛":40,
     "术语":{"Yellowstone":"黄石公园","Alberta":"艾伯塔省","Canada":"加拿大","George Monbiot":"乔治·蒙比奥特","Arthur Middleton":"阿瑟·米德尔顿","University of Wyoming":"怀俄明大学","Utah State University":"犹他州立大学","Elaine Brice":"伊莱恩·布赖斯","Colorado State University":"科罗拉多州立大学","Tom Hobbs":"汤姆·霍布斯","David Cooper":"戴维·库珀","Oregon State University":"俄勒冈州立大学","William Ripple":"威廉·里普尔"}}
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 核对 import 生成并核对
生成并核对(S, out)
