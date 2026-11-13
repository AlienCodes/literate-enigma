from common import save,artwork
zh=[
'1914年12月5日，坚忍号驶离偏远的捕鲸据点南乔治亚岛，前往南极威德尔海。1915年1月，海冰困住了船。10月27日，船体受压变形，众人弃船；11月21日，坚忍号沉没，船长弗兰克·沃斯利记下了沉没地点。',
'自弃船起，被困的人们在冰上熬过五个多月的艰苦日子。1916年4月9日，他们脚下的浮冰裂开。4月15日，救生艇抵达象岛，那是一座荒凉、无人居住、远离航线的岩岛。',
'4月24日，沙克尔顿和另外五人登上单薄的救生艇詹姆斯·凯尔德号，开始约1300公里的危险航程。猛烈大风不断冲击小艇，沃斯利只抓住四次机会观测太阳定位，其余时间靠航向、航速和经过的时间作航位推算。5月10日，他们登上南乔治亚岛空无一人的南岸。',
'沙克尔顿、沃斯利和汤姆·克林用了约36小时，艰苦横越岛上多山的腹地，于5月20日抵达斯特罗姆内斯捕鲸站。浮冰逼退了三次救援尝试，直到8月30日，智利拖船耶乔号才将象岛上受困的22人接走。坚忍号这一队的28人全都挺过磨难、生还归来。',
'2022年3月5日，搜寻者在3008米深的海底发现沉船，它保持正立，完好无损。沉船位于沃斯利在1915年11月记录的位置以南约四英里；那是小艇求援航程开始前几个月记下的位置。在漂移冰面上完成的计算只有这点偏差，已属难得。',
'后世因沙克尔顿的个人感召力称颂他，确有道理。但故事的前后两端，都取决于沃斯利一丝不苟的计算。领导力让28人团结在一起，精确计算则让六人登岸，进入可以求援的范围；一个世纪后，又让他们的船重新进入世人的视野。'
]
v='''departed|depart|v.|驶离；离开|
remote||adj.|偏远的|
whaling||n.|捕鲸|
outpost||n.|偏远据点；前哨站|
for||prep.|前往；开往|
trapped|trap|v.|困住|
vessel||n.|船舶|
hull||n.|船体|her hull buckling
buckling|buckle|v.|受压弯曲；变形|her hull buckling
abandoned|abandon|v.|弃船；放弃|
foundered|founder|v.|沉没|foundered on 21 November
logged|log|v.|记入航海日志|
stranded|stranded|adj.|受困的；滞留的|The stranded men
endured|endure|v.|忍受；熬过|
gruelling||adj.|艰苦难熬的|over five gruelling months
floe||n.|浮冰块|Their floe split
lifeboats|lifeboat|n.|救生艇|
bleak||adj.|荒凉的；凄冷的|a bleak, uninhabited rock
uninhabited||adj.|无人居住的|
shipping lanes|shipping lane|名词短语|航线|
embarked|embark|v.|登船；启程|embarked in the James Caird
in||prep.|表示所乘的船|
fragile||adj.|单薄易损的；脆弱的|
on||prep.|表示所踏上的航程|
perilous||adj.|危险重重的|a perilous voyage
voyage||n.|航程；航海|
ferocious||adj.|猛烈的；凶猛的|As ferocious gales
gales|gale|n.|大风；强风|
battered|batter|v.|反复猛击|
snatched|snatch|v.|抓住机会；匆忙取得|
sights of the sun|sight of the sun|名词短语|观测太阳以确定位置|
deducing|deduce|v.|推算；推断|deducing the rest
dead reckoning||名词短语|航位推算，按航向等估计位置|by dead reckoning
course||n.|航向|
time elapsed||名词短语|经过的时间|
landed on|land on|动词短语|在……登陆；登上|
deserted|deserted|adj.|空无一人的|
traversed|traverse|v.|横越；穿过|traversed its mountainous interior
mountainous||adj.|多山的|
interior||n.|腹地；内部|
exhausting||adj.|令人筋疲力尽的|
repelled|repel|v.|逼退；阻退|Ice repelled three rescue attempts
rescue attempts|rescue attempt|名词短语|救援尝试|
tug||n.|拖船|
evacuated|evacuate|v.|撤出；疏散|evacuated the 22 marooned men
marooned|marooned|adj.|困在荒岛上的|evacuated the 22 marooned men
ordeal||n.|磨难；严酷考验|survived their ordeal
located|locate|v.|找到；确定位置|
wreck||n.|沉船残骸|
upright||adj.|正立的；直立的|
intact||adj.|完好无损的|upright and intact
discrepancy||n.|偏差；差异|a slight discrepancy
calculation||n.|计算|
shifting|shifting|adj.|漂移的；不断移动的|
rightly||adv.|理所应当地；有道理地|
salutes|salute|v.|称颂；致敬|
charisma||n.|个人魅力；感召力|for his charisma
hinge on||动词短语|取决于|hinge on Worsley's
meticulous||adj.|一丝不苟的；细致的|Worsley's meticulous arithmetic
arithmetic||n.|算术；计算|
Leadership|leadership|n.|领导力|
held|hold|v.|使保持；使团结|
together||adv.|在一起；团结一致|
Precision|precision|n.|精准；精确性|
ashore||adv.|上岸；在岸上|
brought|bring|v.|使进入视野；带来|
back||adv.|重新；返回|'''
qa=[
('On 27 October, her hull buckling, the men abandoned ship.','buckling'),
('deducing the rest by dead reckoning from course, speed, and time elapsed.','dead reckoning'),
('She lay about four miles south of the spot Worsley recorded in November 1915, months before the voyage: a slight discrepancy for a calculation on shifting ice.','discrepancy'),
("Yet both ends of the story hinge on Worsley's meticulous arithmetic.",'meticulous')
]
save('24',zh,v,qa,'冰海中的精确计算，怎样换来生路？','28人指坚忍号这一队；1915年记录的沉船位置早于1916年的求援航程。')
artwork('24','/workspace/generated_images/exec-41bac96a-1efe-4bbc-bd1a-98af3895ce53.png','实际图已看并数人：艇内六名男子，前景沃斯利持六分仪、旁边同伴协作；帆布低覆小艇、厚衣帽和海况相合，云间仅小片日光，无字。','仅画1916年六人小艇求援导航，不将全28人塞进小艇；没有混入1915年沉船定位或2022年海底发现的画面，也未把观测条件画成全程晴朗。')
