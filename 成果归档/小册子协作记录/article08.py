from group_01_12 import *
zh=[
'1854年9月的头十天，霍乱在伦敦苏豪区一片人口过密的街区肆虐，500多人丧生。多数医生把流行病归因于瘴气，也就是污秽中产生的恶臭空气。医生约翰·斯诺自1849年起便确信，霍乱的致病物是被吞入人体，而不是随空气吸入；他因此怀疑宽街的公共水泵。',
'泵水中几乎没有肉眼可见的杂质，这让他一度犹豫。随后，他查阅死亡登记册，走访失去亲人的家庭。多数死者住在水泵附近，也喝过那里的水。在他的敦促下，教区官员拆下了泵柄；但在此之前，每天新发的致死病例数，就已经从高峰的143例骤降到12例。他后来才把死亡地点标在地图上。',
'1855年，临床医学教授埃德蒙·帕克斯把地图上的死亡聚集现象，解释成毒物在空气中飘散的结果。然而，地图只能记录人们死在哪里，并不能说明他们喝过什么。',
'真正关键的证据早在1854年就已收集到，存在于那些例外之中。周边街巷死亡接连发生，一所自备水井的济贫院，535名被收容者中却只有5人死亡。附近啤酒厂的70多名工人，既享有啤酒配给，也有自备水井，没有患上重症霍乱。',
'与之相反，汉普斯特德的一位寡妇，已经好几个月没有踏入苏豪区，却每天让人把宽街水泵的水用车运到家中。她去世了；来探望她、也喝了这些水的侄甥女，同样去世了。而汉普斯特德当时并没有流行霍乱。',
'1855年，政府的一次调查拒绝认定水泵应当负责，认为泵水充其量只是吸收了空气中的毒物。与此同时，原本持怀疑态度的助理牧师亨利·怀特黑德，着手寻找证据来驳倒斯诺，却发现喝过泵水的人，死于这种疾病的可能性远高于其他人，反倒印证了斯诺的判断。'
]
rows='''
ravaged|ravage|v.|肆虐；严重毁坏
overcrowded|overcrowded|adj.|人口过密的；过度拥挤的
upwards of|upwards of|phr.|超过
perished|perish|v.|丧生
attributed|attribute|v.|归因于
epidemics|epidemic|n.|流行病；疫情
to|to|prep.|与attribute连用，表示归因于
foul|foul|adj.|恶臭的；污浊的
arising|arise|v.|产生；源于
filth|filth|n.|污秽
physician|physician|n.|医生
convinced|convince|v.|使确信；此处指深信不疑
swallowed|swallow|v.|吞入
inhaled|inhale|v.|吸入
hesitated|hesitate|v.|犹豫
consulted|consult|v.|查阅
register|register|n.|登记册
bereaved|bereaved|adj.|失去亲人的
victims|victim|n.|受害者；此处指死者
urging|urging|n.|敦促；催促
parish|parish|n.|教区
fatal|fatal|adj.|致死的
plunged|plunge|v.|骤降
peak|peak|n.|峰值；最高点
clinical medicine|clinical medicine|n.|临床医学
interpreted|interpret|v.|解释；解读
cluster|cluster|n.|聚集；密集的一群
poison|poison|n.|毒物；毒素
drifting|drift|v.|飘散
chart|chart|v.|绘制；记录分布
crucial|crucial|adj.|至关重要的
lay in|lie in|phr. v.|在于；存在于
exceptions|exception|n.|例外
Amid|amid|prep.|在……之中
surrounding|surrounding|adj.|周围的
workhouse|workhouse|n.|济贫院
a mere|a mere|phr.|仅仅；区区
inmates|inmate|n.|被收容者
allowance|allowance|n.|配给；补助
Conversely|conversely|adv.|相反地；反过来
widow|widow|n.|寡妇
set foot in|set foot in|phr.|踏入
carted|cart|v.|用车运送
niece|niece|n.|侄女；外甥女
then|then|adv.|当时
inquiry|inquiry|n.|调查；官方调查
declined to|decline to|phr. v.|拒绝做……
condemn|condemn|v.|谴责；认定应负责任
contending|contend|v.|主张；坚持认为
absorbed|absorb|v.|吸收
airborne|airborne|adj.|经空气传播的
Meanwhile|meanwhile|adv.|与此同时
sceptical|sceptical|adj.|持怀疑态度的
set out to|set out to|phr. v.|着手去；打算去
refute|refute|v.|驳倒；反驳
succumb to|succumb to|phr. v.|死于（疾病）；屈服于
vindicating|vindicate|v.|证明……正确；印证
'''
core=['ravaged','attributed','foul','physician','convinced','consulted','bereaved','fatal','plunged','interpreted','cluster','crucial','exceptions','Conversely','inquiry','declined to','contending','airborne','sceptical','refute','succumb to','vindicating']
prompt=json.loads((ROOT/'illustrations/08.json').read_text())['prompt']
build('08',zh,rows,core,['fatal','cluster','crucial','Conversely'],'破解霍乱之谜，关键是地图还是饮水？','niece可指侄女或外甥女，原文未进一步区分，译文以“侄甥女”统称。',prompt,{'fatal':'daily fatal attacks','plunged':'had already plunged','exceptions':'lay in exceptions.','declined to':'declined to condemn the pump','succumb to':'succumb to the disease','airborne':'airborne poison.'})
print('08 content and illustration ready')
