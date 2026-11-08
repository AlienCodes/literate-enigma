import json,re,glob,os
# 第66篇初稿（逐词对照）：S = [(段, [chunk, ...])]，chunk = ([(英文组, 中文组), ...], 可选 note)
# 2026-11-08 重点词中文沿用文章定稿（铁律）；不用破折号（T36）；三项并列加牛津逗号（T18）；形容词的“的”进粗体（T38）。
S=[
(1,[[[("In 1941","1941年，"),("George de Mestral, a Swiss engineer,","瑞士工程师乔治·德·梅斯特拉尔")],
     "（a Swiss engineer：同位语，补充说明 George de Mestral）"],
    [[("returned from hunting in the Alps with his **hound**, an Irish Pointer.","带着他的**猎犬**(hound)，一只爱尔兰指示犬，在阿尔卑斯山打猎归来。")],
     "（an Irish Pointer：同位语，补充说明 hound）"]]),
(1,[[[("**Prickly**","**多刺的**(Prickly)"),("burdock","牛蒡"),("**seed-heads**","**种子头**(seed-heads)"),("had **hitched** themselves to","紧紧**挂住了**(hitched)"),("his clothes","他的衣服，")],
     "（had hitched：过去完成时；\nhitch oneself to：挂在……上）"],
    [[("and lay **tangled**","也**缠结**(tangled)"),("in the dog's **fur**.","在狗的**毛皮**(fur)里。")],
     "（lay tangled：系表结构，lay 是 lie 的过去式）"]]),
(1,[[[("Under a microscope","在显微镜下，"),("he saw","他看到"),("thousands of","成千上万个"),("tiny","细小的"),("**barbs**,","**倒刺**(barbs)，")]],
    [[("each a **hook**","每一根都是一个**钩子**(hook)，"),("**grasping**","**钩住**(grasping)"),("the small **loops** in cloth.","布料上的小**毛圈**(loops)。")],
     "（each a hook…：独立主格结构，补充说明 barbs；\ngrasping…：现在分词短语，修饰 hook）"]]),
(2,[[[("Few took his idea **seriously** at first.","起初，很少有人**认真**(seriously)看待他的想法。")],
     "（take A seriously：认真看待 A）"]]),
(2,[[[("In Lyon, then a **weaving** centre,","在当时的**纺织**(weaving)中心里昂，")],
     "（then a weaving centre：同位语，补充说明 Lyon）"],
    [[("a cotton","一个棉制"),("version","版本"),("proved too **frail**","太**脆弱**(frail)，"),("to survive **abrasion**.","经不起**磨损**(abrasion)。")],
     "（too A to do：太 A 而不能……）"]]),
(2,[[[("Working with a **textiles** firm,","他与一家**纺织品**(textiles)公司合作，")],
     "（Working with…：现在分词短语作伴随状语）"],
    [[("he turned to **nylon**,","转而采用**尼龙**(nylon)。")],
     "（turn to：转而采用）"],
    [[("whose hooks","尼龙做成的钩子"),("were **stiff** enough","足够**硬挺**(stiff)，"),("to hold","既能扣住，"),("yet","又"),("easy","容易"),("to pull apart.","拉开。")],
     "（whose…：非限制性定语从句，修饰 nylon；\nA enough to do：足够 A，能……；\npull apart：拉开）"]]),
(2,[[[("The **trial-and-error** at the **looms** and **mills**","在**织机**(looms)旁和**工厂**(mills)里的**反复试验**(trial-and-error)"),("lasted","持续了"),("about","约"),("ten years.","十年。")],
     "（at the looms and mills：后置定语，修饰 trial-and-error）"]]),
(3,[[[("The name Velcro","Velcro 这个名字"),("**merged**","**合并了**(merged)"),("two","两个"),("French words,","法语词，")]],
    [[("velours, meaning","velours 意为"),("**velvet**,","**天鹅绒**(velvet)，"),("and crochet, meaning","crochet 意为"),("hook.","钩子。")],
     "（velours… and crochet…：同位语，补充说明 words；\nmeaning…：现在分词短语，说明词义）"]]),
(3,[[[("A US patent **duly** followed in 1955.","1955年，美国专利**顺理成章地**(duly)到手。")]]]),
(3,[[[("In 1959","1959年，"),("a New York","纽约一场"),("fashion show","时装秀")]],
    [[("sent **apparel** **stitched** with the **fasteners** down the **runway**.","让**缝有**(stitched)这种**搭扣**(fasteners)的**服装**(apparel)走上**T台**(runway)。")],
     "（stitched with…：过去分词短语作后置定语，\n修饰 apparel；\nsend A down B：让 A 走上 B）"]]),
(3,[[[("The public","公众却"),("was less **charmed** than expected,","不如预期那样**着迷**(charmed)，")],
     "（less A than expected：不如预期那样 A）"],
    [[("**mostly**","**主要**(mostly)"),("because of","是因为"),("the **aesthetic**.","它的**外观**(aesthetic)。")]]]),
(4,[[[("The **underdog**","这个不被看好的**弱者**(underdog)"),("proved its **utility** in **outer** space.","在**外层**(outer)空间证明了自己的**用处**(utility)。")]]]),
(4,[[[("NASA","美国航天局"),("used it in the Apollo programme","在阿波罗计划中用它")]],
    [[("to keep **gear**","把**装备**(gear)"),("**anchored**","牢牢**固定**(anchored)住，"),("in weightlessness, so that nothing would **hover**","免得东西在失重状态下**飘浮**(hover)"),("in **mid-air**.","在**半空**(mid-air)中。")],
     "（to keep…：不定式作目的状语；\nkeep A anchored：让 A 保持固定；\nso that…：引导目的状语从句）"]]),
(4,[[[("Apollo 11","阿波罗11号"),("was **equipped** with","**配备了**(equipped)"),("a **sizeable** amount,","**相当多的**(sizeable)用量，"),("about","约"),("3,300","3,300"),("square inches.","平方英寸。")],
     "（be equipped with：配备有；\nabout 3,300 square inches：同位语，补充说明 amount）"]]),
(4,[[[("NASA","美国航天局"),("did not invent","并没有发明"),("the nylon **clasp**.","这种尼龙**扣件**(clasp)。")]]]),
(5,[[[("When the patent ran out in 1978,","1978年专利到期后，")],
     "（When…：时间状语从句；run out：到期）"],
    [[("**cut-price**","来自台湾、中国大陆和韩国的**廉价的**(cut-price)"),("**knock-offs** from Taiwan, China, and South Korea","**仿冒品**(knock-offs)"),("**overran** the market,","大量**涌入**(overran)市场，")],
     "（from Taiwan, China, and South Korea：后置定语，\n修饰 knock-offs）"],
    [[("and a **niche** product","一种**小众**(niche)产品"),("went **mainstream**.","成了**主流**(mainstream)。")],
     "（go mainstream：成为主流）"]]),
(5,[[[("In 2017,","2017年，"),("to stop","为了不让"),("its **brand-name**","自己的**品牌名**(brand-name)"),("**melting** into","逐渐**消融**(melting)为"),("a **generic**","一个**通用的**(generic)"),("**noun**,","**名词**(noun)，")],
     "（to stop…：不定式作目的状语；\nstop A doing：不让 A 做……；\nmelt into：逐渐变成）"],
    [[("the company","公司"),("asked","请"),("people","大家"),("to call such **mimics** hook and loop fasteners.","把这类**仿品**(mimics)称作钩毛搭扣。")],
     "（ask A to do：请 A 做……；\ncall A B：把 A 称作 B）"]]),
(5,[[[("In effect,","实际上，"),("the firm","这家公司"),("was asking","是在请"),("the public","公众"),("to stop using","别再用"),("its own name","它自己的名字"),("for","去称呼"),("rivals' goods.","对手的商品。")],
     "（was asking：过去进行时；\nstop doing：不再做……；\nuse A for B：用 A 称呼 B）\n"
     "（简述：1941年，瑞士工程师乔治·德·梅斯特拉尔打猎归来，发现牛蒡刺果挂在衣服和狗毛上，显微镜下是无数小钩钩住布料上的毛圈。\n"
     "起初很少有人看好，棉制版本经不起磨损，他与纺织品公司合作改用尼龙，反复试验约十年。\n"
     "名字由法语 velours 和 crochet 合成，1955年获美国专利，1959年纽约时装秀上公众反应不如预期，主要是因为外观。\n"
     "美国航天局在阿波罗计划中用它在失重状态下固定装备，阿波罗11号用了约3,300平方英寸，但它不是美国航天局发明的。\n"
     "1978年专利到期后廉价仿品涌入市场，小众产品成了主流；2017年公司请大家把仿品称作钩毛搭扣，免得品牌名变成通用名词。）"]]),
]
G={'S1 George de Mestral, a Swiss engineer': '对齐不了：同位语 a Swiss engineer 中文提到人名前（瑞士工程师乔治·德·梅斯特拉尔），语序整体换了；人名 George de Mestral 是一个专名',
 'S1 returned from hunting in the Alps with his hound, an Irish Pointer': '对齐不了：中文把 with his hound 和 in the Alps 都提到 returned 前（带着猎犬，在阿尔卑斯山打猎归来），语序整体换了',
 'S3 the small loops in cloth': '对齐不了：in cloth 是后置定语，中文提到前面（布料上的小毛圈），拆开语序反了',
 'S4 Few took his idea seriously at first': '对齐不了：at first 中文提到句首（起初），seriously 提到动词前（认真看待），语序整体换了',
 'S5 In Lyon, then a weaving centre': '对齐不了：同位语 then a weaving centre 中文提到 Lyon 前（当时的纺织中心里昂），语序整体换了',
 'S5 proved too frail': '对齐不了：proved 中文不单译（太脆弱），拆开 proved 下面没有中文',
 'S6 to pull apart': '对齐不了：pull apart 是短语动词，整体译“拉开”',
 'S8 velours, meaning': '对齐不了：velours 是法语原词照录，“velours 意为”中间的空格分组后会丢',
 'S8 and crochet, meaning': '对齐不了：crochet 是法语原词照录，“crochet 意为”中间的空格分组后会丢',
 'S9 A US patent duly followed in 1955': '对齐不了：in 1955 中文提到句首（1955年），followed 译“到手”放句末，语序整体换了',
 'S10 fashion show': '对齐不了：fashion show 是复合名词，整体译“时装秀”',
 'S11 was less charmed than expected': '对齐不了：less … than expected 中文作“不如预期那样着迷”，比较结构语序整体换了',
 'S12 proved its utility in outer space': '对齐不了：in outer space 中文提到动词前（在外层空间证明了自己的用处），语序整体换了',
 'S13 used it in the Apollo programme': '对齐不了：in the Apollo programme 中文提到动词前（在阿波罗计划中用它），语序整体换了',
 'S13 in weightlessness, so that nothing would hover': '对齐不了：in weightlessness 中文挪进 so that 从句（免得东西在失重状态下飘浮），语序整体换了',
 'S14 square inches': '对齐不了：square inches 是面积单位，整体译“平方英寸”',
 'S16 When the patent ran out in 1978': '对齐不了：in 1978 中文提到句首（1978年专利到期后），When 译“后”放句末，语序整体换了',
 'S16 knock-offs from Taiwan, China, and South Korea': '对齐不了：from 短语是后置定语，中文提到 廉价的 前面（来自台湾、中国大陆和韩国的），拆开语序反了',
 'S17 to call such mimics hook and loop fasteners': '对齐不了：call A B 中文作“把 A 称作 B”，call 挪到 A 后面；hook and loop fasteners 是一个名称，整体译“钩毛搭扣”',
 'S18 to stop using': '对齐不了：stop using 中文作“别再用”，拆开“别再”“用”不通顺',
 'S18 its own name': '对齐不了：its own 中文作“它自己的”，拆开 own 与 name 中文“自己的名字”不通顺', "S18 rivals' goods": "对齐不了：rivals' goods 所有格名词短语，整体译“对手的商品”"}
