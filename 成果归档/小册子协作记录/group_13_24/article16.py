from common import save,artwork
zh=[
'1909年7月，BASF公司的代表围在弗里茨·哈伯位于卡尔斯鲁厄的实验室工作台旁，看着一台矮壮的机器。在闪亮、用螺栓紧固的阀门后，氮与氢在极高压力和熔炉般的高温下反应，透明的氨液滴开始缓缓滴落。哈伯从空气中撬出了养分。',
'BASF的卡尔·博施将这一方法扩大到工业规模。1913年起，奥保的一座大型工厂开始批量生产氨。哈伯因“从空气中造面包”而广受赞誉，获得了令人向往的1918年诺贝尔奖。氨作为化肥被施入多石的土壤，以粪肥远不能及的能力抵御饥荒，带来丰收。到2008年，它已养活近半数人类。',
'哈伯的雄心也有阴暗的一面。尽管英国实施封锁，氨仍为德国军火库提供制造弹药所需的硝酸盐；而哈伯上尉则组织化学战。1915年4月22日，在伊普尔，德军向协约国战壕排放了约168吨黄绿色的有毒氯气，发动了首次大规模毒气攻击。',
'哈伯的妻子克拉拉·伊梅瓦尔是德国首位获得化学博士学位的女性，她曾反对他的工作。1915年5月2日，在为哈伯举行的庆祝活动之后，她在花园中用他的军用手枪自杀。次日，这位刚刚丧妻的人便前往东线。',
'声望并未给哈伯提供庇护。身为犹太裔，他在希特勒政权掌权后受到排斥，离开德国，1934年死于巴塞尔。他所在研究所的杀虫剂研究曾催生齐克隆；后来的变体齐克隆B被用于纳粹死亡营，他的一些亲属也死在这些营中。',
'我们体内蛋白质和DNA所含的氮，约有一半曾经过哈伯—博施工厂。因此，每个人的身体里都带着一点哈伯化学的痕迹。'
]
v='''envoys|envoy|n.|代表；使者|
squat||adj.|矮壮的；矮而宽的|
bench||n.|实验工作台|
gleaming|gleaming|adj.|闪亮的|
bolted|bolted|adj.|用螺栓紧固的|
valves|valve|n.|阀门|its gleaming, bolted valves
crushing||adj.|极高的；压倒性的|
furnace||n.|熔炉；高温炉|
transparent||adj.|透明的|
beads|bead|n.|液体小滴|
ammonia||n.|氨|transparent beads of ammonia
drip||v.|滴落|
slowly||adv.|缓慢地|
pried|pry|v.|撬出；费力取得|
nourishment||n.|养分；营养|pried nourishment from the air
from||prep.|从；由|
scaled|scale up|动词短语|扩大规模|scaled the method up
up||adv.|表示规模扩大|
gigantic||adj.|巨大的|
mass-produced|mass-produce|v.|批量生产|mass-produced ammonia
Hailed for|hail for|动词短语|因……而受到赞誉|
coveted|coveted|adj.|人人渴望得到的|the coveted 1918 Nobel Prize
Ploughed into|plough into|动词短语|翻耕埋入；施入土壤|
stony||adj.|多石的|
soils|soil|n.|土壤|
fertiliser||n.|化肥；肥料|as fertiliser
wards off|ward off|动词短语|抵御；防止|ammonia wards off famine
famine||n.|饥荒|ammonia wards off famine
manure||n.|粪肥|
heap||n.|堆；一堆|
abundance||n.|丰饶；充裕|bringing abundance
mankind||n.|人类|
ambition||n.|雄心；抱负|
sinister||adj.|险恶的；阴暗的|a sinister side
stocked|stock|v.|为……储备；充实|
arsenal||n.|军火库|Germany's arsenal
with||prep.|用；以（stock…with搭配）|
munitions|munitions|n.|弹药；军需品|nitrates for munitions
blockade||n.|封锁|despite a British blockade
marshalled|marshal|v.|统筹；组织调度|marshalled chemical warfare
vented|vent|v.|排放；释放气体|
greenish||adj.|略带绿色的|
poisonous||adj.|有毒的|
trenches|trench|n.|战壕|
onslaught||n.|猛烈攻击|the first large-scale gas onslaught
doctoral||adj.|博士学位的|
objections to|objection to|名词短语|对……的反对意见|voiced objections to his work
festivities|festivity|n.|庆祝活动|
pistol||n.|手枪|
widower||n.|鳏夫；丧妻的人|
Prestige|prestige|n.|声望；威望|
sanctuary||n.|庇护；避难所|Prestige offered no sanctuary
outcast||n.|被排斥的人|left Germany an outcast
regime||n.|政权|
seized|seize|v.|夺取；攫取|
pesticide||n.|杀虫剂；农药|His institute's pesticide research
variant||n.|变体|A later variant, Zyklon B
nitrogen||n.|氮|nitrogen and hydrogen met
proteins|protein|n.|蛋白质|
passed through|pass through|动词短语|经过；通过|'''
qa=[
('Behind its gleaming, bolted valves, nitrogen and hydrogen met at crushing pressure and furnace heat, and transparent beads of ammonia began to drip slowly.','ammonia'),
('Ploughed into stony soils as fertiliser, ammonia wards off famine as no manure heap could, bringing abundance.','fertiliser'),
("Haber's ambition had a sinister side.",'sinister'),
('Prestige offered no sanctuary.','sanctuary')
]
save('16',zh,v,qa,'同一种化学工艺，为何既能养人也能助战？','齐克隆B是后来的变体；文中未认定哈伯亲属的具体死因。')
artwork('16','/workspace/generated_images/exec-3a8b35ea-b19e-427c-913c-da5d67b1f454.png','已看实际图：高压金属容器、螺栓阀门、连接管、加热段与封闭接收器构成连贯装置；科学家手脸自然；麦穗作为制肥用途的编辑性提示，无字样或化学式。','聚焦1909年实验及粮食用途，不把空气直接变成面包画成事实；不混同合成氨、氯气攻击及后来齐克隆B变体的归属。')
