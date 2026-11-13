from common import save,artwork
zh=[
'1636至1637年冬天，荷兰商人和经纪人聚在小酒馆里，交易还埋在土中的郁金香球茎合约。他们把这门投机生意称为windhandel，即“风中交易”。名贵的“碎色”郁金香花瓣带有条纹，价格一路飙升。',
'1637年2月初，在交易中心哈勒姆的一场买卖中，竟无人愿意出价。几天后，阿尔克马尔的一次拍卖仍有一只球茎售得5200荷兰盾——那是当时荷兰的货币，金额超过熟练工匠十年的工资。但狂热已经结束：价格暴跌，许多买家违约，未结清的合约越积越多。市场为何如此迅速转向，至今仍有争议。',
'两个世纪后，苏格兰记者查尔斯·麦凯在一本讨论群体性错觉的书中重述此事，将它描绘成全国性的狂热。在他的笔下，穷人富人都参与赌博，大商人几乎沦为乞丐，荷兰商业遭到重创。他生动的叙述使“郁金香狂热”成为不计后果的买入所催生的投机泡沫的代名词。',
'然而，档案呈现的规模要小得多。麦凯主要依据1637年那些讽刺贪婪、劝人戒贪的小册子来讲故事。伦敦国王学院历史学家安妮·戈德加仔细搜遍荷兰档案，只找到数百名交易者，大多是商人和工匠。她未找到因郁金香而破产的案例，也未发现经济遭受可衡量损害的证据。许多买家后来获准只支付原价的一小部分便结清合约，倾家荡产者寥寥无几。',
'这场热潮真实存在，却很短暂。真正广为传播、近四个世纪后仍在流传的，是其中的道德教训：一篇源于那些小册子的训诫，被麦凯当作历史重新讲述。'
]
v='''merchants|merchant|n.|商人|
brokers|broker|n.|经纪人；交易中介|merchants and brokers
taverns|tavern|n.|小酒馆|
contracts|contract|n.|合约；合同|contracts for tulip bulbs
tulip||n.|郁金香|
speculative||adj.|投机性的|a speculative business
streaked|streaked|adj.|带条纹的|
petals|petal|n.|花瓣|
soared|soar|v.|飙升；猛涨|soared
hub||n.|中心；枢纽|
bid||v.|出价；竞价|no one would bid
auction||n.|拍卖会|
fetched|fetch|v.|售得；拍出某价格|one bulb still fetched 5,200 guilders
currency||n.|货币|
wages|wage|n.|工资；工钱|
frenzy||n.|狂热|the frenzy was over
collapsed|collapse|v.|暴跌；崩落|Prices collapsed
defaulted|default|v.|违约；未履行付款义务|many buyers defaulted
unsettled||adj.|未结清的|
piled up|pile up|动词短语|堆积；越积越多|
swiftly||adv.|迅速地|
contested|contest|v.|受到争议或质疑|is still contested
journalist||n.|记者|
recounted|recount|v.|讲述；叙述|
episode||n.|事件；一段往事|
popular delusions|popular delusion|名词短语|群体性错觉；大众妄想|
hysteria||n.|群体性狂热|national hysteria
gambled|gamble|v.|赌博|
commerce||n.|商业；贸易|
reeled|reel|v.|遭受冲击；摇摇欲坠|
vivid||adj.|生动的；鲜明的|
mania||n.|狂热|
shorthand for||名词短语|……的代名词|shorthand for bubbles
bubbles|bubble|n.|投机泡沫|
reckless||adj.|不计后果的；鲁莽的|reckless buying
archives|archive|n.|档案；档案资料|the archives tell a smaller story
relied|rely|v.|依赖；依据|
on||prep.|表示依赖或依据的对象|
satirical||adj.|讽刺性的|satirical pamphlets
pamphlets|pamphlet|n.|小册子|satirical pamphlets
preached|preach|v.|宣扬；说教|
against||prep.|反对；抵制|
greed||n.|贪婪|
historian||n.|历史学家|
scoured|scour|v.|彻底搜寻；仔细查遍|scoured Dutch records
bankruptcy||n.|破产|no bankruptcy caused by tulips
measurable||adj.|可以衡量的|no measurable harm to the economy
harm||n.|损害|
economy||n.|经济|
settle||v.|结清；了结合约|settle their contracts
a||art.|不定冠词，表示一份或一部分|
fraction||n.|一小部分；分数|a small fraction of the price
of||prep.|……的|
boom||n.|繁荣；热潮|
fleeting||adj.|短暂的；转瞬即逝的|real but fleeting
circulates|circulate|v.|流传；传播|
moral||n.|寓意；道德教训|
sermon||n.|训诫；说教|'''
qa=[
('Prices collapsed, many buyers defaulted, and unsettled contracts piled up.','defaulted'),
('Why the market turned so swiftly is still contested.','contested'),
("Mackay's story relied largely on satirical pamphlets of 1637 that preached against greed.",'satirical'),
('She found no bankruptcy caused by tulips and no measurable harm to the economy.','measurable')
]
save('19',zh,v,qa,'郁金香真的让整个荷兰破产了吗？','“未找到破产或经济损害的证据”是档案研究的发现，不等于断言无人蒙受损失。')
artwork('19','/workspace/generated_images/exec-5514d927-996e-4da4-9274-387702a2ba7f.png','实际图已看：冬景窗外、四位17世纪衣着商人、无字合约与纸上的碎色郁金香图；人物手脸自然，无可读文字。','画的是有限范围的酒馆合约交易，不把后世的全民倾家荡产传说画成事实；未画冬季盛开花田或实际球茎交货。')
