import json,re,glob
# 第09篇初稿（逐词对照）：S = [(段, [chunk, ...])]，chunk = ([(英文组, 中文组), ...], 可选 note)
# 2026-10-10 按现行做法：程序打底（英文、重点词与文章逐字核对），重点词中文沿用文章定稿（新版定稿/09）的意思，
# 只按《翻译风格》调格式（作定语的形容词“的”、过去时的“了”放进粗体、语序必须倒过来的整组），再做两视角独立审校。
# 08 定稿时用户定下的新规矩一并照做：短语型用法整体标（T22）、被隔开的中文意思两处都标（T23）、
# 后置定语的 note 写出省略了什么（用户 2026-10-10：“gathered = which was gathered，省略了 which was……让他们更好懂”）。
S=[
(1,[[[("Around Campion, Western Australia,","在西澳大利亚州坎皮恩一带，")]],
    [[("most farmers","大多数农民"),("were","是"),("First World War **veterans**,","第一次世界大战的**退伍军人**(veterans)，")]],
    [[("**settlers**","他们作为**定居者**(settlers)，"),("placed by a government scheme","由政府计划安置"),("on **marginal** **parcels** of **farmland**.","在**贫瘠的**(marginal)**小块土地**(parcels)上，以这些**农地**(farmland)为生。")],
     "（settlers…：同位语，说明 veterans；\nplaced… = who were placed…，过去分词短语作后置定语，省略了 who were）"]]),
(1,[[[("They","他们"),("were","是"),("**inexperienced** **growers**,","**缺乏经验的**(inexperienced)**种植者**(growers)，")]],
    [[("and a quarter","已有四分之一的人"),("had already quit.","放弃了土地。")]]]),
(1,[[[("In 1932,","1932年，"),("after drought,","旱灾过后，")]],
    [[("roughly 20,000 emus","约2万只鸸鹋"),("**swarmed** in from **arid** country","从**干旱**(arid)地区**蜂拥而至**(swarmed)，"),("in **flocks**","结成**鸟群**(flocks)，")]],
    [[("and **trampled**","**践踏了**(trampled)"),("the wheat **crops**.","小麦**庄稼**(crops)。")]]]),
(2,[[[("The farmers' **plight**","农民的**困境**(plight)"),("took a military turn.","由此走向了军事手段。")]]]),
(2,[[[("In **desperation**,","**绝望**(desperation)之中，")]],
    [[("a **delegation** of ex-soldiers","一个由退伍士兵组成的**代表团**(delegation)"),("aired their **grievances**","陈述了**不满**(grievances)，")]],
    [[("and asked the Defence Minister","请求国防部长"),("for **machine-guns**.","提供**机枪**(machine-guns)。")],"（air grievances：陈述不满；ask sb for sth：向某人要某物）"]]),
(2,[[[("He agreed,","部长同意了，"),("sending","但派出的"),("not a **battalion**","不是**整营兵力**(battalion)，"),("but a **detachment**:","而是一支**小分队**(detachment)：")]],
    [[("Major Meredith,","梅雷迪思少校，"),("an **artillery** officer,","一名**炮兵**(artillery)军官，")]],
    [[("with two soldiers,","带着两名士兵、"),("two Lewis guns,","两挺刘易斯机枪"),("and 10,000 rounds of **ammunition**.","和1万发**弹药**(ammunition)。")],
     "（sending…：现在分词短语作伴随状语；not A but B：不是A而是B；冒号后具体说明 detachment）"]]),
(2,[[[("The **offensive**","**攻势**(offensive)"),("began on 2 November 1932.","于1932年11月2日展开。")]]]),
(3,[[[("At a dam,","在一处水坝，"),("about a thousand birds","约一千只鸟"),("approached an **ambush**,","走近**伏击圈**(ambush)，")]],
    [[("but a gun **jammed** after a dozen fell.","但打倒十来只后，一挺机枪就**卡壳了**(jammed)。")]]]),
(3,[[[("The flocks","鸟群"),("broke **formation**","打乱**队形**(formation)，"),("into small, **agile** groups,","分成**灵活的**(agile)小群，")]],
    [[("frustrating each **tactical** plan,","让每一个**战术**(tactical)计划都落了空；")]],
    [[("and a truck-mounted gun","装在卡车上的机枪"),("proved **futile**.","也**徒劳无功**(futile)。")],"（frustrating…：现在分词短语作结果状语；prove + 形容词：结果是……）"]]),
(3,[[[("Six days of **wasteful** firing","六天的**浪费**(wasteful)射击"),("spent 2,500 rounds","打掉了2,500发，"),("on perhaps 50 to 200 birds,","只打死大约50至200只鸟，")]],
    [[("a **ludicrous** return.","这样的回报**荒唐可笑**(ludicrous)。")],"（spend A on B：在B上花掉A；a ludicrous return：同位语，评价前面这件事）"]]),
(3,[[[("After **parliamentary** questions","在**议会**(parliamentary)质询"),("and press **ridicule**,","和报界**嘲讽**(ridicule)之后，")]],
    [[("an **embarrassing** **withdrawal**","一场**尴尬的**(embarrassing)**撤出**(withdrawal)"),("came on 8 November,","发生在11月8日；")]],
    [[("though","不过"),("shooting restarted within days.","没过几天，射击又重新开始了。")]]]),
(4,[[[("Meredith","梅雷迪思"),("was recalled on 10 December.","于12月10日被召回。")]]]),
(4,[[[("His **memo**'s **inventory**","他**备忘录**(memo)里开列的**清单**(inventory)"),("counted 986 kills from 9,860 rounds,","显示，9,860发打死了986只，")]],
    [[("a **ratio** of ten **bullets** to one bird.","**比例**(ratio)是十发**子弹**(bullets)对一只鸟。")],"（a ratio of A to B：A比B的比例；a ratio…：同位语，说明前面的数字）"]]),
(4,[[[("He likened","他把"),("the **resilient** birds' **toughness**","这些**耐打的**(resilient)鸟的**坚韧**(toughness)"),("to the **armour** of tanks.","比作坦克的**装甲**(armour)。")],"（liken A to B：把A比作B）"]]),
(4,[[[("Five weeks of **warfare**","五个星期的**战事**(warfare)"),("had barely dented","几乎没有削弱"),("the **hardy** flocks' **endurance**.","这些**顽强的**(hardy)鸟群的**耐力**(endurance)。")],"（dent：本义压出凹痕，这里指削弱）"]]),
(5,[[[("Later **pleas** for **reinforcements**","后来请求**增援**(reinforcements)的**恳求**(pleas)"),("were refused,","都遭到拒绝，")]],
    [[("and **intervention**","**干预**(intervention)"),("gave way to","让位于"),("a **bounty** **sanctioned** by the government.","政府**批准**(sanctioned)的**悬赏**(bounty)。")],
     "（give way to：让位于；sanctioned… = which was sanctioned…，过去分词短语作后置定语，省略了 which was）"]]),
(5,[[[("This **payout** per bird","这种按只计算的**赏款**(payout)"),("gave farmers","给了农民"),("**compensation**","**补偿**(compensation)，")]],
    [[("and an **incentive** for **extermination**.","也成为**灭除**(extermination)鸸鹋的**动力**(incentive)。")]]]),
(5,[[[("Farmers","农民"),("claimed over 57,000 **payments** in six months of 1934,","在1934年的六个月里领取了5.7万多笔**赏金**(payments)，")]],
    [[("more than fifty-seven times Meredith's 986 kills.","是梅雷迪思那986只战果的五十七倍多。")]]]),
]
CONF={}
out={"no":"09","title_en":"The Great Emu War","title_zh":"向鸸鹋宣战","title_fx":{"hl":["Emu","War"],"ghost":[]},"sentences":[],"核对确认":CONF}
for p,chs in S:
    cs=[]
    for c in chs:
        al=[list(x) for x in c[0]]
        d={"en":" ".join(a for a,b in al if a!="\n"),"zh":"".join(b for a,b in al),"align":al}
        if len(c)>1: d["note"]=c[1]
        cs.append(d)
    out["sentences"].append({"para":p,"chunks":cs})
