import json,re,glob,os
# 第48篇初稿（逐词对照）：S = [(段, [chunk, ...])]，chunk = ([(英文组, 中文组), ...], 可选 note)
# 2026-11-04 重点词中文沿用文章定稿（铁律），只按《翻译风格》调格式；形容词的“的”标进粗体；三项并列加牛津逗号（T18）；不用破折号（T36）。
S=[
(1,[[[("In July 1964,","1964年7月，")]],
    [[("**inspecting** rice ear by ear","逐穗**察看**(inspecting)水稻时，"),("in a **paddy** at Anjiang Agricultural School in Hunan province,","在湖南省安江农校的一块**稻田**(paddy)里，")],
     "（inspecting…：现在分词短语作伴随状语；\near by ear：一穗一穗地）"],
    [[("the **instructor**","**教员**(instructor)"),("Yuan Longping","袁隆平"),("spotted","发现了"),("a **peculiar**","一株**奇特的**(peculiar)"),("plant.","稻子。")],
     "（the instructor Yuan Longping：同位语，说明袁隆平的身份）"]]),
(1,[[[("It was","它是"),("male-**sterile**,","雄性**不育**(sterile)株，"),("**shedding** no","**散**(shedding)不出"),("**viable**","**有活力的**(viable)"),("**pollen**.","**花粉**(pollen)。")],
     "（shedding no viable pollen：现在分词短语作伴随状语，\n补充说明 male-sterile）"]]),
(1,[[[("Rice","水稻"),("pollinates itself,","是自花授粉的，")]],
    [[("so","所以，"),("breeding **hybrid** seed **in bulk**","要**大批地**(in bulk)培育**杂交**(hybrid)种子，"),("depends on","就得靠"),("such plants.","这样的植株。")],
     "（breeding… in bulk：动名词短语作主语；\nin bulk：大批，大量地）"]]),
(1,[[[("In February 1966","1966年2月，"),("he","他"),("**detailed**","**详细描述了**(detailed)"),("the **anomaly**","这一**反常现象**(anomaly)，"),("in the **journal**","文章发表在**期刊**(journal)"),("Chinese Science Bulletin.","《科学通报》上。")],
     "（Chinese Science Bulletin：《科学通报》，\n中国的学术期刊）"]]),
(2,[[[("The **specimen**","这株**标本**(specimen)"),("**launched**","**开启了**(launched)"),("a six-year **hunt**:","一场长达六年的**搜寻**(hunt)：")]],
    [[("Yuan and his **colleagues**","袁隆平和**同事们**(colleagues)"),("could not **breed**","始终**培育**(breed)不出"),("a sterile line","一个不育系，")]],
    [[("whose **offspring**","能让**后代**(offspring)"),("**reliably**","**稳定地**(reliably)"),("**inherited**","**遗传**(inherited)"),("the **trait**.","这一**性状**(trait)。")],
     "（whose…：定语从句，修饰 a sterile line）"]]),
(2,[[[("The **breakthrough**","**突破**(breakthrough)"),("came","出现在"),("on 23 November 1970,","1970年11月23日，")]],
    [[("in a **marsh**","地点是一片**沼泽**(marsh)，"),("near Nanhong Farm in Sanya, Hainan.","在海南三亚南红农场附近。")]]]),
(2,[[[("Yuan's assistant, Li Bihu,","袁隆平的助手李必湖"),("and Feng Keshan, a farm **technician**,","和农场**技术员**(technician)冯克珊")],
     "（a farm technician：同位语，补充说明 Feng Keshan）"],
    [[("found","找到了"),("wild rice","一种野生稻，"),("whose pollen","它的花粉"),("was **abortive**.","**败育**(abortive)。")],
     "（whose…：定语从句，修饰 wild rice）"]]),
(3,[[[("Then came","随后，"),("Yuan's","袁隆平迈出了"),("**decisive**","**决定性的**(decisive)"),("move:","一步：")],
     "（Then came…：倒装句，主语是 Yuan's decisive move）"],
    [[("rather than **withhold** the **strain**,","他没有把这个**品系**(strain)**扣在**(withhold)自己手里，")],
     "（rather than…：而不是……）"],
    [[("he","而是"),("**distributed** it **to**","把它**分给了**(distributed to)"),("**collaborators** **nationwide**.","**全国各地的**(nationwide)**协作者**(collaborators)。")],
     "（distribute A to B：把 A 分给 B）"]]),
(3,[[[("Hybrids","杂交稻"),("need","需要"),("three","三个"),("**distinct**","**各不相同的**(distinct)"),("lines:","系：")]],
    [[("a sterile line,","不育系，"),("one to **maintain**","**保持**(maintain)"),("its sterility,","其不育性的保持系，"),("and one","以及使杂交种"),("to **restore**","**恢复**(restore)"),("**fertility** in the hybrids.","**育性**(fertility)的恢复系。")],
     "（one to…：不定式作后置定语，修饰 one（= line））"]]),
(3,[[[("Yan Longan's team","颜龙安的团队"),("in Jiangxi","在江西"),("bred","育成了"),("sterile lines","不育系，")]],
    [[("and Zhang Xiancheng","张先程"),("in Guangxi","在广西"),("first **identified**","率先**找出了**(identified)"),("a restorer line.","恢复系。")]]]),
(3,[[[("In October 1973,","1973年10月，"),("at a national conference in Suzhou,","在苏州召开的全国性会议上，")]],
    [[("Yuan","袁隆平"),("declared","宣布"),("the three-line system","三系"),("complete.","已经配套。")],
     "（declare＋宾语＋形容词：宣布……已经……）"]]),
(4,[[[("By 1976","到1976年，"),("hybrids","杂交稻的"),("were **under cultivation**","**种植**(under cultivation)面积"),("on about 140,000","已达约14万"),("**hectares**.","**公顷**(hectares)。")],
     "（under cultivation：在耕种中，正被种植）"]]),
(4,[[[("The World Food Prize Foundation","据世界粮食奖基金会"),("**estimates**","**估计**(estimates)，")],
     "（estimate that…：估计……）"],
    [[("that hybrid rice","杂交稻"),("can **yield** up to a fifth more **grain** than **conventional** **varieties**.","比**常规**(conventional)**品种**(varieties)最多可多**产**(yield)五分之一的**稻谷**(grain)。")],
     "（up to a fifth more…than…：比……最多多五分之一）"]]),
(4,[[[("By the early 2000s","到21世纪初，"),("it","杂交稻"),("covered","已覆盖"),("almost half","近一半的"),("of China's rice fields.","中国稻田。")]]]),
(5,[[[("Yuan,","袁隆平"),("who shared the 2004 World Food Prize with Sierra Leone's Monty Jones,","曾与塞拉利昂的蒙蒂·琼斯共获2004年世界粮食奖，")],
     "（who…：非限制性定语从句，补充说明 Yuan）"],
    [[("died in Changsha on 22 May 2021,","2021年5月22日在长沙逝世，"),("aged 91.","享年91岁。")]]]),
(5,[[[("Yet","然而，"),("popular **myth**","一种流传甚广的**误解**(myth)"),("**portrays** him **as**","把他**描绘成**(portrays as)"),("a **solitary**","一个**单枪匹马的**(solitary)"),("**genius**.","**天才**(genius)。")],
     "（portray A as B：把 A 描绘成 B）"]]),
(5,[[[("His eye","他的慧眼"),("began","开启了"),("the search;","这场搜寻；")]],
    [[("his **generosity**","他的**慷慨**(generosity)，"),("let","让"),("many hands","许多双手"),("**bring in the harvest**.","一起**迎来了丰收**(bring in the harvest)。")],
     "（bring in the harvest：收庄稼，这里指迎来丰收）\n"
     "（简述：1964年7月，袁隆平在安江农校的稻田里发现一株雄性不育的稻子。\n"
     "此后六年，他和同事们始终培育不出后代能稳定遗传不育性的不育系。\n"
     "1970年11月，李必湖和冯克珊在海南三亚找到花粉败育的野生稻。\n"
     "袁隆平把这个品系分给全国各地的协作者，\n"
     "颜龙安的团队育成不育系，张先程率先找出恢复系，1973年三系配套。\n"
     "杂交稻最多可比常规品种多产五分之一的稻谷，\n"
     "到21世纪初已覆盖中国近一半的稻田。\n"
     "他不是单枪匹马的天才，丰收靠的是许多双手。）"]]),
]
G={
 "S1 inspecting rice ear by ear":"对齐不了：ear by ear 是方式状语，中文“逐穗察看水稻时”（沿用文章定稿“逐穗察看”）“逐穗”必须放到动词前",
 "S3 breeding hybrid seed in bulk":"对齐不了：in bulk 是方式状语，中文“大批地”必须放到动词“培育”前，拆开 breeding、seed 中文不通",
 "S5 a sterile line":"对齐不了：sterile line 是育种术语“不育系”，拆开不通",
 "S7 wild rice":"对齐不了：wild rice 是术语“野生稻”，拆开不通",
 "S9 a sterile line":"对齐不了：sterile line 是育种术语“不育系”，拆开不通",
 "S10 sterile lines":"对齐不了：sterile line 是育种术语“不育系”，拆开不通",
 "S10 a restorer line":"对齐不了：restorer line 是育种术语“恢复系”，拆开不通",
 "S11 at a national conference in Suzhou":"对齐不了：in Suzhou 是后置定语，修饰 conference，中文“在苏州召开的全国性会议上”定语必须提前",
 "S11 the three-line system":"对齐不了：three-line system 是育种术语“三系”，拆开不通",
 "S13 that hybrid rice":"对齐不了：hybrid rice 是术语“杂交稻”，拆开不通",
 "S14 of China's rice fields":"对齐不了：rice fields 中文“稻田”是一个词，拆开不通",
}
CONF={"合组":G,"对齐":{
 "S1-2 inspecting rice ear by ear":"ear by ear 是方式状语，中文“逐穗察看”（沿用文章定稿）必须放到动词前",
 "S1-2 in a paddy at Anjiang Agricult":"at Anjiang Agricultural School in Hunan province 是后置定语，修饰 paddy，中文“在湖南省安江农校的一块稻田里”（沿用文章定稿）定语必须提前；in Hunan province 也要提到校名前，修饰 Anjiang Agricultural School，中文“湖南省安江农校”省名必须提前；专名不能拆",
 "S7-1 and Feng Keshan, a farm techni":"a farm technician 是同位语，补充说明 Feng Keshan，中文“农场技术员冯克珊”（沿用文章定稿）身份必须放到人名前",
 "S3-2 breeding hybrid seed in bulk":"in bulk 是方式状语，中文“要大批地培育杂交种子”必须放到动词前",
 "S6-2 near Nanhong Farm in Sanya, Ha":"地点由小到大 near Nanhong Farm in Sanya, Hainan，中文“海南三亚南红农场附近”必须由大到小倒过来，“附近”放最后",
 "S8-2 rather than withhold the strai":"withhold the strain 中文沿用文章定稿“把这个品系扣在自己手里”，宾语必须提到动词前",
 "S11-1 at a national conference in Su":"in Suzhou 是后置定语，修饰 conference，中文“在苏州召开的全国性会议上”定语必须提前",
 "S13-1 The World Food Prize Foundatio":"专名 World Food Prize Foundation 不能拆，中文“据世界粮食奖基金会”",
 "S13-2 can yield up to a fifth more g":"than conventional varieties 是比较状语，中文“比常规品种最多可多产五分之一的稻谷”（沿用文章定稿）比较对象必须放到动词前",
 "S15-1 who shared the 2004 World Food":"非限制性定语从句，with Sierra Leone's Monty Jones 中文“曾与塞拉利昂的蒙蒂·琼斯共获”必须放到动词前，年份也要提到奖名前",
 "S15-2 died in Changsha on 22 May 202":"时间、地点状语 in Changsha on 22 May 2021，中文“2021年5月22日在长沙逝世”必须放到动词前，时间在地点前",
},
 "们":{"S5-2 **同事们**":"colleagues 是复数，沿用文章定稿“同事们”，们在加粗内"},
 "数字":{"S12-1 140,000":"about 140,000 中文按文章定稿写作“约14万”，数值相同（140,000 = 14万）；英文读 one hundred and forty thousand","S14-1 2000":"the early 2000s 中文按文章定稿写作“21世纪初”（2000年代初 = 21世纪初）；英文读 the early two thousands"},
 "短语":{"S6 breakthrough … in":"不是搭配：in a marsh 是地点状语，不是 breakthrough in 搭配（文中没有“在……方面的突破”）",
  "S8 withhold … to":"不是搭配：to 属于后面的 distributed it to，withhold 后面只有宾语 the strain",
  "S9 maintain … to":"不是搭配：to 是下一项 one to restore 的不定式符号，不是 maintain 的搭配",
  "S13 estimates … to":"不是搭配：to 属于 up to a fifth，estimates 只接 that 从句",
  "S13 yield … to":"不是搭配：up to 修饰 a fifth more grain（最多……），不是 yield 的搭配",
  "S8 collaborators nationwide":"不是搭配：nationwide 是后置修饰语（全国各地的），collaborators 用的就是本义“协作者”（速查表 collaborator n. 合作者，协作者），不是习语"},
}
out={"no":"48","title_en":"Rice for the World","title_zh":"稻济天下","title_fx":{"hl":["Rice","World"],"ghost":[]},"sentences":[],"核对确认":CONF,"结尾解说":"简述",
     "高亮按实际开口":True,"高亮开口门槛":40,
     "术语":{"Yuan Longping":"袁隆平","Yuan":"袁隆平","Anjiang Agricultural School":"安江农校","Hunan":"湖南","Chinese Science Bulletin":"《科学通报》","Li Bihu":"李必湖","Feng Keshan":"冯克珊","Nanhong Farm":"南红农场","Sanya":"三亚","Hainan":"海南","Yan Longan":"颜龙安","Jiangxi":"江西","Zhang Xiancheng":"张先程","Guangxi":"广西","Suzhou":"苏州","World Food Prize Foundation":"世界粮食奖基金会","World Food Prize":"世界粮食奖","China":"中国","Sierra Leone":"塞拉利昂","Monty Jones":"蒙蒂·琼斯","Changsha":"长沙"}}
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 核对 import 生成并核对
生成并核对(S, out)
