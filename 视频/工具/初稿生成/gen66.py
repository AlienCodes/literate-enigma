import json,re,glob,os
# 第66篇初稿（逐词对照）：S = [(段, [chunk, ...])]，chunk = ([(英文组, 中文组), ...], 可选 note)
# 2026-11-08 重点词中文沿用文章定稿（铁律）；不用破折号（T36）；三项并列加牛津逗号（T18）；形容词的“的”进粗体（T38）。
S=[
(1,[[[("In 1941","1941年，"),("George de Mestral, a Swiss engineer,","瑞士工程师乔治·德·梅斯特拉尔")],
     "（a Swiss engineer：同位语，补充说明 George de Mestral）"],
    [[("returned from hunting in the Alps with his **hound**, an Irish Pointer.","带着他的**猎犬**(hound)，一只爱尔兰指示犬，在阿尔卑斯山打猎归来。")],
     "（an Irish Pointer：同位语，补充说明 hound）"]]),
(1,[[[("**Prickly**","**多刺的**(Prickly)"),("burdock","牛蒡"),("**seed-heads**","**种子头**(seed-heads)"),("had **hitched** themselves to","紧紧**挂住**(hitched)了"),("his clothes","他的衣服，")],
     "（had hitched：过去完成时；\nhitch oneself to：挂在……上）"],
    [[("and lay **tangled**","也**缠结**(tangled)"),("in the dog's **fur**.","在狗的**毛皮**(fur)里。")],
     "（lay tangled：系表结构，lay 是 lie 的过去式）"]]),
(1,[[[("Under a microscope","在显微镜下，"),("he saw","他看到"),("thousands of tiny **barbs**,","成千上万个细小的**倒刺**(barbs)，")]],
    [[("each a **hook**","每一根都是一个**钩子**(hook)，"),("**grasping**","**钩住**(grasping)"),("the small **loops** in cloth.","布料上的小**毛圈**(loops)。")],
     "（each a hook…：独立主格结构，补充说明 barbs；\ngrasping…：现在分词短语，修饰 hook）"]]),
(2,[[[("Few took his idea **seriously** at first.","起初，很少有人**认真**(seriously)看待他的想法。")],
     "（take A seriously：认真看待 A）"]]),
(2,[[[("In Lyon, then a **weaving** centre,","在当时的**纺织**(weaving)中心里昂，")],
     "（then a weaving centre：同位语，补充说明 Lyon）"],
    [[("a cotton version","一个棉制版本"),("proved too **frail**","太**脆弱**(frail)，"),("to survive **abrasion**.","经不起**磨损**(abrasion)。")],
     "（too A to do：太 A 而不能……）"]]),
(2,[[[("Working with a **textiles** firm,","他与一家**纺织品**(textiles)公司合作，")],
     "（Working with…：现在分词短语作伴随状语）"],
    [[("he turned to **nylon**,","转而采用**尼龙**(nylon)。")],
     "（turn to：转而采用）"],
    [[("whose hooks","尼龙做成的钩子"),("were **stiff** enough","足够**硬挺**(stiff)，"),("to hold","既能扣住，"),("yet easy to pull apart.","又容易拉开。")],
     "（whose…：非限制性定语从句，修饰 nylon；\nA enough to do：足够 A，能……；\npull apart：拉开）"]]),
(2,[[[("The **trial-and-error** at the **looms** and **mills**","在**织机**(looms)旁和**工厂**(mills)里的**反复试验**(trial-and-error)"),("lasted","持续了"),("about ten years.","约十年。")],
     "（at the looms and mills：后置定语，修饰 trial-and-error）"]]),
(3,[[[("The name Velcro","Velcro 这个名字"),("**merged**","**合并**(merged)了"),("two French words,","两个法语词，")]],
    [[("velours, meaning **velvet**,","velours 意为**天鹅绒**(velvet)，"),("and crochet, meaning hook.","crochet 意为钩子。")],
     "（velours… and crochet…：同位语，补充说明 words；\nmeaning…：现在分词短语，说明词义）"]]),
(3,[[[("A US patent **duly** followed in 1955.","1955年，美国专利**顺理成章地**(duly)到手。")]]]),
(3,[[[("In 1959","1959年，"),("a New York fashion show","纽约一场时装秀")]],
    [[("sent **apparel** **stitched** with the **fasteners** down the **runway**.","让**缝有**(stitched)这种**搭扣**(fasteners)的**服装**(apparel)走上**T台**(runway)。")],
     "（stitched with…：过去分词短语作后置定语，\n修饰 apparel；\nsend A down B：让 A 走上 B）"]]),
(3,[[[("The public","公众却"),("was less **charmed** than expected,","不如预期那样**着迷**(charmed)，")],
     "（less A than expected：不如预期那样 A）"],
    [[("**mostly**","**主要**(mostly)"),("because of","是因为"),("the **aesthetic**.","它的**外观**(aesthetic)。")]]]),
(4,[[[("The **underdog**","这个不被看好的**弱者**(underdog)"),("proved its **utility** in **outer** space.","在**外层**(outer)空间证明了自己的**用处**(utility)。")]]]),
(4,[[[("NASA","美国航天局"),("used it in the Apollo programme","在阿波罗计划中用它")]],
    [[("to keep **gear** **anchored** in weightlessness, so that nothing would **hover** in **mid-air**.","把**装备**(gear)牢牢**固定**(anchored)住，免得东西在失重状态下**飘浮**(hover)在**半空**(mid-air)中。")],
     "（to keep…：不定式作目的状语；\nkeep A anchored：让 A 保持固定；\nso that…：引导目的状语从句）"]]),
(4,[[[("Apollo 11","阿波罗11号"),("was **equipped** with","**配备**(equipped)了"),("a **sizeable** amount,","**相当多的**(sizeable)用量，"),("about 3,300 square inches.","约3,300平方英寸。")],
     "（be equipped with：配备有；\nabout 3,300 square inches：同位语，补充说明 amount）"]]),
(4,[[[("NASA","美国航天局"),("did not invent","并没有发明"),("the nylon **clasp**.","这种尼龙**扣件**(clasp)。")]]]),
(5,[[[("When the patent ran out in 1978,","1978年专利到期后，")],
     "（When…：时间状语从句；run out：到期）"],
    [[("**cut-price** **knock-offs** from Taiwan, China, and South Korea","来自台湾、中国大陆和韩国的**廉价的**(cut-price)**仿冒品**(knock-offs)"),("**overran** the market,","大量**涌入**(overran)市场，")],
     "（from Taiwan, China, and South Korea：后置定语，\n修饰 knock-offs）"],
    [[("and a **niche** product","一种**小众**(niche)产品"),("went **mainstream**.","成了**主流**(mainstream)。")],
     "（go mainstream：成为主流）"]]),
(5,[[[("In 2017,","2017年，"),("to stop","为了不让"),("its **brand-name**","自己的**品牌名**(brand-name)"),("**melting** into","逐渐**消融**(melting)为"),("a **generic** **noun**,","一个**通用的**(generic)**名词**(noun)，")],
     "（to stop…：不定式作目的状语；\nstop A doing：不让 A 做……；\nmelt into：逐渐变成）"],
    [[("the company","公司"),("asked people","请大家"),("to call such **mimics** hook and loop fasteners.","把这类**仿品**(mimics)称作钩毛搭扣。")],
     "（ask A to do：请 A 做……；\ncall A B：把 A 称作 B）"]]),
(5,[[[("In effect,","实际上，"),("the firm","这家公司"),("was asking the public","是在请公众"),("to stop using its own name","别再用它自己的名字"),("for rivals' goods.","去称呼对手的商品。")],
     "（was asking：过去进行时；\nstop doing：不再做……；\nuse A for B：用 A 称呼 B）\n"
     "（简述：1941年，瑞士工程师乔治·德·梅斯特拉尔打猎归来，发现牛蒡刺果挂在衣服和狗毛上，显微镜下是无数小钩钩住布料上的毛圈。\n"
     "起初很少有人看好，棉制版本经不起磨损，他与纺织品公司合作改用尼龙，反复试验约十年。\n"
     "名字由法语 velours 和 crochet 合成，1955年获美国专利，1959年纽约时装秀上公众反应不如预期，主要是因为外观。\n"
     "美国航天局在阿波罗计划中用它在失重状态下固定装备，阿波罗11号用了约3,300平方英寸，但它不是美国航天局发明的。\n"
     "1978年专利到期后廉价仿品涌入市场，小众产品成了主流；2017年公司请大家把仿品称作钩毛搭扣，免得品牌名变成通用名词。）"]]),
]
G={}
DZ={}
CONF={"合组":G,"对齐":DZ}
out={"no":"66","title_en":"The Burrs That Became Velcro","title_zh":"一颗刺果钩出的发明","title_fx":{"hl":["Burrs","Velcro"],"ghost":[]},"sentences":[],"核对确认":CONF,"结尾解说":"简述",
     "高亮按实际开口":True,"高亮开口门槛":40,
     "术语":{"George de Mestral":"乔治·德·梅斯特拉尔","Swiss":"瑞士","Alps":"阿尔卑斯山","Irish Pointer":"爱尔兰指示犬","Lyon":"里昂","Velcro":"Velcro","French":"法语","US":"美国","New York":"纽约","NASA":"美国航天局","Apollo":"阿波罗","Taiwan":"台湾","China":"中国大陆","South Korea":"韩国"}}
