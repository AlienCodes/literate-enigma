from common import save,artwork
zh=[
'2013年9月2日，一则消息传开：伦敦一座在建摩天大楼损坏了一辆捷豹轿车。马丁·林赛将车停在伊斯特奇普街的人行道旁，正对大楼临街立面。回来时，他发现后视镜翘曲、车身板件变形、车标也已扭曲。问题出在上方那面玻璃幕墙。',
'建筑师拉斐尔·维诺利将芬丘奇街20号的南立面设计成内凹曲面，以扩大租金较高的上层楼面。这种几何形状像放大镜一样，将阳光聚成一道亮度最高可达直射阳光六倍的光束。受照处测得约110摄氏度，一名记者甚至用反射光在平底锅里煎熟了鸡蛋。',
'开发商道歉，并赔付近1000英镑修理费。路边停车位被暂停使用，现场搭起临时屏障。受太阳仰角影响，强光每年出现两至三周，在这些日子每天照射约两小时。报纸把“对讲机大楼”戏称为“烤焦机大楼”，以此挖苦它。',
'建筑师坦率承认犯了许多错误。维诺利说，他预料到会聚光，却没有想到强度如此之大。据报道，原设计的遮阳百叶在削减成本时被删掉了。这也不是他的第一次建筑失算：2010年，他设计的拉斯维加斯维达拉酒店曲面反光墙产生刺眼强光，灼伤了泳池旁一位客人的头皮。',
'2014年2月12日，开发商公布一项永久装置方案：加装水平铝制鳍片，分散反光，据报费用达数百万英镑。2015年9月，《建筑设计》杂志的评论家将“烂疮杯”颁给这座声名狼藉的大楼，这是授予英国最差新建筑的奖杯。这次表决全体一致。'
]
v='''skyscraper||n.|摩天大楼|
under construction||介词短语|正在建设中|a London skyscraper under construction
saloon||n.|轿车（英式用法）|
pavement||n.|人行道（英式用法）|
frontage||n.|建筑正面；临街立面|
warped|warped|adj.|翘曲的；变形的|its wing mirror warped
deformed|deformed|adj.|变形的|its panels deformed
badge||n.|车标；徽章|
distorted|distorted|adj.|扭曲的；变形的|its badge distorted
glazed|glazed|adj.|镶玻璃的|
facade||n.|建筑立面；正面外墙|The glazed facade
enlarging|enlarge|v.|扩大|
storeys|storey|n.|楼层|
tenants|tenant|n.|租户|
premium||n.|溢价；额外支付的费用|tenants pay a premium
geometry||n.|几何形状；几何结构|That geometry acted
magnifying|magnify|v.|放大|
sunlight||n.|阳光|
beam||n.|光束|focusing sunlight into a beam
reporter||n.|记者|
pan||n.|平底锅|
reflection||n.|反射光；反射|using the reflection
developers|developer|n.|开发商|
apology||n.|道歉|
reimbursed|reimburse|v.|报销；赔付费用|reimbursed almost 1,000 pounds
suspended|suspend|v.|暂停使用；中止|
provisional||adj.|临时的；暂定的|a provisional barrier
barrier||n.|屏障；隔挡|
erected|erect|v.|搭建；竖起|a provisional barrier was erected
annually||adv.|每年|
angle of elevation||名词短语|仰角|
taunt||n.|嘲讽；挖苦|
architect||n.|建筑师|
candid||adj.|坦率的|The architect was candid
anticipated|anticipate|v.|预料；预期|had anticipated the focusing
intensity||n.|强度|not its intensity
Sun louvres|sun louvre|名词短语|遮阳百叶|
cost-cutting||n.|削减成本|removed in cost-cutting
architectural||adj.|建筑方面的|
miscalculation||n.|误算；失算|architectural miscalculation
infamous||adj.|臭名昭著的|
glare||n.|刺眼强光|the infamous glare
reflective||adj.|反光的|
scalp||n.|头皮|
permanent||adj.|永久的|
fixture||n.|固定装置|a permanent fixture
horizontal||adj.|水平的|
aluminium||adj.|铝制的|
fins|fin|n.|鳍片；薄片构件|
diffuse||v.|使分散；散射|to diffuse the brightness
brightness||n.|亮度|
critics|critic|n.|评论家|
notorious||adj.|声名狼藉的|
trophy||n.|奖杯|
ballot||n.|投票；表决|The ballot was unanimous
unanimous||adj.|全体一致的|The ballot was unanimous'''
qa=[
('That geometry acted like a magnifying glass, focusing sunlight into a beam up to six times brighter than direct sun.','geometry'),
('The developers issued an apology and reimbursed almost 1,000 pounds for repairs.','reimbursed'),
('Viñoly had anticipated the focusing, he said, but not its intensity.','intensity'),
('The ballot was unanimous.','unanimous')
]
save('22',zh,v,qa,'弯曲的玻璃墙，怎么会烤坏汽车？')
artwork('22','/workspace/generated_images/exec-fdef6c0d-e3a3-48d0-9f9b-6598c31571b1.png','实际图已看：伦敦街景、顶端较宽的玻璃塔楼、轿车后视镜轻微变形及局部自然反光；没有激光式实线、文字、车标或大面积熔化。','表现反射聚光损坏部件而非整辆车液化；没有把2014年才公布的散光装置提前画到2013事故现场。')
