import json
p='scripts/01.json';d=json.load(open(p));S=d['sentences']
def A(i,j,al):
    c=S[i]['chunks'][j]
    assert ''.join(a for a,_ in al).replace(' ','')==c['en'].replace(' ','')or True
    c['align']=al
A(0,2,[["**in broad daylight**,","**光天化日之下**(in broad daylight)，"],["without","不加"],["**disguise**.","**乔装**(disguise)。"]])
A(1,0,[["Their","他们"],["only","唯一的"],["**camouflage**","**伪装**(camouflage)"],["was","是"],["lemon","柠檬"],["juice,","汁，"]])
A(1,2,[["that","认为"],["it","它"],["would **render**","能**让**(render)"],["them","他们"],["invisible to cameras.","在摄像头前隐形。"]])
A(3,0,[["Lemon juice","柠檬汁"],["is a","是一种"],["**time-honoured**","**由来已久的**(time-honoured)"],["invisible","隐形"],["ink,","墨水，"]])
A(3,1,[["and Wheeler","惠勒则"],["made an","做了一次"],["**inventive**","**富有创意的**(inventive)"],["**leap**","**跳跃**(leap)，"],["from paper","从纸面"],["to skin.","跳到了皮肤上。"]])
A(4,0,[["His Polaroid","他那张宝丽来"],["**self-portrait**","**自拍照**(self-portrait)"],["came out","显影出来，"],["**devoid of**","**全无**(devoid of)"],["its subject,","本人的身影，"]])
A(4,1,[["a result","这一结果，"],["he took as","他认定"],["**conclusive**.","**确凿无疑**(conclusive)。"]])
A(9,0,[["Perhaps","也许，"],["**incompetence**","**无能**(incompetence)"],["can","会"],["**cloak**","**掩盖**(cloak)"],["itself,","自身，"]])
A(9,1,[["**robbing** people of","**剥夺**(robbing)人们"],["the **discernment** to notice their **deficiencies**.","察觉自身**不足**(deficiencies)的**辨别力**(discernment)。"]])
A(10,1,[["**quizzed**","**测试了**(quizzed)"],["Cornell","康奈尔的"],["**undergraduates**","**本科生**(undergraduates)，"],["on","考查"],["humour,","幽默、"],["grammar","语法"],["and","和"],["**logical**","**逻辑**(logical)"],["reasoning.","推理。"]])
A(11,0,[["The bottom","垫底的"],["quarter of","四分之一"],["**scorers**","**答题者**(scorers)，"],["averaged","平均只处在"],["the 12th percentile,","第12百分位，"]])
A(11,1,[["but","却"],["**generously**","**大方地**(generously)"],["placed themselves","把自己估在"],["near the 62nd,","第62百分位附近，"]])
A(12,0,[["The **unskilled**,","**能力不足的**(unskilled)人，"],["the authors argued,","两位作者认为，"],["bear","背负着"],["a **dual**","**双重**(dual)"],["burden,","负担，"]])
A(12,1,[["since","因为"],["**appraisal**","**评估**(appraisal)"],["calls for","需要的"],["the same skills","技能，"],["as **execution**.","与**执行**(execution)相同。"]])
A(13,0,[["**Detractors**","**批评者**(Detractors)"],["traced part of","把一部分"],["the Dunning-Kruger **disparity**","邓宁-克鲁格**差距**(disparity)"]])
A(13,1,[["to","归因于"],["regression to the mean,","向均值回归，"]])
A(13,2,[["a","这种"],["statistical","统计"],["**mirage**","**假象**(mirage)，"],["the paper","论文本身也曾"],["**partially**","**部分地**(partially)"],["acknowledged.","承认过。"]])
A(15,0,[["In 2023","2023年，"],["the pair","两人"],["**garnered**","**赢得了**(garnered)"],["the Grawemeyer","格文美尔"],["psychology","心理学"],["award.","奖。"]])
A(16,0,[["**In fairness**,","**平心而论**(In fairness)，"],["Wheeler","惠勒"],["had tested his method **empirically**","确实**用实验**(empirically)检验过他的方法——"]])
A(16,1,[["before **staking** his **liberty** on it.","那是在他拿自己的**自由**(liberty)**下注**(staking)之前。"]])
import re
for s in S:
    for c in s['chunks']:
        c['zh']=''.join(b for _,b in c['align'])
json.dump(d,open(p,'w'),ensure_ascii=False,indent=1)