DZ={}
CONF={"合组":G,"对齐":DZ}
out={"no":"66","title_en":"The Burrs That Became Velcro","title_zh":"一颗刺果钩出的发明","title_fx":{"hl":["Burrs","Velcro"],"ghost":[]},"sentences":[],"核对确认":CONF,"结尾解说":"简述",
     "高亮按实际开口":True,"高亮开口门槛":40,
     "术语":{"George de Mestral":"乔治·德·梅斯特拉尔","Swiss":"瑞士","Alps":"阿尔卑斯山","Irish Pointer":"爱尔兰指示犬","Lyon":"里昂","Velcro":"Velcro","French":"法语","US":"美国","New York":"纽约","NASA":"美国航天局","Apollo":"阿波罗","Taiwan":"台湾","China":"中国大陆","South Korea":"韩国"}}
out.update({"非人声区间": {"S1": [[2.7475, 3.013125, "紧贴词头"]], "S11": [[2.460125, 2.732417, "紧贴词头"]], "S17": [[1.667125, 1.890208]], "S2": [[3.4585, 3.801333, "紧贴词头"]], "S10": [[3.312917, 3.43, "紧贴词尾"]], "S16": [[8.67, 8.895583, "紧贴词头"]]}, "合成标点": {"S8": [["velvet, and", "velvet; and"], ["velours, meaning", "velours; meaning"]]}})   # 2026-11-08 逐 2.5 ms 实测（dossier_66 #2/#19/#30 A19 停顿后吸气）：S1 Mestral, 后 2.75–3.01 吸气（-38～-58 dB、重心 2.0–2.6 kHz、低频 -10～-22 dB），3.0175 起 a；S11 expected, 后 2.46–2.73 吸气（-47～-57 dB、重心 1.9–2.6 kHz、低频 -6～-19 dB），2.735 起 mostly 的 /m/ 浊音（周期 0.44）保留；S17 2017, 后 1.6675–1.89 吸气（起点挪到 1.667125，外侧 1.6625–1.667 为 -58 dB）（-43～-58 dB、重心 2.0–3.1 kHz、低频 -12～-24 dB），1.89–1.905 是 to 的闭塞静音，1.9075 起 /t/ 除阻；S8 velvet 的 /t/ 连进 and、没有闭塞（4.35–4.43 一直 -23～-40 dB），无处移植，合成时逗号换分号让配音自己停（G57 合成标点）
# 2026-11-08 接手会话逐 2.5 ms 实测（⑤ 纯人声 #2/#3/#9/#14）：S2 clothes|and 之间 3.455–3.80 吸气 345 ms（-44～-52 dB、重心 2.0–2.7 kHz、周期 0.1–0.3、低频 -10～-20），左 3.455 是 -61 dB 低谷，右 3.8025 起 and 的元音（-33→-18 dB），and 不是 h 开头；S10 show|sent 之间 3.3125–3.43 吸气（-44～-49 dB、重心 1.6–2.6 kHz、低频 -9～-15），3.285–3.31 是 show 的 ʊ 浊音尾（低频 -1～-4）保留，右 3.43 是 -59 dB 低谷、3.44 起 sent 的 /s/；S16 8.67–8.896 自动切点.py 判定（market|and 之间吸气，旧会话已实测）
out.update({"分段增益dB":{"S8":{"1":1.5,"2":1.0}},"句子增益dB":{"S18":-0.6}})   # K129：S8 第1段 French words, 的 words（53.9–54.3s）比全片低 5.6 dB（61 起门槛 5.0），整段补 +1.5；响度一致性：S18（含 In effect, 122.7–123.3s 那一小段）比全片响 2.1–2.3 LU、与 S17 差 2.6 LU，整句 -0.6
out.update({"停顿插入点": {"S16": {"3": [6.310792, "交界"]}, "S8": {"1": [2.390708, "交界"], "4": [5.175958, "交界"]}}})   # K131（2026-11-08 逐 2.5 ms 实测）：S16 China, | and 连读，China 衰减到 6.31 的低谷（-46 dB），6.3175 起 and 的起音；原插入点 6.34 在 and 起音里、被渐强吃掉；插入点挪到低谷过零 6.310792，写成交界；S8（合成标点后 w）words, | velours 无缝：/z/ 2.27–2.39（重心 4.3–6 kHz），2.3925 起 /v/（重心降到 3.1→2.5 kHz），插在 2.390708；crochet, | meaning 无缝：eɪ 到 5.175（重心 1.5 kHz），5.177 起 /m/（重心 0.78→0.5 kHz），插在 5.175958
CONF["停顿位置"]={
 "S8 words, / velours, @2.391":"2026-11-08 逐 2.5 ms 看声音实测（S8 w，合成标点后）：words 的 /z/ 2.27–2.39（-12～-28 dB、重心 4.3–6.0 kHz、低频 -2～-42 dB），2.3925 起 velours 的 /v/（重心降到 3.1、2.6、2.5 kHz，2.405 起 1.3 kHz 浊音），两词无缝连读；停顿插在 2.390708（交界过零点），正好在 words 与 velours 之间；带时长模型把 velours 开头算到 2.416，偏晚",
 "S16 China, / and @6.311":"2026-11-08 逐 2.5 ms 实测（S16 w）：China 的 ə 6.29–6.305（-24～-32 dB），衰减到 6.31 的低谷（-46 dB、周期 0.17），6.315 起 and 的起音（-39→-22 dB）；停顿插在 6.310792（交界过零点），正好在 China 与 and 之间；带时长模型把 and 开头算到 6.411，偏晚",
 "S16 market, / and @8.575":"2026-11-08 逐 10 ms 实测（S16 w）：market 的 /t/ 在 8.50 移植除阻（词尾除阻 4），8.50–8.66 是 -54～-66 dB 的闭塞后静音，8.66–8.895 吸气已按非人声区间换成静音，and 的起音 8.92 起（-38→-6.5 dB）；删静音 8.575–8.885 整段在 market 与 and 之间，没碰词；带时长模型把 market 末音素算到 8.651，是闭塞静音",
 "S8 crochet, / meaning @5.176":"2026-11-08 逐 2.5 ms 看声音实测（S8 w，合成标点后）：crochet 的 eɪ 到 5.175（-12～-19 dB、重心 1.4–3.0 kHz），5.177 起 meaning 的 /m/（周期 0.48、重心 0.78→0.44–0.66 kHz 的鼻音，一直到 5.265），两词无缝连读；停顿插在 5.175958（交界过零点），正好在 crochet 与 meaning 之间；带时长模型把 meaning 开头算到 5.291，是 m 之后的元音"}
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 核对 import 生成并核对
生成并核对(S, out)
