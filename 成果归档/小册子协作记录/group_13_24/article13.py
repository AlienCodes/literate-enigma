from common import save
zh=[
'1963年12月28日，圣迭戈一所高中里，17岁的科学爱好者兰迪·加德纳为参加地区科学展，开始尝试不睡觉。每当他的精神松懈下来，两名同伴就尽力把他唤醒，并记录他的情绪。这项自愿开展的尝试后来获得了第一名。',
'斯坦福大学睡眠研究者威廉·德门特读到有关报道后产生了兴趣。他开车来到圣迭戈，协助海军研究员约翰·J.罗斯密切观察这名不眠的少年。随着缺觉程度逐步加重，两位研究者仔细记录着他状态的变化。',
'不良后果很快加剧。加德纳变得喜怒无常，注意力难以集中，短时记忆也受到损害。他开始多疑，有时甚至出现偏执妄想，还产生了幻觉。到第四天，他竟认定自己是一名职业美式橄榄球运动员。',
'1964年1月8日，加德纳结束了这场令人疲惫的挑战，历时264.4小时，约合11天零25分钟。之后，他酣睡约14小时，醒来时似乎恢复了精神。研究者在1965年的一篇学术论文中探讨了这个案例，使人们更加关注“微睡眠”：人会不由自主地短暂入睡，持续几秒钟。加德纳可能经历过这种短暂睡眠，自己却没有察觉。',
'1997年，吉尼斯世界纪录因健康风险停止监测此类挑战，此后仍有人声称自己保持清醒的时间更长。2017年接受采访时，加德纳说，严重失眠已折磨了自己约十年，他本人将其归咎于当年的实验。那个曾经看似睡个长觉便能从极度疲惫中恢复的少年，几十年后却几乎连打个盹都做不到。'
]
v='''enthusiast||n.|爱好者|a 17-year-old science enthusiast
forgo||v.|放弃；不享用|to forgo slumber
slumber||n.|睡眠|
regional||adj.|地区的；区域性的|
companions|companion|n.|同伴|
diligently||adv.|尽心尽力地|
jolted|jolt|v.|使猛然惊醒|
awake||adj.|醒着的|
alertness||n.|警觉；清醒程度|his alertness waned
waned|wane|v.|减弱；衰退|his alertness waned
mood||n.|情绪|
voluntary||adj.|自愿的|a voluntary endeavour
endeavour||n.|尝试；努力|a voluntary endeavour
take first place||动词短语|获得第一名|
coverage||n.|新闻报道|
intrigued|intrigue|v.|使感兴趣|was intrigued
assisted|assist|v.|协助；帮助|
in||prep.|在……方面（assist…in）|
sleepless||adj.|不眠的；未睡的|
closely||adv.|密切地|
investigators|investigator|n.|研究者；调查人员|
attentively||adv.|专注地；仔细地|
fluctuations|fluctuation|n.|波动；变化|the fluctuations in his state
deprivation||n.|剥夺；缺失|the deprivation progressively deepened
progressively||adv.|逐步地；不断地|
deepened|deepen|v.|加深；加重|
consequences|consequence|n.|后果|
mounted|mount|v.|增加；加剧|
moody||adj.|喜怒无常的|
concentration||n.|注意力；专注|lost concentration
short-term||adj.|短期的；短时的|
impaired|impair|v.|损害；使受损|short-term memory impaired
suspicious||adj.|多疑的；猜疑的|
paranoid||adj.|偏执多疑的；有妄想的|at times paranoid
hallucinate||v.|产生幻觉|began to hallucinate
gripped by|be gripped by|动词短语|被强烈情绪或想法控制|
delusion||n.|妄想；错误的确信|gripped by the delusion
wearying||adj.|令人疲惫的|
soundly||adv.|（睡得）熟；酣畅地|
refreshed|refreshed|adj.|恢复精神的|
probed|probe|v.|深入探究|
scholarly||adj.|学术的|
highlight||v.|使受到关注；凸显|
involuntary||adj.|不由自主的|involuntary lapses into sleep
lapses into|lapse into|动词短语|不由自主地陷入|
momentary||adj.|短暂的；瞬间的|
bouts|bout|n.|一阵；一段发作|
discontinued|discontinue|v.|停止；终止|discontinued monitoring such attempts
perils|peril|n.|危险；风险|because of the health perils
alleged|allege|v.|声称（尚未证实）|
stints|stint|n.|一段时间|
insomnia||n.|失眠|severe insomnia
tormented|torment|v.|折磨；使痛苦|had tormented him for about a decade
pinned the blame on|pin the blame on|动词短语|把责任归咎于|pinned the blame on the experiment
bounce back from||动词短语|从……中迅速恢复|bounce back from exhaustion
exhaustion||n.|精疲力竭|bounce back from exhaustion
barely||adv.|几乎不；勉强|
doze off||动词短语|打瞌睡；短暂入睡|'''
qa=[
('Two companions diligently jolted him awake whenever his alertness waned and logged his mood.','alertness'),
('The project, a voluntary endeavour, went on to take first place.','endeavour'),
('Gardner grew moody, lost concentration, and found his short-term memory impaired.','impaired'),
('He became suspicious, at times paranoid, and began to hallucinate.','hallucinate')
]
save('13',zh,v,qa,'十一天不睡觉，身体会怎样？','晚年失眠与当年实验的因果关系，文中并未证实。')
