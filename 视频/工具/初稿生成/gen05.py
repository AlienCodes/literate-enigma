import json,re,glob,os
# 第05篇（逐词对照）：S = [(段, [chunk, ...])]，chunk = ([(英文组, 中文组), ...], 可选 note)
# 2026-11-10 补齐：以 2026-10-08 独立审校后的对照稿（对照文本/05-文本.docx）为底；重点词中文沿用文章定稿（铁律）；不用破折号（T36）。
S=[
(1,[[[("In November 1983","1983年11月，"),("a 15-year-old girl","一名15岁的女孩")]],
    [[("was murdered in the Leicestershire village of Narborough,","在莱斯特郡的纳伯勒村遇害，")]],
    [[("and the **homicide**","这起**凶杀案**(homicide)"),("went","一直"),("**unsolved**.","**未能侦破**(unsolved)。")],
     "（go + 形容词：一直处于某种状态）"]]),
(1,[[[("In the summer of 1986","1986年夏天，"),("a second 15-year-old","又一名15岁的女孩")]],
    [[("was **slain** near **neighbouring** Enderby.","在**邻近的**(neighbouring)恩德比附近**被杀**(slain)。")]]]),
(1,[[[("A 17-year-old local youth","一名17岁的当地青年"),("**confessed** to","**供认了**(confessed)"),("the second killing,","第二起命案，")]],
    [[("and to **detectives**","在**警探**(detectives)看来，"),("the **perplexing**","这场**扑朔迷离的**(perplexing)"),("**investigation**","**调查**(investigation)"),("was **seemingly**","**似乎**(seemingly)"),("**resolved**.","已经**了结**(resolved)。")],
     "（to sb：在某人看来）"]]),
(2,[[[("The **revelation**","这个**发现**(revelation)"),("had come two years **previously**.","**早在**(previously)两年前就已经出现了。")],
     "（had come：过去完成时，比上一段1986年的事更早）"]]),
(2,[[[("On 10 September 1984","1984年9月10日，"),("Alec Jeffreys,","亚历克·杰弗里斯，")]],
    [[("a **geneticist**","一位**遗传学家**(geneticist)"),("at the University of Leicester,","在莱斯特大学（任职），")]],
    [[("**discerned** on an X-ray film","在一张X光片上**看出**(discerned)"),("**molecular** **markers**","一些**分子**(molecular)**标记**(markers)，")],
     "（宾语 molecular markers 带着 whose 从句，\n所以放到了状语后面）"],
    [[("whose **layout**","这些标记的**排布**(layout)"),("**varied** **considerably** from person to person.","在人与人之间**各异**(varied)，差别**相当大**(considerably)。")]]]),
(2,[[[("He called them","他把这些标记称为"),("DNA fingerprints,","DNA指纹，")]],
    [[("since,","因为"),("like fingerprints,","像指纹一样，"),("they **differentiated** individuals.","它们能把不同的人**区分**(differentiated)开来。")],
     "（since：因为，不是自从；\nlike fingerprints 是插入成分）"]]),
(2,[[[("The journal Nature","《自然》期刊"),("**promptly**","**很快**(promptly)就"),("carried his paper in March 1985.","在1985年3月刊登了他的论文。")],
     "（carry：指报刊刊登、登载）"]]),
(3,[[[("Police","警方"),("**enlisted** Jeffreys,","**请来了**(enlisted)杰弗里斯，")],
     "（enlist：请来帮忙、争取帮助）"],
    [[("and his **genetic** tests","他的**基因**(genetic)检测"),("**overturned**","**推翻了**(overturned)"),("the **erroneous** **confession**.","那份**错误的**(erroneous)**供词**(confession)。")]]]),
(3,[[[("The youth","那名青年"),("was not","不是"),("the **perpetrator**,","**行凶者**(perpetrator)，")]],
    [[("and","而且"),("the same **attacker**","是同一个**袭击者**(attacker)"),("had killed","杀害了"),("both girls.","这两名女孩。")]]]),
(3,[[[("The youth","这名青年"),("became","成为")]],
    [[("the first person known to be cleared by DNA evidence.","已知第一个凭DNA证据被证明清白的人。")],
     "（known to be cleared…：后置定语，修饰 the first person）"]]),
(3,[[[("The **forensic** **innovation**","这项**法医**(forensic)**创新**(innovation)"),("had freed an **innocent**","早已让一名**无辜者**(innocent)重获自由，")]],
    [[("before","在"),("it **implicated** anyone.","它**牵连**(implicated)到任何人之前。")],
     "（A before B：先 A 后 B；\nimplicate：牵连，表明……涉案）"]]),
(4,[[[("In January 1987","1987年1月，"),("police","警方"),("**commenced**","**开始了**(commenced)")]],
    [[("the world's first","世界上首次"),("**large-scale**","**大规模的**(large-scale)"),("DNA screening,","DNA筛查，")]],
    [[("asking","请"),("more than 5,000 men in three villages","三个村庄的5,000多名男子"),("for blood or **saliva**.","提供血液或**唾液**(saliva)。")],
     "（ask sb for sth：请某人提供某物；\nasking… 是伴随状语）"]]),
(4,[[[("None","没有一份样本"),("matched.","吻合。")]]]),
(4,[[[("The **elusive** killer,","这个**难以捉摸的**(elusive)凶手，"),("a local baker,","一名当地的面包师，")]],
    [[("had **induced**","事先**诱使**(induced)"),("a **co-worker**","一名**同事**(co-worker)"),("to give a sample in his name,","冒他的名字提供了样本，")],
     "（induce sb to do sth：诱使某人做某事；\nin his name：以他的名义）"],
    [[("**evading** **suspicion**.","**躲过了**(evading)**怀疑**(suspicion)。")],
     "（evading…：分词作结果状语，逻辑主语是凶手）"]]),
(4,[[[("In August 1987","1987年8月，"),("someone","有人"),("**overheard**","**无意中听到**(overheard)")]],
    [[("the co-worker","这名同事"),("discussing","在谈论"),("the **substitution**","**冒名顶替**(substitution)的事，")],
     "（overhear sb doing sth：无意中听到某人在做某事）"],
    [[("and **notified** police.","并**告知了**(notified)警方。")]]]),
(5,[[[("Colin Pitchfork","科林·皮奇福克"),("was **detained** on 19 September 1987,","在1987年9月19日被**拘留**(detained)，")]],
    [[("and his DNA **profile**","他的DNA**图谱**(profile)"),("matched.","（与凶手的）吻合。")]]]),
(5,[[[("In January 1988","1988年1月，"),("he","他"),("**pleaded** guilty","**认罪**(pleaded)")]],
    [[("and was **jailed** for life,","并被**判处**(jailed)终身监禁，")]],
    [[("the first person convicted of murder on the basis of DNA evidence.","（成为）第一个依据DNA证据被判谋杀罪的人。")],
     "（the first person… 是 he 的同位语；\nconvicted of：被判……罪；plead guilty：认罪）"]]),
(5,[[[("A **tip-off**,","是一条**举报**(tip-off)，"),("not the screening,","而不是那次筛查，"),("had **unmasked** him.","让他**现出原形**(unmasked)。")],
     "（A, not B, had done：是 A 而不是 B 做了……）"]]),
(5,[[[("The test's first **beneficiary**","这项检测的第一个**受益者**(beneficiary)"),("had been","是"),("a **blameless** **juvenile**","一名**清白的**(blameless)**少年**(juvenile)，")]],
    [[("who had","他曾"),("**falsely**","**违心地**(falsely)"),("admitted","认下"),("the **offence**.","这项**罪行**(offence)。")],
     "（简述：悬案：1983年和1986年，\n纳伯勒一带两名15岁女孩先后遇害，\n一名17岁当地青年供认了第二起命案。\n"
     "发现：1984年9月10日，\n杰弗里斯在X光片上看出DNA指纹，1985年3月论文刊登。\n"
     "翻案：他的检测证明青年清白，两起命案是同一个人所为。\n"
     "筛查：1987年1月起，\n三个村庄5,000多名男子接受世界首次大规模DNA筛查，\n凶手让同事冒名送样躲过。\n"
     "落网：1987年8月有人听到同事谈起冒名并报警，\n皮奇福克被拘留，1988年1月认罪，被判终身监禁。）"]]),
]
G={}
DZ={}
CONF={"合组":G,"对齐":DZ}
out={"no":"05","title_en":"The Fingerprint in the Blood","title_zh":"血里的指纹","title_fx":{"hl":["Fingerprint","Blood"],"ghost":[]},"sentences":[],"核对确认":CONF,"结尾解说":"简述",
     "高亮按实际开口":True,"高亮开口门槛":40,
     "术语":{"Leicestershire":"莱斯特郡","Narborough":"纳伯勒","Enderby":"恩德比","Alec Jeffreys":"亚历克·杰弗里斯","Jeffreys":"杰弗里斯","University of Leicester":"莱斯特大学","Nature":"《自然》","Colin Pitchfork":"科林·皮奇福克","DNA":"DNA"}}
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 核对 import 生成并核对
生成并核对(S, out)
