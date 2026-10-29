import json,re,glob,os
# 第31篇初稿（逐词对照）：S = [(段, [chunk, ...])]，chunk = ([(英文组, 中文组), ...], 可选 note)
# 2026-10-28 重点词中文沿用文章定稿（铁律），只按《翻译风格》调格式；非重点词也逐词对齐（G47）；短语型用法整体标（T22）；不用破折号（T36）。
S=[
(1,[[[("In 1990,","1990年，"),("on a","在一列"),("**delayed**","**晚点的**(delayed)"),("train","列车上，"),("from Manchester","这列车从曼彻斯特"),("to London's King's Cross,","开往伦敦国王十字车站，")],
     "（from Manchester to London's King's Cross：后置定语，修饰 train；\nKing's Cross：国王十字车站）"],
    [[("Joanne Rowling,","乔安妮·罗琳，"),("a **would-be**","一位**有志成为**(would-be)"),("**novelist**,","**小说家**(novelist)的人，")],
     "（a would-be novelist：同位语，补充说明 Joanne Rowling；\nwould-be：想要成为……的）"],
    [[("was **unexpectedly**","**出乎意料地**(unexpectedly)"),("struck by","得到了"),("the **inspiration** for Harry Potter,","哈利·波特的**灵感**(inspiration)，")],
     "（be struck by the inspiration for…：突然得到……的灵感）"],
    [[("an **orphaned**","哈利是一个**父母双亡的**(orphaned)"),("young **wizard**.","少年**巫师**(wizard)。")],
     "（an orphaned young wizard：同位语，补充说明 Harry Potter）"]]),
(1,[[[("**Grief**","**悲痛**(Grief)"),("soon","很快就"),("**overshadowed**","**盖过了**(overshadowed)"),("that **spark**:","那点**火花**(spark)：")],
     "（overshadow：使黯然失色，盖过；\n冒号后面交代悲痛的由来）"],
    [[("her mother","她的母亲"),("died on 30 December 1990,","于1990年12月30日去世，"),("aged 45.","终年45岁。")],
     "（aged 45：终年45岁，补充说明去世时的年龄）"]]),
(1,[[[("Rowling","罗琳"),("then","随后"),("**relocated**","**移居**(relocated)"),("to Porto","到波尔图，"),("to teach English.","教英语。")],
     "（to teach English：不定式作目的状语；\nPorto：波尔图，葡萄牙城市）"]]),
(2,[[[("Rowling","罗琳"),("married in Porto in October 1992,","于1992年10月在波尔图结婚；")],
     "（in Porto、in October 1992：地点状语和时间状语）"],
    [[("and","而"),("a daughter's **arrival** in July 1993","1993年7月，女儿的**降生**(arrival)"),("**ushered in**","**开启了**(ushered in)"),("**motherhood**.","她**为人母**(motherhood)的生活。")],
     "（usher in：开启，引来；\narrival：到来，这里指婴儿出生）"]]),
(2,[[[("At the end of 1993","1993年底，"),("she","她"),("**resettled**","**重新安家**(resettled)"),("in Edinburgh,","在爱丁堡，")],
     "（resettle：重新定居，重新安顿）"],
    [[("a **lone** mother","成了一位**独自**(lone)带孩子的母亲，"),("**reliant on**","**依靠**(reliant on)"),("state **welfare**.","国家**福利**(welfare)生活。")],
     "（a lone mother…：同位语，补充说明 she；\nreliant on…：形容词短语作后置定语，依靠……的）"]]),
(2,[[[("She","她"),("**habitually**","**习惯**(habitually)"),("wrote in cafés,","在咖啡馆里写作，")],
     "（habitually：习惯地，惯常地）"],
    [[("**patiently**","**耐心地**(patiently)"),("**polishing**","**打磨**(polishing)"),("her","她那部"),("**unfinished**","**尚未完成的**(unfinished)"),("novel.","小说。")],
     "（patiently polishing…：现在分词短语作伴随状语；\npolish：润色，打磨）"]]),
(3,[[[("A **literary** agent,","**文学**(literary)经纪人"),("Christopher Little,","克里斯托弗·利特尔"),("took on","接下了"),("the manuscript","这部书稿，")],
     "（Christopher Little：同位语，补充说明 A literary agent；\ntake on：接受，承担）"],
    [[("and","并"),("**pitched** it **repeatedly** to","**多次**(repeatedly)把它**推荐**(pitched)给"),("**prospective**","**潜在的**(prospective)"),("buyers.","买家。")],
     "（pitch：推荐，推销；to 引出推荐的对象；\nprospective：潜在的，可能的）"]]),
(3,[[[("It","书稿"),("was reportedly","据报道"),("**rejected** by twelve publishers **in succession**,","**接连**(in succession)遭到十二家出版社**拒绝**(rejected)，")],
     "（in succession：接连地，一个接一个地）"],
    [[("a **relentless** run of","这一连串**毫不留情的**(relentless)"),("**refusals**","**回绝**(refusals)，"),("that offered","没给"),("the **newcomer**","这位**新人**(newcomer)"),("little **encouragement**.","多少**鼓励**(encouragement)。")],
     "（a relentless run of refusals：同位语，概括前面的接连被拒；\nthat offered…：定语从句，修饰 a relentless run of refusals）"]]),
(4,[[[("At Bloomsbury,","在布卢姆斯伯里出版社，"),("the chairman","董事长"),("Nigel Newton","奈杰尔·牛顿"),("gave the first chapter","把第一章交给了"),("to his","他"),("eight-year-old","八岁的"),("daughter,","女儿"),("Alice,","爱丽丝，")],
     "（Alice：同位语，补充说明 his eight-year-old daughter）"],
    [[("who **relished** it","她读得**津津有味**(relished)，"),("and **eagerly**","还**急切地**(eagerly)"),("asked for","要看"),("the next **instalment**.","下一**部分**(instalment)。")],
     "（who relished it…：非限制性定语从句，修饰 Alice；\ninstalment：（连载的）一部分）"]]),
(4,[[[("The firm","出版社"),("paid","支付了"),("a **sum** of 1,500 pounds","1,500英镑的**款项**(sum)"),("as an advance.","作为预付金。")],
     "（a sum of…：一笔……的款项；as an advance：作为预付金）"]]),
(4,[[[("**Fearful** that","由于**担心**(Fearful)"),("boys","男孩们"),("might **disregard**","可能会**忽视**(disregard)"),("a book by a woman,","女性写的书，")],
     "（Fearful that…：形容词短语作原因状语，\nthat 从句交代担心的内容）"],
    [[("the publishers","出版方"),("**opted for**","**选择**(opted for)用"),("initials","名字缩写"),("to **mask**","来**隐去**(mask)"),("her **gender**.","她的**性别**(gender)。")],
     "（opt for…：选择……；to mask…：不定式作目的状语）"]]),
(4,[[[("Having no","由于没有"),("middle","中间"),("name,","名，"),("Rowling","罗琳"),("took the K","把 K"),("for her **pseudonym**","用作她**笔名**(pseudonym)的一部分，"),("from her grandmother Kathleen.","它取自祖母凯瑟琳的名字。")],
     "（Having no middle name：现在分词短语作原因状语；\ntake A from B：从 B 那里取来 A）"]]),
(5,[[[("Harry Potter and the Philosopher's Stone","《哈利·波特与魔法石》（Philosopher's Stone）"),("was published on 26 June 1997,","于1997年6月26日出版，")],
     "（Harry Potter and the Philosopher's Stone：\n英国版书名《哈利·波特与魔法石》）"],
    [[("in a **cautious** first print run","首印**谨慎地**(cautious)定为"),("of 500 hardbacks,","500册精装本，"),("300","其中300册"),("**allocated**","**分配**(allocated)"),("to libraries.","给图书馆。")],
     "（print run：一次印刷的数量；\n300 allocated to libraries：独立主格结构，300 后面省略了 hardbacks）"]]),
(5,[[[("The American publisher Scholastic","美国的学乐出版社"),("paid $105,000","以105,000美元"),("for the US rights,","买下了美国版权，")],
     "（pay … for…：为……付出……）"],
    [[("and","而"),("the **renamed** Sorcerer's Stone","**改名**(renamed)为 Sorcerer's Stone 的这本书"),("appeared there on 1 September 1998.","于1998年9月1日在美国出版。")],
     "（the renamed Sorcerer's Stone：\n改名后的 Sorcerer's Stone；\nthere 指美国）"]]),
(5,[[[("The **series**","这个**系列**(series)"),("and its **spin-off**","及其**衍生的**(spin-off)"),("**volumes**","**图书**(volumes)"),("have **collectively**","**合计**(collectively)"),("**surpassed**","已**超过了**(surpassed)"),("500 million copies","5亿册"),("sold,","的销量，"),("in 80 languages.","涉及80种语言。")],
     "（spin-off volumes：衍生图书；\nhave surpassed：现在完成时，表示到现在为止的累计）"]]),
(5,[[[("Alice's **appetite**","爱丽丝的**胃口**(appetite)，"),("was **evidently**","**显然**(evidently)"),("shared by millions.","千百万读者都有。")],
     "（be shared by…：被……共有；\nappetite：胃口，这里指对这本书的兴趣）\n"
     "（简述：1990年，罗琳在一列晚点的火车上得到了哈利·波特的灵感。\n"
     "同年12月30日母亲去世，她随后移居波尔图教英语。1992年10月她在波尔图结婚，\n"
     "1993年7月女儿出生；1993年底她在爱丁堡重新安家，独自带孩子，依靠国家福利生活，\n"
     "常在咖啡馆里耐心打磨小说。文学经纪人克里斯托弗·利特尔接下书稿，多次推荐给买家，\n"
     "据报道接连遭到十二家出版社拒绝。布卢姆斯伯里出版社董事长八岁的女儿爱丽丝读了第一章，\n"
     "急着要看下一部分，出版社支付了1,500英镑预付金。\n"
     "出版方担心男孩忽视女性写的书，用名字缩写隐去她的性别，K 取自祖母凯瑟琳的名字。\n"
     "1997年6月26日此书首印500册精装本；美国版改名 Sorcerer's Stone，\n"
     "1998年9月1日出版。这个系列及其衍生图书合计已超过5亿册，涉及80种语言。）"]]),
]
CONF={"合组":{
 "S6 wrote in cafés":"对齐不了：in cafés 是地点状语，中文“在咖啡馆里写作”地点必须放到动词前，拆开成“写作在咖啡馆里”不通",
 "S9 gave the first chapter":"对齐不了：give A to B 中文“把 A 交给 B”，动词要放到 A 后面，拆开语序就乱",
 "S11 a book by a woman":"对齐不了：by a woman 是后置定语修饰 book，中文“女性写的书”定语必须提前",
 "S13 in a cautious first print run":"对齐不了：first print run 是一个名词（第一次印刷的数量），中文就是“首印”一个词；cautious 修饰它，中文“首印谨慎地定为”（文章定稿译法），拆开语序就乱",
 "S16 shared by millions":"对齐不了：被动 be shared by millions 中文“千百万读者都有”，施动者 millions 必须提到动词前"}}
