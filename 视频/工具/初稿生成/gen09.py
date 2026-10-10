import json,re,glob
# 第09篇初稿（逐词对照）：S = [(段, [chunk, ...])]，chunk = ([(英文组, 中文组), ...], 可选 note)
# 2026-10-10 按现行做法：程序打底（英文、重点词与文章逐字核对），重点词中文沿用文章定稿（新版定稿/09）的意思，
# 只按《翻译风格》调格式（作定语的形容词“的”、过去时的“了”放进粗体、语序必须倒过来的整组），再做两视角独立审校。
# 08 定稿时用户定下的新规矩一并照做：短语型用法整体标（T22）、被隔开的中文意思两处都标（T23）、
# 后置定语的 note 写出省略了什么（用户 2026-10-10：“gathered = which was gathered，省略了 which was……让他们更好懂”）。
S=[
(1,[[[("Around Campion, Western Australia,","在西澳大利亚州坎皮恩一带，")]],
    [[("most farmers","大多数农民"),("were","是"),("First World War","第一次世界大战的"),("**veterans**,","**退伍军人**(veterans)，")]],
    [[("**settlers**","他们作为**定居者**(settlers)，"),("placed by a government scheme","由政府计划安置"),("on **marginal** **parcels**","在**贫瘠的/边缘的**(marginal)**小块土地**(parcels)上，"),("of **farmland**.","以这些**农地**(farmland)为生。")],
     "（settlers…：同位语，说明 veterans；placed…：过去分词短语作后置定语，\nplaced = who were placed，省略了 who were）"]]),
(1,[[[("They","他们"),("were","是"),("**inexperienced** **growers**,","**缺乏经验的**(inexperienced)**种植者**(growers)，")]],
    [[("and a quarter had already quit.","已有四分之一的人放弃了土地。")]]]),
(1,[[[("In 1932,","1932年，"),("after drought,","旱灾过后，")]],
    [[("roughly 20,000 emus","约2万只鸸鹋"),("**swarmed** in from **arid** country **in flocks**","**成群地**(in flocks)从**干旱**(arid)地区**蜂拥而至**(swarmed)，")]],
    [[("and **trampled**","**践踏了**(trampled)（指动物破坏）"),("the wheat **crops**.","小麦**庄稼**(crops)。")]]]),
(2,[[[("The farmers'","农民的"),("**plight**","**困境**(plight)"),("took a military turn.","由此走向了军事手段。")]]]),
(2,[[[("**In desperation**,","**绝望之中**(In desperation)，")]],
    [[("a **delegation** of ex-soldiers","一个由退伍士兵组成的**代表团**(delegation)"),("**aired**","**公开表达了**(aired)"),("their **grievances**","他们的**不满/委屈**(grievances)，")]],
    [[("and asked","请求"),("the Defence Minister","国防部长"),("for **machine-guns**.","提供**机枪**(machine-guns)。")],"（air：作动词，公开说出；ask sb for sth：向某人要某物）"]]),
(2,[[[("He agreed,","部长同意了，"),("sending","但派出的"),("not a **battalion**","不是**一个营**(battalion)，"),("but a **detachment**:","而是一支**小分队**(detachment)：")]],
    [[("Major Meredith,","梅雷迪思少校，"),("an **artillery** officer,","一名**炮兵**(artillery)军官，")]],
    [[("with","带着"),("two soldiers,","两名士兵、"),("two Lewis guns,","两挺刘易斯机枪"),("and 10,000 rounds","和1万发"),("of **ammunition**.","**弹药**(ammunition)。")],
     "（sending…：现在分词短语作伴随状语；not A but B：不是A而是B；\n冒号后具体说明 detachment）"]]),
(2,[[[("The **offensive**","**进攻**(offensive)"),("began on 2 November 1932.","于1932年11月2日展开。")]]]),
(3,[[[("At a dam,","在一处水坝，"),("about a thousand birds","约一千只鸟"),("approached","靠近了"),("an **ambush**,","**埋伏/伏击范围**(ambush)，")]],
    [[("but","但"),("a gun **jammed** after a dozen fell.","打倒十来只后，一挺机枪就**卡壳了**(jammed)。")]]]),
(3,[[[("The flocks","鸟群"),("broke","打乱了"),("**formation**","（它们自己的）**队形**(formation)，"),("into","（它们）分成了"),("small, **agile** groups,","**灵活的**(agile)小群体，")]],
    [[("**frustrating**","**挫败了**(frustrating)"),("each **tactical** plan,","每一个**战术**(tactical)计划；")]],
    [[("and a truck-mounted gun","装在卡车上的机枪"),("proved **futile**.","也**徒劳无功**(futile)。")],"（frustrating…：现在分词短语作结果状语；prove + 形容词：结果是……）"]]),
(3,[[[("Six days of","六天的"),("**wasteful** firing","**浪费的**(wasteful)射击"),("spent","花费了/消耗了"),("2,500 rounds","2,500发，"),("on perhaps 50 to 200 birds,","只打死大约50至200只鸟，")]],
    [[("a **ludicrous** return.","这是一个**荒唐可笑的**(ludicrous)回报。")],"（spend A on B：在B上花掉A；\na ludicrous return：同位语，评价前面这件事）"]]),
(3,[[[("After **parliamentary** questions","在**议会**(parliamentary)质询"),("and press **ridicule**,","和报界**嘲笑/嘲讽**(ridicule)之后，")]],
    [[("an **embarrassing** **withdrawal**","一场**尴尬的**(embarrassing)**撤退**(withdrawal)"),("came","发生在"),("on 8 November,","11月8日；")]],
    [[("though","不过"),("shooting restarted within days.","没过几天，射击又重新开始了。")]]]),
(4,[[[("Meredith","梅雷迪思"),("was recalled on 10 December.","于12月10日被召回。")]]]),
(4,[[[("His **memo**'s","他在**备忘录**(memo)里开列的"),("**inventory**","**清单**(inventory)"),("counted","计数（显示），"),("986 kills from 9,860 rounds,","9,860发打死了986只，")]],
    [[("a **ratio**","**比例**(ratio)是"),("of ten **bullets**","十发**子弹**(bullets)"),("to one bird.","对一只鸟。")],"（a ratio of A to B：A比B的比例；\na ratio…：同位语，说明前面的数字）"]]),
(4,[[[("He","他"),("**likened**","**把**(likened to)"),("the **resilient** birds'","这些**耐打的**(resilient)鸟的\n{{（人或动物）对困境|resilient}}\n{{有承受力的，有复原力的|resilient}}"),("**toughness**","**坚韧**(toughness)"),("**to**","**比作**(likened to)"),("the **armour** of tanks.","坦克的**装甲**(armour)。")],"（liken A to B：把A比作B）"]]),
(4,[[[("Five weeks of","五个星期的"),("**warfare**","**战事**(warfare)"),("had barely","几乎没有"),("dented","削弱"),("the **hardy** flocks'","这些**顽强的**(hardy)鸟群的"),("**endurance**.","**耐受力/抗造力**(endurance)。")],"（dent：本义压出凹痕，这里指削弱）"]]),
(5,[[[("Later","后来"),("**pleas** for **reinforcements**","请求**增援**(reinforcements)的**恳求**(pleas)"),("were refused,","都遭到拒绝，")]],
    [[("and **intervention**","**干预**(intervention)"),("**gave way to**","**转变为**(gave way to)（让步于）"),("a **bounty** **sanctioned** by the government.","政府**批准**(sanctioned)的**悬赏**(bounty)。")],
     "（give way to：转变为，让步于；\nsanctioned…：过去分词短语作后置定语，\nsanctioned = which was sanctioned，省略了 which was）"]]),
(5,[[[("This **payout** per bird","这种按只计算的**钱款支出**(payout)（赏金）"),("gave farmers","给了农民"),("**compensation**","**补偿**(compensation)，")]],
    [[("and an **incentive** for **extermination**.","也成为**彻底消灭**(extermination)鸸鹋的**激励**(incentive)。")]]]),
(5,[[[("Farmers","农民"),("claimed over 57,000 **payments** in six months of 1934,","在1934年的六个月里领取了5.7万多笔（赏金）**支付**(payments)，")]],
    [[("more than fifty-seven times Meredith's 986 kills.","是梅雷迪思那986只战果的五十七倍多。")],"（claim：这里指申领；fifty-seven times + 名词：是……的五十七倍）\n（结局：军队打了五个星期，只打死986只；政府改成悬赏，\n让农民自己打、按只领赏金，1934年半年里就领了5.7万多笔，\n也就是打死了5.7万多只，是军队战果的五十七倍多。\n可见悬赏的效率远远高于出动军队：对农民是好结局，\n既拿到了补偿，又有了动力；对军队则是一场难堪的失败。）"]]),
]
# 2026-10-10 两视角独立审校后我逐条判定（见 制作记录/09.md）：采纳细切分组、注释分行与改准、恢复文章原话（结成鸟群…蜂拥而至、他在备忘录里开列的清单、已有四分之一的人放弃了土地）、
# 作定语的形容词带“的”（浪费的射击、荒唐可笑的回报）；涉及定稿用词的（parcels/farmland、payments、swarmed in、撤出/撤退、走向/转向、（军队）干预）只作建议交用户定。
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
import os
if os.path.exists("scripts/09.json"):                      # 保留后来写进脚本的核对确认、列举逗号、结尾句等（初稿程序只管句子）
    old=json.load(open("scripts/09.json"))
    for k_,v_ in old.items():
        if k_ not in ("no","title_en","title_zh","title_fx","sentences"): out[k_]=v_
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
        sb.append(w); assert "("+w+")" in c["zh"] or any(w in k.split() for k in re.findall(r"\*\*[^*]+\*\*\(([^)]+)\)",c["zh"])),w
    for w in re.findall(r"\*\*[^*]+\*\*\(([^)]+)\)",c["zh"]): assert "**"+w+"**" in c["en"] or all("**"+x+"**" in c["en"] for x in w.split()),w
