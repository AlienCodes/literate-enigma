import json,re,glob,os
# 第28篇初稿（逐词对照）：S = [(段, [chunk, ...])]，chunk = ([(英文组, 中文组), ...], 可选 note)
# 2026-10-28 重点词中文沿用文章定稿（铁律），只按《翻译风格》调格式；非重点词也逐词对齐（G47）；三项以上并列加牛津逗号（T35）。
S=[
(1,[[[("Project 523,","523项目"),("a","是一项"),("**covert**","**秘密的/隐秘的**(covert)"),("**military**","**军事**(military)"),("**mission**","**任务**(mission)，"),("involving","涉及"),("many institutes,","多家机构，")],
     "（a covert military mission…：同位语，补充说明 Project 523；\ninvolving many institutes：现在分词短语作后置定语）"],
    [[("was named","得名"),("after","于"),("its","它的"),("launch","启动"),("date,","日期，"),("23 May 1967.","1967年5月23日。")],
     "（be named after…：以……命名）"]]),
(1,[[[("Its","它的"),("**urgent** target","**紧迫**(urgent)目标"),("was","是"),("the chloroquine-**resistant**","对氯喹**产生耐药性的**(resistant)"),("**malaria**","**疟疾**(malaria)，")],
     "（chloroquine-resistant：对氯喹产生耐药性的，chloroquine 是氯喹）"],
    [[("**weakening**","它**削弱了**(weakening)"),("**troops** in the **Vietnam War**.","**越南战争**(Vietnam War)中的**部队**(troops)。")],
     "（weakening troops…：现在分词短语作后置定语，修饰 malaria）"]]),
(1,[[[("In January 1969","1969年1月，"),("Tu Youyou","屠呦呦"),("was **entrusted with**","**受命**(entrusted with)"),("leading","领导"),("her institute's","她所在研究所的"),("research","研究"),("group,","组，")],
     "（be entrusted with doing…：被委以做……的重任，受命做……）"],
    [[("**despite**","**尽管**(despite)她"),("having no **doctorate**","既没有**博士学位**(doctorate)，"),("or","也没有"),("foreign","在国外"),("training.","受过训练。")],
     "（despite doing…：尽管……，despite 是介词，后面接动名词）"]]),
(2,[[[("In an","在一次"),("**exhaustive** search,","**彻底的**(exhaustive)搜寻中，"),("her team","她的团队"),("**combed**","**仔细翻检了**(combed)"),("over 2,000","2,000多个"),("**folk** recipes,","**民间**(folk)药方，")],
     "（comb：梳理，这里指仔细翻检；over 2,000：2,000多个）"],
    [[("**compiled**","**编纂/汇编了**(compiled)"),("640 **prescriptions**,","640个**处方/药方**(prescriptions)，"),("and **evaluated**","并**评估了**(evaluated)"),("about 380 extracts","约380种提取物，"),("from","它们来自"),("some 200","200种左右的"),("**medicinal**","**药用**(medicinal)"),("**herbs**.","**草药**(herbs)。")],
     "（some 200：大约200，some 表示“大约”）"]]),
(2,[[[("Qinghao,","青蒿，"),("or **sweet wormwood**,","也就是**黄花蒿**(sweet wormwood)，"),("showed **flashes** of","不时**闪现**(flashes)"),("promise,","希望，"),("yet","但"),("its results","它的效果"),("were **erratic**.","**时好时坏**(erratic)。")],
     "（or：也就是，引出同一种植物的另一个名称；\nshow flashes of promise：不时显出希望）"]]),
(2,[[[("Seeking","为了寻找"),("a **clue**,","一条**线索**(clue)，"),("Tu","屠呦呦"),("**revisited**","**重新翻阅了**(revisited)"),("the **classical** texts.","**古典**(classical)文献。")],
     "（Seeking a clue：现在分词短语作状语，表示目的）"]]),
(3,[[[("Around AD 340,","约公元340年，"),("the physician","医学家"),("Ge Hong's","葛洪的"),("**handbook**","**手册**(handbook)"),("advised","建议"),("taking","服用：")],
     "（advise doing…：建议做……；handbook：手册，指葛洪的《肘后备急方》）"],
    [[("\"a handful of qinghao","“青蒿一握，"),("immersed in two litres of water\".","以水二升渍”。")],
     "（a handful of…：一把……；immersed in…：过去分词短语，浸在……里；\n引文是《肘后备急方》原文“青蒿一握，以水二升渍”的英译）"]]),
(3,[[[("This","这个方法"),("**bypassed**","**绕开了**(bypassed)"),("boiling.","煮沸。")],
     "（This 指上面用水浸泡青蒿的做法；\nbypass：绕过，避开）"]]),
(3,[[[("Tu","屠呦呦"),("suspected","怀疑，"),("heat during **extraction**","**提取**(extraction)时的高温"),("was **degrading**","**破坏了**(degrading)"),("a","某种"),("**delicate**","**不耐热的**(delicate)"),("**component**,","**成分**(component)，")],
     "（suspected 后面省略了 that，引出宾语从句；\ndelicate：这里指不耐热、容易被破坏的）"],
    [[("so","于是"),("she","她"),("switched to","改用了"),("**ether**,","**乙醚**(ether)，")],
     "（switch to…：改用……，换成……）"],
    [[("a","一种"),("**volatile**","**易挥发的**(volatile)"),("**solvent**","**溶剂**(solvent)，"),("boiling at","沸点为"),("about 35 degrees Celsius.","约35摄氏度。")],
     "（a volatile solvent…：同位语，补充说明 ether；\nboiling at…：现在分词短语作后置定语，在……时沸腾）"]]),
(3,[[[("On 4 October 1971","1971年10月4日，"),("sample 191","第191号样品"),("completely","完全"),("**inhibited**","**抑制了**(inhibited)"),("the **parasite** in **infected** mice.","**受感染**(infected)小鼠体内的**疟原虫**(parasite)。")],
     "（parasite：寄生虫，这里指疟原虫；\nin infected mice：后置定语，修饰 the parasite）"]]),
(4,[[[("**Efficacy** in mice","在小鼠身上有**药效**(Efficacy)，"),("**indicated** nothing about","并不能**说明**(indicated)"),("human","人"),("safety.","是否安全。")],
     "（indicate nothing about…：对……什么也说明不了）"]]),
(4,[[[("In July 1972,","1972年7月，"),("to **assess**","为了**检验**(assess)"),("its **toxicity**,","它的**毒性**(toxicity)，"),("Tu","屠呦呦"),("and two colleagues","和两名同事"),("**voluntarily**","**自愿**(voluntarily)"),("took","服下了"),("the extract.","这种提取物。")],
     "（to assess…：不定式作目的状语）"]]),
(4,[[[("**Thereafter**,","**此后**(Thereafter)，"),("from August to October,","从8月到10月，"),("it","这种提取物"),("was **administered to**","**用于治疗**(administered to)"),("21","21名"),("malaria","疟疾"),("patients","病人，"),("in Hainan,","在海南，")],
     "（administer A to B：给 B 施用 A，这里指给病人用药）"],
    [[("and","而"),("on 8 November","在11月8日，"),("her team","她的团队"),("**obtained**","**得到了**(obtained)"),("pure **crystals** of the **substance**","这种**物质**(substance)的纯净**晶体**(crystals)，"),("later","它后来"),("named","被命名为"),("artemisinin.","青蒿素。")],
     "（later named artemisinin：过去分词短语作后置定语，\n修饰 the substance）"]]),
(5,[[[("In September 2011","2011年9月，"),("Tu","屠呦呦"),("was named","被评为"),("a Lasker Award","拉斯克奖"),("**recipient**;","**得主**(recipient)；")],
     "（be named…：被评为……；\nLasker Award：拉斯克奖，美国重要的医学奖项）"],
    [[("its **jury**","该奖的**评审团**(jury)"),("credited","称，"),("the drug","这种药"),("with saving","挽救了"),("millions.","数百万人。")],
     "（credit A with B：认为 B 是 A 的功劳）"]]),
(5,[[[("On 5 October 2015","2015年10月5日，"),("she","她"),("won","获得了"),("half","一半的"),("the Nobel Prize in","诺贝尔"),("**Physiology**","**生理学**(Physiology)"),("or Medicine,","或医学奖，")],
     "（won half the Nobel Prize：获得了诺贝尔奖的一半，\n另一半由另外两位学者分享）"],
    [[("the first","成为第一位"),("Chinese woman","中国女性"),("Nobel **laureate**.","诺贝尔奖**获得者**(laureate)。")],
     "（the first Chinese woman Nobel laureate：同位语，补充说明 she）"]]),
(5,[[[("Since 2006","自2006年起，"),("WHO **guidelines**","世界卫生组织的**指南**(guidelines)"),("have **endorsed**","一直**推荐**(endorsed)"),("artemisinin-based","以青蒿素为基础的"),("**combination**","**联合**(combination)"),("**therapies**","**疗法**(therapies)，"),("against","用来对付"),("malaria's","疟疾中"),("**deadliest** form.","**最致命的**(deadliest)一种。")],
     "（WHO：世界卫生组织；artemisinin-based：以青蒿素为基础的；\nhave endorsed：现在完成时，表示从2006年一直到现在）"]]),
(5,[[[("The **essence** of Ge Hong's line","葛洪那句话的**精髓**(essence)，"),("lay in","正在于"),("the boiling it **skipped**.","它**略去**(skipped)的煮沸。")],
     "（lie in…：在于……，lay 是 lie 的过去式；\nit skipped：定语从句，\n修饰 the boiling，省略了 that）\n"
     "（简述：523项目是一项秘密军事任务，\n1967年5月23日启动，\n目标是越战中对氯喹产生耐药性的疟疾。\n"
     "1969年1月，屠呦呦受命领导研究组。\n团队翻检了2,000多个民间药方，\n评估了约380种提取物，\n"
     "青蒿的效果却时好时坏。屠呦呦重新翻阅古典文献，\n看到葛洪的手册只用水浸泡青蒿，绕开了煮沸，\n"
     "便怀疑高温破坏了某种不耐热的成分，\n改用沸点约35摄氏度的乙醚。\n"
     "1971年10月4日，\n第191号样品完全抑制了小鼠体内的疟原虫。\n"
     "1972年她和两名同事自愿试服，\n随后在海南用于治疗21名病人，\n11月得到纯净晶体，后来命名为青蒿素。\n"
     "她先后获得拉斯克奖和一半的诺贝尔奖，\n成为第一位获得诺贝尔奖的中国女性；\n"
     "世界卫生组织也推荐以青蒿素为基础的联合疗法。\n关键正在于葛洪那句话略去的煮沸。）"]]),
]
CONF={
"牛津逗号":{"S3 her institute's research group, despite having no doctorate or":"不是三项并列：despite 引出让步状语，后面 no doctorate or foreign training 只有两项",
 "S12 to assess its toxicity, Tu and":"不是三项并列：to assess its toxicity 是目的状语，并列的只有 Tu 和 two colleagues 两项"},
"方向":{"S1-2 after→于":"after 属于 be named after（以……命名），不是时间方向词，“得名于”方向不涉及先后"},
"短语":{
 "S4 compiled … from":"不是搭配：from 属于 extracts from some 200 medicinal herbs（来自……的提取物），compiled 的宾语是 640 prescriptions",
 "S4 evaluated … from":"不是搭配：from 引出提取物的来源（extracts from herbs），evaluated 的宾语是 about 380 extracts",
 "S5 flashes … of":"不是搭配：show flashes of promise 里 flashes 单独是“闪现”，of promise 是普通的 of 结构（希望的闪现），已在说明里写出整句意思",
 "S7 handbook … of":"不是搭配：of 属于引文 a handful of qinghao，和 handbook 无关",
 "S9 degrading … to":"不是搭配：to 属于 switched to（改用），degrading 的宾语是 a delicate component",
 "S13 administered … on":"不是搭配：on 引出时间 on 8 November，administered to 已整体标",
 "S13 obtained … of":"不是搭配：of 属于 crystals of the substance（这种物质的晶体），obtained 的宾语是 pure crystals",
 "S15 in … Physiology":"不是搭配：in 属于奖项名称 the Nobel Prize in Physiology or Medicine，不是 in flocks 那样的固定用法",
 "S17 essence … of":"不是搭配：the essence of A 是普通的 of 结构（A 的精髓），essence 单独是重点词",
 "S4 an exhaustive search":"不是搭配：exhaustive 本身就是“详尽的、彻底的”，search 是普通名词“搜寻”，各自对齐即可"},
"合组":{
 "S2 troops in the Vietnam War.":"对齐不了：in the Vietnam War 是后置定语修饰 troops，中文“越南战争中的部队”定语必须提前",
 "S9 heat during extraction":"对齐不了：during extraction 是后置定语修饰 heat，中文“提取时的高温”定语必须提前",
 "S10 the parasite in infected mice.":"对齐不了：in infected mice 是后置定语修饰 the parasite，中文“受感染小鼠体内的疟原虫”定语必须提前",
 "S11 Efficacy in mice":"对齐不了：in mice 修饰 efficacy，中文“在小鼠身上有药效”介词短语必须提前",
 "S13 pure crystals of the substance":"对齐不了：the crystals of A 中文“A 的晶体”，of 结构语序必须倒过来",
 "S17 The essence of Ge Hong's line":"对齐不了：the essence of A 中文“A 的精髓”，of 结构语序必须倒过来",
 "S17 the boiling it skipped.":"对齐不了：it skipped 是定语从句修饰 the boiling，中文“它略去的煮沸”定语必须提前",
 "S7 \"a handful of qinghao":"对齐不了：引文回译成《肘后备急方》原文“青蒿一握”，文言语序（一握放在青蒿后面），拆开不通",
 "S7 immersed in two litres of water\"":"对齐不了：引文回译成《肘后备急方》原文“以水二升渍”，文言语序，拆开不通"},
"对齐":{
 "S2-2 troops in the Vietnam War.":"in the Vietnam War 是后置定语修饰 troops，中文“越南战争中的部队”定语提前，语序必须倒过来；troops、Vietnam War 两个重点词因此同在一组（T34 倒装）",
 "S9-1 heat during extraction":"during extraction 是后置定语修饰 heat，中文“提取时的高温”定语提前，语序必须倒过来",
 "S10-1 the parasite in infected mice.":"in infected mice 是后置定语修饰 the parasite，中文“受感染小鼠体内的疟原虫”定语提前，语序必须倒过来；parasite、infected 两个重点词因此同在一组（T34 倒装）",
 "S11-1 Efficacy in mice":"in mice 修饰 efficacy，中文“在小鼠身上有药效”介词短语提前，语序必须倒过来",
 "S13-2 pure crystals of the substance":"the crystals of A 中文“A 的晶体”，of 结构语序必须倒过来；crystals、substance 两个重点词因此同在一组（T34 倒装）",
 "S17-1 The essence of Ge Hong's line":"the essence of A 中文“A 的精髓”，of 结构语序必须倒过来",
 "S7-2 immersed in two litres of wate":"引文回译成《肘后备急方》原文“以水二升渍”，文言语序（渍放在最后），语序必须倒过来",
 "S17-1 the boiling it skipped.":"it skipped 是定语从句修饰 the boiling，中文“它略去的煮沸”定语提前，语序必须倒过来"}}
out={"no":"28","title_en":"A Handful of Wormwood That Saved Millions","title_zh":"青蒿一握，济世千万","title_fx":{"hl":["Wormwood","Millions"],"ghost":[]},"sentences":[],"核对确认":CONF,"结尾解说":"简述",
     "高亮按实际开口":True,"高亮开口门槛":40,
     "术语":{"Project 523":"523项目","Vietnam War":"越南战争","Tu Youyou":"屠呦呦","Qinghao":"青蒿","Ge Hong":"葛洪","Hainan":"海南","Lasker Award":"拉斯克奖","Nobel Prize":"诺贝尔","WHO":"世界卫生组织","artemisinin":"青蒿素","chloroquine":"氯喹","Celsius":"摄氏度"}}
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 核对 import 生成并核对
生成并核对(S, out)
