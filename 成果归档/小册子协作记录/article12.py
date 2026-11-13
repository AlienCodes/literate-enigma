from group_01_12 import *
zh=[
'百事可乐曾在全美各地的购物中心设置摊位，请购物者小口品尝两种未标明品牌的饮料，并说出自己更喜欢哪一种。结果因地区而异，但品尝者总体上选择百事的次数更多。这些让消费者只凭味觉判断的摊位，同时也起着宣传作用。',
'可口可乐的测试既细致又广泛。近二十万次盲测显示，一种更甜的配方比原配方和百事更受欢迎。1985年4月23日，公司宣布，要更换使用了99年的糖浆配方，此时距它的百年诞辰只差一年。公众把这种汽水称为“新可乐”。甜味让它在口味比较中胜出，但推出这种调制饮料，却是一场冒险。',
'随之而来的是民众自发的强烈反对。消费者热线每天接到的电话，从约400通增至约1500通，几乎全是愤怒的投诉。抗议团体组织起来，一些忠实消费者开始囤积原版可乐。1985年6月，抗议者盖伊·马林斯提起诉讼，要求禁止新可乐使用与原版相似的包装。一周后，这项诉讼被驳回。',
'百事首席执行官把对手改换配方视为可口可乐的让步，给员工放了一天假。79天后，也就是1985年7月11日，原配方以“可口可乐经典”的名称重新上市。这次转向，让原配方的忠实拥护者觉得自己的坚持得到了证明。ABC电视台中断一部肥皂剧，播报原配方回归的消息；这条消息还成了两家电视网新闻节目的头条。',
'可口可乐误判了测试究竟衡量到了什么。测试捕捉到的是一小口饮料的味道，却没有测出近一个世纪的熟悉感所累积的情感依恋。对许多人而言，旧口味承载着怀旧情绪与传统。测试向每一位品尝者隐藏了品牌，因此无法量化：这个品牌对那些极其忠诚的消费者，究竟意味着什么。'
]
rows='''
booths|booth|n.|摊位；小亭
shoppers|shopper|n.|购物者
sip|sip|v.|小口喝；啜饮
unmarked|unmarked|adj.|未作标记的；未标品牌的
beverages|beverage|n.|饮料
preference|preference|n.|偏好；更喜欢的事物
tasters|taster|n.|品尝者
consumers|consumer|n.|消费者
palate|palate|n.|味觉；品味能力
publicity|publicity|n.|宣传；公众关注
thorough|thorough|adj.|全面细致的；彻底的
extensive|extensive|adj.|广泛的；覆盖面大的
formula|formula|n.|配方
syrup|syrup|n.|糖浆
centenary|centenary|n.|一百周年；百年纪念
soda|soda|n.|汽水
sweetness|sweetness|n.|甜味
flavour|flavour|n.|味道；口味
concoction|concoction|n.|调制品；混合饮料
wager|wager|n.|赌注；冒险之举
backlash|backlash|n.|强烈反对；反弹
grassroots|grassroots|adj.|基层的；普通民众自发的
outcry|outcry|n.|强烈抗议；公愤
hotline|hotline|n.|热线电话
furious|furious|adj.|极其愤怒的
complaints|complaint|n.|投诉；抱怨
Protest groups|protest group|n.|抗议团体
organised|organise|v.|组织；筹组
faithful|faithful|adj.|忠实的
lawsuit|lawsuit|n.|诉讼
dismissal|dismissal|n.|驳回（诉讼）
chief executive|chief executive|n.|首席执行官
employees|employee|n.|员工
concession|concession|n.|让步
relaunched|relaunch|v.|重新推出；重新上市
U-turn|U-turn|n.|彻底转向；政策大反转
vindication|vindication|n.|证明正确；获得认可
loyalists|loyalist|n.|忠实拥护者
interrupted|interrupt|v.|打断；中断
broadcast|broadcast|v.|播报；广播
comeback|comeback|n.|回归；复出
news bulletins|news bulletin|n.|新闻简报；新闻节目
misjudged|misjudge|v.|误判
mouthful|mouthful|n.|一口的量
emotional|emotional|adj.|情感的
attachment|attachment|n.|依恋；情感联系
familiarity|familiarity|n.|熟悉；熟悉感
nostalgia|nostalgia|n.|怀旧；对往昔的眷恋
heritage|heritage|n.|传统；传承下来的事物
quantify|quantify|v.|量化
fiercely|fiercely|adv.|强烈地；极其
loyal|loyal|adj.|忠诚的
'''
core=['unmarked','beverages','preference','palate','publicity','thorough','extensive','formula','wager','backlash','grassroots','outcry','faithful','lawsuit','dismissal','concession','relaunched','vindication','misjudged','attachment','nostalgia','quantify']
prompt=json.loads((ROOT/'illustrations/12.json').read_text())['prompt']
build('12',zh,rows,core,['extensive','wager','dismissal','misjudged'],'盲测胜出的新可乐，为什么遭到反对？','',prompt,{'unmarked':'two unmarked beverages','preference':'state a preference.','palate':'judge by palate alone','thorough':'thorough and extensive.','extensive':'thorough and extensive.','formula':'a sweeter formula','wager':'launching the concoction was a wager.','backlash':'The backlash was a grassroots outcry.','grassroots':'a grassroots outcry.','outcry':'a grassroots outcry.','faithful':'some faithful drinkers','lawsuit':'filed a lawsuit','dismissal':'Its dismissal came a week later.','concession':"Coke\'s concession.",'relaunched':'relaunched as Coca-Cola Classic.','vindication':'a vindication for loyalists.','misjudged':'misjudged what the tests measured.','attachment':'the emotional attachment','nostalgia':'nostalgia and heritage.','quantify':'could not quantify what it meant'})
print('12 content and illustration ready')
