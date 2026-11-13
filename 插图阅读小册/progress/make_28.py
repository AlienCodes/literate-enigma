import sys
sys.path.insert(0,'/workspace/work/booklet70/progress')
from group_25_36_work import save
save('28',[
'“523项目”是一项多家研究机构参与的秘密军事任务，名称来自启动日期：1967年5月23日。项目急需解决的是对氯喹产生耐药性的疟疾，当时这种疾病正削弱越南战争中的部队。1969年1月，尽管没有博士学位，也未在国外受过训练，屠呦呦仍受命领导所在研究所的研究组。',
'团队进行了全面搜寻，仔细翻检2000多份民间药方，汇编640个方剂，评估了来自约200种药用植物的约380种提取物。青蒿，也就是黄花蒿，时而显出效果，结果却不稳定。为寻找线索，屠呦呦重新翻阅古代文献。',
'公元340年前后，医师葛洪的手册建议取“一把浸在两升水中的青蒿”。这种做法不经煮沸。屠呦呦怀疑，提取过程中的高温会破坏某种不耐热的成分，于是改用乙醚：一种沸点约35摄氏度、容易挥发的溶剂。1971年10月4日，第191号样品完全抑制了感染小鼠体内的疟原虫。',
'小鼠身上有效，并不能说明对人体是否安全。1972年7月，为评估毒性，屠呦呦与两名同事自愿服下提取物。随后，8月至10月间，提取物用于海南21名疟疾患者；11月8日，团队取得了这种物质的纯净晶体，它后来被命名为青蒿素。',
'2011年9月，屠呦呦获拉斯克奖，评审团认为这种药物挽救了数百万人的生命。2015年10月5日，她获得当年诺贝尔生理学或医学奖的一半份额，成为首位中国女性诺贝尔奖得主。自2006年起，世卫组织指南就推荐以青蒿素为基础的多药联合疗法，对抗最致命的一类疟疾。葛洪那句话的关键，恰在于没有煮沸。'
],'''
covert|covert|adj.|秘密的；隐蔽的
military|military|adj.|军事的
mission|mission|n.|任务
urgent|urgent|adj.|紧迫的
resistant|resistant|adj.|有抗药性的
malaria|malaria|n.|疟疾
weakening|weaken|v.|削弱
troops|troop|n.|部队
Vietnam War|Vietnam War|专名|越南战争
entrusted with|entrust with|动词短语|受托承担；受命负责
despite|despite|prep.|尽管
doctorate|doctorate|n.|博士学位
exhaustive|exhaustive|adj.|全面彻底的
combed|comb|v.|仔细搜寻；翻检
folk|folk|adj.|民间的
compiled|compile|v.|汇编
prescriptions|prescription|n.|药方
 evaluated|evaluate|v.|评估
extracts|extract|n.|提取物
medicinal|medicinal|adj.|药用的
herbs|herb|n.|草药；药用植物
sweet wormwood|sweet wormwood|名词短语|黄花蒿
flashes|flash|n.|短暂显现
promise|promise|n.|有效的希望；前景
erratic|erratic|adj.|不稳定的；时好时坏的
clue|clue|n.|线索
revisited|revisit|v.|重新审阅
classical|classical|adj.|古代经典的
handbook|handbook|n.|手册
immersed in|immerse in|动词短语|浸在……中
litres|litre|n.|升
bypassed|bypass|v.|避开；略过
extraction|extraction|n.|提取
degrading|degrade|v.|降解；使成分受破坏
delicate|delicate|adj.|易受损的；此处指不耐热的
component|component|n.|成分
switched to|switch to|动词短语|改用
ether|ether|n.|乙醚
volatile|volatile|adj.|易挥发的
solvent|solvent|n.|溶剂
degrees Celsius|degree Celsius|名词短语|摄氏度
inhibited|inhibit|v.|抑制
parasite|parasite|n.|寄生虫；此处指疟原虫
infected|infected|adj.|受感染的
Efficacy|efficacy|n.|药效；效力
indicated|indicate|v.|表明；说明
assess|assess|v.|评估
toxicity|toxicity|n.|毒性
voluntarily|voluntarily|adv.|自愿地
Thereafter|thereafter|adv.|此后
administered to|administer to|动词短语|给……用药
patients|patient|n.|患者
obtained|obtain|v.|获得
crystals|crystal|n.|晶体
substance|substance|n.|物质
recipient|recipient|n.|获奖者
jury|jury|n.|评审团
Physiology|physiology|n.|生理学
laureate|laureate|n.|获奖者；此处指诺奖得主
guidelines|guideline|n.|指南
endorsed|endorse|v.|认可；推荐
combination|combination|n.|联合；合用
therapies|therapy|n.|疗法
deadliest|deadly|adj.|最致命的
 essence|essence|n.|关键；精髓
skipped|skip|v.|略过；省去
'''.replace('\n evaluated|','\nevaluated|').replace('\n essence|','\nessence|'),'resistant|entrusted with|exhaustive|combed|compiled|evaluated|extracts|erratic|extraction|degrading|component|volatile|solvent|inhibited|Efficacy|assess|toxicity|administered to|substance|endorsed|combination|essence',[
{'text_with_blank':'This ______ boiling.','answer':'bypassed'},
{'text_with_blank':'Efficacy in mice indicated nothing about human ______.','answer':'safety'},
{'text_with_blank':'In July 1972, to assess its ______, Tu and two colleagues voluntarily took the extract.','answer':'toxicity'},
{'text_with_blank':"The ______ of Ge Hong's line lay in the boiling it skipped.",'answer':'essence'}
],'古方里没有煮沸这一步，怎样启发了青蒿素研究？','Tu Youyou and one colleague at a modest Chinese research laboratory bench around 1971, thoughtfully examining sweet-wormwood leaves and a small unheated glass extraction flask containing pale herbal liquid. A neatly gathered sprig of Artemisia annua with fine divided leaves lies beside the flask. A second supporting detail is an old stitched Chinese medical handbook lying open but with absolutely blank, unlettered pages, suggesting a historical clue without fabricated writing. Tu wears a plain period pale lab coat, practical short dark hair, dignified calm concentration. Focal story is low-temperature extraction inspired by a method without boiling: no flame, no hot plate, no steaming pot, no triumphant miracle cure, no patients or self-dosing. Credible simple laboratory glassware with stoppered ether flask; no visible chemical labels or numbers. Ivory-and-sage editorial painting, not a generic scientist portrait.',overrides={
'resistant':'chloroquine-resistant malaria','entrusted with':'entrusted with leading','exhaustive':'In an exhaustive search','combed':'combed over 2,000 folk recipes','compiled':'compiled 640 prescriptions','evaluated':'evaluated about 380 extracts','extracts':'evaluated about 380 extracts','erratic':'its results were erratic','extraction':'heat during extraction','degrading':'was degrading a delicate component','component':'a delicate component','volatile':'a volatile solvent','solvent':'a volatile solvent','inhibited':'completely inhibited the parasite','Efficacy':'Efficacy in mice','assess':'to assess its toxicity','toxicity':'to assess its toxicity','administered to':'administered to 21 malaria patients','substance':'pure crystals of the substance','endorsed':'have endorsed artemisinin-based','combination':'combination therapies','essence':"The essence of Ge Hong's line"})
