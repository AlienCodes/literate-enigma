from pathlib import Path
from group_37_48_worker import build
S=Path('/workspace/work/booklet70/illustration-style-standard.txt').read_text()
build(37,[
'1847年前后，意大利化学家索布雷罗首次制得硝酸甘油。这是一种无色、油状、极不稳定的液体。他报告说，仅在舌头上滴一小滴，就会使头部剧烈抽痛数小时。1864年9月3日，斯德哥尔摩一间存放硝酸甘油的棚屋爆炸，造成五人死亡，其中包括阿尔弗雷德·诺贝尔的弟弟埃米尔。',
'诺贝尔将这种液体与多孔的硅藻土混合，制成糊状物，再塑成棒状，使它变得更可控。这种炸药于1867年获得专利，用于采矿、采石和拆除工程，让他积累了巨额财富。他在1895年立下遗嘱，以这笔财产设立奖项基金，奖项于1901年首次颁发。',
'硝酸甘油也有副作用。工厂工人饱受剧烈头痛之苦；他们在一周工作中逐渐产生的耐受性，到周末又会减退。每到星期一，头痛便再次发作，还伴有眩晕和心悸，因此被称为“星期一病”。1879年，威廉·默雷尔在《柳叶刀》报告了硝酸甘油治疗心绞痛的用途。心绞痛就是阵发性的胸痛。',
'1896年10月25日，患有心绞痛的诺贝尔写信给助手，感叹命运的讽刺：医生竟开了硝酸甘油让他内服。他解释说，这种药另取名为Trinitrin，是为了不吓到药剂师或公众。他没有遵从医嘱。后来，他因脑出血而部分瘫痪，于1896年12月10日在圣雷莫的别墅中去世。',
'1977年，穆拉德查明，硝酸甘油会释放一氧化氮，使血管扩张。1980年，弗奇戈特在血管内壁发现了一种身份尚不明确的舒张因子；1986年，伊格纳罗认定它就是一氧化氮。三人共同获得1998年诺贝尔生理学或医学奖。12月10日颁奖时，致辞引用了诺贝尔那封感叹命运讽刺的信；那天也正是他的逝世纪念日。'
],'''Italian|Italian|adj.|意大利的
chemist|chemist|n.|化学家
nitroglycerin|nitroglycerin|n.|硝酸甘油
colourless|colourless|adj.|无色的
oily|oily|adj.|油状的
liquid|liquid|n.|液体
acute|acute|adj.|极度的；严重的
instability|instability|n.|不稳定性
mere|mere|adj.|仅仅的；不过是
droplet|droplet|n.|小滴
throbbing|throb|v.|一阵阵抽痛
violently|violently|adv.|剧烈地
shed|shed|n.|棚屋
tragic|tragic|adj.|悲惨的
tamed|tame|v.|使受控；驯服
blending|blend|v.|混合
porous|porous|adj.|多孔的
paste|paste|n.|糊状物
rods|rod|n.|棒；条
harnessed|harness|v.|控制并利用
mining|mining|n.|采矿
quarrying|quarrying|n.|采石
demolition|demolition|n.|拆除工程
enriching|enrich|v.|使富有
immensely|immensely|adv.|极其
testament|testament|n.|遗嘱
fortune|fortune|n.|巨额财富
endowment|endowment|n.|捐赠基金
Nitroglycerin|nitroglycerin|n.|硝酸甘油
side-effects|side effect|n.|副作用
Factory operatives|factory operative|n.|工厂工人
racking|racking|adj.|剧烈折磨人的
tolerance|tolerance|n.|耐受性
ebbed|ebb|v.|减退
recurrence|recurrence|n.|复发
dizziness|dizziness|n.|眩晕
palpitations|palpitation|n.|心悸
hence|hence|adv.|因此
therapeutic|therapeutic|adj.|治疗的；有疗效的
aide|aide|n.|助手
by an irony of fate|by an irony of fate|介词短语|命运弄人地
prescribed|prescribe|v.|开具（药物）处方
internally|internally|adv.|通过内服
alias|alias|n.|别名
frightening|frighten|v.|使害怕
pharmacists|pharmacist|n.|药剂师
comply|comply|v.|遵从
Partly|partly|adv.|部分地
paralysed|paralyse|v.|使瘫痪
cerebral haemorrhage|cerebral haemorrhage|n.|脑出血
villa|villa|n.|别墅
ascertained|ascertain|v.|查明
nitric oxide|nitric oxide|n.|一氧化氮
widens|widen|v.|使扩张
unidentified|unidentified|adj.|尚未确认身份的
factor|factor|n.|因子
vascular|vascular|adj.|血管的
linings|lining|n.|内壁；内层
trio|trio|n.|三人组
Nobel Prize|Nobel Prize|n.|诺贝尔奖
presentation|presentation|n.|颁授；颁奖
anniversary|anniversary|n.|周年纪念日
quoted|quote|v.|引用
ironic|ironic|adj.|具有讽刺意味的''',
'chemist|nitroglycerin|acute|instability|tamed|blending|porous|harnessed|demolition|enriching|testament|fortune|endowment|tolerance|recurrence|therapeutic|prescribed|comply|ascertained|unidentified|vascular|anniversary'.split('|'),
['instability','tolerance','comply','ascertained'],'同一种液体，怎样既能炸山又能救心？',S+'\nSpecific scene: A coherent late-19th-century archival still life on a pale wooden chemist\'s writing desk: an unlabelled small medicine vial with a glass stopper beside a folded blank letter is the focal point; a separate shallow wooden tray in the background holds two plain paper-wrapped dynamite rods without fuses. The editorial juxtaposition evokes Nobel\'s ironic angina prescription, not an experiment to imitate. Soft sage glass shadows, a restrained lemon-yellow reflection, ample ivory margins. No explosion, no swallowing, no human injury, no readable writing, no Nobel medal or invented molecular diagram.',
'未遵医嘱与死亡不应混作因果；文章明确交代诺贝尔脑出血。')

