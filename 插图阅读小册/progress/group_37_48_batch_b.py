from pathlib import Path
from group_37_48_worker import build
S=Path('/workspace/work/booklet70/illustration-style-standard.txt').read_text()
build(40,[
'1968年，3M公司的科学家斯潘塞·西尔弗着手研制超强黏合剂，做出的聚合物却有另一种性能：微小球粒形成黏性较弱的涂层，让纸张暂时贴住，揭下后还能重新贴上。对追求黏合强度的发明者来说，这个配方却是一次挫折。',
'此后五年，西尔弗在3M内部不断推广它，在闲聊和研讨会上反复介绍。用他自己的话说，这是一个还没找到问题的解决方案。他的坚持换来的却是冷淡。这种不同寻常的材料始终找不到用途，探索似乎毫无结果。',
'1974年，听过他一次讲座的同事阿特·弗莱在教堂遇到一件烦心事：夹在唱诗班赞美诗集里的纸书签总是移位、掉落。这种挫败感让他想到，没人要的弱黏胶，也许能做出贴在书页上、不易移动、揭下又不伤纸的书签。',
'1977年，这种便条以Press ’n Peel之名在美国四个城市试销，购买者反应冷淡。1978年，3M的营销人员在爱达荷州博伊西发动密集推广，向办公室免费派发一包包便条。试用过的受访者中，超过90%表示愿意购买。产品终于由冷遇迎来转机。',
'1980年4月6日，产品以“便利贴”的新名字在美国全国销售，1981年又进入加拿大和欧洲。如今这种文具已是常用品；它标志性的金丝雀黄色却纯属偶然：当时隔壁实验室只有剩下的黄纸。'
],'''set out to|set out to|动词短语|着手；开始做
super-strong|super-strong|adj.|超强的
adhesive|adhesive|n.|黏合剂
polymer|polymer|n.|聚合物
something else|something else|代词短语|别的东西；另一回事
spheres|sphere|n.|球状颗粒
tack|tack|n.|黏着力
temporary|temporary|adj.|暂时的
adhere|adhere|v.|黏附
peel off|peel off|动词短语|揭下；剥离
reapplied|reapply|v.|重新贴上
inventor|inventor|n.|发明者
formulation|formulation|n.|配方
setback|setback|n.|挫折
acted as|act as|动词短语|充当
promoter|promoter|n.|推广者
corporate|corporate|adj.|公司的
informal|informal|adj.|非正式的
seminars|seminar|n.|研讨会
summary|summary|n.|概括；总结
solution|solution|n.|解决方案
perseverance|perseverance|n.|坚持不懈
indifference|indifference|n.|冷淡；漠不关心
unconventional|unconventional|adj.|不同寻常的
found no use|find no use|动词短语|找不到用途
pursuit|pursuit|n.|探索；追求
fruitless|fruitless|adj.|无结果的
annoyance|annoyance|n.|烦心事
bookmarks|bookmark|n.|书签
wedged|wedge|v.|夹住；塞入
choir|choir|n.|唱诗班
hymn|hymn|n.|赞美诗
dislodged|dislodge|v.|使移位
falling out|fall out|动词短语|掉出来
frustration|frustration|n.|挫败；懊恼
unwanted|unwanted|adj.|没人要的
cling to|cling to|动词短语|黏在；紧附
stay put|stay put|动词短语|留在原处
undamaged|undamaged|adj.|完好无损的
notes|note|n.|便条
test-marketed|test-market|v.|试销
purchasers|purchaser|n.|购买者
enthusiasm|enthusiasm|n.|热情
marketers|marketer|n.|营销人员
staged|stage|v.|组织；发起
blitz|blitz|n.|密集攻势
dispensed|dispense|v.|分发
complimentary|complimentary|adj.|免费赠送的
packets|packet|n.|小包
respondents|respondent|n.|受访者
coolness|coolness|n.|冷淡
turnaround|turnaround|n.|转机；好转
pads|pad|n.|便笺本
rebranded as|rebrand as|动词短语|更名为；改品牌为
Post-it Notes|Post-it Notes|n.|便利贴（产品名）
nationally|nationally|adv.|在全国
stationery|stationery|n.|文具
staple|staple|n.|常用品
signature|signature|adj.|标志性的
canary|canary|adj.|金丝雀黄色的
tone|tone|n.|色调
unplanned|unplanned|adj.|计划外的
leftover|leftover|adj.|剩余的''',
'adhesive|polymer|tack|temporary|adhere|peel off|formulation|setback|perseverance|indifference|unconventional|fruitless|dislodged|frustration|cling to|test-marketed|enthusiasm|dispensed|complimentary|respondents|turnaround|staple'.split('|'),
['adhesive','perseverance','complimentary','turnaround'],'黏得不牢的胶，为什么成了畅销文具？',S+'\nSpecific scene: The pivotal hymn-book bookmark idea, close view of an adult\'s two anatomically natural hands at a modest 1970s wooden reading table. One hand gently peels a small plain buttery-yellow sticky paper bookmark from an open sage clothbound hymn book while the other steadies the undamaged blank page. Two loose plain paper bookmarks rest beside the book, quietly explaining the former slipping problem. Blank book pages with faint paper texture only, absolutely no musical notation, letters, words or logos. Show the flexible note curling cleanly away without torn fibers, not strong glue strands. Airy ivory composition, tactile matte paper, elegant adult watercolor.',
'超过90%说愿意购买，指试用后的受访者，不是所有消费者，也不是实际购买率。')

