from common import save,artwork
zh=[
'1991年9月19日，两名德国徒步者在奥茨塔尔阿尔卑斯山远足时，于冰川旁发现一具遗体。它位于奥地利与意大利交界处、海拔约3210米的山脊上。人们最初以为，一名现代登山者死在高山坡地上，毕竟冰川有时会吐露冰冻的遗骸。',
'救援人员以为这是近期的死亡事件，使用风钻凿冰，结果撕损了死者左侧髋部的皮肉。但他的随身物品讲述了另一种故事：皮革和草编衣物、铜斧、弓箭，全是史前器物。这具被称为奥茨的天然木乃伊是一名男子，生活于约5300年前，即公元前3350至前3105年之间。',
'2001年，X光检查发现一枚燧石箭头嵌在他的左肩里，十年前的检查者并未发现它。扫描显示，穿刺伤撕裂了一条动脉，造成大量出血的致命损伤，并留下一个大血块。研究者认为，他在几分钟内便死亡，当时约46岁。',
'人们认为，他是遭人杀害的。研究者根据伤口深度推断，弓箭手从他背后约30米处射箭，很可能是在他毫无防备时出手。2018年的研究发现，他最后吃过干野山羊肉和脂肪、马鹿肉与单粒小麦。这是一顿丰盛而营养丰富的饭，据报道在死前两小时内吃下。',
'如今，博尔扎诺的馆藏保管人员保存着奥茨的遗体。他关节和脊柱上的61处文身，也许是一种早期针灸形式。弓箭手的身份仍是谜团，任何作案动机都只是猜测。奥茨有名字、最后一餐和死因；对于那名身份不明的凶手，我们却连这些信息都不知道。'
]
v='''hikers|hiker|n.|徒步者|
trek||n.|长途徒步；远足|
corpse||n.|尸体；遗体|
glacier||n.|冰川|a corpse by a glacier
ridge||n.|山脊|on a ridge at about 3,210 metres
border||n.|边界；交界处|
assumption||n.|假定；最初的判断|The assumption was
modern-day||adj.|现代的；当代的|
climber||n.|登山者|
alpine||adj.|高山的；阿尔卑斯山的|
slope||n.|山坡；斜坡|
jackhammer||n.|风钻；气动破碎工具|
ripped|rip|v.|撕裂；扯下|
flesh||n.|皮肉；肌肉组织|
hip||n.|髋部|
possessions|possession|n.|随身物品；所有物|His possessions told another story
leather||n.|皮革|
copper||adj.|铜制的|
axe||n.|斧子|
prehistoric||adj.|史前的|all prehistoric artefacts
artefacts|artefact|n.|人工制品；考古器物|all prehistoric artefacts
mummy||n.|木乃伊；保存下来的干尸|the natural mummy
flint||n.|燧石|a flint arrowhead
lodged|lodge|v.|嵌入；卡住|lodged in his left shoulder
unseen||adj.|未被看见或发现的|
by||prep.|被；由|
examiners|examiner|n.|检查人员|
scanner||n.|扫描仪|
puncture||n.|穿刺伤；刺孔|the puncture had ruptured an artery
ruptured|rupture|v.|使破裂；撕裂|had ruptured an artery
mortal||adj.|致命的|a mortal injury
bleeding||n.|出血|
clot||n.|血块|
it is thought||插入语|据认为；人们推测|
inferred|infer|v.|推断；推知|researchers inferred
archer||n.|弓箭手|
rear||n.|后方；背后|
shooter||n.|射手|
caught|catch|v.|使措手不及；趁其不备|
unawares||adv.|在没有防备时|caught him unawares
dined on|dine on|动词短语|吃；进食|
red deer||名词短语|马鹿|
hearty||adj.|丰盛的；充足的|
nourishing||adj.|有营养的|a hearty, nourishing meal
consumed|consume|v.|食用；吃下|
Curators|curator|n.|馆藏保管人员；策展人|Curators in Bolzano
tattoos|tattoo|n.|文身|
spine||n.|脊柱|
acupuncture||n.|针灸|an early form of acupuncture
identity||n.|身份|The archer's identity
enigma||n.|谜团|an enigma
motive||n.|动机|any motive is conjecture
conjecture||n.|猜测；推测|any motive is conjecture
anonymous||adj.|身份不明的；不知姓名的|his anonymous killer
killer||n.|凶手|'''
qa=[
('The assumption was that a modern-day climber had died on an alpine slope, since glaciers sometimes yield frozen remains.','assumption'),
("From the wound's depth researchers inferred that an archer shot him from the rear, at about 30 metres.",'inferred'),
('Curators in Bolzano now keep Ötzi, whose 61 tattoos on joints and spine were perhaps an early form of acupuncture.','acupuncture'),
("The archer's identity is an enigma, and any motive is conjecture.",'conjecture')
]
save('20',zh,v,qa,'冰人的箭伤，揭开了怎样的古老谜案？')
artwork('20','/workspace/generated_images/exec-000db172-6985-4b0d-8045-3240e94e3e5d.png','实际图已看：保管人员戴手套检查木柄铜斧，皮革与草编材料呼应史前身份，手脸自然；淡远阿尔卑斯山景，无文字或血腥内容。','铜斧是原文所列随身器物，不被画作杀人凶器；没有虚构凶手身份、射箭现场或针灸用途已证实的情景。')
