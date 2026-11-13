from common import save,artwork
zh=[
'1922年11月4日，在埃及帝王谷，考古学家霍华德·卡特雇用的工人发现了一段凿入岩石的阶梯。11月26日，富有的赞助人卡纳冯勋爵站在身旁，卡特在封住的入口上开了一个小孔，瞥见少年国王图坦卡蒙墓中闪耀的黄金。这一惊人发现吸引了全世界的目光。',
'卡纳冯将独家报道权卖给《泰晤士报》，使其他竞争记者严重缺少消息。许多人转而猜测，或向外界评论者寻求说法。1923年3月，畅销小说家玛丽·科雷利公开警告，任何进入封闭陵墓的人都会受到可怕的惩罚。不到两周，她的话就将显得诡异。',
'当月，一只蚊子叮了卡纳冯。他刮胡子时用剃刀划破叮咬处，伤口感染化脓，随后败血症引发肺炎。1923年4月5日，他在开罗去世。报纸声称，就在他去世的一刻，开罗全城停电，他在英国的狗也嚎叫着死去。然而，停电在当时的开罗几乎天天发生。',
'墓中从未发现过诅咒铭文。2002年12月，《英国医学杂志》的一项研究追溯了当时身在埃及的44名西方人的命运。接触过陵墓的25人平均享年70岁，其余人平均75岁，这一差距在统计上并不显著。死亡统计并未为那则不祥的传闻提供可信依据。',
'卡纳冯的过早离世助长了诅咒传说，使它越传越广。但亲自打开陵墓的发掘者卡特，直到1939年3月才去世，享年64岁，比赞助人的去世时间晚了近16年。这位开墓者却明显没有遭遇传说中的灾祸。'
]
v='''labourers|labourer|n.|工人；体力劳动者|
engaged|engage|v.|雇用；聘请|
uncovered|uncover|v.|发现；发掘|
staircase||n.|楼梯；阶梯|
carved into|carve into|动词短语|雕凿于；刻入|
wealthy||adj.|富有的|
sponsor||n.|赞助人；资助者|his wealthy sponsor Lord Carnarvon
doorway||n.|门口；入口|
glittering|glittering|adj.|闪闪发光的|
spectacular||adj.|惊人的；壮观的|
riveted|rivet|v.|牢牢吸引注意力|The spectacular find riveted the world
exclusive||adj.|独家的；专属的|sold exclusive rights
monopoly||n.|垄断；独占|a monopoly
competing|competing|adj.|相互竞争的|
starved of|be starved of|动词短语|严重缺少|reporters starved of news
resorted to|resort to|动词短语|转而采用；诉诸|resorted to speculation
speculation||n.|猜测；推测|resorted to speculation
commentators|commentator|n.|评论者|
best-selling||adj.|畅销的|
dire||adj.|可怕的；极其严重的|dire punishment
punishment||n.|惩罚|
tomb||n.|陵墓|
fortnight||n.|两周|Within a fortnight
uncanny||adj.|诡异的；不可思议的|her words would seem uncanny
mosquito||n.|蚊子|
nicked|nick|v.|轻轻划破；割破|
razor||n.|剃刀|
shaving|shave|v.|刮胡子|
turned septic|turn septic|动词短语|感染化脓|it turned septic
pneumonia||n.|肺炎|blood poisoning led to pneumonia
at that instant||介词短语|就在那一瞬间|
howled|howl|v.|嚎叫|
blackouts|blackout|n.|停电|
occurrence||n.|发生的事；事件|
inscription||n.|铭文；刻文|No curse inscription
fate||n.|命运；遭遇|
exposed to|be exposed to|动词短语|接触到|The 25 exposed to the tomb
versus||prep.|与……相比|
margin||n.|差距；差额|a margin not statistically significant
significant||adj.|（统计上）显著的|not statistically significant
mortality||n.|死亡情况；死亡统计|The mortality figures
ominous||adj.|不祥的|
rumour||n.|传闻；谣言|
credibility||n.|可信度|no credibility
untimely||adj.|过早的；不合时宜的|
demise||n.|去世；死亡|Carnarvon's untimely demise
fuelled|fuel|v.|助长；促使加剧|had fuelled the tale
impetus||n.|推动力|giving it impetus
excavator||n.|发掘者|
unsealed|unseal|v.|启封；打开封口|
burial||n.|埋葬；墓葬|
patron||n.|资助人；赞助人|
conspicuously||adv.|显眼地；格外醒目地|conspicuously unharmed
unharmed||adj.|未受伤害的|'''
qa=[
('Carnarvon sold exclusive rights to The Times, a monopoly that left competing reporters starved of news.','monopoly'),
('Many resorted to speculation or sought outside commentators.','speculation'),
('No curse inscription was ever found in the tomb.','inscription'),
('The mortality figures lent the ominous rumour no credibility.','credibility')
]
save('17',zh,v,qa,'法老的诅咒，经得起证据检验吗？','卡特晚近16年去世，指死亡日期的间隔，并非二人的寿命相差16年。')
artwork('17','/workspace/generated_images/exec-7b40a5bf-7cfb-409d-9451-f00091622757.png','实际图已看：两名1920年代人物、石阶、封闭入口小孔与微弱金光；手脸自然；没有文字、木乃伊或超自然特效。','聚焦1922年观察墓室的真实发现；未将诅咒、停电或狗死亡的报道画成已证实因果。')
