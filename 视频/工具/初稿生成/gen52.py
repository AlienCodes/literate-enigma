import json,re,glob,os
# 第52篇初稿（逐词对照）：S = [(段, [chunk, ...])]，chunk = ([(英文组, 中文组), ...], 可选 note)
# 2026-11-05 重点词中文沿用文章定稿（铁律），只按《翻译风格》调格式；三项并列加牛津逗号（T18）；不用破折号（T36）；形容词的“的”进粗体。
S=[
(1,[[[("On Friday 5 December 1952,","1952年12月5日，星期五，"),("cold,","寒冷而"),("**stagnant**","**凝滞的**(stagnant)"),("air","空气"),("**descended on** London.","**降临**(descended on)伦敦。")],
     "（descend on…：降临，笼罩（某地））"]]),
(1,[[[("**Overhead**,","**头顶上方**(Overhead)，"),("warmer","较暖的"),("air","空气"),("pressed down","压了下来，"),("like a **lid**,","像**盖子**(lid)一样，")]],
    [[("holding","把"),("the **chill**","**寒气**(chill)"),("**captive**","**困**(captive)"),("beneath.","在下面。")],
     "（holding…：现在分词短语作状语，表结果；\nhold sth captive：把……困住）"]]),
(1,[[[("Londoners","伦敦人"),("were **accustomed to**","早已**习惯**(accustomed to)"),("**murky**,","**昏暗的**(murky)、"),("**dreary**","**阴沉的**(dreary)"),("winters.","冬天。")],
     "（be accustomed to…：习惯于……）"]]),
(1,[[[("This time, though,","不过这一次，"),("the capital's","首都的"),("smoke","煤烟"),("was trapped too,","也被困住了，")]],
    [[("thickening into","越积越浓，成了"),("a **choking**","**令人窒息的**(choking)"),("**smog**,","**烟雾**(smog)，"),("a mix of","也就是"),("smoke","烟"),("and fog.","与雾的混合物。")],
     "（thickening into…：现在分词短语作状语，表结果；\na mix of smoke and fog：同位语，补充说明 smog）"]]),
(2,[[[("That smoke,","这些煤烟"),("from","来自"),("coal","煤，"),("burned","是"),("in **domestic**","在**家庭**(domestic)"),("**fireplaces**","**壁炉**(fireplaces)"),("and power stations,","和发电厂里烧的，")],
     "（from coal…：介词短语作后置定语，修饰 smoke；\nburned in…：过去分词短语作后置定语，修饰 coal）"],
    [[("was **laden with**","**满含**(laden with)"),("soot","烟尘"),("and **noxious**","和**有毒的**(noxious)"),("sulphur dioxide.","二氧化硫。")],
     "（be laden with…：满载……，充满……）"]]),
(2,[[[("In places,","有些地方，"),("**visibility**","**能见度**(visibility)"),("fell to","降到只有"),("a few","几"),("metres.","米。")]]]),
(2,[[[("**Ambulance** services","**救护车**(Ambulance)服务"),("were suspended,","暂停；")]],
    [[("an opera","一场歌剧"),("at the Sadler's Wells","在萨德勒之井"),("theatre","剧院"),("was abandoned at the **interval**,","演到**幕间休息**(interval)被迫中止；")],
     "（an opera at…：介词短语作后置定语，修饰 opera；\nat the interval：在幕间休息时）"],
    [[("and prize","而获奖的"),("**cattle**","**牛**(cattle)，"),("at the Smithfield","在史密斯菲尔德"),("**agricultural**","**农业**(agricultural)"),("show","展会上"),("died","有的死去，"),("or had to be **slaughtered**.","有的只得**宰杀**(slaughtered)。")],
     "（at the Smithfield agricultural show：后置定语，修饰 cattle；\nhad to be slaughtered：不得不被宰杀）"]]),
(3,[[[("The smog","烟雾"),("**dissipated**","**消散**(dissipated)于"),("on Tuesday 9 December.","12月9日，星期二。")]]]),
(3,[[[("Officials at the time","当时的官员"),("put","估计"),("the **excess**","**超额**(excess)"),("deaths","死亡"),("at about 4,000,","约4,000人，")],
     "（put A at B：估计 A 为 B）"],
    [[("but","但"),("a 1954 Ministry of Health report","卫生部1954年的一份报告"),("blamed","把"),("later","后来的"),("deaths","死亡"),("on **influenza**.","归因于**流感**(influenza)。")],
     "（blame A on B：把 A 归咎于 B）"]]),
(3,[[[("A study published in Environmental Health Perspectives in 2001","2001年发表于《环境健康展望》的一项研究")],
     "（published in…：过去分词短语作后置定语，修饰 study）"],
    [[("**reassessed**","**重新评估了**(reassessed)"),("the evidence","证据，"),("and cast","并"),("doubt on","质疑了"),("that **explanation**,","这一**解释**(explanation)，")],
     "（cast doubt on…：对……提出质疑，质疑……）"],
    [[("estimating","估计"),("about 12,000","约12,000人"),("excess","超额"),("deaths","死亡，"),("between December 1952","时间在1952年12月"),("and February 1953.","至1953年2月间。")],
     "（estimating…：现在分词短语作状语，补充说明研究结论）"]]),
(4,[[[("For decades","几十年来，"),("Londoners","伦敦人"),("had **tolerated**","一直**容忍**(tolerated)"),("the smoke","煤烟，"),("as a **nuisance**.","把它看成一种**麻烦**(nuisance)。")],
     "（tolerate A as B：把 A 当作 B 来容忍）"]]),
(4,[[[("One **villain**","有一个**元凶**(villain)"),("**flickered**","就**摇曳**(flickered)在"),("in their own","他们自家的"),("grates,","炉栅里，")],
     "（grates：炉栅，壁炉里放煤的铁架）"],
    [[("a source of","它带来"),("**warmth**","**温暖**(warmth)"),("and **comfort**","与**舒适**(comfort)，"),("so **habitual**","人们早已**习以为常**(habitual)，")],
     "（a source of…：同位语，补充说明 villain；\nso… that…：如此……以至于……）"],
    [[("that few","很少有人"),("thought to **accuse** it.","想到要**指责**(accuse)它。")]]]),
(4,[[[("Such **complacency**","这种**麻痹大意**(complacency)"),("may","或许"),("help to","有助于"),("explain","说明，"),("the government's","政府为何"),("**grudging**","**勉强**(grudging)"),("**response**.","作出**回应**(response)。")],
     "（the government's grudging response：\n政府勉强作出的回应）"]]),
(4,[[[("It","政府"),("**withstood**","一直**顶住**(withstood)"),("pressure for an inquiry","要求调查的压力，"),("until May 1953.","直到1953年5月才松口。")],
     "（pressure for an inquiry：要求调查的压力）"]]),
(5,[[[("Reform","改革"),("proved **protracted**,","**旷日持久**(protracted)，"),("slowed by","又因"),("official","官方的"),("**inertia**.","**惰性**(inertia)而进展迟缓。")],
     "（prove＋形容词：结果是……，\n事实证明……；\nslowed by…：过去分词短语作状语）"]]),
(5,[[[("The Clean Air Act","《清洁空气法》"),("became","成为"),("law","法律，"),("on 5 July 1956,","时间是1956年7月5日，")]],
    [[("three and a half years after the smog.","距那场烟雾已有三年半。")],
     "（three and a half years after the smog：\n补充说明时间）"]]),
(5,[[[("It","该法"),("**empowered**","**授权**(empowered)"),("**municipal**","**市镇**(municipal)"),("councils","议会"),("to create","设立"),("**smokeless** zones,","**无烟**(smokeless)区，")],
     "（empower sb to do sth：授权某人做某事）"],
    [[("**combating** smoke at its **source**.","从**源头**(source)上**遏制**(combating)煤烟。")],
     "（combating…：现在分词短语作状语；\nat source：从源头）"]]),
(5,[[[("The **cosy** **hearth**, **beloved** of British families,","英国家庭**深受喜爱的**(beloved)、**温馨的**(cosy)**炉膛**(hearth)，")],
     "（beloved of…：受……喜爱，作后置定语，修饰 hearth）"],
    [[("had,","原来"),("all along,","一直"),("been among","都在"),("the chief","主要的"),("**offenders**.","**肇事者**(offenders)之列。")],
     "（all along：一直，始终；\nbe among…：在……之列，是……之一）\n"
     "（简述：1952年12月5日，冷空气被上方的暖空气压住，伦敦的煤烟散不出去，成了令人窒息的烟雾。\n"
     "煤烟来自家庭壁炉和发电厂，能见度只有几米，救护车停运，歌剧中止，展会上的获奖牛死去或被宰杀。\n"
     "12月9日烟雾散去，当时估计超额死亡约4,000人，1954年的报告却归因于流感，\n"
     "2001年的研究对此提出质疑，估计超额死亡约12,000人。\n"
     "伦敦人对自家炉火习以为常，政府也回应勉强，直到1953年5月才不再顶住调查的压力。\n"
     "1956年《清洁空气法》授权市镇议会设立无烟区，原来温馨的炉膛一直是主要肇事者之一。）"]]),
]
G={
 "S4 This time, though":"对齐不了：though 是转折副词，中文“不过”必须放句首，“这一次”跟在后面，拆开语序不通",
 "S4 was trapped too":"对齐不了：too 中文“也”必须放到动词“被困住”前",
 "S5 and power stations":"对齐不了：power stations 是一个词“发电厂”，拆开不通",
 "S5 sulphur dioxide":"对齐不了：sulphur dioxide 是化学名“二氧化硫”，一个词，拆开不通",
 "S7 was abandoned at the interval":"对齐不了：at the interval 是时间状语，中文“演到幕间休息”必须放到“被迫中止”前",
 "S10 A study published in Environmental Health Perspectives in 2001":"对齐不了：published in… in 2001 是过去分词短语作后置定语，修饰 study，中文“2001年发表于《环境健康展望》的一项研究”定语必须提前，刊名不能拆",
 "S14 pressure for an inquiry":"对齐不了：for an inquiry 是介词短语作后置定语，修饰 pressure，中文“要求调查的压力”定语必须提前",
 "S16 three and a half years after the smog":"对齐不了：three and a half years after the smog 是时间状语，中文“距那场烟雾已有三年半”语序必须倒过来",
}
CONF={"合组":G,"已告诉用户被去掉的重点词":"2026-11-05 已在会话中把 suspended（暂停）因与第22篇撞词被去掉的话原样告诉用户"}
out={"no":"52","title_en":"The Killer Smog of 1952","title_zh":"夺命毒雾：伦敦1952","title_fx":{"hl":["Killer","Smog"],"ghost":[]},"sentences":[],"核对确认":CONF,"结尾解说":"简述",
     "高亮按实际开口":True,"高亮开口门槛":40,
     "术语":{"London":"伦敦","Londoners":"伦敦人","Sadler's Wells":"萨德勒之井剧院","Smithfield":"史密斯菲尔德","Ministry of Health":"卫生部","Environmental Health Perspectives":"《环境健康展望》","Clean Air Act":"《清洁空气法》","British":"英国"}}
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 核对 import 生成并核对
生成并核对(S, out)
