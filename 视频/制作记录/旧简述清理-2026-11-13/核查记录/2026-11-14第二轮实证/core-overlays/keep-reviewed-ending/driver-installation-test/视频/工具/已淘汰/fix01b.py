import json,re
p='scripts/01.json';d=json.load(open(p));S=d['sentences']
def k(en,zh):  # mark keyword: en has **x**, zh has **y** -> **y**(x)
    kws=re.findall(r'\*\*([^*]+)\*\*',en); out=zh
    for x in kws: out=out.replace('{'+x+'}','**%s**(%s)'%(x_zh[x],x),1) if False else out
    return [en,zh]
def A(i,j,al,note=None):
    c=S[i]['chunks'][j]; c['align']=al
    c['en']=' '.join(a for a,_ in al if a!='\n')
    if note: c['note']=note
    elif 'note' in c: del c['note']
A(0,0,[["On 6 January 1995,","1995年1月6日，"],["McArthur Wheeler","麦克阿瑟·惠勒"],["and","和"],["an","一名"],["**accomplice**","**同伙**(accomplice)"]])
A(1,0,[["Their","他们"],["only","唯一的"],["**camouflage**","**伪装**(camouflage)"],["was","是"],["lemon juice,","柠檬汁，"]])
A(1,1,[["**rubbed on**","**涂抹**(rubbed on)在身上，"],["in the","怀着"],["**earnest**","**真心实意的**(earnest)"],["**conviction**","**信念**(conviction)，"]],note="#Y（另译：对此深信不疑）")
A(1,2,[["that","认为"],["it","它"],["would","能"],["**render**","**使**(render)"],["them","他们"],["**invisible** to cameras.","在镜头前**隐形**(invisible)。"]],note="（render：使……处于某种状态）")
A(2,0,[["The","这套"],["**rationale**","**逻辑**(rationale)"],["had","倒也有"],["a **kernel** of truth.","几分真实的**内核**(kernel)。"]])
S[3]['chunks'][1]['align'].insert(1,["\n",""])
c=S[3]['chunks'][0]; c['align']=[["Lemon juice","柠檬汁"],["is a","是一种"],["**time-honoured**","**由来已久的**(time-honoured)"],["**invisible**","**隐形**(invisible)"],["**ink**,","**墨水**(ink)，"]]; c['en']=' '.join(a for a,_ in c['align'])
A(4,0,[["His","他的"],["Polaroid","宝丽来"],["**self-portrait**","**自拍照**(self-portrait)"],["came out","洗出来后，"],["\n",""],["**devoid of**","**完全没有**(devoid of)"],["its","照片的"],["subject,","拍摄对象（他本人），"]])
A(4,1,[["a result","这个结果，"],["he","他"],["took as","当成了"],["**conclusive**.","**确凿的**(conclusive)证据。"]],note="（他用这个相机拍了一张自拍，实际上没拍到，但他以为是他自己涂了柠檬水，隐身了。）")
A(5,0,[["The security cameras","监控摄像头"],["**begged to differ**.","可**不敢苟同**(begged to differ)。"]])
A(8,0,[["Reading about","读到"],["the case,","这个案子时，"]])
A(8,1,[["the Cornell psychologist","康奈尔大学心理学家"],["David Dunning","戴维·邓宁"],["**pondered**","**仔细思考了**(pondered)"],["a","一个"],["**disquieting**","**令人不安的**(disquieting)"],["**proposition**.","**观点**(proposition)。"]])
A(9,0,[["Perhaps","也许，"],["**incompetence**","**无能**(incompetence)（这种东西）"],["can","会"],["**cloak**","**掩藏住**(cloak)"],["itself,","它自己，"]])
A(9,1,[["**robbing** people of","**剥夺**(robbing)人们的"],["the **discernment**","**识别能力**(discernment)，"],["to notice","去注意到"],["their **deficiencies**.","他们自身的**不足**(deficiencies)。"]])
A(10,1,[["**quizzed**","**测试了**(quizzed)"],["Cornell","康奈尔的"],["**undergraduates**","**本科生**(undergraduates)，"],["\n",""],["on","考察了（关于）"],["humour,","幽默、"],["grammar","语法"],["and","和"],["**logical** reasoning.","**逻辑**(logical)推理的能力。"]])
A(11,0,[["The bottom","垫底的"],["quarter of","四分之一"],["**scorers**","**答题者**(scorers)，"],["averaged","平均只处在"],["the 12th percentile","（倒数）第12百分位，"]])
A(11,1,[["but","却"],["**generously**","**大方地**(generously)（高估自己）"],["placed themselves","把自己估在"],["near the 62nd,","第62百分位附近，"]])
A(11,2,[["whereas","而"],["**high achievers**","**成绩优异者**(high achievers)"],["showed","却表现出"],["**undue**","**过分的**(undue)"],["**modesty**.","**谦虚**(modesty)。"]])
A(12,0,[["The **unskilled**,","**能力不足的**(unskilled)人，"],["the authors argued,","两位作者认为，"],["bear","背负着"],["a **dual** burden,","**双重**(dual)负担，"]])
A(12,1,[["since","因为"],["**appraisal**","**评估**(appraisal)（自我评估）"],["**calls for**","**需要**(calls for)"],["the same skills","相同的技能，"],["as **execution**.","与**执行**(execution)（所需）的一样。"]])
A(13,0,[["**Detractors**","**批评者**(Detractors)"],["traced","查明"],["part of","部分"],["the Dunning-Kruger **disparity**","邓宁-克鲁格**差异**(disparity)，"]])
A(13,1,[["to","源于"],["regression to the mean,","均值回归，"]],note="（trace A to B：追溯 A 的来源到 B、查明 A 源于 B）")
A(13,2,[["a","一种"],["statistical","统计学的"],["**mirage**","**假象**(mirage)，"],["\n",""],["the paper","该论文（即前文1999年邓宁-克鲁格论文）"],["**partially**","也曾**部分**(partially)"],["acknowledged.","承认过。"]])
A(17,0,[["The camera that missed him","那台没拍到他的相机，"]])
A(17,1,[["was","正是"],["the one he","他"],["turned","转动（将镜头）"],["on","对准"],["himself.","自己的那一台。"]],note="（那相机只是没有拍到他，他却以为自己隐形了，误以为是柠檬水的作用）")
A(7,0,[["**Confronted with**","**面对**(Confronted with)"],["the tapes,","这些录像，"]])
A(7,1,[["he","他"],["protested","坚决表示"],["in **sheer**","**完全**(sheer)"],["**disbelief**","**不相信**(disbelief)，"],["that","说"],["he had worn","自己明明抹了"],["the juice.","柠檬汁。"]])
c=S[14]['chunks'][1]; c['align']=[[a,(b.replace('**确实存在的**','**切实存在的**'))] for a,b in c['align']]
A(16,0,[["**In fairness**,","**平心而论**(In fairness)，"],["\n",""],["Wheeler","惠勒"],["had tested his method **empirically**","确实**用实证的方法**(empirically)检验过他的这套办法，"]])
A(16,1,[["before","在"],["**staking** his **liberty** on it.","他把自己的**自由**(liberty)**赌**(staking)在抢劫上之前。"]],note="（stake A on B：把A赌在B上）")
S[10]["chunks"][0]["align"].insert(1,["\n",""])
d["title_fx"]={"hl":["Lemon","Juice"],"ghost":["Invisible"]}
for s in S:
    for c in s['chunks']: c['zh']=''.join(b for _,b in c['align'])
json.dump(d,open(p,'w'),ensure_ascii=False,indent=1)
# sanity: en words unchanged
o=json.load(open('scripts/01.bak.json'))
norm=lambda t:re.sub(r'[\*\s]','',t)
for a,b in zip(o['sentences'],S):
    x=norm(''.join(c['en'] for c in a['chunks']));y=norm(''.join(c['en'] for c in b['chunks']))
    if x!=y: print('DIFF',x,'\n    ',y)
