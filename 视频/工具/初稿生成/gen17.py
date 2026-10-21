import json,re,glob,os
# 第17篇初稿（逐词对照）：S = [(段, [chunk, ...])]，chunk = ([(英文组, 中文组), ...], 可选 note)
# 2026-10-16 程序打底：英文、重点词与文章逐字核对，重点词中文沿用文章定稿（铁律），只按《翻译风格》调格式（“的”“了”进粗体）。
# 08–12 用户定下的规矩一开始就照做：过去时“了”、顺着英文语序排、代词译出（his→他的）、英文没有引号中文不加、
#   短语型用法整体标（T22：carved into、resorted to、starved of、exposed to、turned septic）、结尾解说（T28）、术语不漏（T30）。
S=[
(1,[[[("On 4 November 1922,","1922年11月4日，"),("in the Valley of the Kings,","在帝王谷，")]],
    [[("**labourers** **engaged** by the archaeologist Howard Carter","考古学家霍华德·卡特**聘用**(engaged)的**工人**(labourers)，")],
     "（@labourer 尤指户外的体力劳动者，劳工，工人）"],
    [[("**uncovered**","**发掘出了**(uncovered)"),("a **staircase** **carved into** the rock.","一段**雕刻在**(carved into)岩石**上面**(carved into)的**阶梯**(staircase)。")],
     "（engaged by…：过去分词短语作后置定语，修饰 labourers；\ncarved into the rock 同样作后置定语，修饰 staircase）\n（@carved into the rock 文字、图案或符号被雕刻在石头表面并留下刻痕）"]]),
(1,[[[("On 26 November,","11月26日，"),("with his **wealthy** **sponsor** Lord Carnarvon beside him,","在他那**富有的**(wealthy)**赞助人**(sponsor)卡纳冯勋爵的陪同下，")]],
    [[("Carter","卡特"),("made a small hole in the sealed **doorway**","在封住的**门道**(doorway)上开了一个小孔，")]],
    [[("and glimpsed","并瞥见了"),("the **glittering** gold of the boy king Tutankhamun.","少年国王图坦卡蒙**闪闪发光的**(glittering)黄金。")],
     "（with + 名词 + beside him：with 复合结构作伴随状语，“在……的陪同下”）"]]),
(1,[[[("The **spectacular** find","这一**惊人的/壮观的**(spectacular)发现，"),("**riveted** the world.","**牢牢吸引了**(riveted)全世界的**注意力**(riveted)。")]]]),
(2,[[[("Carnarvon","卡纳冯"),("sold **exclusive** rights to The Times,","将**独家的**(exclusive)新闻报道权卖给了《泰晤士报》，")]],
    [[("a **monopoly**","这种**垄断**(monopoly)"),("that left **competing** reporters **starved of** news.","让**相互竞争的**(competing)其他记者**严重缺少**(starved of)新闻。")],
     "（a monopoly…：同位语，概括前面的独家协议；\nleave sb starved of sth：让某人严重缺少某物）"]]),
(2,[[[("Many","许多人"),("**resorted to** **speculation**","（只能）**诉诸于**(resorted to)**猜测**(speculation)，"),("or sought outside **commentators**.","或者是找外界的**评论员**(commentators)。")],
     "（resort to：不得已而采用，诉诸于）"]]),
(2,[[[("In March 1923","1923年3月，"),("the **best-selling** novelist Marie Corelli","**畅销**(best-selling)小说家玛丽·科雷利"),("warned publicly","公开警告，")]],
    [[("that **dire** **punishment**","**极其严重的**(dire)**惩罚**(punishment)"),("awaited","等待着"),("anyone who entered a sealed **tomb**.","任何进入封闭**陵墓**(tomb)的人。")],
     "（that…：宾语从句；who…：定语从句，修饰 anyone）\n（@dire 情况、后果或处境极其严重，糟糕到令人担忧，通常还带有强烈的紧迫感。）"]]),
(2,[[[("Within a **fortnight**,","**两周**(fortnight)之内，"),("her words","她的话"),("would seem **uncanny**.","就会显得**诡异而又邪门**(uncanny)。")],
     "（would：过去将来，从1923年3月看之后的事）\n（within + 时间段 = “在……（时间）之内”，通常指“不超过这个期限”。）\n（@uncanny = 诡异、邪门、让人心里发毛（牛津释义：奇怪且难以解释）。）"]]),
(3,[[[("That month","当月，"),("a **mosquito**","一只**蚊子**(mosquito)"),("bit Carnarvon.","叮了卡纳冯。")]]]),
(3,[[[("He","他"),("**nicked** the bite with a **razor** while **shaving**,","**刮胡子**(shaving)时用**剃刀**(razor)**划破了**(nicked)叮咬处，")]],
    [[("it **turned septic**,","伤口**感染化脓了**(turned septic)，"),("and blood poisoning led to **pneumonia**.","继而血液中毒又引发了**肺炎**(pneumonia)。")],
     "（while shaving：在刮胡子时；turn septic：变得感染化脓，turn 作系动词）"]]),
(3,[[[("He","他"),("died in Cairo on 5 April 1923.","于1923年4月5日在开罗去世。")]]]),
(3,[[[("Newspapers reported","报纸报道称，")]],
    [[("that the city's lights failed **at that instant**","就**在那一瞬间**(at that instant)，全城（开罗）的灯都熄灭了，")]],
    [[("and that his dog in England","而他在英国的狗也"),("**howled** and died.","**嚎叫**(howled)着死去了。")],
     "（两个 that 从句并列，都作 reported 的宾语）"]]),
(3,[[[("Yet","然而，"),("**blackouts**","**停电**(blackouts)"),("were almost a daily **occurrence** in Cairo.","在当时的开罗几乎是天天都有的**事情**(occurrence)。")]]]),
(4,[[[("No curse **inscription** was ever found in the tomb.","墓中从未发现过任何诅咒**铭文**(inscription)。")],
     "（No… was ever found：no 否定主语，全句否定，“从未发现过任何……”）"]]),
(4,[[[("In December 2002","2002年12月，"),("a British Medical Journal study","《英国医学杂志》的一项研究"),("traced","追溯了")]],
    [[("the **fate** of 44 Westerners in Egypt at the time.","当时身在埃及的44名西方人的**命运**(fate)。")],
     "（in Egypt at the time：后置定语，修饰 Westerners）"]]),
(4,[[[("The 25 **exposed to** the tomb","其中曾**接触**(exposed to)这座陵墓的25人，"),("died at an average age of 70,","平均死亡年龄为70岁，")]],
    [[("**versus** 75 for the rest,","**相比之下**(versus)其余的人为75岁；"),("a **margin** not statistically **significant**.","这一**差距**(margin)在统计上并不**显著**(significant)。")],
     "（exposed to the tomb：过去分词短语作后置定语，\n修饰 The 25；\na margin…：同位语，概括前面的差距）"]]),
(4,[[[("The **mortality** figures","这些**死亡**(mortality)数据"),("lent the **ominous** **rumour** no **credibility**.","让这则**不祥的**(ominous)**传言**(rumour)毫无**可信度**(credibility)。")],
     "（lend sth no credibility：不让某事显得可信）"]]),
(5,[[[("Carnarvon's **untimely** **demise**","卡纳冯的**过早**(untimely)**离世**(demise)"),("had **fuelled** the tale,","**助长了**(fuelled)这一传言，"),("giving it **impetus**.","并为其**推波助澜**(impetus)。")],
     "（giving…：现在分词短语作结果状语）\n（giving it impetus：赋予它推动力\n（让它加速发展、更有势头）。）\n（@impetus 的核心词义就是：冲力、推动力、促进因素。）\n（在这个语境里，就是让这个谣言传播得更猛、发展得更快。）"]]),
(5,[[[("Carter,","卡特，"),("the **excavator** who had **unsealed** the **burial** place,","这位**启封了**(unsealed)这处**墓葬**(burial)的**发掘者**(excavator)，")]],
    [[("died in March 1939,","于1939年3月去世，"),("aged 64,","终年64岁，"),("almost sixteen years after his **patron**.","距他的**资助人**(patron)去世已近十六年。")],
     "（the excavator who…：同位语，说明 Carter；\nalmost sixteen years after his patron：在他的资助人之后近十六年）"]]),
(5,[[[("The legend","这个传说"),("had left him **conspicuously** **unharmed**.","偏偏让他**毫发无损**(unharmed)，这一点**格外醒目**(conspicuously)。")],
     "（leave sb unharmed：让某人未受伤害；conspicuously 修饰 unharmed）\n（结局：卡纳冯的过早离世让诅咒的说法传开，\n可墓中从未发现诅咒铭文，开罗停电也是常事；\n2002年的研究显示，接触过陵墓的人死亡年龄\n与其余的人相比，差距在统计上并不显著；\n亲手启封墓葬的卡特，在卡纳冯之后又活了近十六年。）"]]),
]
CONF={"短语":{"S1 engaged … by":"labourers engaged by the archaeologist：by 只引出被动的施动者（被……聘用），不是 engage 的固定搭配（速查表搭配是 engage a lawyer、be engaged in）"},
 "中文意思":{"S15 versus":"文章定稿译作“相比之下”（一个完整的词，不被隔开），沿用定稿（铁律），不拆成“与……相比”"}}
out={"no":"17","title_en":"The Curse of the Pharaoh","title_zh":"法老的诅咒","title_fx":{"hl":["Curse","Pharaoh"],"ghost":[]},"sentences":[],"核对确认":CONF,"结尾解说":"结局","allow_clash":["turned septic"],
     "高亮按实际开口":True,"高亮开口门槛":40,
     "结尾句":{"S19":{"整句语速":0.8,"依据":"全篇结尾句按 07 定下的标准（用户 2026-10-10 同意并要求所有视频统一）：最后一句没有句中标点，整句 0.80 倍速（01、02 的写法）"}},
     "术语":{"Valley of the Kings":"帝王谷","Howard Carter":"霍华德·卡特","Carnarvon":"卡纳冯","Carter":"卡特","Tutankhamun":"图坦卡蒙","The Times":"泰晤士报",
            "Marie Corelli":"玛丽·科雷利","Cairo":"开罗","England":"英国","British Medical Journal":"英国医学杂志","Egypt":"埃及","Westerners":"西方人"}}
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 核对 import 生成并核对
生成并核对(S, out)
