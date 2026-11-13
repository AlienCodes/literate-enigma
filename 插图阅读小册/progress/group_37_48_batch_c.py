from pathlib import Path
from group_37_48_worker import build
S=Path('/workspace/work/booklet70/illustration-style-standard.txt').read_text()
build(43,[
'1985年5月，经历一场激烈交锋后，苹果董事会最终支持了首席执行官约翰·斯卡利。30岁的史蒂夫·乔布斯，在自己参与创办的公司里被解除管理职务。同年9月，遭到架空和疏远的他辞职了。',
'把时间倒回三十年前。乔布斯于1955年2月24日生于旧金山，出生不久便被收养。1976年4月1日，他和史蒂夫·沃兹尼亚克创办苹果；首批样机由电子工程师沃兹尼亚克研制。苹果的“车库起源”很大程度上具有象征意义，沃兹尼亚克认为它的重要性被夸大了。苹果于1980年12月12日上市，旗舰产品Macintosh于1984年1月24日首次推出。',
'离开苹果后的岁月颇有成果。1985年晚些时候，乔布斯创办电脑初创公司NeXT。1986年2月，他收购卢卡斯影业的电脑图形团队，后来发展为皮克斯。皮克斯起初制造专用硬件，主要还不是动画工作室。1995年11月22日上映的《玩具总动员》，成为首部长篇电脑动画电影。',
'转折发生在1996年12月20日：苹果同意收购NeXT，获得后来Mac OS X所用的核心软件，也让这家公司的创始人与旧东家重新走到一起。1997年8月，微软向陷入困境的竞争对手苹果投资1.5亿美元；同年9月，乔布斯接掌大权，出任临时负责人。他后来回忆，当时苹果离破产只差几周。此后，iMac、iPod和iPhone相继问世，其中iPhone于2007年1月9日公开亮相。',
'2003年10月，乔布斯被诊断患有一种罕见的恶性胰腺肿瘤。2011年8月，苹果一度超过埃克森美孚，成为全球市值最高的公司。乔布斯于2011年8月24日卸任，10月5日去世，终年56岁。在那家曾经将他逐出的公司里，他重新掌舵了将近十四年。'
],'''bruising|bruising|adj.|激烈而令人受挫的
confrontation|confrontation|n.|对抗；交锋
board|board|n.|董事会
ultimately|ultimately|adv.|最终
executive|executive|n.|高管；执行官
stripped of|be stripped of|动词短语|被剥夺
managerial|managerial|adj.|管理的
co-founded|co-found|v.|共同创办
sidelined|sideline|v.|使失去实权；架空
alienated|alienate|v.|使疏远
resigned|resign|v.|辞职
Rewind|rewind|v.|倒回；回溯
San Francisco|San Francisco|n.|旧金山
adopted|adopt|v.|收养
newborn|newborn|n.|新生儿
founded|found|v.|创办
electronics|electronics|n.|电子技术
prototypes|prototype|n.|样机
origins|origin|n.|起源
symbolic|symbolic|adj.|象征性的
significance|significance|n.|重要性；意义
inflated|inflate|v.|夸大
floated|float|v.|使公司上市
flagship|flagship|adj.|旗舰的；主打的
debuted|debut|v.|首次推出
Exile|exile|n.|被迫离开的时期
productive|productive|adj.|富有成果的
start-up|start-up|n.|初创公司
acquired|acquire|v.|收购
graphics|graphics|n.|电脑图形
outfit|outfit|n.|团队；机构
Pixar|Pixar|n.|皮克斯
manufacturer|manufacturer|n.|制造商
specialised|specialised|adj.|专用的
hardware|hardware|n.|硬件
animation|animation|n.|动画
studio|studio|n.|工作室
released|release|v.|上映；发行
feature-length|feature-length|adj.|长篇电影长度的
computer-animated|computer-animated|adj.|电脑动画制作的
reversal|reversal|n.|局面逆转
core|core|adj.|核心的
eventual|eventual|adj.|后来出现的；最终的
reuniting with|reunite with|动词短语|与……重聚
estranged|estranged|adj.|关系疏远的
invested|invest|v.|投资
in|in|prep.|向；对（投资对象）
distressed|distressed|adj.|陷入财务困境的
competitor|competitor|n.|竞争对手
took the reins|take the reins|动词短语|接掌大权
interim|interim|adj.|临时的
ruin|ruin|n.|破产；毁灭
showcased|showcase|v.|公开展示
diagnosis|diagnosis|n.|诊断
uncommon|uncommon|adj.|罕见的
cancerous|cancerous|adj.|恶性的
pancreatic|pancreatic|adj.|胰腺的
tumour|tumour|n.|肿瘤
briefly|briefly|adv.|短暂地
overtook|overtake|v.|超过
most valuable|valuable|adj.|有价值的；此处指市值高
tenure|tenure|n.|任期
at the helm of|at the helm of|介词短语|掌管；领导
ousted|oust|v.|逐出''',
'confrontation|board|executive|stripped of|managerial|sidelined|resigned|prototypes|symbolic|significance|productive|acquired|manufacturer|reversal|eventual|estranged|distressed|competitor|interim|diagnosis|tenure|at the helm of'.split('|'),
['confrontation','prototypes','acquired','interim'],'离开苹果后，乔布斯怎样走回苹果？',S+'\nSpecific scene: A coherent editorial still life of the crucial NeXT-to-Apple return: on a modest mid-1990s design-office desk sits an accurately proportioned matte black NeXT-style computer CUBE with no logo, beside its blank dark monitor and keyboard. A compact earlier beige Macintosh-style computer with an equally blank screen sits a little farther back. The black cube is the focal object, evoking the acquisition that brought core software and Jobs back, not suggesting that hardware parts were physically fused. A pair of adult hands gently sets the cube on the desk; no celebrity portrait is necessary. Soft window daylight, muted sage shelving and warm ivory space. No company marks, operating-system lettering, money, timelines or charts.',
'eventual Mac OS X指后来出现的系统，不是某个“最终版本”；微软投资的对象是苹果。')