CONF.update({
"牛津逗号":{"S7 Christopher Little, took on the manuscript and":"不是三项并列：Christopher Little 是同位语，and 连接 took on 和 pitched 两个谓语，只有两项",
 "S9 Alice, who relished it and":"不是三项并列：Alice 是同位语，and 连接从句里 relished 和 asked for 两个谓语，只有两项"},
"数字":{"S15-1 500":"500 million 中文按文章定稿写作“5亿”，数值相同（500 million = 5亿）"},
"对齐":{"S1-3 the inspiration for Harry Pott":"the inspiration for A 中文“A 的灵感”，for 结构作后置定语，语序必须倒过来",
 "S2-2 died on 30 December 1990,":"on 30 December 1990 是时间状语，中文“于1990年12月30日去世”时间必须放到动词前，语序必须倒过来",
 "S4-1 married in Porto in October 19":"in Porto、in October 1992 是地点、时间状语，中文“于1992年10月在波尔图结婚”状语必须放到动词前",
 "S4-2 a daughter's arrival in July 1":"in July 1993 是后置定语修饰 arrival，中文“1993年7月，女儿的降生”时间必须提前",
 "S5-1 At the end of 1993":"the end of 1993 是 of 结构，中文“1993年底”语序必须倒过来",
 "S8-1 rejected by twelve publishers ":"被动 rejected by A in succession 中文“接连遭到 A 拒绝”，施动者和状语 in succession 必须放到“拒绝”前面；rejected、in succession 两个重点词因此同在一组（T34 倒装）",
 "S10-1 a sum of 1,500 pounds":"a sum of A 中文“A 的款项”，of 结构语序必须倒过来",
 "S11-1 a book by a woman,":"by a woman 是后置定语修饰 book，中文“女性写的书”定语必须提前",
 "S13-1 Harry Potter and the Philosoph":"书名整体一个专名，中文《哈利·波特与魔法石》是一个书名，拆开不通",
 "S13-1 was published on 26 June 1997,":"on 26 June 1997 是时间状语，中文“于1997年6月26日出版”时间必须放到动词前",
 "S13-2 in a cautious first print run":"first print run 是一个名词（第一次印刷的数量），中文就是“首印”；cautious 修饰它，中文“首印谨慎地定为”（文章定稿译法），语序必须倒过来",
 "S14-2 appeared there on 1 September ":"there、on 1 September 1998 是地点、时间状语，中文“于1998年9月1日在美国出版”状语必须放到动词前"},
"词性":{"S13-2 cautious 谨慎地":"文章定稿译法“首印谨慎地定为”（铁律：定稿中文意思不改）；cautious 修饰 print run，中文把它化成修饰“定为”的状语，意思一样"},
"中文意思":{"S1 would-be":"would-be 的“想要成为……的”两部分在中文里是“有志成为”和后面的“的人”；“的”只是定语标记，文章定稿只标“有志成为”，不是被隔开的同一个意思"},
})
CONF["停顿位置"]={"S9 daughter, / Alice, @5.650":"2026-10-29 逐段看声音实测（S9 w）：daughter 末尾 ɚ 到 5.59s 还是浊音（-24 dB），5.61s 降到 -44 dB、5.62s -52 dB，5.6525s 是两词之间最低处 -55.2 dB，5.6625s 起 Alice 的起音回升到 -20.6 dB；插在交界最低点，不切前后词（A42）"}
CONF["短语"]={"S1 inspiration … for":"不是搭配：for 引出灵感的对象（for Harry Potter），inspiration 单独就是“灵感”",
 "S3 relocated … to":"不是搭配：to 是普通方向介词，引出去处（Porto）；relocate 单独就是“移居”",
 "S5 resettled … in":"不是搭配：in 引出地点（Edinburgh）；resettle 单独就是“重新安家”",
 "S7 pitched … to":"不是搭配：to 引出推荐的对象（prospective buyers）；pitch 单独就是“推荐/推销”，速查表搭配 pitch an idea to investors 里 to 也是普通介词",
 "S8 rejected … of":"不是搭配：of 属于 a relentless run of refusals（一连串回绝），和 rejected 无关",
 "S8 succession … of":"不是搭配：in succession 已整体标；of 属于后面的 a relentless run of refusals",
 "S9 relished … for":"不是搭配：for 属于 asked for（要求），relished 的宾语是 it",
 "S10 sum … of":"不是搭配：a sum of A 是普通的 of 结构（A 的款项），sum 单独是重点词",
 "S11 opted … to":"不是搭配：opted for 已整体标；to 是不定式 to mask（目的状语）",
 "S13 allocated … to":"不是搭配：to 引出分配的去处（libraries）；allocate 单独就是“分配”，同 send to、give to",
 "S14 renamed … on":"不是搭配：on 引出时间 on 1 September 1998，属于 appeared",
 "S1 a delayed train":"不是搭配：delayed 就是本义“晚点的”（速查表第一个意思），train 是普通名词“列车”，各自对齐即可"}
out={"no":"31","title_en":"The Book Twelve Publishers Turned Down","title_zh":"被拒绝了十二次的哈利·波特","title_fx":{"hl":["Twelve","Publishers"],"ghost":[]},"sentences":[],"核对确认":CONF,"结尾解说":"简述",
     "说明放宽特批":{"S16":{"倍数":"整屏","依据":"用户 2026-10-28 特批：“29、30、31 结尾简述都整屏、字号放到最大”（用户同意记录）"}},
     "非人声区间":{"S2":[[6.12,6.315]],"S9":[[0.985,1.16]]},
     "高亮按实际开口":True,"高亮开口门槛":40,
     "术语":{"Manchester":"曼彻斯特","King's Cross":"国王十字车站","Joanne Rowling":"乔安妮·罗琳","Harry Potter":"哈利·波特","Rowling":"罗琳","Porto":"波尔图","Edinburgh":"爱丁堡","Christopher Little":"克里斯托弗·利特尔","Bloomsbury":"布卢姆斯伯里","Nigel Newton":"奈杰尔·牛顿","Alice":"爱丽丝","Kathleen":"凯瑟琳","Philosopher's Stone":"魔法石","Scholastic":"学乐"}}
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 核对 import 生成并核对
生成并核对(S, out)
