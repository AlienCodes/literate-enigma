from group_01_12 import *
zh=[
'据说，围棋可能出现的局面，比宇宙中的原子还多，这给计算带来了艰巨挑战。2015年10月，DeepMind的AlphaGo达成了一项里程碑：成为首个在全尺寸棋盘上、不让子的条件下击败职业棋手的程序。2016年3月，在首尔一场电视转播的对决中，它的对手是拥有18项国际冠军头衔的韩国围棋高手李世石。',
'3月10日的第二局，AlphaGo第37手下出一记肩冲，也就是在对方棋子的斜对角相邻处落子。这一手落在从棋盘边缘数起的第五线上，很不合常规。解说员觉得这个出人意料的落点十分怪异，其中一人还以为它下错了。李世石离开对局室，暂停下来思考了十多分钟。',
'DeepMind的诊断工具显示，AlphaGo曾估计，人类下出这一手的概率只有万分之一，罕见得令人惊叹。AlphaGo起初学习模仿网上实力强劲的业余棋手，随后通过数千万盘模拟自我对弈磨砺棋力。李世石后来也认可了这一手的独创性与美感。',
'3月13日的第四局，双方的角色巧妙地对调了。李世石第78手扭转局势，许多职业棋手将其誉为“神之一手”。DeepMind团队估算，职业棋手找到这一手的可能性约为万分之一。AlphaGo以4比1取得压倒性胜利，李世石唯一的一胜，则给他带来了一丝安慰。',
'2019年11月，李世石退出职业棋坛，并将这次告别与人工智能无可匹敌的优势联系起来。他称人工智能是不可战胜的存在，表示自己已无法企及那个巅峰。然而，带来他唯一胜局的那一手，按照DeepMind的数据，人类找到它的概率，和下出AlphaGo那记大胆肩冲的概率一样渺茫。'
]
rows='''
configurations|configuration|n.|布局；局面
atoms|atom|n.|原子
daunting|daunting|adj.|艰巨的；令人望而生畏的
computational|computational|adj.|计算的
milestone|milestone|n.|里程碑
handicap|handicap|n.|让子；比赛中给对手的优势
opponent|opponent|n.|对手
televised|televise|v.|通过电视转播
showdown|showdown|n.|对决；决战
strategist|strategist|n.|战略家；善于布局的高手
tactic|tactic|n.|战术；招数
adjacent to|adjacent to|phr.|与……相邻的
diagonal|diagonal|n.|斜线；对角线方向
grid|grid|n.|网格；此处指棋盘格线
orthodox|orthodox|adj.|正统的；合乎常规的
unexpected|unexpected|adj.|出人意料的
placement|placement|n.|放置；此处指落子位置
bizarre|bizarre|adj.|怪异的；异乎寻常的
pause|pause|n.|暂停
deliberation|deliberation|n.|审慎思考；斟酌
diagnostic|diagnostic|adj.|诊断的；用于分析问题的
odds|odds|n.|概率；可能性
staggering|staggering|adj.|惊人的；令人震惊的
rarity|rarity|n.|罕见；罕见之事
imitate|imitate|v.|模仿
amateurs|amateur|n.|业余爱好者
sharpened|sharpen|v.|磨砺；提高（技艺）
simulated|simulated|adj.|模拟的
acknowledged|acknowledge|v.|承认；认可
originality|originality|n.|独创性
reversed|reverse|v.|颠倒；互换
neat|neat|adj.|巧妙的；恰到好处的
symmetry|symmetry|n.|对称；相互呼应
turned the tide|turn the tide|phr.|扭转局势
heralded|herald|v.|称赞；誉为
as|as|prep.|与herald连用，表示誉为
divine|divine|adj.|神妙的；此处指神之一手
computed|compute|v.|计算；估算
likelihood|likelihood|n.|可能性；概率
consolation|consolation|n.|安慰
overwhelming|overwhelming|adj.|压倒性的
withdrew from|withdraw from|phr. v.|退出；撤离
circuit|circuit|n.|职业巡回赛事；职业赛场
farewell|farewell|n.|告别
unrivalled|unrivalled|adj.|无可匹敌的
dominance|dominance|n.|主导地位；优势
invincible|invincible|adj.|不可战胜的
entity|entity|n.|实体；独立存在
summit|summit|n.|顶峰；巅峰
slim|slim|adj.|微小的；渺茫的（概率）
audacious|audacious|adj.|大胆的；敢于冒险的
'''
core=['configurations','daunting','computational','milestone','handicap','tactic','orthodox','bizarre','deliberation','diagnostic','odds','imitate','simulated','originality','symmetry','turned the tide','likelihood','consolation','overwhelming','unrivalled','invincible','audacious']
prompt=json.loads((ROOT/'illustrations/11.json').read_text())['prompt']
build('11',zh,rows,core,['milestone','bizarre','originality','consolation'],'两步万分之一的棋，为什么令人惊叹？','文中两次“万分之一”都是对人类选出某一步棋的概率估计，不是落下这步棋后的获胜概率。',prompt,{'configurations':'allow more configurations','daunting':'a daunting computational challenge.','computational':'a daunting computational challenge.','milestone':'reached a milestone','handicap':'without a handicap.','orthodox':'hardly orthodox.','deliberation':'pause for deliberation','diagnostic':"DeepMind\'s diagnostic tools",'odds':'the odds of a human playing that stone','imitate':'imitate strong amateurs online','simulated':'simulated games against itself.','originality':"the stone\'s originality and beauty.",'turned the tide':"Lee\'s 78th move turned the tide",'likelihood':"a professional\'s likelihood",'consolation':"Lee\'s only win was a consolation",'overwhelming':"AlphaGo\'s overwhelming 4–1 victory.",'unrivalled':"AI\'s unrivalled dominance.",'invincible':'AI an invincible entity','audacious':"AlphaGo\'s audacious shoulder hit."})
print('11 content and illustration ready')