build(41,[
'在澳大利亚东北部昆士兰州，灰背蔗甲虫的幼虫啃食根系，困扰着利润丰厚的甘蔗种植业。1935年6月，当地从夏威夷引进102只甘蔗蟾蜍。这些体型笨重的两栖动物原产美洲。同年8月，约2400只繁育出的幼蟾被放到野外。用一种生物控制另一种害虫的生物防治，就这样迎来了一位雄心勃勃的“新兵”。',
'这项草率的计划遭到反对。1935年11月，昆虫专家沃尔特·弗罗格特说服官员暂停释放，但昆士兰州游说后，释放又在1936年9月恢复。计划最终失败：蟾蜍几乎没有减少甲虫数量，可能因为这些昆虫待在高高的甘蔗茎秆上。',
'蟾蜍自身反而繁盛起来。它们天敌很少，雌蟾一次产下数千枚卵，于是数量不受控制地增加。入侵前沿最初每年推进约10公里，在热带北部加速到每年约50公里。2009年2月，已知的第一只蟾蜍越过了西澳大利亚州边界。',
'蟾蜍皮肤中的毒腺，使捕食它们可能成为致命的一餐。一些地区的巨蜥和北袋鼬数量大幅下降，某些地方的袋鼬种群甚至消失了。巨蜥是大型蜥蜴，北袋鼬则是捕食小动物的有袋类。蟾蜍造成了严重生态破坏，但影响并不均匀，一些物种反而兴盛起来。',
'生物防治也有成功的例子。自1926年起，仙人掌螟在约十年间清除了昆士兰州和新南威尔士州大部分入侵的仙人掌属植物。它的幼虫事先经过检验，宁可饿死也不吃另外15种植物；蟾蜍却没有接受过这样的测试。根据1984年10月通过的法律，如今引入生物防治物种需要严格审查。这次失误始于仓促，又因游说压过警告而成为定局：一个未经检验的“盟友”，一旦放出，就可能再也召不回来。'
],'''beetles|beetle|n.|甲虫
larvae|larva|n.|幼虫
devour|devour|v.|大量啃食
plaguing|plague|v.|困扰
lucrative|lucrative|adj.|利润丰厚的
plantations|plantation|n.|种植园
imported|import|v.|引进
bulky|bulky|adj.|体积庞大笨重的
amphibians|amphibian|n.|两栖动物
native to|native to|形容词短语|原产于
released|release|v.|释放
Biological|biological|adj.|生物的
species|species|n.|物种
pest|pest|n.|害虫；有害生物
ambitious|ambitious|adj.|雄心勃勃的
recruit|recruit|n.|新成员；新兵
hasty|hasty|adj.|草率仓促的
opposition|opposition|n.|反对
persuaded|persuade|v.|说服
halt|halt|v.|停止
lobbying|lobbying|n.|游说
resumed|resume|v.|恢复；重新开始
scheme|scheme|n.|计划
flopped|flop|v.|彻底失败
dented|dent|v.|削减；产生影响
stalks|stalk|n.|茎秆
thrived|thrive|v.|繁盛
foes|foe|n.|敌手；此处指天敌
fertile|fertile|adj.|能繁殖的
spawning|spawn|v.|产卵
multiplied|multiply|v.|大量繁殖
unchecked|unchecked|adj.|未受遏制的
invasion|invasion|n.|入侵
frontier|frontier|n.|前沿
accelerated|accelerate|v.|加速
tropical|tropical|adj.|热带的
breached|breach|v.|突破；越过
Toxin|toxin|n.|毒素
glands|gland|n.|腺体
lizards|lizard|n.|蜥蜴
marsupial|marsupial|adj.|有袋类的
slumped|slump|v.|锐减
wiped out|wipe out|动词短语|彻底消灭
wreaked|wreak|v.|造成（破坏）
havoc|havoc|n.|严重破坏
uneven|uneven|adj.|不均等的
prospered|prosper|v.|兴盛
triumph|triumph|v.|大获成功
moth|moth|n.|蛾
prickly|prickly|adj.|多刺的
invasive|invasive|adj.|入侵性的
cactus|cactus|n.|仙人掌
starved|starve|v.|饿死
stringent|stringent|adj.|严格的
scrutiny|scrutiny|n.|仔细审查
blunder|blunder|n.|严重错误
haste|haste|n.|仓促
overrode|override|v.|压过；推翻
untested|untested|adj.|未经检验的
ally|ally|n.|盟友
loose|loose|adj.|被放出的；不受约束的
recalled|recall|v.|召回''',
'larvae|devour|lucrative|amphibians|native to|species|pest|hasty|opposition|persuaded|lobbying|resumed|thrived|unchecked|invasion|accelerated|Toxin|wiped out|invasive|stringent|scrutiny|overrode'.split('|'),
['lucrative','opposition','unchecked','scrutiny'],'引进的灭虫帮手，为什么成了生态难题？',S+'\nSpecific scene: A cane toad at the base of a 1930s Queensland sugar-cane field, viewed at ground level with dignified naturalistic wildlife detail. The bulky brown toad is the clear focal point. On one tall cane stalk well above its reach sits a tiny grey cane beetle, a subtle supporting observation that does not claim a proven sole cause. A plain open wooden transport crate is set discreetly at the field edge, evoking the historical introduction. No toad eating a beetle, no magical poison clouds, no dead wildlife, no universal ruined ecosystem. Soft sage cane leaves and an ivory sky with generous margins.',
'原文只说甲虫在高处“可能”解释防治失败；生态损害也并非对所有物种相同。')

