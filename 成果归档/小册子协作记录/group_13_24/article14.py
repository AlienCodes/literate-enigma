from common import save,artwork
zh=[
'在泰国雨林深处，一只木匠蚁脱离了高处树冠中的蚁群队列。它腿脚不稳，摇摇晃晃地向下游荡，仿佛喝醉一般，钻进枝叶茂密的林下植被。正午前后，它用双颚紧紧咬住一片叶子背面的主叶脉，那里离地面约25厘米。',
'到黄昏时，蚂蚁已经死去，却仍牢牢咬住叶子。真菌破坏了它的颚部肌肉，使其无法放松。两三天后，一根菌柄从蚂蚁头部伸出，向下方地面散播具有传染性的孢子，那里正有觅食的蚂蚁经过。',
'这种入侵者叫偏侧蛇虫草菌，对位置很挑剔。戴维·休斯及其同事发现，咬合点大多位于植物的西北侧，那里空气潮湿，温度也适合真菌。研究者将受感染的蚂蚁移到更高处后，真菌生长得不正常；放到地面的蚁尸则不见了。',
'2017年，宾夕法尼亚州立大学的团队通过三维显微成像检查受感染的蚂蚁。真菌细胞在腿部和颚部的肌肉纤维周围织成相互交错的网络，令人联想到操纵木偶的提线。然而，真菌并未侵入蚂蚁的大脑。',
'由戴维·阿滕伯勒解说的纪录片《地球脉动》曾在一集中展示过这样一只蚂蚁。这启发了2013年电子游戏《最后生还者》的创作者，他们设想这种寄生菌转而感染人类。这种假想情景给玩家带来了一场虚构的噩梦。',
'现实中，这种寄生现象的历史要久远得多，可以追溯到地质记录之中。德国梅塞尔出土的一片4800万年前的叶子化石上，带有同样具有代表性的咬痕。'
]
v='''rainforest||n.|雨林|
carpenter||n.|木匠（木匠蚁名称的一部分）|
colony||n.|（蚂蚁等的）群体|its colony's column
column||n.|行进的队列|
lofty||adj.|高耸的；高处的|
canopy||n.|森林的树冠层|in the lofty canopy
Swaying|sway|v.|摇晃；摇摆|
unsteady||adj.|不稳的|on unsteady legs
wanders|wander|v.|游荡；漫无目的地走|it wanders downward
downward||adv.|向下|
as if||连词短语|仿佛；好像|
intoxicated|intoxicated|adj.|醉酒般的|as if intoxicated
leafy||adj.|枝叶茂密的|
undergrowth||n.|林下灌丛；林下植被|into leafy undergrowth
midday||n.|正午|
clenches|clench|v.|紧咬；紧闭|it clenches its jaws
jaws|jaw|n.|颚；口部咬合器官|
vein||n.|叶脉|a major vein underneath a leaf
dusk||n.|黄昏|By dusk
lifeless||adj.|死去的；无生命的|
rigidly||adv.|僵硬地；牢牢地|the bite holds rigidly
muscles|muscle|n.|肌肉|
loosen||v.|放松；松开|
fungal||adj.|真菌的|
infectious||adj.|具有传染性的|releases infectious spores
tread||v.|行走；踏过|where foraging ants tread
invader||n.|入侵者|
fussy||adj.|挑剔的|is fussy about location
location||n.|位置；地点|
bites|bite|n.|咬合点；咬痕|
north-west||n.|西北侧；西北方|
humid||adj.|潮湿的|the air is humid
abnormally||adv.|不正常地；反常地|the fungus grew abnormally
disappeared|disappear|v.|消失；不见|
three-dimensional||adj.|三维的|
microscope||n.|显微镜|
intertwined|intertwined|adj.|交织的；缠绕的|an intertwined lattice
lattice||n.|网格；格状结构|an intertwined lattice
evokes|evoke|v.|使人联想到|a picture that evokes
puppet||n.|木偶|
infiltrated|infiltrate|v.|侵入；渗入|had not infiltrated the brain
narration||n.|解说；旁白|
inspire||v.|启发；赋予灵感|
makers|maker|n.|创作者；制作者|
envisioned|envision|v.|设想；想象|
hypothetical||adj.|假想的；假设的|The hypothetical scenario
scenario||n.|情景；设想|The hypothetical scenario
gamers|gamer|n.|电子游戏玩家|
fictional||adj.|虚构的|
geological||adj.|地质的|
fossil||n.|化石|fossil leaf from Messel
characteristic||adj.|有代表性的；典型的|
scars|scar|n.|疤痕；留下的痕迹|'''
qa=[
('Around midday it clenches its jaws on a major vein underneath a leaf, about 25 centimetres above the ground.','clenches'),
('When researchers moved infected ants higher, the fungus grew abnormally.','abnormally'),
('Yet the fungus had not infiltrated the brain.','infiltrated'),
('The hypothetical scenario gave gamers a fictional nightmare.','hypothetical')
]
save('14',zh,v,qa,'蚂蚁为何会咬住叶片不松口？')
artwork('14','/workspace/generated_images/exec-c4920680-6e31-49de-945b-7ea4f869ce8f.png','已看最终编辑图：低叶叶背、咬合叶脉和独立菌柄可辨；修正了初图菌柄像口器延伸的问题，最终菌柄从后脑处长出，腿有自然前后重叠。暖象牙、鼠尾草绿、羽化边缘，无文字或图示。','仅画观察到的蚁尸、叶脉和头部长出的菌柄；没有脑侵入剖面、提线或感染人类的虚构。原生成与编辑图均保留。')
