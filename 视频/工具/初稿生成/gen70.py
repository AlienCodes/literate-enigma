import json,re,glob,os
# 第70篇初稿（逐词对照）：S = [(段, [chunk, ...])]，chunk = ([(英文组, 中文组), ...], 可选 note)
# 2026-11-08 重点词中文沿用文章定稿（铁律）；中英尽量对齐、标色优先；不用破折号（T36）；三项并列加牛津逗号（T18）；英文没有引号中文不加。
S=[
(1,[[[("Before 1840,","1840年以前，"),("British **postage**","英国的**邮费**(postage)"),("was **levied** according to the number of sheets in a letter and the **mileage** of its **carriage**.","按信件的页数和**运送**(carriage)**里程**(mileage)**收取**(levied)。")],
     "（according to A and B：按 A 和 B；its 指 letter）"]]),
(1,[[[("The sum","这笔钱"),("was usually","通常"),("**payable** on **delivery**,","在**投递**(delivery)时**支付**(payable)，")]],
    [[("so","因此"),("the person receiving the **correspondence**, not the **sender**, settled it.","付钱的是收到**信件**(correspondence)的人，而不是**寄信人**(sender)。")],
     "（receiving the correspondence：现在分词短语作后置定语，修饰 person；\nit 指 the sum）"]]),
(1,[[[("Prices","价格"),("thus","也就"),("**fluctuated** from one **postal** item to the next.","随每件**邮政**(postal)物品而**波动**(fluctuated)。")],
     "（from one … to the next：从一件到下一件）"]]),
(2,[[[("In 1837","1837年，"),("Rowland Hill","罗兰·希尔"),("published a **booklet**","出版了一本**小册子**(booklet)，"),("urging reform.","呼吁改革。")],
     "（urging reform：现在分词短语，补充说明 booklet）"]]),
(2,[[[("Parliament **enacted** the **campaigner**'s **proposal** in 1839,","1839年，议会将这位**改革倡导者**(campaigner)的**提议**(proposal)**立法通过**(enacted)；")],
     "（campaigner 指 Rowland Hill）"],
    [[("and on 10 January 1840","1840年1月10日，"),("the Uniform Penny Post","统一便士邮资"),("began.","开始实行。")]]]),
(2,[[[("A letter of up to half an **ounce**","重量不超过半**盎司**(ounce)的信"),("now cost one penny to any **destination** in Britain,","寄往英国境内任何**目的地**(destination)，都只需一便士，")],
     "（of up to half an ounce：介词短语作后置定语，修饰 letter）"],
    [[("and the fee","费用"),("was **prepaid** by whoever sent it.","由寄信的一方**预付**(prepaid)。")],
     "（whoever sent it：名词性从句作 by 的宾语；it 指 letter）"]]),
(2,[[[("One **flat-rate** charge","统一的**单一费率**(flat-rate)"),("replaced **variation** with **simplicity**.","以**简便**(simplicity)取代了**差异**(variation)。")],
     "（replace A with B：以 B 取代 A）"]]),
(3,[[[("The Penny Black,","黑便士"),("a one-penny **denomination**,","是一枚一便士**面值**(denomination)的邮票，")],
     "（a one-penny denomination：同位语，补充说明 Penny Black）"],
    [[("was released on 1 May 1840,","于1840年5月1日发行，")]],
    [[("its **validity**","**有效期**(validity)"),("starting on 6 May.","从5月6日开始。")],
     "（its validity starting…：独立主格结构）"]]),
(3,[[[("**Engraved** on it was","上面**雕刻**(engraved)着")],
     "（倒装句：Engraved on it 提前，主语是 a youthful likeness…；\nit 指 Penny Black）"],
    [[("a **youthful** **likeness** of Queen Victoria, the reigning **monarch**.","当时在位的**国君**(monarch)维多利亚女王**年轻的**(youthful)**肖像**(likeness)。")],
     "（the reigning monarch：同位语，补充说明 Queen Victoria）"]]),
(3,[[[("An **aggregate** of 68,808,000 were printed.","印制**总数**(aggregate)为68,808,000枚。")],
     "（an aggregate of：总共）"]]),
(3,[[[("The sheets","整版邮票之间"),("had no holes for **separation**,","没有用于**分隔**(separation)的孔，")]],
    [[("so each stamp","每枚"),("was cut out **individually** with **scissors**.","都要用**剪刀**(scissors)**逐一**(individually)剪下。")],
     "（was cut out：被动语态；cut out：剪下）"]]),
(4,[[[("**Mailings**","寄送的**邮件**(mailings)"),("doubled,","翻了一番，")]],
    [[("from about 80 million **items** in 1839","从1839年的约8,000万件**邮品**(items)"),("to over 169 million in 1840.","增至1840年的1.69亿件以上。")],
     "（from A to B：从 A 增至 B）"]]),
(4,[[[("The design","这一设计"),("had a **drawback**.","有个**缺点**(drawback)。")]]]),
(4,[[[("Against black,","在黑色底上，"),("the red cancelling mark","红色注销戳"),("was barely **noticeable**,","几乎不**显眼**(noticeable)，"),("lacking **contrast**,","缺乏**反差**(contrast)，")],
     "（lacking contrast：现在分词短语，说明原因）"],
    [[("and the ink","墨迹"),("could be **erased**,","又能被**擦除**(erased)，")]],
    [[("leaving stamps","邮票"),("**vulnerable** to **reuse**.","**容易遭到**(vulnerable)**重复使用**(reuse)。")],
     "（leaving…：现在分词短语作结果状语；\nleave A vulnerable to B：使 A 容易遭到 B）"]]),
(4,[[[("In February 1841","1841年2月，"),("the Penny Red, cancelled in black ink,","改用黑色墨迹注销的红便士")],
     "（cancelled in black ink：过去分词短语，补充说明 Penny Red）"],
    [[("arrived","问世，"),("to deter **tampering** and **fraud**.","以防**篡改**(tampering)和**欺诈**(fraud)。")],
     "（to deter…：不定式作目的状语）"]]),
(5,[[[("As the **initiator** of postage stamps,","作为邮票的**首创者**(initiator)，"),("Britain","英国"),("set a **precedent**","开创了**先例**(precedent)，"),("and earned an **exemption**.","并赢得一项**豁免**(exemption)。")]]]),
(5,[[[("Its stamps","英国邮票"),("are **nameless**,","是**无名的**(nameless)，"),("with no country **inscribed** on them.","上面没有**刻印**(inscribed)国名。")],
     "（with no country inscribed on them：with 复合结构；Its 指 Britain）"]]),
(5,[[[("By international agreement,","根据国际协议，"),("the **sovereign**'s head","**君主**(sovereign)头像"),("**suffices** for **identification**,","就**足以**(suffices)作为**识别**(identification)标志，")]],
    [[("an **implicit** **designation**","这是一种**隐含的**(implicit)**标识**(designation)，"),("that other countries spell out in print.","其他国家则把国名印在邮票上。")],
     "（an implicit designation：同位语，补充说明前面整句；\nthat other countries spell out in print：定语从句，修饰 designation；\nspell out：明确写出）\n"
     "（简述：1840年以前，英国邮费按页数和里程计算，通常在投递时由收信人支付。\n"
     "1837年罗兰·希尔出版小册子呼吁改革，1839年议会立法，1840年1月10日统一便士邮资开始实行：半盎司以内的信寄往英国境内任何地方都是一便士，由寄信人预付。\n"
     "1840年5月，印着年轻的维多利亚女王肖像的黑便士发行，共印68,808,000枚，要用剪刀逐枚剪下。\n"
     "邮件量一年翻了一番，但红色注销戳在黑邮票上不显眼，墨迹还能擦掉，1841年2月改用黑墨注销的红便士。\n"
     "作为邮票的首创者，英国邮票不印国名，只凭君主头像识别。）"]]),
]
G={}
DZ={}
CONF={"合组":G,"对齐":DZ}
out={"no":"70","title_en":"The Stamp That Changed the Post","title_zh":"一枚邮票改变通信","title_fx":{"hl":["Stamp","Post"],"ghost":[]},"sentences":[],"核对确认":CONF,"结尾解说":"简述",
     "高亮按实际开口":True,"高亮开口门槛":40,
     "术语":{"Rowland Hill":"罗兰·希尔","Parliament":"议会","Uniform Penny Post":"统一便士邮资","Britain":"英国","British":"英国的","Penny Black":"黑便士","Queen Victoria":"维多利亚女王","Penny Red":"红便士"}}
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 核对 import 生成并核对
生成并核对(S, out)