build(42,[
'1990年4月24日，发现号航天飞机将哈勃空间望远镜送入轨道。这座安放在载荷舱中的太空天文台耗资约15亿美元，是一笔用于凝视宇宙与星系的巨额投资。但人们很快发现，花钱并不一定能买来清晰的影像。',
'哈勃传回的首批照片模糊不清。1990年6月，美国航天局宣布主镜有缺陷：外缘磨得过平，与正确形状相差2.2微米，约为头发丝宽度的五十分之一。这点偏差损害了光学系统，使光线无法准确聚焦。',
'问题出在校准上。检测主镜形状的装置中，一块透镜错位了约1.3毫米，主镜因此被磨成了错误的曲面。承包商珀金-埃尔默公司另一项独立测试曾给出不同结果，但工程师和美国航天局管理人员认为该测试较不可靠，没有深入追查那组相互矛盾的读数。',
'主镜无法在轨道上修复，于是工程师为它设计了一副“定制眼镜”。矫正装置COSTAR的箱体约有冰箱大小，可调机械臂上装着小反射镜，在光线进入仪器前将其截住，抵消有缺陷的主镜造成的畸变。主镜本身保持不动，同时还准备了一台新的主相机。',
'1993年12月2日，奋进号载着七名宇航员升空。完成交会后，他们协同作业，通过五次太空行走，用约35个半小时安装了COSTAR和新相机。哈勃的影像恢复清晰，仿佛重获视力。但主镜那2.2微米的缺陷仍然存在，光线是在离开主镜之后才得到矫正的。'
],'''lofted|loft|v.|向高处送出
Telescope|telescope|n.|望远镜
into|into|prep.|进入；到……中
observatory|observatory|n.|天文台
cradled|cradle|v.|稳妥安放
payload|payload|n.|有效载荷
lavish|lavish|adj.|耗资巨大的
investment|investment|n.|投资
gaze|gaze|n.|凝视；目光
cosmos|cosmos|n.|宇宙
galaxies|galaxy|n.|星系
clarity|clarity|n.|清晰度
snapshots|snapshot|n.|照片；快照
blurred|blurred|adj.|模糊的
fuzzy|fuzzy|adj.|模糊不清的
flaw|flaw|n.|缺陷
outer|outer|adj.|外侧的
rim|rim|n.|边缘
flattened|flatten|v.|磨平；使变平
width|width|n.|宽度
deviation|deviation|n.|偏差
marred|mar|v.|损害
optics|optics|n.|光学系统
sharp|sharp|adj.|清晰锐利的
calibration|calibration|n.|校准
lens|lens|n.|透镜
assembly|assembly|n.|装置；组件
offset|offset|v.|使偏离位置
millimetres|millimetre|n.|毫米
was ground to|be ground to|动词短语|被磨成
curve|curve|n.|曲面；曲线
independent test|independent test|n.|独立测试
contractor|contractor|n.|承包商
divergent|divergent|adj.|不同的；不一致的
reliable|reliable|adj.|可靠的
contradictory|contradictory|adj.|相互矛盾的
unexplored|unexplored|adj.|未被深入调查的
prescribed|prescribe|v.|开出；提出（方案）
tailored|tailored|adj.|量身定制的
corrective|corrective|adj.|矫正的
cabinet|cabinet|n.|箱体
refrigerator|refrigerator|n.|冰箱
adjustable|adjustable|adj.|可调节的
intercepted|intercept|v.|截住
compensated for|compensate for|动词短语|弥补；抵消
imperfect|imperfect|adj.|有缺陷的
distortion|distortion|n.|畸变
untouched|untouched|adj.|未改动的
ascended|ascend|v.|升空；上升
rendezvous|rendezvous|n.|交会
in tandem|in tandem|介词短语|协同地
spacewalks|spacewalk|n.|太空行走
exertion|exertion|n.|费力；辛苦作业
installing|install|v.|安装
imagery|imagery|n.|影像
crisp|crisp|adj.|清晰鲜明的
vision|vision|n.|视力
renewed|renew|v.|使恢复
gathers|gather|v.|收集''',
'observatory|payload|lavish|clarity|flaw|deviation|optics|calibration|assembly|offset|contractor|divergent|reliable|contradictory|corrective|intercepted|compensated for|distortion|untouched|rendezvous|in tandem|imagery'.split('|'),
['calibration','reliable','untouched','imagery'],'主镜没有修好，影像怎样变清晰？',S+'\nSpecific scene: The 1993 Hubble servicing mission, a single astronaut in a credible white space suit tethered at the open SIDE instrument-access bay of the silver cylindrical Hubble telescope. The astronaut guides a refrigerator-sized corrective instrument cabinet into the side bay, with a few small folded gold-toned mirror arms visible on the instrument. The primary mirror remains entirely inside the main telescope tube, hidden and untouched; never show it being polished, patched, replaced or cracked. A cropped portion of the shuttle work platform and a faint sage Earth curve support the scene. No logos or letter patches, no optical ray diagrams or labels. Space is rendered as a very pale grey-green watercolor wash into generous warm ivory, restrained and adult.',
'2.2微米是主镜形状误差，1.3毫米是检测装置透镜的错位；安装矫正装置并未修磨主镜。')