json.dump(out,open("scripts/09.json","w"),ensure_ascii=False,indent=1)
art=open(glob.glob("/home/user/postgraduate-vocabulary/新版定稿/09-*.md")[0]).read()
eng=art.split("## 英文")[1].split("## 中文")[0].strip().split("\n\n")
ok=True
for i,pp in enumerate(eng,1):
    got=" ".join(c["en"] for s in out["sentences"] if s["para"]==i for c in s["chunks"])
    if got!=pp.strip(): ok=False; print('段',i,'英文不一致'); print(got); print(pp)
abold=re.findall(r"\*\*(.+?)\*\*","\n".join(eng)); sb=[]
for s in out["sentences"]:
  for c in s["chunks"]:
    assert c["zh"]=="".join(b for a,b in c["align"])
    for w in re.findall(r"\*\*(.+?)\*\*",c["en"]):
        sb.append(w); assert "("+w+")" in c["zh"],w
    for w in re.findall(r"\*\*[^*]+\*\*\(([^)]+)\)",c["zh"]): assert "**"+w+"**" in c["en"],w
print('英文与文章逐字一致' if ok else '英文不一致', '| 重点词', len(abold), '个，对照里', len(sb), '个，完全一致' if sorted(abold)==sorted(sb) else set(abold)^set(sb))
zh=[(w, re.findall(r"\*\*([^*]+)\*\*\("+re.escape(w)+r"\)", c["zh"])[0]) for s in out["sentences"] for c in s["chunks"] for w in re.findall(r"\*\*(.+?)\*\*",c["en"])]
dup={}
for w,z in zh: dup.setdefault(z,[]).append(w)
print('不同英文用了同一个中文：',{k:v for k,v in dup.items() if len(v)>1} or '无')
# 重点词中文与文章定稿逐个比对（只许格式差别：“的”“了”进粗体）
artzh={e.lower():z for z,e in re.findall(r"\*\*([^*]+)\*\*\(([^)]+)\)",art.split("## 中文")[1].split("## 速查表")[0])}
diff=[(w,z,artzh.get(w.lower())) for w,z in zh if artzh.get(w.lower()) not in (z, z.rstrip('的'), z.replace('了',''))]
print('重点词中文与文章定稿不同：', diff or '无（只有“的”“了”进粗体的格式差别）')
g=[a for s in out["sentences"] for c in s["chunks"] for a,z in c["align"]]
print('句数',len(out["sentences"]),'chunk',sum(len(s["chunks"]) for s in out["sentences"]),'组',len(g),'每组英文词',round(sum(len(re.sub(r"\*\*","",a).split()) for a in g)/len(g),2),'note',sum(1 for s in out["sentences"] for c in s["chunks"] if c.get("note")))
