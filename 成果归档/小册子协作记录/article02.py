from group_01_12 import *
zh=[
'想象一下20世纪60年代末至70年代初，斯坦福大学校园里的一所幼儿园。一个四五岁的孩子独自坐在一份零食前，面对一个直截了当的选择：现在吃掉它，或者抵住诱惑，等上约15分钟，就能得到两份。冲动的孩子往往马上放弃等待，意志坚定的孩子则坚持下去。',
'后续追踪研究让这项测验广为人知。1990年发表于《发展心理学》的一项研究发现，进入青少年时期后，当初等得更久的孩子，往往在美国大学入学考试SAT中取得更高分数。一份不起眼的零食成了美德的象征，四岁时表现出的克制，也被过分推崇为预测人生走向的指标。',
'然而，这一结论的基础并不牢靠。进入SAT成绩分析的孩子只有几十名，而且主要是斯坦福大学教职员工和研究生的子女。这样一个背景相似、条件优越的群体，很难代表普通家庭。富裕的家庭环境，也可能同时有助于培养耐心和取得学业成功。',
'2018年5月发表于《心理科学》的一项研究进行了概念性重复实验：沿用同一研究思路，换用新的样本，并调整研究方法。研究者对来自不同背景的900多名儿童，在四岁半和15岁时分别进行了评估。未经调整的关联强度，大约只有早期研究结果的一半；进一步控制家庭背景和早期认知能力的影响后，这种关联又缩小了约三分之二，大多数估计结果都未达到统计显著性。',
'这项测验并非毫无价值，它或许仍能反映一些有实质意义的信息。2013年1月发表于《认知》的一项研究补充了背景：刚刚遭遇成年人失信的孩子，等待时间明显短于与守信成年人相处的同龄人。孩子能坚持多久，部分取决于他们觉得身边的大人有多可信。'
]
rows='''
nursery school|nursery school|n.|幼儿园
campus|campus|n.|大学校园
in solitude|in solitude|phr.|独自；独处地
blunt|blunt|adj.|直截了当的
bargain|bargain|n.|交易；约定的条件
resist|resist|v.|抵挡；忍住
temptation|temptation|n.|诱惑
earn|earn|v.|挣得；赢得
Impulsive|impulsive|adj.|冲动的
surrender|surrender|v.|放弃抵抗；屈服
instantly|instantly|adv.|立即；马上
resolute|resolute|adj.|意志坚定的
hold out|hold out|phr. v.|坚持下去
Follow-ups|follow-up|n.|后续追踪研究
legendary|legendary|adj.|广为传颂的；著名的
adolescents|adolescent|n.|青少年
attain|attain|v.|达到；取得
trivial|trivial|adj.|微不足道的
snack|snack|n.|零食
emblem|emblem|n.|象征；标志
virtue|virtue|n.|美德
restraint|restraint|n.|克制；自制
glorified|glorify|v.|过分美化；推崇
predictor|predictor|n.|预测因素；预测指标
destiny|destiny|n.|命运；人生走向
foundation|foundation|n.|（结论的）基础
precarious|precarious|adj.|不稳固的；不可靠的
a few dozen|a few dozen|phr.|几十个
predominantly|predominantly|adv.|主要地；大多
faculty|faculty|n.|大学全体教员
postgraduate|postgraduate|adj.|研究生的
homogeneous|homogeneous|adj.|同质的；背景相似的
privileged|privileged|adj.|享有优越条件的
scarcely|scarcely|adv.|几乎不
ordinary|ordinary|adj.|普通的
prosperous|prosperous|adj.|富裕的
foster|foster|v.|培养；促进
alike|alike|adv.|同样地；两者都
conceptual|conceptual|adj.|概念层面的
replication|replication|n.|重复研究；重复实验
modified|modify|v.|修改；调整
youngsters|youngster|n.|儿童；少年
diverse|diverse|adj.|多种多样的
assessed|assess|v.|评估
link|link|n.|关联；联系
Adjusting for|adjust for|phr. v.|控制……的影响
cognitive|cognitive|adj.|认知的
statistically|statistically|adv.|在统计学上
insignificant|insignificant|adj.|未达统计显著性的
worthless|worthless|adj.|毫无价值的
reflect|reflect|v.|反映
substantive|substantive|adj.|有实质意义的
context|context|n.|背景；具体情境
betrayed|betray|v.|辜负；背弃
markedly|markedly|adv.|明显地
peers|peer|n.|同龄人
perseveres|persevere|v.|坚持；不放弃
depends|depend|v.|取决于（常与on连用）
on|on|prep.|与depend连用，表示取决于
trustworthy|trustworthy|adj.|可信赖的
'''
core=['resist','temptation','Impulsive','surrender','resolute','hold out','legendary','restraint','glorified','predictor','precarious','homogeneous','privileged','foster','replication','diverse','assessed','Adjusting for','cognitive','insignificant','betrayed','trustworthy']
prompt=json.loads((ROOT/'illustrations/02.json').read_text())['prompt']
build('02',zh,rows,core,['resolute','precarious','insignificant','trustworthy'],'一颗棉花糖能预测孩子的未来吗？','“统计上不显著”不等于已经证明不存在关联；这里强调，计入背景差异后，早期结论的支持力度明显减弱。',prompt,{'foster':'foster patience and academic success','homogeneous':'a homogeneous, privileged group','privileged':'a homogeneous, privileged group','cognitive':'early cognitive ability','betrayed':'trust an adult had just betrayed'})
print('02 content and illustration ready')
