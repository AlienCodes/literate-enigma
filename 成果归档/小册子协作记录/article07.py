from group_01_12 import *
zh=[
'2016年初的一个夜晚，新西兰内皮尔国家水族馆的饲养员离开后，一只名叫Inky的章鱼从水箱顶部网罩的开口悄悄爬了出来。这名“逃脱者”大概先落到地板上，穿过房间，再把柔软而有弹性的身体挤进排水口；那里的管道长约50米，一直通向太平洋。',
'工作人员根据它留下的黏液痕迹，还原了这条可能的路线。Inky自2014年起便生活在圈养环境中；当时，一名渔民从内皮尔附近海域的捕虾笼中取出了它。这次出逃约三个月都没有见诸报道，直到2016年4月公开后，故事才传遍全球。',
'章鱼如此敏捷，得益于柔韧的身体：它没有骨骼，也没有外壳，唯一坚硬的部位是喙。所以，只要缝隙能容下喙，身体便能通过。章鱼约5亿个神经元中，大约三分之二分布在腕足里；腕足会处理感觉信息，并能在一定程度上自主作出反应。',
'它的智力与身体构造一样，表现出多样的能力。西雅图的一只巨型太平洋章鱼学会了打开螺旋盖罐子，最初需要15分钟，后来只需约两分钟。在2010年的一项研究中，章鱼逐渐学会区分两个原本陌生的人：一个给它们喂食，另一个拿硬毛棒碰它们。面对不同的人，它们会呈现不同的颜色和姿态。',
'2012年7月，《剑桥意识宣言》把章鱼列为具有支撑意识的神经基础的动物之一。2021年11月，英国政府的一份评估报告建议把它们视为有感知能力的动物；2022年4月，《动物福利（感知）法》也将它们纳入适用范围。然而，这些都不能证明章鱼拥有主观的内在体验。在管道另一头某处的Inky，依然对人们的这场争论一无所知。'
]
rows='''
keepers|keeper|n.|饲养员
crept|creep|v.|悄悄爬行
aperture|aperture|n.|开口；孔隙
mesh|mesh|n.|网；网罩
atop|atop|prep.|在……顶部
fugitive|fugitive|n.|逃脱者；逃亡者
presumably|presumably|adv.|据推测；大概
compressed|compress|v.|压缩；挤压
elastic|elastic|adj.|有弹性的
stretched|stretch|v.|延伸
reconstructed|reconstruct|v.|根据线索还原
slime|slime|n.|黏液
residue|residue|n.|残留物；痕迹
deposited|deposit|v.|留下；沉积
resided|reside|v.|居住；栖居
captivity|captivity|n.|圈养；囚禁状态
retrieved|retrieve|v.|取出；取回
crayfish pot|crayfish pot|n.|捕虾笼
breakout|breakout|n.|逃脱；越狱
unreported|unreported|adj.|未被报道的
globe|globe|n.|全球；世界
agility|agility|n.|敏捷；灵活
stems from|stem from|phr. v.|源于
pliable|pliable|adj.|柔韧的；易弯曲的
skeleton|skeleton|n.|骨骼
beak|beak|n.|喙
crevice|crevice|n.|窄缝；裂隙
accommodates|accommodate|v.|容纳
neurons|neuron|n.|神经元
limbs|limb|n.|肢体；此处指腕足
sensory input|sensory input|n.|感觉信息；感官输入
autonomy|autonomy|n.|自主性
wits|wits|n.|智力；机智
versatile|versatile|adj.|多才多能的；功能多样的
anatomy|anatomy|n.|身体构造
jars|jar|n.|罐子
at the outset|at the outset|phr.|起初
discriminate|discriminate|v.|区分；辨别
feeder|feeder|n.|喂食者
adopting|adopt|v.|采取；呈现
hue|hue|n.|颜色；色调
posture|posture|n.|姿态
possessing|possess|v.|具有；拥有
neurological|neurological|adj.|神经系统的
substrates|substrate|n.|活动所依托的物质基础
conscious|conscious|adj.|有意识的
awareness|awareness|n.|意识；觉察
sentient|sentient|adj.|有感知能力的
encompassed|encompass|v.|涵盖；纳入
inner|inner|adj.|内在的；内心的
wholly|wholly|adv.|完全地
oblivious|oblivious|adj.|对……毫不知情的
'''
core=['aperture','presumably','compressed','reconstructed','residue','captivity','agility','pliable','crevice','neurons','sensory input','autonomy','versatile','anatomy','discriminate','hue','posture','neurological','substrates','awareness','sentient','oblivious']
prompt=json.loads((ROOT/'illustrations/07.json').read_text())['prompt']
build('07',zh,rows,core,['reconstructed','agility','autonomy','oblivious'],'章鱼的聪明，等于拥有意识吗？','',prompt,{'sensory input':'handle sensory input','autonomy':'react with some autonomy.','substrates':'neurological substrates','awareness':'conscious awareness.','oblivious':'wholly oblivious to the debate.'})
print('07 content and illustration ready')
