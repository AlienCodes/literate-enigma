from group_01_12 import *
zh=[
'1984年，弗里曼特尔医院32岁的医生巴里·马歇尔喝下了一份牛肉清汤混合液，里面加入了从两个培养皿中刮取的微生物培养物。',
'当时占主导地位的学说把溃疡归因于压力、辛辣食物和胃酸分泌过多。医学界坚信，没有细菌能够在这样具有腐蚀性、又不利于生存的环境中存活。',
'然而，皇家珀斯医院的病理学家罗宾·沃伦，已经在胃炎患者的胃部活检样本中看到了弯曲、盘绕的细菌。马歇尔开始与他合作。培养这种病菌的尝试一直未获成功，直到1982年复活节期间，培养皿在培养箱里原封不动地放了约五天。通常，这些培养皿两天后就会被丢弃。菌落这一次长了出来。这种微生物后来被命名为幽门螺杆菌。',
'1983年，澳大利亚胃肠病学会的评审者对这项研究并不看好，把两人的论文列入了当年投稿中排名最低的十分之一。让猪感染这种细菌的努力也同样没有成功。于是，马歇尔把自己当成了实验对象。',
'几天之内，马歇尔开始呕吐，呼出的气带有难闻的气味，身体也逐渐感到疲倦。大约十天后，胃镜检查发现他患了胃炎，也就是胃黏膜的炎症，属于溃疡的前期病变，但它本身并不是溃疡。研究者还直接从他的胃中培养出了这种病菌。',
'在妻子不断催促下，马歇尔服用了抗生素，感染随之被清除。后来，溃疡也逐渐开始采用这类药物治疗。',
'2005年，马歇尔与沃伦因发现幽门螺杆菌及其在胃炎和消化性溃疡中的作用，共同获得诺贝尔生理学或医学奖。马歇尔当年主动让自己患上的胃炎，也被写进了获奖评语。'
]
rows='''
brew|brew|n.|调制的混合液
broth|broth|n.|肉汤；清汤
microbial|microbial|adj.|微生物的
scraped|scrape|v.|刮取；刮下
prevalent|prevalent|adj.|盛行的；普遍接受的
doctrine|doctrine|n.|学说；信条
ulcers|ulcer|n.|溃疡
spicy|spicy|adj.|辛辣的
acid|acid|n.|酸；此处指胃酸
secretion|secretion|n.|分泌
bacterium|bacterium|n.|细菌（单数）
profession|profession|n.|此处指医学界
firmly|firmly|adv.|坚定地
withstand|withstand|v.|经受住；抵御
caustic|caustic|adj.|有腐蚀性的
hostile|hostile|adj.|不利于生存的
habitat|habitat|n.|栖息环境
pathologist|pathologist|n.|病理学家
coiled|coiled|adj.|盘绕的；卷曲的
gastric|gastric|adj.|胃部的
biopsies|biopsy|n.|活体组织检查；活检样本
collaborate|collaborate|v.|合作
Attempts|attempt|n.|尝试
culture|culture|v.|培养（细菌）
germ|germ|n.|病菌
invariably|invariably|adv.|无一例外地；总是
unsuccessful|unsuccessful|adj.|未成功的
undisturbed|undisturbed|adj.|未被移动或打扰的
incubator|incubator|n.|培养箱
ordinarily|ordinarily|adv.|通常
binned|bin|v.|丢进垃圾箱
blossomed|blossom|v.|繁盛生长
unimpressed|unimpressed|adj.|不以为然的
assessors|assessor|n.|评审人员
relegated|relegate|v.|把……降至较低地位
submissions|submission|n.|提交的论文；投稿
Efforts|effort|n.|努力
swine|swine|n.|猪
likewise|likewise|adv.|同样地
in vain|in vain|phr.|徒劳；没有结果
guinea pig|guinea pig|n.|实验对象；试验品
vomiting|vomit|v.|呕吐
disagreeable|disagreeable|adj.|令人不快的
odour|odour|n.|气味
weariness|weariness|n.|疲倦；乏力
set in|set in|phr. v.|开始出现并持续
revealed|reveal|v.|显示；揭示
inflammation|inflammation|n.|炎症
mucous membrane|mucous membrane|n.|黏膜
precursor|precursor|n.|前兆；先发生的事物
albeit|albeit|conj.|尽管；虽然
directly|directly|adv.|直接地
Spurred on|spur on|phr. v.|催促；激励
insistent|insistent|adj.|坚持要求的
spouse|spouse|n.|配偶
antibiotics|antibiotic|n.|抗生素
medication|medication|n.|药物
role|role|n.|作用
willingly|willingly|adv.|自愿地
prize citation|prize citation|n.|获奖评语；颁奖词
'''
core=['prevalent','doctrine','withstand','hostile','pathologist','gastric','biopsies','collaborate','culture','invariably','incubator','relegated','in vain','guinea pig','inflammation','mucous membrane','precursor','albeit','Spurred on','antibiotics','role','prize citation']
prompt=json.loads((ROOT/'illustrations/03.json').read_text())['prompt']
build('03',zh,rows,core,['withstand','collaborate','in vain','antibiotics'],'一杯菌液，如何改变对胃病的认识？','本文的自我试验导致胃炎，并非溃疡；两者在叙述中需要严格区分。',prompt,{'mucous membrane':"the stomach's mucous membrane",'prize citation':'is named in the prize citation.','albeit':'albeit not an ulcer itself.','role':'its role in gastritis'})
print('03 content and illustration ready')