build(38,[
'生态学中一个格外浪漫的观念，竟起源于塑料袋。在加拿大的一片森林里，研究人员把纸桦和花旗松的幼苗罩进袋中，分别让两种幼苗接触掺有不同示踪物的二氧化碳。碳在两种树之间双向转移，似乎经由连接根系的真菌传递。不过，花旗松最终获得了少量净盈余，在遮荫更深的地方，盈余也更大。',
'大多数陆生植物都与这类真菌共存。真菌的菌丝寻找水分和包括氮在内的养分，再拿这些资源换取植物的糖分。一个真菌就能将多株植物连成共享网络。《自然》于1997年8月7日发表这项研究，封面还用上了一个好记的新词：“林木万维网”。',
'这个比喻实在太有吸引力。2015年至2021年间，一位护林人的畅销书、一部广受好评的小说和一位生态学家的回忆录，都告诉读者：树木能够交谈、相互示警，还会像“母树”一样养育亲族。可1997年实验中的树只是幼苗，并不是年迈的母亲。',
'2023年2月，三位研究者系统梳理了野外证据。他们认为，这些证据或太少、或互不一致、或含糊不清，不足以证明共享网络普遍存在。在26项野外研究中，帮助与妨碍幼苗的结果出现得大致同样频繁，而最多见的是没有明显影响。没有一项经同行评审的野外研究表明，成年树木会偏爱自己的后代。后续论文中缺乏依据的断言在25年间翻了一倍，引用也偏向正面结果。',
'这些批评并不能否定网络的存在。2025年1月，网络说的拥护者质疑了那篇批评文章的方法；批评者也承认，碳和养分能够在树木之间经地下迁移。网络究竟传输了多少、这种传输在生态上有多大作用，必须由真实森林中的证据来判定，不能取决于一段“树木家族传奇”有多动人。'
],'''ecology|ecology|n.|生态学
romantic|romantic|adj.|富有浪漫色彩的
grew out of|grow out of|动词短语|源自；由……发展而来
enclosed|enclose|v.|把……围住；罩住
seedlings|seedling|n.|幼苗
in|in|prep.|在……里面
bathed|bathe|v.|使浸在；使充分接触
laced with|be laced with|动词短语|掺有
tracer|tracer|n.|示踪物
shuttled|shuttle|v.|往返移动
apparently|apparently|adv.|似乎；看来
fungi|fungus|n.|真菌
linking|link|v.|连接
slight|slight|adj.|少量的；轻微的
surplus|surplus|n.|盈余
shade|shade|n.|遮荫
terrestrial|terrestrial|adj.|陆生的
harbour|harbour|v.|容纳；携带
filaments|filament|n.|丝状体；此处指菌丝
forage for|forage for|动词短语|搜寻（水或养分）
nutrients|nutrient|n.|养分
nitrogen|nitrogen|n.|氮
swapping|swap|v.|交换
knit|knit|v.|联结；编织
into|into|prep.|进入；连成
shared network|shared network|n.|共享网络
unveiled|unveil|v.|公布；发表
catchy|catchy|adj.|好记而吸引人的
coinage|coinage|n.|新造词
metaphor|metaphor|n.|比喻
irresistible|irresistible|adj.|难以抗拒的
bestseller|bestseller|n.|畅销书
acclaimed|acclaimed|adj.|广受赞誉的
memoir|memoir|n.|回忆录
converse|converse|v.|交谈
warn one another|warn one another|动词短语|互相警告
nurture|nurture|v.|养育；培育
kin|kin|n.|亲族
elderly|elderly|adj.|年迈的
combed through|comb through|动词短语|仔细梳理；彻底搜查
sparse|sparse|adj.|稀少的
inconsistent|inconsistent|adj.|互不一致的
ambiguous|ambiguous|adj.|含糊不清的
demonstrate|demonstrate|v.|证明
widespread|widespread|adj.|普遍存在的
hindered|hinder|v.|妨碍
neutral|neutral|adj.|无明显正负影响的
predominating|predominate|v.|占多数
peer-reviewed|peer-reviewed|adj.|经同行评审的
mature|mature|adj.|成熟的；成年的
favouring|favour|v.|偏爱
offspring|offspring|n.|后代
Unsupported|unsupported|adj.|缺乏依据的
assertions|assertion|n.|断言
 doubled|double|v.|翻倍
citations|citation|n.|引文；引用
skewed|skew|v.|使偏向
towards|towards|prep.|朝；偏向
positive results|positive result|n.|正面结果
disproves|disprove|v.|证明……不成立
existence|existence|n.|存在
defenders|defender|n.|拥护者
faulted|fault|v.|指责；挑出问题
critique|critique|n.|批评性分析
critics|critic|n.|批评者
concede|concede|v.|承认（先前不愿承认的事）
migrate|migrate|v.|迁移
unearthed|unearth|v.|发掘
allure|allure|n.|吸引力
saga|saga|n.|传奇故事
convey|convey|v.|传输；输送
matters|matter|v.|有重要意义'''.replace('\n doubled|','\ndoubled|'),
'ecology|seedlings|tracer|apparently|surplus|terrestrial|filaments|nutrients|metaphor|nurture|combed through|sparse|inconsistent|ambiguous|demonstrate|widespread|neutral|peer-reviewed|assertions|citations|concede|convey'.split('|'),
['surplus','metaphor','neutral','concede'],'树木的地下联系，哪些已有证据？',S+'\nSpecific scene: Observational field botany in a Canadian forest, with one adult researcher kneeling beside a paper-birch seedling and a Douglas-fir seedling. One small translucent sampling bag gently encloses the birch foliage and a second bag encloses the fir foliage, both visibly above ground; a compact unmarked sampling instrument rests nearby. Natural roots stay below undisturbed soil, no cutaway. The focus is the careful real-world investigation behind the carbon-tracer study. No glowing fungal networks, no arrows, no mother-tree faces, no offspring being fed, no magical transfer between plants. Soft ivory clearing and sage forest, a few buttery birch leaves, calm scientific restraint.',
'“无明显影响最多”与“帮助、妨碍的次数接近”并不矛盾；复核未证明网络不存在。')

