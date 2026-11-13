from common import save,artwork
zh=[
'1928年9月，伦敦圣玛丽医院的细菌学家亚历山大·弗莱明度假回来，发现一团偶然出现的霉菌污染了一只培养葡萄球菌的培养皿，霉菌周围没有细菌生长。流行传说认为孢子从敞开的窗户飘入；它们其实很可能来自楼下的实验室，那里有位同事在培养霉菌。',
'弗莱明将霉菌产生的液汁称为青霉素，并于1929年6月发表研究。然而，粗制液汁不稳定，极难提纯；他和请来的化学家又缺乏精炼它的专业知识。他主要用它分离其他微生物，青霉素因此沉寂下来，仍是一件引人好奇的科学奇物，而非治病良药。',
'约十年后，在牛津，澳大利亚病理学家霍华德·弗洛里与德国出生的化学家、犹太难民恩斯特·钱恩重启研究。同事诺曼·希特利就地取材，制作了一套巧妙装置来提取这种化合物。1940年5月25日，八只小鼠接受致死剂量的细菌，只有同时注射青霉素的四只存活。权威期刊《柳叶刀》于同年8月发表了结果。',
'1941年2月，牛津警员艾伯特·亚历山大因感染病情危重，用上青霉素后有所好转。但稀缺的药物耗尽后，他于3月去世：难关在于产量。从1941年7月起，伊利诺伊州皮奥里亚的一家政府实验室利用淀粉生产副产物玉米浆，使产量达到原先的约十倍。后来，市场上的一只发霉甜瓜又提供了更高产的菌株。到1944年6月诺曼底登陆时，工业发酵已能满足盟军需求。',
'1945年10月，弗莱明、弗洛里和钱恩共同获得诺贝尔奖，希特利却被忽略了。机缘将霉菌送入弗莱明的培养皿，而多支团队锲而不舍、辛劳多年，才把它变成救人的良药。'
]
v='''stray||adj.|偶然出现的；零散的|
mould||n.|霉菌|
contaminated|contaminate|v.|污染；使混入杂质|a stray mould had contaminated
bacteria|bacterium|n.|细菌（复数）|
Popular mythology|popular mythology|名词短语|流行传说|
spores|spore|n.|孢子|the spores probably originated
originated in|originate in|动词短语|起源于；来自|
cultivated|cultivate|v.|培养；培育|
penicillin||n.|青霉素|the mould's juice penicillin
crude||adj.|粗制的；未经精炼的|the crude juice
unstable||adj.|不稳定的|the crude juice was unstable
stubbornly||adv.|顽固地；格外难以|
purify||v.|提纯；纯化|stubbornly hard to purify
expertise||n.|专业知识；专长|lacked the expertise to refine it
refine||v.|精炼；提纯|
chiefly||adv.|主要地|
isolate||v.|分离；隔离|to isolate other microbes
microbes|microbe|n.|微生物|
lay dormant|lie dormant|动词短语|沉寂；暂未得到发展|
curiosity||n.|引人好奇的事物|
cure||n.|疗法；有效的治疗手段|
revived|revive|v.|重启；使恢复活力|revived the work
chemist||n.|化学家|
refugee||n.|难民|
improvised|improvise|v.|就地取材制作；临时拼装|improvised an ingenious apparatus
ingenious||adj.|巧妙的；独创的|an ingenious apparatus
apparatus||n.|装置；设备|an ingenious apparatus
extract||v.|提取|to extract the compound
compound||n.|化合物|
lethal||adj.|致死的|a lethal dose of bacteria
dose||n.|剂量|
injected with|inject with|动词短语|注射（药物）|
prestigious||adj.|享有盛誉的|
outcome||n.|结果|
constable||n.|警员|
gravely ill||形容词短语|病情危重的|
infection||n.|感染|
rallied|rally|v.|病情好转；恢复|
scarce||adj.|稀缺的；不足的|the scarce supply
ran out|run out|动词短语|用尽；耗尽|
obstacle||n.|障碍；难关|the obstacle was quantity
quantity||n.|数量；产量|the obstacle was quantity
boosted|boost|v.|提高；增加|
tenfold||adv.|增至十倍|boosted yields about tenfold
corn-steep liquor||名词短语|玉米浆|
starch||n.|淀粉|
mouldy||adj.|发霉的|
melon||n.|甜瓜|
furnished|furnish|v.|提供；供应|
with||prep.|表示提供的东西|
prolific||adj.|高产的；多产的|a more prolific strain
industrial||adj.|工业的|
fermentation||n.|发酵|industrial fermentation
Allied|Allied|adj.|盟军的|
overlooked|overlook|v.|忽视；未给予应有认可|
Fortune|fortune|n.|机缘；运气|
tenacious||adj.|锲而不舍的；顽强的|tenacious teams
toil||n.|辛劳；苦干|
transformed|transform|v.|使转化；改变|
into||prep.|变成；成为|
remedy||n.|良药；治疗手段|transformed it into a remedy'''
qa=[
('Yet the crude juice was unstable and stubbornly hard to purify, and he and the chemists he enlisted lacked the expertise to refine it.','purify'),
('Their colleague Norman Heatley improvised an ingenious apparatus to extract the compound.','improvised'),
('When the scarce supply ran out, he died in March: the obstacle was quantity.','quantity'),
('By D-Day in June 1944 industrial fermentation met Allied needs.','fermentation')
]
save('18',zh,v,qa,'从一团霉菌到救命药，中间还差什么？')
artwork('18','/workspace/generated_images/exec-97066f87-2880-4c61-ab4d-2ec99f19c9b7.png','实际图已看：培养皿中央霉菌与周围无菌生长的清晰环带可辨，发霉甜瓜和生产器皿相配；手部自然，无文字。','这是研究、菌株与增产的编辑性实验室场景，未把未证实的开窗传说画成来源；人物不宣称是某次真实会议的精确肖像。')