out.update({"非人声区间": {"S1": [[2.7475, 3.013125, "紧贴词头"]], "S11": [[2.460125, 2.732417, "紧贴词头"]], "S17": [[1.663875, 1.890208]]}, "合成标点": {"S8": [["velvet, and", "velvet; and"]]}})   # 2026-11-08 逐 2.5 ms 实测（dossier_66 #2/#19/#30 A19 停顿后吸气）：S1 Mestral, 后 2.75–3.01 吸气（-38～-58 dB、重心 2.0–2.6 kHz、低频 -10～-22 dB），3.0175 起 a；S11 expected, 后 2.46–2.73 吸气（-47～-57 dB、重心 1.9–2.6 kHz、低频 -6～-19 dB），2.735 起 mostly 的 /m/ 浊音（周期 0.44）保留；S17 2017, 后 1.665–1.89 吸气（-43～-58 dB、重心 2.0–3.1 kHz、低频 -12～-24 dB），1.89–1.905 是 to 的闭塞静音，1.9075 起 /t/ 除阻；S8 velvet 的 /t/ 连进 and、没有闭塞（4.35–4.43 一直 -23～-40 dB），无处移植，合成时逗号换分号让配音自己停（G57 合成标点）
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 核对 import 生成并核对
生成并核对(S, out)
