import json,re,glob,os
# 第37篇初稿（逐词对照）：S = [(段, [chunk, ...])]，chunk = ([(英文组, 中文组), ...], 可选 note)
# 重点词中文沿用文章定稿（铁律），只按《翻译风格》调格式；短语型用法整体标（T22）；不用破折号（T36）；三项并列加牛津逗号（T18）。
S=[
(1,[[[("Around 1847","1847年前后，"),("the Italian","意大利"),("chemist","化学家"),("Sobrero","索布雷罗"),("first","首次"),("made","制得"),("nitroglycerin,","硝酸甘油，")]],
    [[("a **colourless**,","这是一种**无色**(colourless)、"),("**oily**","**油状的**(oily)"),("**liquid**","**液体**(liquid)，"),("of","具有"),("**acute**","**极度的**(acute)"),("**instability**.","**不稳定性**(instability)。")],
     "（a colourless, oily liquid…：同位语，补充说明 nitroglycerin；\nof acute instability：of 结构作后置定语，修饰 liquid）"]]),
(1,[[[("A **mere**","**仅仅**(mere)一"),("**droplet**","**小滴**(droplet)"),("on the tongue,","放在舌头上，"),("he","他"),("reported,","报告说，")],
     "（he reported：插入语，表示这是他自己的说法）"],
    [[("left","就让"),("his head","他头部"),("**throbbing** **violently**","**剧烈地**(violently)**抽痛了**(throbbing)"),("for hours.","好几个小时。")],
     "（leave sb/sth doing：使……处于某种状态；\nthrobbing violently：现在分词短语作宾语补足语）"]]),
(1,[[[("On 3 September 1864","1864年9月3日，"),("a","一间"),("nitroglycerin","硝酸甘油"),("shed","棚屋"),("in Stockholm","在斯德哥尔摩"),("exploded.","发生爆炸。")]]]),
(1,[[[("The","这场"),("**tragic**","**悲惨的**(tragic)"),("blast","爆炸"),("killed","炸死了"),("five,","五个人，"),("including","其中包括"),("Alfred Nobel's","阿尔弗雷德·诺贝尔的"),("younger brother","弟弟"),("Emil.","埃米尔。")],
     "（including…：介词短语，补充说明死者中有谁）"]]),
(2,[[[("Nobel","诺贝尔"),("**tamed**","**驯服了**(tamed)"),("the liquid","这种液体，")]],
    [[("by **blending** it with kieselguhr, a **porous** earth,","方法是把它与硅藻土这种**多孔的**(porous)土**混合**(blending)，"),("into a **paste**","制成**糊状物**(paste)，"),("shaped into **rods**.","再做成一根根**棒条**(rods)。")],
     "（blend A with B into C：把 A 与 B 混合成 C；\na porous earth：同位语，补充说明 kieselguhr；\nshaped into rods：过去分词短语作后置定语，修饰 paste）"]]),
(2,[[[("Patented in 1867 as dynamite,","1867年作为炸药获得专利后，")],
     "（Patented…：过去分词短语作状语，表被动）"],
    [[("it","它"),("was **harnessed**","被**用于**(harnessed)"),("for mining,","采矿、"),("**quarrying**,","**采石**(quarrying)"),("and demolition,","和拆除工程，")],
     "（be harnessed for…：被用于……）"],
    [[("**enriching** him","让他**获利**(enriching)"),("**immensely**.","十分**丰厚**(immensely)。")],
     "（enriching…：现在分词短语作结果状语）"]]),
(2,[[[("His","他"),("1895","在1895年立下的"),("**testament**","**遗嘱**(testament)"),("made","使"),("the fortune","这笔财产"),("an **endowment**","成为一笔**基金**(endowment)，"),("for prizes,","用来设立奖项，")],
     "（make A B：使 A 成为 B）"],
    [[("first","奖项首次"),("awarded","颁发"),("in 1901.","于1901年。")],
     "（first awarded…：过去分词短语作后置定语，修饰 prizes）"]]),
(3,[[[("Nitroglycerin","硝酸甘油"),("had","有"),("**side-effects**.","**副作用**(side-effects)。")]]]),
(3,[[[("**Factory operatives**","**工厂工人**(Factory operatives)"),("suffered","饱受"),("**racking**","**折磨人的**(racking)"),("headaches,","头痛，")]],
    [[("and their","他们的"),("**tolerance**,","**耐受性**(tolerance)"),("built over the week,","在一周中逐渐建立，"),("**ebbed** at weekends.","到周末又**减退**(ebbed)。")],
     "（built over the week：过去分词短语作插入语，修饰 tolerance）"]]),
(3,[[[("Mondays","每逢星期一，"),("brought a **recurrence**,","头痛便**复发**(recurrence)，"),("with","还伴有"),("**dizziness**","**眩晕**(dizziness)"),("and **palpitations**,","和**心悸**(palpitations)，")],
     "（with…：介词短语作伴随状语）"],
    [[("**hence**","**因此**(hence)"),("the name","得名"),("Monday disease.","星期一病。")],
     "（hence＋名词：因此有了……，省略了谓语）"]]),
(3,[[[("In 1879","1879年，"),("William Murrell","威廉·默雷尔"),("reported in The Lancet","在《柳叶刀》上报告了"),("on its **therapeutic** use against angina pectoris,","它对心绞痛的**治疗**(therapeutic)用途，")],
     "（report on…：报告关于……的情况；\nagainst angina pectoris：后置定语，修饰 use）"],
    [[("attacks","也就是阵发性的"),("of chest pain.","胸痛。")],
     "（attacks of chest pain：同位语，补充说明 angina pectoris）"]]),
(4,[[[("On 25 October 1896","1896年10月25日，"),("Nobel, who had angina,","患有心绞痛的诺贝尔")],
     "（who had angina：非限制性定语从句，补充说明 Nobel）"],
    [[("wrote","写信"),("to his **aide**","给他的**助手**(aide)，"),("that","说"),("by an irony of fate","命运真是讽刺，")],
     "（that…：宾语从句，说明信的内容；\nby an irony of fate：说来讽刺，命运弄人）"],
    [[("doctors","医生"),("had prescribed him","竟给他开了"),("nitroglycerin","硝酸甘油"),("to take **internally**.","让他**内服**(internally)。")],
     "（prescribe sb sth：给某人开某药；\nto take internally：不定式表目的）"]]),
(4,[[[("Its **alias**,","这种药的**别名**(alias)"),("Trinitrin,","Trinitrin"),("was chosen,","是特意选的，"),("he explained,","他解释说，")],
     "（Trinitrin：同位语，补充说明 alias；\nhe explained：插入语）"],
    [[("to avoid","为的是避免"),("**frightening**","**吓到**(frightening)"),("**pharmacists**","那些**药剂师**(pharmacists)"),("or the public.","和公众。")],
     "（avoid doing：避免做某事）"]]),
(4,[[[("He","他"),("did not","没有"),("**comply**.","**遵从**(comply)医嘱。")]]]),
(4,[[[("**Partly**","身体**部分**(Partly)"),("**paralysed**","**瘫痪**(paralysed)，"),("by a **cerebral haemorrhage**,","是由**脑部出血**(cerebral haemorrhage)造成的，")],
     "（Partly paralysed by…：过去分词短语作状语，\n说明他去世前的状况）"],
    [[("he","他"),("died at his San Remo **villa** on 10 December 1896.","于1896年12月10日在圣雷莫的**别墅**(villa)中去世。")],
     "（at his San Remo villa：地点状语；\non 10 December 1896：时间状语）"]]),
(5,[[[("In 1977","1977年，"),("Murad","穆拉德"),("**ascertained**","**查明**(ascertained)"),("that nitroglycerin","硝酸甘油"),("releases","会释放"),("nitric oxide,","一氧化氮，")],
     "（that…：宾语从句）"],
    [[("which **widens**","它会**扩张**(widens)"),("blood vessels.","血管。")],
     "（which…：非限制性定语从句，修饰 nitric oxide）"]]),
(5,[[[("Furchgott","弗奇戈特"),("found","发现了"),("an **unidentified**","一种**未经鉴定的**(unidentified)"),("relaxing **factor**","舒张**因子**(factor)，"),("in **vascular**","存在于**血管的**(vascular)"),("**linings**","**内壁**(linings)里，"),("in 1980,","这是1980年的事；")],
     "（relaxing factor：舒张因子，能让血管放松的物质；\nin vascular linings：地点状语）"],
    [[("and Ignarro","伊格纳罗"),("recognised it","认定它"),("as nitric oxide","就是一氧化氮，"),("in 1986.","这是1986年的事。")],
     "（recognise A as B：认定 A 是 B）"]]),
(5,[[[("The **trio**","这个**三人组**(trio)"),("shared","分享了"),("the 1998","1998年"),("Nobel Prize","诺贝尔"),("in Physiology or Medicine.","生理学或医学奖。")]]]),
(5,[[[("Its","这个奖的"),("**presentation**","**颁奖**(presentation)"),("speech,","致辞"),("on 10 December,","在12月10日，"),("the anniversary of Nobel's death,","也就是诺贝尔的忌日，")],
     "（on 10 December：时间状语；\nthe anniversary of Nobel's death：同位语，补充说明 10 December）"],
    [[("**quoted**","**引述了**(quoted)"),("his","他那封"),("**ironic**","感叹命运**讽刺**(ironic)的"),("letter.","信。")],
     "（quote：引用，引述）\n"
     "（简述：1847年前后，索布雷罗制得极不稳定的硝酸甘油，一小滴就让他头痛数小时。\n"
     "1864年，斯德哥尔摩的一场爆炸夺走了诺贝尔弟弟的生命。\n"
     "诺贝尔把它与硅藻土混合制成炸药，1867年获专利，靠采矿、采石和拆除发了大财，\n"
     "1895年又立遗嘱用这笔财产设立奖项。制炸药的工人饱受头痛之苦，星期一最重，\n"
     "1879年默雷尔报告它能治心绞痛。晚年患心绞痛的诺贝尔也被医生开了硝酸甘油，\n"
     "他在信里说这是命运的讽刺，却没有遵从医嘱，1896年12月10日在圣雷莫去世。\n"
     "后来三位科学家查明它释放一氧化氮、使血管扩张，分享了1998年诺贝尔奖，\n"
     "颁奖致辞正是在他的忌日引述了那封信。）"]]),
]
CONF={
"合组": {
"S4 younger brother": "对齐不了：younger brother 中文就是一个词“弟弟”",
"S5 by blending it with kieselguhr, a porous earth": "对齐不了：blend A with B 中文“把 A 与 B 混合”，动词“混合”必须放到最后；a porous earth 是同位语，中文“硅藻土这种多孔的土”，拆开不通",
"S9 built over the week": "对齐不了：over the week 是时间状语，中文“在一周中逐渐建立”时间必须放到动词前",
"S11 on its therapeutic use against angina pectoris": "对齐不了：against angina pectoris 是后置定语，修饰 use，中文“它对心绞痛的治疗用途”必须提前；angina pectoris 是一个病名“心绞痛”",
"S11 of chest pain": "对齐不了：chest pain 中文就是一个词“胸痛”",
"S12 by an irony of fate": "对齐不了：by an irony of fate 是固定说法“说来讽刺，命运弄人”，拆开不通",
"S16 nitric oxide": "对齐不了：nitric oxide 是化学名，中文就是一个词“一氧化氮”",
"S16 blood vessels": "对齐不了：blood vessels 中文就是一个词“血管”",
"S17 as nitric oxide": "对齐不了：nitric oxide 是化学名，中文就是一个词“一氧化氮”",
"S19 the anniversary of Nobel's death": "对齐不了：the anniversary of A's death 中文就是“A 的忌日”，of 结构必须倒过来，anniversary of death 合成一个词“忌日”"
},
"对齐": {
"S5-2 by blending it with kieselguhr": "blend A with B 中文“把 A 与 B 混合”，动词必须放到最后；a porous earth 是同位语，补充说明 kieselguhr",
"S6-1 Patented in 1867 as dynamite,": "过去分词短语作状语，中文“1867年作为炸药获得专利后”时间、方式状语必须放到动词前",
"S11-1 on its therapeutic use against": "against angina pectoris 是后置定语，修饰 use，中文“对心绞痛的治疗用途”必须提前",
"S12-2 by an irony of fate": "by an irony of fate 是固定说法，拆开不通",
"S15-2 died at his San Remo villa on ": "at his San Remo villa 地点状语、on 10 December 1896 时间状语，中文“于……在……中去世”时间、地点必须放到动词前",
"S19-1 the anniversary of Nobel's dea": "the anniversary of A's death 中文“A 的忌日”，of 结构必须倒过来"
},
"短语": {
"S2 throbbing … for": "不是搭配：for hours 是时间状语（好几个小时），和 throbbing 无关",
"S5 tamed … with": "不是搭配：with 属于 blending it with kieselguhr，和 tamed 无关",
"S5 blending … with": "不是搭配：blend A with B 里 with 引出混合的另一方（kieselguhr），blend 单独就是“混合”，同 34 篇 bundle A with B 先例",
"S5 blending … into": "不是搭配：into a paste 引出混合的结果（制成糊状物），blend 单独就是“混合”",
"S6 harnessed … for": "不是搭配：for 引出用途（采矿、采石和拆除），harness 单独就是“利用，用于”",
"S10 with … dizziness": "不是搭配：with 是普通介词，引出伴随的症状 dizziness and palpitations（还伴有眩晕和心悸）",
"S15 paralysed … by": "不是搭配：by 是被动句引出原因的普通介词（由脑部出血造成），paralyse 单独就是“瘫痪”",
"S19 presentation … of": "不是搭配：of 属于 the anniversary of Nobel's death，和 presentation 无关"
},
"牛津逗号": {
"S10 Mondays brought a recurrence, with dizziness and": "不是三项并列：逗号隔开的是伴随状语 with dizziness and palpitations，只有 dizziness、palpitations 两项",
"S13 he explained, to avoid frightening pharmacists or": "不是三项并列：逗号隔开的是插入语 he explained，pharmacists or the public 只有两项"
}
}
out={"no":"37","title_en":"Dynamite for the Heart","title_zh":"炸药大王的救心药","title_fx":{"hl":["Dynamite","Heart"],"ghost":[]},"sentences":[],"核对确认":CONF,"结尾解说":"简述",
     "说明放宽特批":{"S19":{"倍数":"整屏","依据":"用户 2026-10-25 看 25 简述截图：“以后以后一定要合理的安排，不要压缩成这个样子……这个地方特批一下”（用户同意记录：原话适用以后各篇，26 起沿用）"}},
     "高亮按实际开口":True,"高亮开口门槛":40,
     "术语":{"Sobrero":"索布雷罗","Italian":"意大利","Stockholm":"斯德哥尔摩","Alfred Nobel":"阿尔弗雷德·诺贝尔","Nobel":"诺贝尔","Emil":"埃米尔","William Murrell":"威廉·默雷尔","The Lancet":"柳叶刀","San Remo":"圣雷莫","Murad":"穆拉德","Furchgott":"弗奇戈特","Ignarro":"伊格纳罗","Trinitrin":"Trinitrin"}}
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 核对 import 生成并核对
生成并核对(S, out)