build(44,[
'1955年瑞典举行公投，约83%的投票者选择保留靠左行驶，以压倒性多数拒绝改变。然而，1963年5月10日，议会推翻选民的选择，不顾这项计划在民众中缺乏支持，批准自1967年起改为靠右行驶。',
'改制的理由是与邻国统一。挪威和芬兰都靠右行驶，每年约有500万车次过境，瑞典靠左便带来隔阂和出行不便。安全也支持统一：约90%的汽车方向盘位于左侧，司机在狭窄的双车道公路上超车时，容易面临迎面相撞的危险。',
'一个国家机构负责这项庞大的准备工程，以带箭头的大写H为标识。宣传还包括电视歌曲比赛，获胜的广告歌用歌词劝人靠右行驶，甚至登上歌曲排行榜第五名。约36万件道路标识被更换，1000多辆右侧开门的新公交车也采购到位。',
'切换在1967年9月3日星期日进行。凌晨1点至6点，非必要车辆不得上路，必要车辆获得豁免。4点50分，仍在路上的车辆全部停下，再缓缓移到另一侧；5点、天亮之前，车辆统一按相反的行驶侧重新出发。斯德哥尔摩和马尔默的封路时间更长，从周六上午到周日下午，施工人员在此期间改造交叉路口。',
'随后的星期一报告了125起事故，此前几个星期一则有130至198起。这一统计上的改善，被归因于司机对新制度尚不熟悉，开车格外小心。紧张感似乎后来消退了，谨慎习惯也随之淡去：到1969年，事故率和死亡率已回到原来的基准水平。'
],'''referendum|referendum|n.|全民公投
overwhelmingly|overwhelmingly|adv.|压倒性地
rejection|rejection|n.|拒绝
legislators|legislator|n.|立法者
parliament|parliament|n.|议会
overruled|overrule|v.|推翻（决定或意见）
electorate|electorate|n.|全体选民
in defiance of|in defiance of|介词短语|不顾；违抗
populace|populace|n.|民众
unpopular|unpopular|adj.|不得人心的
conformity|conformity|n.|一致；统一
orientation|orientation|n.|方向；取向
isolation|isolation|n.|孤立
inconvenient|inconvenient|adj.|不便的
alignment|alignment|n.|统一；保持一致
motorists|motorist|n.|驾车者
overtaking|overtake|v.|超车
lane|lane|n.|车道
highways|highway|n.|公路
head-on collisions|head-on collision|n.|迎头相撞
mammoth|mammoth|adj.|庞大的
preparation|preparation|n.|准备工作
logo|logo|n.|标识
arrow|arrow|n.|箭头
propaganda|propaganda|n.|宣传
contest|contest|n.|比赛
jingle|jingle|n.|广告短歌
lyrics|lyric|n.|歌词
chart|chart|n.|歌曲排行榜
signage|signage|n.|各类标识
massive|massive|adj.|巨大的
fleet|fleet|n.|车队
procured|procure|v.|采购；取得
transition|transition|n.|转变；过渡
curfew|curfew|n.|宵禁；限行令
non-essential|non-essential|adj.|非必要的
asphalt|asphalt|n.|沥青路面
exempt|exempt|adj.|获豁免的
crawled|crawl|v.|缓慢移动
dawn|dawn|n.|黎明
flipped|flip|v.|翻转；改变方向
closure|closure|n.|封闭
reconfigured|reconfigure|v.|重新设置；改造
junctions|junction|n.|交叉路口
statistical|statistical|adj.|统计上的
improvement|improvement|n.|改善
put down to|put … down to …|动词短语|把……归因于……
heightened|heightened|adj.|增强的
hesitant|hesitant|adj.|犹豫不决的
nervousness|nervousness|n.|紧张
subsided|subside|v.|消退
prudent|prudent|adj.|谨慎的
faded|fade|v.|逐渐消失
fatality rates|fatality rate|n.|死亡率
reverted to|revert to|动词短语|回到；恢复到
baseline|baseline|n.|基准水平''',
'referendum|legislators|overruled|electorate|in defiance of|conformity|isolation|alignment|overtaking|head-on collisions|preparation|signage|procured|transition|exempt|reconfigured|statistical|put down to|subsided|prudent|reverted to|baseline'.split('|'),
['referendum','signage','exempt','baseline'],'全国换边行驶，怎样在一个清晨完成？',S+'\nSpecific scene: The calm dawn AFTER Sweden\'s September 1967 change to right-hand traffic, a restrained bird\'s-eye three-quarter view of one simple two-lane street bending through modest Nordic town buildings. A period 1960s Volvo-style car and a cream-and-sage bus move AWAY on the RIGHT-hand half of the road; one oncoming period car uses the LEFT-hand half in the image, correctly on its own right. Clear center line, no crossing or collision, very few vehicles. A road worker stands safely on the sidewalk with a plain lowered flag; a few cones recall the supervised transition. Right-side bus doors are appropriate. No signs with lettering, dates, numbers, logos, road slogans or written arrows; architectural shapes and coherent correct traffic directions carry the story. Misty ivory dawn, adult watercolor.',
'左侧方向盘与靠左行驶不是一回事；首个周一事故少，并不意味着长期事故率持续下降。')

