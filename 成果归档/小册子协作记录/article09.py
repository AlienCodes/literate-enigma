from group_01_12 import *
zh=[
'在西澳大利亚州坎皮恩一带，多数农民是第一次世界大战的退伍军人；政府通过一项安置计划，让这些移民在一块块贫瘠农地上定居。他们缺少种植经验，已有四分之一放弃了耕作。1932年旱灾过后，约两万只鸸鹋从干旱地区成群涌入，践踏小麦庄稼。',
'农民的困境由此走向了军事解决。在绝望之中，一支由退伍士兵组成的代表团公开诉说不满，向国防部长请求机枪。部长答应了；派来的却不是一个营，而是一支小分队：炮兵军官梅雷迪思少校、两名士兵、两挺刘易斯机枪，以及一万发弹药。行动于1932年11月2日开始。',
'在一座水坝旁，约一千只鸸鹋接近伏击地点；但只打倒十来只，一挺机枪便卡了壳。鸟群散成灵活的小群，使一个个战术计划落空，卡车上架设的机枪也未能奏效。六天中低效的射击消耗了2500发子弹，可能只打死50至200只鸟，成效实在令人啼笑皆非。议会提出质询，报界加以嘲讽，部队于11月8日尴尬撤退，不过几天后便又恢复了射击。',
'梅雷迪思于12月10日被召回。他的备忘录列出的清单显示，9860发子弹打死986只鸟，相当于每只鸟耗费十发子弹。他把这些鸟顽强的抗击打能力比作坦克装甲。五个星期的战事，几乎没能削弱这些顽强鸟群的耐力。',
'此后，请求增援的恳求都遭到拒绝，军事干预让位于政府批准的悬赏制度。按每只鸟发放的赏金，既给农民提供了补偿，也成为扑杀鸸鹋的激励。1934年的六个月内，农民申领了五万七千多笔赏金，数量是梅雷迪思所报986只击杀数的五十七倍多。'
]
rows='''
veterans|veteran|n.|退伍军人
settlers|settler|n.|定居者；移民
marginal|marginal|adj.|贫瘠的；不适宜耕作的
parcels|parcel|n.|一块（土地）
farmland|farmland|n.|农地
inexperienced|inexperienced|adj.|缺乏经验的
growers|grower|n.|种植者
swarmed|swarm|v.|蜂拥而至
arid|arid|adj.|干旱的
in flocks|in flocks|phr.|成群地（尤指鸟）
trampled|trample|v.|践踏；踩坏
crops|crop|n.|庄稼；农作物
plight|plight|n.|困境；苦境
In desperation|in desperation|phr.|在绝望之中
delegation|delegation|n.|代表团
aired|air|v.|公开表达
grievances|grievance|n.|不满；委屈
machine-guns|machine-gun|n.|机枪
battalion|battalion|n.|营（军队编制）
detachment|detachment|n.|小分队；分遣队
artillery|artillery|n.|炮兵；火炮
ammunition|ammunition|n.|弹药
offensive|offensive|n.|进攻；攻势
ambush|ambush|n.|伏击；埋伏
jammed|jam|v.|卡住；卡壳
formation|formation|n.|队形
agile|agile|adj.|灵活的；敏捷的
frustrating|frustrate|v.|使受挫；使落空
tactical|tactical|adj.|战术的
futile|futile|adj.|徒劳的；无效的
wasteful|wasteful|adj.|浪费的
ludicrous|ludicrous|adj.|荒唐可笑的
parliamentary|parliamentary|adj.|议会的
ridicule|ridicule|n.|嘲笑；嘲讽
embarrassing|embarrassing|adj.|令人尴尬的
withdrawal|withdrawal|n.|撤退；撤离
memo|memo|n.|备忘录
inventory|inventory|n.|清单
ratio|ratio|n.|比例；比率
bullets|bullet|n.|子弹
likened|liken|v.|把……比作
resilient|resilient|adj.|顽强的；承受力强的
toughness|toughness|n.|坚韧；耐打程度
to|to|prep.|与liken连用，表示比作
armour|armour|n.|装甲
warfare|warfare|n.|战事；战争
hardy|hardy|adj.|顽强的；耐受力强的
endurance|endurance|n.|耐力；持久力
pleas|plea|n.|恳求
reinforcements|reinforcement|n.|增援部队；援兵
intervention|intervention|n.|干预；介入
gave way to|give way to|phr. v.|让位于；被……取代
bounty|bounty|n.|赏金；悬赏
sanctioned|sanction|v.|批准；准许
payout|payout|n.|支付的款项
compensation|compensation|n.|补偿；赔偿
incentive|incentive|n.|激励；诱因
extermination|extermination|n.|彻底消灭；扑灭
payments|payment|n.|支付款项
'''
core=['veterans','marginal','arid','plight','delegation','grievances','detachment','ammunition','ambush','agile','frustrating','futile','ludicrous','withdrawal','ratio','resilient','reinforcements','intervention','gave way to','bounty','compensation','incentive']
prompt=json.loads((ROOT/'illustrations/09.json').read_text())['prompt']
build('09',zh,rows,core,['plight','withdrawal','ratio','reinforcements'],'机枪为何没能解决鸸鹋危机？','',prompt,{'marginal':'on marginal parcels of farmland.','plight':"farmers\' plight",'agile':'small, agile groups','frustrating':'frustrating each tactical plan','futile':'proved futile.','resilient':"the resilient birds\' toughness",'gave way to':'intervention gave way to a bounty','incentive':'an incentive for extermination.'})
print('09 content and illustration ready')