print('英文与文章逐字一致' if ok else '英文不一致', '| 重点词', len(abold), '个，对照里', len(sb), '个，完全一致' if sorted(abold)==sorted(sb) else set(abold)^set(sb))
zh=[(e, z) for s in out["sentences"] for c in s["chunks"] for e, z in dict((e_, z_) for z_, e_ in re.findall(r"\*\*([^*]+)\*\*\(([^)]+)\)", c["zh"])).items()]
dup={}
for w,z in zh: dup.setdefault(z,[]).append(w)
print('不同英文用了同一个中文：',{k:v for k,v in dup.items() if len(v)>1} or '无')
# 重点词中文与文章定稿逐个比对（只许格式差别：“的”“了”进粗体）
artzh={e.lower():z for z,e in re.findall(r"\*\*([^*]+)\*\*\(([^)]+)\)",art.split("## 中文")[1].split("## 速查表")[0])}
diff=[(w,z,artzh.get(w.lower())) for w,z in zh if artzh.get(w.lower()) not in (z, z.rstrip('的'), z.replace('了',''))]
print('重点词中文与文章定稿不同：', diff or '无（只有“的”“了”进粗体的格式差别）')
g=[a for s in out["sentences"] for c in s["chunks"] for a,z in c["align"]]
print('句数',len(out["sentences"]),'chunk',sum(len(s["chunks"]) for s in out["sentences"]),'组',len(g),'每组英文词',round(sum(len(re.sub(r"\*\*","",a).split()) for a in g)/len(g),2),'note',sum(1 for s in out["sentences"] for c in s["chunks"] if c.get("note")))
