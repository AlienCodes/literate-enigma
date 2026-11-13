from common import save,artwork
zh=[
'艾伦·图灵生于1912年6月，二十出头便展现出非凡才智。1936年11月宣读的一篇论文中，他提出“通用机器”的轮廓：只要给出正确指令，这种装置就能执行任何计算。这一植根于数理逻辑的抽象构想，后来成为现代计算机的理论蓝图。',
'1939年9月4日，图灵加入布莱切利园的机密破译工作，领导针对德国海军恩尼格玛加密机的研究。波兰数学家早在1932年底就已破译恩尼格玛，并于1939年7月向英国和法国分享了思路。图灵团队的机器借鉴这些成果，从1940年3月投入运行，将每天搜寻转子设置的繁重工作自动化。',
'1950年10月，图灵在哲学期刊《心灵》上提出一个发人深思的问题：“机器能思考吗？”他建议用一种实际可行的替代办法来讨论这个问题，即“模仿游戏”，如今通常称为图灵测试。提问者通过打字与两名隐藏的参与者交流，一方是人，另一方是机器。如果提问者无法稳定地区分二者，机器就算通过测试。',
'卓越的战时贡献并未保护图灵。1952年3月31日，他因“严重猥亵”罪被定罪，这是当时用来惩治男同性恋者的罪名。他失去接触机密资料的资格，并为避免入狱而接受激素注射。1954年6月7日，他死于氰化物中毒。验尸官的死因调查裁定为自杀，但有人对此存疑。',
'认可来得很迟。2009年9月10日，英国首相公开道歉；2013年12月24日，图灵获得身后皇家赦免。2021年6月23日，他生日当天，印有他肖像的50英镑纸币开始流通。曾经起诉他的国家，将他的面容印在了自己的货币上。'
]
v='''formidable||adj.|非凡的；强大的|
intellect||n.|才智；智力|a formidable intellect
outlined|outline|v.|概述；勾勒|
device||n.|装置；设备|
execute||v.|执行（指令或任务）|able to execute any computation
computation||n.|计算|able to execute any computation
abstract||adj.|抽象的|That abstract construct
construct||n.|理论构想；概念模型|That abstract construct
rooted in|be rooted in|动词短语|根源于；植根于|
mathematical||adj.|数学的|
logic||n.|逻辑|
theoretical||adj.|理论的|
blueprint||n.|蓝图；设计基础|the theoretical blueprint
classified||adj.|机密的；保密的|the classified codebreaking effort
codebreaking effort||名词短语|密码破译工作|
naval||adj.|海军的|
encryption||n.|加密|Germany's encryption machine
deciphered|decipher|v.|破译；解读|had deciphered Enigma
insights|insight|n.|深刻见解；关键思路|shared their insights
exploited|exploit|v.|利用；运用|
operational||adj.|投入运行的|operational from March 1940
automated|automate|v.|使自动化|automated the laborious search
laborious||adj.|费力耗时的|automated the laborious search
rotor||n.|转子|
philosophy||n.|哲学|
posed|pose|v.|提出（问题）|
provocative||adj.|发人深思的；引起争议的|a provocative question
proposed|propose|v.|提议；建议|
practical||adj.|切实可行的|
substitute||n.|替代办法；替代物|a practical substitute
widely||adv.|广泛地；普遍地|
interrogator||n.|提问者；询问者|
concealed|concealed|adj.|隐藏的|
consistently||adv.|稳定地；始终如一地|cannot consistently distinguish them
distinguish||v.|区分；辨别|cannot consistently distinguish them
exceptional||adj.|杰出的；非凡的|
wartime||adj.|战时的|
contribution||n.|贡献|
convicted of|be convicted of|动词短语|被判犯有……罪|he was convicted of
forfeited|forfeit|v.|丧失；被剥夺|He forfeited his security clearance
security clearance||名词短语|涉密资格；接触机密的许可|
avert||v.|避免；防止|to avert imprisonment
imprisonment||n.|监禁；入狱|
submitted to|submit to|动词短语|接受；屈从于|
hormone||n.|激素|
injections|injection|n.|注射|
cyanide poisoning||名词短语|氰化物中毒|
coroner||n.|验尸官|
suicide||n.|自杀|
Recognition|recognition|n.|认可；承认|
lagged|lag|v.|滞后；迟迟未到|
publicly||adv.|公开地|
apologised|apologise|v.|道歉|
was|be|aux.|构成过去时被动语态|
posthumously||adv.|在死后；身后地|posthumously granted
granted|grant|v.|授予；给予|
pardon||n.|赦免|a royal pardon
portrait||n.|肖像|
circulation||n.|（货币等的）流通|
prosecuted|prosecute|v.|起诉；提起公诉|'''
qa=[
('That abstract construct, rooted in mathematical logic, became the theoretical blueprint of the modern computer.','blueprint'),
("His team's machines exploited them and, operational from March 1940, automated the laborious search for each day's rotor settings.",'laborious'),
('If the interrogator cannot consistently distinguish them, the machine passes.','distinguish'),
('Turing was posthumously granted a royal pardon.','posthumously')
]
save('23',zh,v,qa,'图灵的贡献，为何没能保护他？','图灵测试是行为区分标准，不能直接等同于机器具有意识的证明。')
artwork('23','/workspace/generated_images/exec-839402f0-b5cc-423d-a182-1ee6c59a254d.png','实际图已看：木屋、机电转子柜、图灵与同事合作工作，手脸自然；转盘无可读字母数字，纸面无字；无现代屏幕或机器人。','这是战时破译工作的插画，不将机电破译柜混作1936年抽象通用机器；未画争议死因、毒苹果或机器有意识的事实主张。')