build(45,[
'1977年夏末，美国航天局在两艘旅行者号探测器起飞前，各固定上一张直径30厘米的镀金铜唱片。谁也不知道，究竟会不会有谁、又会是谁来播放它们。',
'康奈尔大学卡尔·萨根带领的顾问团队，把地球家园浓缩成这份汇编。人声用55种语言向听者问候，接着是雷声、风声、鲸声、脚步声、笑声和有节奏的心跳。约90分钟的音乐包容了不同文化和时代，其中包括巴赫的作品，以及查克·贝里的《Johnny B. Goode》。',
'唱片中还有以模拟方式编码的115幅图像，并附有两位政治家吉米·卡特和库尔特·瓦尔德海姆的书面致辞。封套上给出了播放方法，以及一幅用脉冲星作信标、标定太阳位置的示意图。',
'1990年2月14日，应萨根的请求，旅行者1号转动相机，从约60亿公里外回望。60帧画面组成太阳系全景；地球在其中只是一点微光，宽度约为八分之一个像素。这些画面在3月至5月1日之间传回地球，信号单程需要五个半小时。',
'在1994年的一本书中，萨根借那颗暗淡的小点，帮助人们重新审视自己在浩瀚宇宙中渺小、短暂的位置。',
'旅行者1号于2012年8月进入星际空间，成为首个到达那里的人工物体；旅行者2号于2018年跟进。两者仍在工作，寿命在美国航天局的任务中无可匹敌；但随着电力耗尽，预计几年内就会沉寂。',
'旅行者号携带的唱片仍将继续向外穿越虚空，作为来自人类的信使，带着一幅指回太阳的地图。'
],'''fastened|fasten|v.|固定；系牢
disc|disc|n.|唱片；圆盘
wrought|wrought|adj.|制成的；加工成形的
gilded|gilded|adj.|镀金的
copper|copper|n.|铜
centimetres|centimetre|n.|厘米
spaceship|spaceship|n.|宇宙飞船；航天器
takeoff|takeoff|n.|起飞
foresee|foresee|v.|预见
Advisers|adviser|n.|顾问
distilled|distil|v.|提炼；浓缩
earthly|earthly|adj.|地球上的
abode|abode|n.|住所；家园
compendium|compendium|n.|汇编
greet|greet|v.|向……问候
listener|listener|n.|听者
rumble|rumble|n.|隆隆声
thunder|thunder|n.|雷声
whistle|whistle|n.|呼啸声
laughter|laughter|n.|笑声
rhythmic|rhythmic|adj.|有节奏的
heartbeat|heartbeat|n.|心跳
eclectic|eclectic|adj.|兼收并蓄的
a spectrum of|a spectrum of|名词短语|一系列；多种多样的
eras|era|n.|时代
notably|notably|adv.|尤其
array of|an array of|名词短语|一系列
encoded|encode|v.|编码
statesmen|statesman|n.|政治家
sleeve|sleeve|n.|唱片封套
guidance|guidance|n.|指引
diagram|diagram|n.|示意图
beacons|beacon|n.|信标
at|at|prep.|应（某人的请求）
request|request|n.|请求
pivoted|pivot|v.|转动
glance|glance|n.|一瞥
backwards|backwards|adv.|向后
frames|frame|n.|画面；帧
panorama|panorama|n.|全景
mosaic|mosaic|n.|拼接图
glimmer|glimmer|n.|微光
pixel|pixel|n.|像素
across|across|adv.|从一侧到另一侧；宽
receivers|receiver|n.|接收设备
signal|signal|n.|信号
pale|pale|adj.|暗淡的
perspective|perspective|n.|看待问题的视角
ephemeral|ephemeral|adj.|短暂的
cosmic|cosmic|adj.|宇宙的
vastness|vastness|n.|浩瀚；辽阔
interstellar|interstellar|adj.|恒星之间的
human-made|human-made|adj.|人造的
longevity|longevity|n.|长寿；长久持续
unmatched|unmatched|adj.|无可匹敌的
depletion|depletion|n.|耗竭
glide on|glide on|动词短语|继续滑行
outwards|outwards|adv.|向外
void|void|n.|虚空
messengers|messenger|n.|信使''',
'fastened|wrought|gilded|foresee|distilled|abode|compendium|eclectic|encoded|guidance|beacons|pivoted|panorama|mosaic|pixel|signal|perspective|ephemeral|interstellar|longevity|unmatched|depletion'.split('|'),
['foresee','compendium','encoded','ephemeral'],'如果有人找到这张唱片，会认识地球吗？',S+'\nSpecific scene: A close, scientifically restrained view of a Voyager-type deep-space probe, with its golden copper record and protective circular cover mounted on the side of the foil-wrapped instrument bus as the focal point. Show fine plain concentric grooves only on a small visible part of the disc, no engraved writing or diagrams. A cropped white high-gain antenna and delicate structural struts provide two quiet supporting shapes. The craft drifts in pale grey-sage cosmic distance dissolving into warm ivory, with a tiny muted blue Earth-like point far away, not aliens or a prediction of contact. Credible 1970s spacecraft materials, no solar panels, no logos, text, numbers, constellation maps, fabricated charts or radiating magical messages.',
'文中的信号需五个半小时，是从当时旅行者1号的位置到地球的单程时间。')
