from common import save,artwork
zh=[
'1912年4月10日，豪华邮轮泰坦尼克号驶离南安普敦，开始首航。1911年，一本行业期刊曾将它和姊妹船称为“几乎不会沉没的船”。4月14日晚约11时40分，它撞上一座冰山；到次日凌晨2时20分，船已沉入海中，最终遇难人数超过1500。',
'坊间说法将灾难归咎于傲慢。然而，泰坦尼克号符合当时的法律。根据1894年的规定，英国海事监管机构按总吨位确定救生艇数量；总吨位衡量的是容积，并非重量。这套分级标准的上限，是对1万总吨及以上的船只要求配备16艘救生艇。泰坦尼克号约4.6万总吨，带了20艘，超过法定要求。但这些艇只能容纳1178人，约为船上2200人的一半：法律上足够，海上救生却不足。',
'在无线电通信范围内，加州人号轮船的值班惯例同样没有违规。船上唯一的报务员西里尔·埃文斯受雇于马可尼公司；他一休息，电台也随之无人值守。晚上约11时30分，他关掉了设备。事后看来，这或许可称为疏忽，但当时没有规定要求他保持值守，因此泰坦尼克号急切的求救信号在加州人号上无人听到。',
'1912年4月至7月，华盛顿和伦敦的调查听取了幸存者和加州人号船员的证词。同年7月，美国立法强制要求全天候无线电值守。1914年1月，13个国家的代表签署首部《海上人命安全公约》，规定救生艇座位必须足够全员使用、电台连续值守，并开展冰情巡逻。第一次世界大战使公约搁置，冰情巡逻却仍然开展起来。',
'这艘在劫难逃的邮轮不到三小时就沉没了。它所遵循的过时规定，却自1894年起一直照常施行；直到船上众多生命逝去，这些规定才失去了公信力。'
]
v='''opulent||adj.|豪华的；奢华的|the opulent liner Titanic
liner||n.|大型客轮；邮轮|
maiden voyage||名词短语|首航|on her maiden voyage
trade journal||名词短语|行业期刊|
dubbed|dub|v.|把……称为|had dubbed her and her sister ship
practically||adv.|几乎；实际上|
unsinkable||adj.|不会沉没的|
collided with|collide with|动词短语|与……相撞|she collided with an iceberg
iceberg||n.|冰山|
vanished|vanish|v.|消失|
death toll||名词短语|遇难人数|the death toll would surpass 1,500
surpass||v.|超过|
Folklore|folklore|n.|坊间流传的说法|
arrogance||n.|傲慢；自大|Folklore blames arrogance
compliant with||形容词短语|符合；遵守|was compliant with the law
maritime||adj.|海事的；海上的|
regulator||n.|监管机构|Britain's maritime regulator
pegged|peg|v.|使挂钩；按某标准确定|
to||prep.|与……（peg…to搭配）|
gross tonnage||名词短语|总吨位（衡量船内容积）|gross tonnage (volume, not weight)
scale||n.|分级标准；等级表|
topped out at|top out at|动词短语|最高达到；上限为|
exceeding|exceed|v.|超过|
requirement||n.|规定的要求|
capacity||n.|容纳人数；容量|Their capacity was 1,178
roughly||adv.|大约；大致|
sufficient||adj.|足够的|sufficient in law
inadequate||adj.|不足的；不够的|inadequate at sea
equally||adv.|同样地|
lawful||adj.|合法的；未违规的|
sole||adj.|唯一的|
wireless||adj.|无线电的|
operator||n.|操作员；报务员|
on the payroll of||介词短语|受雇于；领取……的薪酬|
switched off|switch off|动词短语|关掉（设备）|
Hindsight|hindsight|n.|事后认识；后见之明|Hindsight may call that negligence
negligence||n.|疏忽；失职|Hindsight may call that negligence
obliged|oblige|v.|强制；要求|no rule obliged him to stay vigilant
vigilant||adj.|警觉的；保持值守的|no rule obliged him to stay vigilant
frantic||adj.|慌乱而急切的|
distress calls|distress call|名词短语|求救呼叫；求救信号|
unheard||adj.|未被听见的|
testimony||n.|证词；证言|heard testimony from survivors
survivors|survivor|n.|幸存者|
legislation||n.|立法；法律|American legislation
round-the-clock||adj.|全天候的；不间断的|
compulsory||adj.|强制的；必须履行的|radio watch compulsory
delegates|delegate|n.|代表|
convention||n.|国际公约|Safety of Life at Sea convention
stipulating|stipulate|v.|规定；明确要求|stipulating lifeboat seats for all
continuous||adj.|连续的；不间断的|
patrol||n.|巡逻|
stalled|stall|v.|使暂缓；使停滞|
treaty||n.|条约|
regardless||adv.|尽管如此；仍然|
doomed||adj.|在劫难逃的|
outdated||adj.|过时的|
stayed afloat|stay afloat|动词短语|维持有效；继续存在（比喻）|
discredit||v.|使失去信誉；证明不可靠|to discredit them'''
qa=[
('Yet the Titanic was compliant with the law.','compliant with'),
('Their capacity was 1,178, roughly half the 2,200 aboard: sufficient in law, inadequate at sea.','inadequate'),
("Hindsight may call that negligence, yet no rule obliged him to stay vigilant, so the Titanic's frantic distress calls went unheard there.",'negligence'),
('That July, American legislation made round-the-clock radio watch compulsory.','compulsory')
]
save('15',zh,v,qa,'守法的泰坦尼克号，为何仍救不了所有人？','总吨位衡量容积；“没有违规”并不表示法律要求报务员关机。')
artwork('15','/workspace/generated_images/exec-8af1b1e9-5f17-4acc-8c2b-539c57bd775d.png','已看实际图：夜间平静海面、木质救生艇、吊艇架和1910年代衣着及浅色救生衣相合，人物自然，无字样。画面聚焦救生艇与邮轮规模，不含伤亡场面。','画面是对救生配置和救援反应的叙事呈现，不把旧法规画成撞冰原因，也未将加州人号的电台搬到泰坦尼克号。')