build(39,[
'千年虫漏洞最初源于一种省事的做法。当内存和硬件还很昂贵时，程序员只用两位数字储存年份，例如以“99”代表1999年。这种精简代码暗藏歧义：计算机可能把“00”理解成1900年，导致利息、年龄或截止日期计算出错。',
'各国政府和企业严阵以待，准备应对可能出现的混乱。1998年2月，克林顿总统成立委员会，协调美国的应对工作。顾问们审查旧系统，修补有问题的日期处理逻辑。1999年11月，美国商务部估计，美国各级政府和企业将为此花费约1000亿美元；对全球总支出的预测则高达数千亿美元。',
'1999年12月31日午夜来临，结果几乎没有出大问题。偶尔出现的小故障也大多轻微。日本志贺核电站的辐射监测设备失灵，但没有威胁安全；美国国防部一套处理间谍卫星数据的地面系统也出了故障。2000年2月，美国参议院的一个委员会认定，这些支出是合理的。',
'许多人却持不同看法，认为威胁被夸大了，甚至是个骗局。但局面之所以平稳，很大程度上正是因为大量问题已经修好。这就是“防备悖论”：预防措施发挥作用，使所抵御的危险没有出现，危险反而看起来像是凭空捏造的。繁琐的修复工作换来的不是感谢，而是嘲笑。',
'批评者指出，意大利和韩国花的钱少得多，结果却并不更差。但这种比较具有误导性：较低的支出数字往往没有算上企业的花费，而且很多修补工作也替换了早该升级的过时系统。没人能逐笔说清，哪些开支必不可少，哪些花得过多。奏效的预防可能只留下账单，人们只能拿它与那场本可能发生的灾难作比较。'
],'''bug|bug|n.|程序漏洞
millennium|millennium|n.|千年；千禧年
shortcut|shortcut|n.|捷径；省事的办法
memory|memory|n.|计算机内存
hardware|hardware|n.|硬件
costly|costly|adj.|昂贵的
programmers|programmer|n.|程序员
digits|digit|n.|数字
compact|compact|adj.|精简紧凑的
code|code|n.|程序代码
ambiguity|ambiguity|n.|歧义
corrupting|corrupt|v.|使出错；破坏
deadlines|deadline|n.|截止日期
braced for|brace for|动词短语|准备应对（困难）
chaos|chaos|n.|混乱
President|president|n.|总统
council|council|n.|委员会
coordinate|coordinate|v.|协调
Consultants|consultant|n.|顾问
audited|audit|v.|审查；核查
legacy|legacy|adj.|沿用的；旧有的
patched|patch|v.|修补（程序）
faulty|faulty|adj.|有缺陷的
Commerce Department|Commerce Department|n.|美国商务部
enterprises|enterprise|n.|企业
projections|projection|n.|预测
global|global|adj.|全球的
midnight|midnight|n.|午夜
struck|strike|v.|（钟）敲响
Glitches|glitch|n.|小故障
crop up|crop up|动词短语|意外出现
sporadic|sporadic|adj.|零星的；偶发的
minor|minor|adj.|轻微的
faltered|falter|v.|失灵；运转不稳
spy|spy|n.|间谍
concluded|conclude|v.|得出结论
expenditure|expenditure|n.|支出
justified|justified|adj.|合理的；有正当理由的
exaggerated|exaggerate|v.|夸大
hoax|hoax|n.|骗局
prevailed|prevail|v.|占上风；普遍存在
largely|largely|adv.|很大程度上
preparedness paradox|preparedness paradox|n.|防备悖论
precautions|precaution|n.|预防措施
ward off|ward off|动词短语|抵御
imaginary|imaginary|adj.|想象出来的
Tedious|tedious|adj.|繁琐乏味的
mockery|mockery|n.|嘲笑
gratitude|gratitude|n.|感激
South Korea|South Korea|n.|韩国
fared no worse|fare no worse|动词短语|情况并不更差
comparison|comparison|n.|比较
misleads|mislead|v.|误导
omitted|omit|v.|遗漏
remedial|remedial|adj.|补救的
obsolete|obsolete|adj.|过时的
overdue for|overdue for|形容词短语|早该进行……的
essential|essential|adj.|必不可少的
excessive|excessive|adj.|过多的；过度的
Prevention|prevention|n.|预防
invoice|invoice|n.|账单
be weighed against|be weighed against|动词短语|与……权衡比较
catastrophe|catastrophe|n.|灾难''',
'bug|shortcut|ambiguity|corrupting|braced for|coordinate|audited|legacy|patched|projections|sporadic|expenditure|justified|exaggerated|hoax|preparedness paradox|precautions|ward off|omitted|obsolete|essential|catastrophe'.split('|'),
['ambiguity','patched','sporadic','precautions'],'危机没有发生，能说明预防多余吗？',S+'\nSpecific scene: A quiet late-1999 computer maintenance room at dawn, one adult software engineer seated at a beige CRT terminal, calmly checking a neat open computer case beside the keyboard. A single sage server cabinet stands behind, with restrained unlabelled indicator lights. The CRT is a soft blank glow with no characters, interface, date, digits or fake chart; a closed unmarked binder is the only extra detail. The mood conveys painstaking preventative work and an uneventful transition, not an actual worldwide breakdown. Period-accurate bulky computer equipment, warm ivory daylight and muted green shadows. No explosions, no panic, no millennium date text.',
'文中的约1000亿美元是当时的估计；平稳过渡不代表每笔支出都已被证明必要。')
