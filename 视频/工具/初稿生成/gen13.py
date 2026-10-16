import json,re,glob,os
# 第13篇初稿（逐词对照）：S = [(段, [chunk, ...])]，chunk = ([(英文组, 中文组), ...], 可选 note)
# 2026-10-16 程序打底：英文、重点词与文章逐字核对，重点词中文沿用文章定稿（铁律），只按《翻译风格》调格式（“的”“地”“了”进粗体）。
# 08–12 用户定下的规矩一开始就照做：过去时“了”、顺着英文语序排、代词译出（his→他的）、英文没有引号中文不加、
# 三项并列加牛津逗号（S8 lost concentration, and）；正文不用“即”（S13 改“也就是”）。
#   短语型用法整体标（T22：jolt sb awake、be gripped by、assist sb in、lapse into、pin the blame on、bounce back from、doze off），被隔开的中文意思每处都标（T23）、结尾解说（T28）、术语不漏（T30）。
S=[
(1,[[[("On 28 December 1963","1963年12月28日，")]],
    [[("Randy Gardner, a 17-year-old science **enthusiast** at a San Diego high school,","圣迭戈一名17岁的高中科学**爱好者**(enthusiast)兰迪·加德纳，")]],
    [[("set out to **forgo** **slumber** for a **regional** science fair.","为了参加一场**地区性的**(regional)科学展，开始尝试**放弃**(forgo)**睡眠**(slumber)。")],
     "（a 17-year-old science enthusiast…：同位语，说明 Randy Gardner 的身份；\nset out to do：着手做，开始尝试做）"]]),
(1,[[[("Two **companions**","两名**同伴**(companions)"),("**diligently**","**尽心尽力**(diligently)，")]],
    [[("**jolted** him **awake** whenever his **alertness** **waned**","每当他的**警觉**(alertness)**减弱**(waned)，就**让**(jolted awake)他**猛然清醒过来**(jolted awake)，")]],
    [[("and logged his **mood**.","并记录了他的**情绪**(mood)。")],
     "（jolt sb awake：使某人猛然清醒；whenever…：时间状语从句，每当……）"]]),
(1,[[[("The project,","这个项目，"),("a **voluntary** **endeavour**,","一次**自愿的**(voluntary)**尝试**(endeavour)，")]],
    [[("went on to **take first place**.","继而**夺得了第一名**(take first place)。")],
     "（a voluntary endeavour：同位语，补充说明 the project；\ngo on to do：后来接着做成……）"]]),
(2,[[[("William Dement,","威廉·德门特，"),("a sleep researcher at Stanford,","斯坦福大学的睡眠研究者，")]],
    [[("read press **coverage** of the attempt","读到了媒体对这次尝试的**报道**(coverage)，"),("and was **intrigued**.","并且**非常感兴趣**(intrigued)。")]]]),
(2,[[[("He drove to San Diego","他驾车前往圣迭戈，")]],
    [[("and **assisted** John J. Ross, a Navy researcher,","**协助**(assisted in)约翰·J·罗斯，一位海军研究员，"),("**in** monitoring the **sleepless** boy **closely**.","去**密切**(closely)监视这个**不眠的**(sleepless)少年。")],
     "（assist sb in doing：协助某人做……；\na Navy researcher：同位语，说明 Ross 的身份）"]]),
(2,[[[("The two **investigators**","两位**研究人员**(investigators)"),("**attentively** noted the **fluctuations** in his state","**专心地**(attentively)记下了他状态的种种**波动**(fluctuations)，")]],
    [[("as the **deprivation** **progressively** **deepened**.","其间睡眠**剥夺**(deprivation)**逐步**(progressively)**加深**(deepened)。")],
     "（as…：时间状语从句，在……的过程中）\n（睡眠剥夺（sleep deprivation）通常译为“睡眠剥夺”，\n日常也常说“睡眠不足”，\n指睡眠时间不足、睡眠被反复打断或完全缺乏睡眠，\n进而影响身心功能的状态。）"]]),
(3,[[[("The **consequences**","**后果**(consequences)"),("soon **mounted**.","很快便开始**不断加剧**(mounted)。")],
     "（@mount “数量逐渐增加、\n@mount|程度不断加剧、不断累积（上升）”\n@mount|（例如：tension mounted 紧张局势加剧，\n@mount|costs mounted 成本不断攀升）。）"]]),
(3,[[[("Gardner","加德纳"),("grew **moody**,","变得**喜怒无常**(moody)，")]],
    [[("lost **concentration**,","**注意力**(concentration)难以集中，")]],
    [[("and found his **short-term** memory **impaired**.","他的**短时**(short-term)记忆也**受损了**(impaired)。")],
     "（grow + 形容词：变得……；\nfind + 宾语 + 过去分词：发现……处于某种状态）\n（@impaired 几乎是一个医疗和科研专属词汇。\n@impaired|它经常用来描述人的感官、认知或身体机能出现障碍：\n@impaired|hearing impaired = 听力受损 / 听障（绝对不能用 damaged 或 injured）\n@impaired|visually impaired = 视力受损 / 视障\n@impaired|cognitively impaired = 认知受损 / 认知障碍）"]]),
(3,[[[("He became **suspicious**,","他变得**多疑**(suspicious)，"),("at times **paranoid**,","有时甚至**偏执/妄想性的**(paranoid)，")]],
    [[("and began to **hallucinate**.","还开始**出现幻觉**(hallucinate)。")]]]),
(3,[[[("On the fourth day","第四天，"),("he was **gripped by** the **delusion**","他**被**(gripped by)一种**妄想/错觉**(delusion)**攫住了**(gripped by)，")]],
    [[("that he was a professional American football player.","以为自己是一名美式橄榄球职业球员。")],
     "（be gripped by：被……攫住；that…：同位语从句，说明 delusion 的内容）"]]),
(4,[[[("Gardner","加德纳"),("ended the **wearying** attempt on 8 January 1964,","于1964年1月8日结束了这场**令人疲惫的**(wearying)尝试，")]],
    [[("after 264.4 hours,","共历时264.4小时，"),("about 11 days and 25 minutes.","约合11天零25分钟。")]]]),
(4,[[[("He then","随后他"),("slept **soundly**","**酣畅地/深度地**(soundly)睡了"),("for about 14 hours","约14小时，")]],
    [[("and woke","醒来时"),("apparently **refreshed**.","似乎**神清气爽/恢复精神的**(refreshed)。")],
     "（@soundly 是专门用来表示这个睡眠非常的酣畅深度。）"]]),
(4,[[[("Researchers","研究者们"),("**probed** the case in a 1965 **scholarly** paper,","在1965年的一篇**学术**(scholarly)论文中**探究了/深入研究**(probed)这一案例，")]],
    [[("which helped **highlight** microsleeps,","该论文有助于**凸显**(highlight)微睡眠——")]],
    [[("**involuntary** **lapses into** sleep lasting a few seconds.","**不由自主地**(involuntary)**陷入**(lapses into)持续几秒钟短暂睡眠的状态。")],
     "（which…：非限制性定语从句，指这篇论文；\ninvoluntary lapses into sleep…：同位语，解释 microsleeps；\nlasting…：现在分词短语作后置定语）\n@lapses into|（lapse into: 不知不觉地陷入（某种状态），\n@lapses into|尤指无意识的、非自愿的，或者是不太好的状态。）"]]),
(4,[[[("Gardner","加德纳"),("may have had such **momentary** **bouts**","可能经历过这种**短暂的**(momentary)**发作**(bouts)"),("without noticing.","而未曾察觉。")],
     "（may have done：对过去情况的推测，可能已经……）\n@bouts|（bout 一阵、一场、一回、一次发作\n@bouts|（通常指疾病、情绪或活动的阵发性发作，如 a bout of fever 一阵发烧））"]]),
(5,[[[("In 1997","1997年，"),("Guinness World Records","吉尼斯世界纪录")]],
    [[("{{=}}**discontinued** monitoring such attempts because of the health **perils**,","因健康**风险**(perils)**停止了**(discontinued)监测此类尝试；")]],
    [[("and others have since **alleged**","此后，其他人**声称/宣称**(alleged)"),("longer **stints** awake.","有过更长的**清醒时段**(stints)。")],
     "（discontinue doing：停止做……；have since done：从那以后已经……；stints awake：清醒的时段）"]]),
(5,[[[("In a 2017 interview","在2017年的一次采访中，"),("Gardner said","加德纳说")]],
    [[("severe **insomnia**","严重的**失眠**(insomnia)"),("had **tormented** him for about a decade,","**折磨了**(tormented)他约十年，")]],
    [[("and he himself","他本人"),("**pinned the blame on** the experiment.","**把**(pinned the blame on)它**归咎于**(pinned the blame on)这次实验。")],
     "（pin the blame on…：把责任归到……身上，归咎于……；\nhe himself：他本人，强调是他自己的看法）"]]),
(5,[[[("The boy who had seemed to **bounce back from** **exhaustion** with one long rest","那个曾看似只要睡个长觉，就能**从**(bounce back from)**精疲力竭**(exhaustion)**中迅速恢复**(bounce back from)的少年，")]],
    [[("would, decades later,","几十年后，"),("**barely** **doze off**.","却**几乎**(barely)连**打个盹**(doze off)都费劲。")],
     "（who…：定语从句，修饰 the boy；\nbounce back from：从……中恢复过来；\ndoze off：打盹/打瞌睡/凑合着短睡一下）\n（结局：17岁的加德纳为一场科学展尝试不睡觉，\n历时264.4小时，项目获得了第一名；\n他随后睡了约14小时，醒来时似乎神清气爽，\n可在2017年的采访中，他说严重的失眠折磨了他约十年，\n他本人把它归咎于这次实验。）"]]),
]
CONF={"牛津逗号":{"S11 4 hours, about 11 days and":"不是三项并列：about 11 days and 25 minutes 是同位语，换算前面的 264.4 hours；11 days and 25 minutes 是一个时长"},
 "短语":{"S8 short-term memory":"short-term 本身就是“短期的，短时的”（速查表两个释义同义），short-term memory 是“短时 + 记忆”字面相加，memory 是普通名词，不是靠整体成义的习语；文章也只标 short-term"}}
Q1="用户 2026-10-16：S1 中文照用户原话按用户的中文顺序——“1963年12月28日，圣迭戈一名17岁的高中科学爱好者兰迪·加德纳，为了参加一场地区性的 科学展，开始尝试 放弃 睡眠。”"
out={"no":"13","title_en":"Eleven Days Without Sleep","title_zh":"十一天不睡觉的少年","title_fx":{"hl":["Eleven","Sleep"],"ghost":[]},"sentences":[],"核对确认":CONF,"换行变更已获同意":{"S1":Q1,"S15":"用户 2026-10-16：S15 那一屏英文保持一行（字号自动缩小一点，字一个不改）——“OK”"},"结尾解说":"结局",
     "allow_clash":["pinned the blame on"],"高亮按实际开口":True,"高亮开口门槛":40,
     "术语":{"Randy Gardner":"兰迪·加德纳","Gardner":"加德纳","William Dement":"威廉·德门特","John J. Ross":"约翰·J·罗斯","San Diego":"圣迭戈","Stanford":"斯坦福","Navy":"海军",
            "Guinness World Records":"吉尼斯世界纪录","microsleeps":"微睡眠","American football":"美式橄榄球"}}
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 核对 import 生成并核对
生成并核对(S, out)
