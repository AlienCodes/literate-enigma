import json,re,glob,os
# 第53篇初稿（逐词对照）：S = [(段, [chunk, ...])]，chunk = ([(英文组, 中文组), ...], 可选 note)
# 2026-11-05 重点词中文沿用文章定稿（铁律），只按《翻译风格》调格式；三项并列加牛津逗号（T18）；不用破折号（T36）；“了”进粗体；英文没有引号中文不加。
S=[
(1,[[[("On the morning of 7 November 1940,","1940年11月7日上午，"),("a **sustained** wind of about 40 miles an hour","一股时速约40英里的**持续**(sustained)大风"),("set","使"),("the Tacoma Narrows Bridge","塔科马海峡大桥"),("**twisting**.","**扭动**(twisting)起来。")],
     "（of about 40 miles an hour：后置定语，修饰 wind；\nset sth doing：使……（不停地）做某事）"]]),
(1,[[[("Its **deck**","它的**桥面**(deck)"),("**tilted** from side to side","左右**倾侧**(tilted)，"),("in ever more **violent** **oscillations**","**振荡**(oscillations)愈发**剧烈**(violent)，")],
     "（ever more＋形容词：越来越……）"],
    [[("until","直到"),("most of the main span","主跨大部分"),("**tore apart**","**断裂**(tore apart)、"),("and **tumbled** into the water.","**跌落**(tumbled)水中。")],
     "（until…：时间状语从句，直到……）"]]),
(1,[[[("No one died.","无人丧生。")]]]),
(1,[[[("**Footage** of the **spectacle**","这一**奇观**(spectacle)的**影像**(Footage)"),("would later","后来"),("**fascinate**","**吸引了**(fascinate)"),("students worldwide.","世界各地的学生。")],
     "（would later do：过去将来，后来会……）"]]),
(2,[[[("The bridge","这座桥"),("had opened in July 1940","于1940年7月通车，")],
     "（had opened：过去完成时，通车早于坍塌）"],
    [[("as the third-longest **suspension** **span** in the world at the time,","其主跨是当时世界上第三长的**悬索**(suspension)桥**跨径**(span)，")],
     "（as…：作为……；at the time：在当时）"],
    [[("its roadway","路面"),("hung from steel cables.","悬挂在钢缆上。")],
     "（its roadway hung from…：独立主格结构，补充说明桥的结构）"]]),
(2,[[[("Girders only eight feet deep stiffened the deck,","加劲桥面的钢梁只有8英尺高，")],
     "（only eight feet deep：后置定语，修饰 Girders）"],
    [[("making it","使桥身"),("**slender**,","**纤细**(slender)、"),("**elegant**,","**优雅**(elegant)"),("and **economical**,","而又**省钱**(economical)，"),("but far from **rigid**.","却远谈不上**刚硬**(rigid)。")],
     "（making it…：现在分词短语作结果状语；\nfar from：远非）"]]),
(2,[[[("Even **faint** **breezes**","哪怕**轻微的**(faint)**微风**(breezes)"),("made it **heave**,","也会让它**起伏**(heave)，")],
     "（make sth do：使……做）"],
    [[("earning the **nickname**","由此得了个**绰号**(nickname)："),("Galloping Gertie.","舞动的格蒂。")],
     "（earning…：现在分词短语作结果状语）"]]),
(3,[[[("**Textbooks**","**教科书**(Textbooks)"),("have long","长期以来一直"),("**invoked**","**援引**(invoked)"),("**resonance**:","**共振**(resonance)来解释：")],
     "（have long done：现在完成时，长期以来一直……）"],
    [[("a **periodic** push that matches an object's natural **frequency**","与物体固有**频率**(frequency)相合的**周期性的**(periodic)推力"),("can **amplify**","能**放大**(amplify)"),("its motion,","其运动，")],
     "（that matches…：定语从句，修饰 push）"],
    [[("as when","就像"),("well-timed shoves","合拍的一次次推送"),("**propel**","**推动**(propel)"),("a child on a swing.","秋千上的孩子越荡越高。")],
     "（as when…：就像……的时候那样）"]]),
(3,[[[("The **analogy**","这个**类比**(analogy)"),("is **intuitive**","**直观**(intuitive)"),("but **deceptive**.","却**具有迷惑性**(deceptive)。")]]]),
(3,[[[("That morning's wind","那天上午的风"),("did not **pulse** in time with the bridge;","并没有合着大桥的节拍**一阵阵涌动**(pulse)；")],
     "（in time with：合着……的节拍）"],
    [[("it blew","它吹得"),("fairly **steadily**.","还算**平稳**(steadily)。")]]]),
(4,[[[("The **mechanism**","其**机理**(mechanism)"),("was **subtler**.","要**更为微妙**(subtler)。")]]]),
(4,[[[("Each twist","每一次扭动都"),("**altered**","**改变了**(altered)"),("the passing airflow,","掠过的气流，")]],
    [[("which","而气流又"),("**reinforced**","**加强了**(reinforced)"),("the next twist:","下一次扭动：")],
     "（which…：非限制性定语从句，指代 the passing airflow）"],
    [[("a **feedback** loop that kept **tapping** the wind for energy.","这是一个不断从风中**汲取**(tapping)能量的**反馈**(feedback)回路。")],
     "（a feedback loop：同位语，概括前面的过程；\nkeep doing：不断做；tap A for B：从 A 汲取 B）"]]),
(4,[[[("In March 1941","1941年3月，"),("a federal **panel**","一个联邦**调查委员会**(panel)"),("blamed","把原因归于"),("the deck's **flexibility**","桥面的**柔性**(flexibility)"),("and wing-like lift.","和类似机翼的升力。")],
     "（blame…：把（事故）归咎于……）"]]),
(4,[[[("Later analysis","后来的分析"),("called the mechanism flutter;","把这一机理称为颤振；")],
     "（call A B：把 A 称为 B）"],
    [[("in February 1991","1991年2月，"),("two engineers","两位工程师"),("**asserted** in a physics journal","在一份物理学期刊上**断言**(asserted)，"),("that textbooks had **erred**.","教科书**说错了**(erred)。")],
     "（that…：宾语从句，作 asserted 的宾语；\nhad erred：过去完成时）"]]),
(5,[[[("The panel","该委员会"),("urged","力主进行"),("**wind-tunnel** tests,","**风洞**(wind-tunnel)试验，")]],
    [[("and trials on **scaled-down** **replicas**","而用**按比例缩小的**(scaled-down)**模型**(replicas)做试验"),("**gradually**","也**逐渐**(gradually)"),("became **customary** for suspension bridges.","成为悬索桥的**惯例**(customary)。")],
     "（trials on…：用……做的试验；\nbecome customary：成为惯例）"]]),
(5,[[[("A **sturdier** **replacement**","一座**更坚固的**(sturdier)**替代**(replacement)桥"),("opened in October 1950.","于1950年10月通车。")]]]),
(5,[[[("Gertie's fall","格蒂的倒塌"),("may still **instruct** engineers,","或许至今仍能给工程师以**教益**(instruct)，"),("if read **accurately**:","只要解读得**准确**(accurately)：")],
     "（if read accurately：省略形式，= if it is read accurately）"],
    [[("the wind never kept time with the bridge —","风从未合着大桥的节拍，"),("the bridge's own motion","是大桥自身的运动"),("turned a sustained wind destructive.","让持续不断的风变得具有破坏力。")],
     "（keep time with：合着……的节拍；\nturn A＋形容词：使 A 变得……）\n"
     "（简述：1940年11月7日，一股持续的大风让塔科马海峡大桥扭动起来，振荡越来越剧烈，主跨断裂坠入水中，无人丧生。\n"
     "这座悬索桥当年7月才通车，桥身纤细、省钱却不够刚硬，微风就能让它起伏，人称舞动的格蒂。\n"
     "教科书常用共振来解释，但那天的风吹得平稳，并没有合着大桥的节拍涌动。\n"
     "真正的机理是扭动改变气流、气流又加强扭动的反馈回路，后来称为颤振，1991年两位工程师指出教科书错了。\n"
     "此后风洞模型试验成为惯例，1950年更坚固的新桥通车。）"]]),
]
CONF={}
out={"no":"53","title_en":"The Wind That Kept No Time: The Fall of Galloping Gertie","title_zh":"不合拍的风：塔科马大桥的陨落","title_fx":{"hl":["Wind","Galloping Gertie"],"ghost":[]},"sentences":[],"核对确认":CONF,"结尾解说":"简述",
     "高亮按实际开口":True,"高亮开口门槛":40,
     "术语":{"Tacoma Narrows Bridge":"塔科马海峡大桥","Galloping Gertie":"舞动的格蒂","Gertie":"格蒂"}}
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 核对 import 生成并核对
生成并核对(S, out)
