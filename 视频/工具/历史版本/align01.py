import json,re
A=[
[[["On 6 January 1995,","1995年1月6日，"],["McArthur Wheeler","麦克阿瑟·惠勒"],["and","和"],["an accomplice","一名同伙"]],
 [["**raided** two Pittsburgh-area banks at gunpoint","持枪**抢劫了**(raided)匹兹堡地区的两家银行，"]],
 [["**in broad daylight**,","**光天化日之下**(in broad daylight)，"],["without **disguise**.","也没做任何**乔装**(disguise)。"]]],
[[["Their","他们"],["only","唯一的"],["**camouflage**","**伪装**(camouflage)"],["was","是"],["lemon juice,","柠檬汁，"]],
 [["**rubbed on**","是**抹上**(rubbed on)的，"],["in the","怀着"],["**earnest**","**真心实意的**(earnest)"],["**conviction**","**信念**(conviction)："]],
 [["that it","相信它"],["would **render**","能**让**(render)"],["them","他们"],["invisible to cameras.","在摄像头前隐形。"]]],
[[["The **rationale**","这套**理由**(rationale)"],["had","倒也有"],["a **kernel** of truth.","几分真实的**内核**(kernel)。"]]],
[[["Lemon juice","柠檬汁"],["is a","是一种"],["**time-honoured**","**由来已久的**(time-honoured)"],["invisible ink,","隐形墨水，"]],
 [["and Wheeler","惠勒则"],["made an","做了一次"],["**inventive**","**富有创意的**(inventive)"],["**leap**","**跳跃**(leap)，"],["from paper to skin.","把它从纸上搬到了皮肤上。"]]],
[[["His Polaroid","他那张宝丽来"],["**self-portrait**","**自拍照**(self-portrait)"],["came out","洗出来，"],["**devoid of**","**全无**(devoid of)"],["its subject,","本人的身影，"]],
 [["a result","这个结果"],["he took as","在他看来"],["**conclusive**.","**确凿无疑**(conclusive)。"]]],
[[["The security cameras","监控摄像头"],["**begged to differ**.","**恕难苟同**(begged to differ)。"]]],
[[["On 19 April","4月19日，"],["the eleven o'clock news","11点新闻"]],
 [["showed **viewers**","向**观众**(viewers)播出了"],["the","那些"],["**damning**","**足以定罪的**(damning)"],["images,","画面，"]],
 [["and Wheeler was arrested shortly after midnight.","午夜刚过不久，惠勒就被捕了。"]]],
[[["**Confronted with**","**面对**(Confronted with)"],["the tapes,","录像，"]],
 [["he","他"],["protested in **sheer** **disbelief**","在**极度的**(sheer)**难以置信**(disbelief)中辩称，"],["that he had worn the juice.","自己明明抹了柠檬汁。"]]],
[[["Reading about the case,","读到这个案子时，"]],
 [["the Cornell psychologist","康奈尔大学心理学家"],["David Dunning","戴维·邓宁"],["**pondered**","**思索**(pondered)起"],["a","一个"],["**disquieting**","**令人不安的**(disquieting)"],["**proposition**.","**命题**(proposition)。"]]],
[[["Perhaps","也许，"],["**incompetence**","**无能**(incompetence)"],["can **cloak** itself,","会把自身**掩盖**(cloak)起来，"]],
 [["**robbing** people of the **discernment** to notice their **deficiencies**.","**剥夺**(robbing)人们察觉自身**不足**(deficiencies)的**辨别力**(discernment)。"]]],
[[["For a 1999 paper,","为了1999年的一篇论文，"],["Dunning","邓宁"],["and","和"],["his student","他的学生"],["Justin Kruger","贾斯汀·克鲁格"]],
 [["**quizzed**","**测试了**(quizzed)"],["Cornell","康奈尔的"],["**undergraduates**","**本科生**(undergraduates)"],["on humour, grammar and **logical** reasoning.","，考查幽默、语法和**逻辑**(logical)推理。"]]],
[[["The bottom quarter of **scorers**","成绩垫底的四分之一**答题者**(scorers)，"],["averaged","平均只处在"],["the 12th percentile","第12百分位，"]],
 [["but","却"],["**generously**","**慷慨地**(generously)"],["placed themselves","把自己估在"],["near the 62nd,","第62百分位附近，"]],
 [["whereas","而"],["**high achievers**","**成绩优异者**(high achievers)"],["showed","却表现出"],["**undue**","**过分的**(undue)"],["**modesty**.","**谦虚**(modesty)。"]]],
[[["The **unskilled**, the authors argued,","两位作者认为，**能力不足的**(unskilled)人"],["bear","背负着"],["a **dual**","**双重**(dual)"],["burden,","负担，"]],
 [["since","因为"],["**appraisal**","**评估**(appraisal)"],["calls for the same skills as **execution**.","与**执行**(execution)需要的是同一套技能。"]]],
[[["**Detractors**","**批评者**(Detractors)"],["traced part of the Dunning-Kruger **disparity**","把邓宁-克鲁格**差距**(disparity)的一部分"]],
 [["to regression to the mean,","归因于向均值回归，"]],
 [["a statistical **mirage**","这种统计**假象**(mirage)，"],["the paper","论文本身"],["**partially** acknowledged.","也曾**部分地**(partially)承认过。"]]],
[[["Studies designed to avoid it","专为避开这一问题而设计的研究"]],
 [["still find","仍发现了"],["a smaller","一个较小"],["but **tangible**","但**确实存在的**(tangible)"],["effect.","效应。"]]],
[[["In 2023","2023年，"],["the pair","两人"],["**garnered**","**赢得了**(garnered)"],["the Grawemeyer psychology award.","格文美尔心理学奖。"]]],
[[["**In fairness**,","**平心而论**(In fairness)，"],["Wheeler","惠勒"],["had tested his method **empirically**","确实**用实验**(empirically)检验过他的方法，"]],
 [["before","之后才"],["**staking** his **liberty** on it.","把自己的**自由**(liberty)**押了上去**(staking)。"]]],
[[["The camera that missed him","漏拍了他的那台相机，"]],
 [["was","恰恰是"],["the one he turned on himself.","他对准自己的那一台。"]]],
]
d=json.load(open("scripts/01.json"))
assert len(A)==len(d["sentences"])
n=0;big=[]
for s,a in zip(d["sentences"],A):
  assert len(a)==len(s["chunks"])
  for c,al in zip(s["chunks"],a):
    assert " ".join(e for e,_ in al)==c["en"],(c["en"])
    c["zh"]="".join(z for _,z in al); c["align"]=al
    for b in re.findall(r"\*\*(.+?)\*\*",c["en"]):
      assert c["zh"].count(f"({b})")==1,b
    n+=len(al)
    for e,_ in al:
      if len(e.replace("*","").split())>=5: big.append(e)
json.dump(d,open("scripts/01.json","w"),ensure_ascii=False,indent=1)
print(n,n/38);print(*big,sep="\n")
