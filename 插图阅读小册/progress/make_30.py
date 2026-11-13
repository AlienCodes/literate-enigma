import sys
sys.path.insert(0,'/workspace/work/booklet70/progress')
from group_25_36_work import save
save('30',[
'1858年夏天酷热难耐。新议会大厦的窗帘浸了含氯漂白粉，沉甸甸地垂着，只为让空气勉强可以忍受。泰晤士河腐败发臭，议员们考虑搬离。',
'这条河已成伦敦的厕所。老旧下水道和排污口，把约300万市民未经处理的污水排进河中，粪便在暑热中沤积、腐烂。恶臭强烈得令人无法忍受，这场事件因此有了一个名字：“大恶臭”。',
'7月15日，财政大臣本杰明·迪斯雷利替这份厌恶发了声，公开斥责河流是一潭地狱般、恐怖得让人无法忍受的污水。为新下水道拨款的法案加速审议，约18天便成为法律。',
'工程师约瑟夫·巴泽尔杰特主持设计这套应对工程。82英里坚固的截流下水道，在污水流入河中之前将其截住，改道向东，送往城市下游。约1100英里的街道下水道汇入这套系统，整项基础设施用了3.18亿块砖。他算出各条管道所需的内径后，又将直径加倍。系统主干埋在当时新建的维多利亚、阿尔伯特和切尔西河堤之下。管网到1875年基本建成，大部分至今仍在使用。',
'然而，这项公共卫生工程建立在一个错误观念之上。当时占主导的“瘴气说”把疾病归因于污浊空气与蒸气，因此修下水道主要是为了压住臭味。它们却因另一个并非设计初衷的原因而奏效：保护了伦敦人的饮用水水质。',
'1866年霍乱再次出现，在伦敦东区夺走约5600条生命；那里正是唯一尚未接入管网的地区。',
'原本冲着鼻子去的补救措施，保护的却是肠胃。'
],'''
fierce heat|fierce heat|名词短语|酷热
Houses of Parliament|Houses of Parliament|专名|英国议会大厦
lime|lime|n.|石灰；文中为含氯漂白剂成分
bleach|bleach|n.|漂白剂
tolerable|tolerable|adj.|可忍受的
festered|fester|v.|腐败发臭
contemplated|contemplate|v.|考虑
lavatory|lavatory|n.|厕所
Antiquated|antiquated|adj.|陈旧过时的
outlets|outlet|n.|排污口
discharged|discharge|v.|排放
untreated|untreated|adj.|未经处理的
sewage|sewage|n.|污水
dwellers|dweller|n.|居民
currents|current|n.|水流
excrement|excrement|n.|粪便
stewed|stew|v.|在闷热中沤积
decayed|decay|v.|腐败；腐烂
vile|vile|adj.|恶心的；恶劣的
fumes|fume|n.|难闻的气体
overpowering|overpowering|adj.|强烈得难以忍受的
episode|episode|n.|事件；一段经历
Stink|stink|n.|恶臭
Disgust|disgust|n.|厌恶
Chancellor of the Exchequer|Chancellor of the Exchequer|专名|英国财政大臣
denounced|denounce|v.|公开斥责
as|as|prep.|是；引出斥责中的定性
hellish|hellish|adj.|地狱般的
unbearable|unbearable|adj.|难以忍受的
bill|bill|n.|法案
fast-tracked|fast-track|v.|加速办理；加快审议
masterminded|mastermind|v.|主持策划
stout|stout|adj.|坚固的
intercepting sewers|intercepting sewer|名词短语|截流下水道
short of|short of|介词短语|在到达……之前
diverted|divert|v.|使改道
downstream|downstream|adv.|向下游
tributaries|tributary|n.|支流；汇入主干的支管
infrastructure|infrastructure|n.|基础设施
bricks|brick|n.|砖块
adequate|adequate|adj.|足够的
calibre|calibre|n.|管道内径
doubled|double|v.|使加倍
backbone|backbone|n.|主干
buried|bury|v.|埋在地下
underneath|underneath|prep.|在……下面
newly|newly|adv.|新近地
Substantially|substantially|adv.|基本上；大体上
in use|in use|介词短语|在使用中
sanitation|sanitation|n.|公共卫生设施
rested on|rest on|动词短语|建立在……之上
fallacy|fallacy|n.|错误观念；谬误
predominant|predominant|adj.|占主导的
belief|belief|n.|观念；看法
foul air|foul air|名词短语|污浊空气
vapours|vapour|n.|蒸气
principally|principally|adv.|主要地
suppress|suppress|v.|压制；消除
unintended|unintended|adj.|非本意的；未预期的
purity|purity|n.|洁净
resurfaced|resurface|v.|再次出现
locality|locality|n.|地区
aimed at|aim at|动词短语|针对；旨在改善
gut|gut|n.|肠胃
''','tolerable|Antiquated|discharged|untreated|sewage|denounced|bill|fast-tracked|masterminded|intercepting sewers|diverted|infrastructure|adequate|calibre|sanitation|fallacy|predominant|suppress|unintended|purity|resurfaced|aimed at',[
{'text_with_blank':'The engineer Joseph Bazalgette ______ the response.','answer':'masterminded'},
{'text_with_blank':'Having calculated an adequate calibre for each pipe, he ______ it.','answer':'doubled'},
{'text_with_blank':'Yet that sanitation rested on a ______.','answer':'fallacy'},
{'text_with_blank':'A remedy ______ the nose protected the gut.','answer':'aimed at'}
],'下水道本为消除臭味，为什么还能减少疾病？','A mid-nineteenth-century London riverside engineering scene showing construction of a substantial red-brick intercepting sewer beneath a new Thames embankment. A clearly readable open brick arch and short exposed section of the tunnel run PARALLEL to the river into the distance, conveying diversion along the riverbank rather than dumping sewage straight into the nearby river. One dignified Victorian engineer in a plain dark coat inspects the wide arch beside a small stack of bricks; his partly rolled plan is entirely blank and unlettered. The Thames and softly suggested Parliament buildings sit beyond the embankment as supporting context. Focal point is the generous brick-lined tunnel and practical infrastructure response, not a portrait or a disgusting sewage close-up. No arrows, cutaway labels, invented maps, green stink clouds, disease symbols or graphic filth. Warm ivory sky, muted sage river, dusty terracotta bricks.',overrides={
 'tolerable':'to make the air tolerable','Antiquated':'Antiquated sewers and outlets','discharged':'discharged the untreated sewage','untreated':'the untreated sewage','sewage':'the untreated sewage','denounced':'denounced the river','bill':'A bill funding new sewers','fast-tracked':'fast-tracked into law','masterminded':'masterminded the response','intercepting sewers':'stout intercepting sewers','diverted':'diverted it east','infrastructure':'the infrastructure took','adequate':'an adequate calibre','calibre':'an adequate calibre for each pipe','sanitation':'that sanitation rested on a fallacy','fallacy':'rested on a fallacy','predominant':'The predominant belief','suppress':'to suppress the smell','unintended':'an unintended reason','purity':'the purity of the water','resurfaced':'Cholera resurfaced in 1866','aimed at':'A remedy aimed at the nose'})
