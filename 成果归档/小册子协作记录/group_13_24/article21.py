from common import save,artwork
zh=[
'1925年，六名废金属商人在巴黎克里雍酒店秘密会面。邮电部的一名副总负责人私下告诉他们一则重大消息：埃菲尔铁塔将当作废铁出售。他邀请商人投标，并要求每个人郑重发誓保密，表面上的理由是避免引起公愤。',
'这个借口并不荒唐。铁塔为1889年世博会而建，原本计划二十年后拆除。那位位高权重的“副总负责人”其实是骗子维克多·卢斯蒂格，带有政府部门抬头的信笺也是伪造的。他曾在报上看到，当局抱怨铁塔维护费用高昂。',
'急于在巴黎站稳脚跟的商人安德烈·普瓦松中标。卢斯蒂格暗示，自己微薄的公务员薪酬需要补贴，普瓦松便又付了一笔贿赂。随后，卢斯蒂格带着到手的钱前往维也纳。',
'普瓦松被骗了钱，却因羞于报警而默默咽下损失。报纸上连关于这场骗局的一点风声都没有。',
'大约一个月后，卢斯蒂格竟又厚着脸皮回来，向新一批商人重演旧把戏。这一次，中标者起了疑心，前去报警。事情登上报纸，卢斯蒂格逃之夭夭。广为流传的“第二次卖成铁塔”，其实只是虚构故事。',
'后来，卢斯蒂格在美国因制造假币被捕。他从拘留处逃出，27天后再次落网，并在恶魔岛监狱服刑。1947年，他死于肺炎。',
'卢斯蒂格的两个行骗对象中，付了钱的那人守口如瓶，保住钱的那人反而报了警。'
]
v='''scrap-metal||adj.|废金属的|six scrap-metal traders
traders|trader|n.|商人；交易者|
secretly||adv.|秘密地|
deputy||adj.|副职的|
director-general||n.|总负责人；总局长|
momentous||adj.|重大的；影响深远的|
confidentially||adv.|私下地；保密地|confidentially
tenders|tender|n.|投标|He invited tenders'''
v+='''
solemnly||adv.|郑重地；严肃地|
vow||v.|发誓；郑重保证|solemnly vow secrecy
secrecy||n.|保密；秘密状态|
ostensibly||adv.|表面上；声称地|ostensibly to spare
public indignation||名词短语|公愤；公众愤怒|the public indignation
pretext||n.|借口；托词|The pretext was not absurd
absurd||adj.|荒唐的|
monument||n.|纪念建筑；纪念物|
originally||adv.|原本；最初|
destined|destined|adj.|原定的；注定的|destined to come down
come down||动词短语|被拆除；倒下|
high-ranking||adj.|高级别的；位高权重的|
crook||n.|骗子；不法之徒|a crook
ministerial||adj.|政府部门的；部级机关的|
stationery||n.|信笺；办公文具|ministerial stationery
forgery||n.|伪造品；伪造文件|was a forgery
lamented|lament|v.|哀叹；抱怨|
hefty cost||名词短语|高昂费用|
upkeep||n.|维护；保养|the tower's upkeep
businessman||n.|商人|
impatient||adj.|急切的；迫不及待的|
gain a foothold||动词短语|站稳脚跟；取得一席之地|gain a foothold in Paris
intimated|intimate|v.|暗示|Lustig intimated
civil-service||adj.|公务员的；文官的|
remuneration||n.|报酬；薪酬|civil-service remuneration
supplementing|supplement|v.|补充；补贴|
additional||adj.|额外的|
bribe||n.|贿赂；贿款|an additional bribe
takings||n.|到手的钱；收入|
Fleeced|fleece|v.|骗取钱财；敲竹杠|Fleeced and too ashamed
ashamed||adj.|羞愧的；感到丢人的|
quietly||adv.|默默地；不声张地|
whisper||n.|一点风声；耳语|
deceit||n.|欺骗；骗局|a whisper of the deceit
had the gall to|have the gall to|动词短语|竟敢厚着脸皮做……|had the gall to reappear
reappear||v.|再次出现|
encore||n.|重演；再来一遍|
script||n.|台词；既定说辞|
grew distrustful|grow distrustful|动词短语|起疑；变得不信任|the winner grew distrustful
affair||n.|事件；事情|
getaway||n.|逃脱；逃走|
much-repeated||adj.|被反复讲述的|
fairy tale||名词短语|童话；虚构故事|
fake||adj.|假的；伪造的|
detention||n.|拘留；羁押|broke out of detention
recaptured|recapture|v.|再次抓获|
served time|serve time|动词短语|服刑|
penal||adj.|刑罚的；监禁的|
kept mum|keep mum|动词短语|守口如瓶；保持沉默|the one who paid kept mum'''
qa=[
('The pretext was not absurd.','pretext'),
('The high-ranking deputy was Victor Lustig, a crook whose ministerial stationery was a forgery.','forgery'),
('Lustig intimated that his modest civil-service remuneration needed supplementing, and Poisson paid an additional bribe.','remuneration'),
("Of Lustig's two marks, the one who paid kept mum and the one who kept his money went to the police.",'kept mum')
]
save('21',zh,v,qa,'铁塔怎么成了骗子的“货物”？','标题里的“两次卖掉”是传说；原文明确，第二次骗局没有得手。')
artwork('21','/workspace/generated_images/exec-8d03cde2-abc2-4b6e-8477-7d5b52a39f19.png','实际图已看：两名1920年代衣着人物、无字文件与信封，远处单座埃菲尔铁塔；人物无嘲弄，手部和透视自然。','仅表现第一笔行骗交易；没有第二次成交或铁塔合法产权转移的画面。')
