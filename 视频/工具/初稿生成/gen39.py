import json,re,glob,os
# 第39篇初稿（逐词对照）：S = [(段, [chunk, ...])]，chunk = ([(英文组, 中文组), ...], 可选 note)
# 2026-11-03 重点词中文沿用文章定稿（铁律），只按《翻译风格》调格式；三项并列加牛津逗号（T18）；不用破折号（T36）；英文没引号中文不加。
S=[
(1,[[[("The Y2K **bug**,","Y2K **漏洞**(bug)，"),("or **millennium** bug,","又称**千年**(millennium)虫，"),("began as a **shortcut**.","起初只是一条**捷径**(shortcut)。")],
     "（Y2K：Year 2000 的缩写，K 代表“千”；\nor：或者说，引出另一个名称）"]]),
(1,[[[("When","当年"),("memory and **hardware**","内存和**硬件**(hardware)"),("were **costly**,","都很**昂贵**(costly)，")],
     "（When…：时间状语从句）"],
    [[("**programmers**","**程序员**(programmers)"),("stored years","便把年份存成"),("as two **digits**,","两位**数字**(digits)，"),("writing","用"),("\"99\"","“99”"),("for 1999.","表示1999年。")],
     "（store A as B：以 B 的形式存储 A；\nwriting…：现在分词短语作伴随状语）"]]),
(1,[[[("That","这种"),("**compact**","**简洁紧凑的**(compact)"),("**code**","**代码**(code)"),("hid","暗藏着"),("an **ambiguity**:","一种**歧义**(ambiguity)：")]],
    [[("a machine","机器"),("might read \"00\" as 1900,","可能把“00”读成1900年，")],
     "（read A as B：把 A 读成 B）"],
    [[("**corrupting**","从而**搞错**(corrupting)"),("calculations of interest, ages, or **deadlines**.","利息、年龄或**截止日期**(deadlines)的计算。")],
     "（corrupting…：现在分词短语作结果状语）"]]),
(2,[[[("Governments and firms","各国政府和企业"),("**braced for**","都在**严阵以待**(braced for)，**准备迎接**(braced for)"),("**chaos**.","一场**混乱**(chaos)。")],
     "（brace for sth：准备应对（不好的事））"]]),
(2,[[[("In February 1998","1998年2月，"),("President Clinton","美国总统克林顿"),("created","设立了"),("a **council**","一个**委员会**(council)"),("to **coordinate**","来**协调**(coordinate)"),("America's effort.","全美的应对工作。")],
     "（to coordinate…：不定式作目的状语）"]]),
(2,[[[("**Consultants**","**顾问**(Consultants)们"),("**audited**","**审查了**(audited)"),("**legacy** systems","**遗留**(legacy)系统，")],
     "（legacy systems：遗留系统，\n指仍在使用的旧计算机系统）"],
    [[("and **patched** **faulty** date logic.","并给**有缺陷的**(faulty)日期处理逻辑**打上补丁**(patched)。")],
     "（patch A：给 A 打补丁）"]]),
(2,[[[("In November 1999","1999年11月，"),("the Commerce Department","美国商务部"),("estimated","估算，"),("American governments","美国各级政府"),("and **enterprises**","和**企业**(enterprises)"),("would spend","将为此花费"),("about $100bn;","约1,000亿美元；")],
     "（estimated 后省略了 that，引出宾语从句；\n$100bn：100 billion dollars，1,000亿美元）"],
    [[("**projections** of the **global** bill","对**全球**(global)总账单的各种**预测**(projections)"),("ran to","则高达"),("hundreds of billions.","数千亿美元。")],
     "（projections of A：对 A 的预测；\nrun to：（数量）达到）"]]),
(3,[[[("Then","随后，"),("**midnight** struck on 31 December 1999,","1999年12月31日的**午夜**(midnight)钟声敲响，")],
     "（strike：（钟）敲响，过去式 struck）"],
    [[("and little","几乎没"),("went wrong.","出什么问题。")],
     "（little：几乎没有，表否定）"]]),
(3,[[[("Glitches that did **crop up**","确实**冒出来**(crop up)的故障"),("were **sporadic**","也是**零星的**(sporadic)，"),("and mostly **minor**.","而且大多**轻微**(minor)。")],
     "（that did crop up：定语从句修饰 Glitches，\ndid 加强语气，意为“确实”）"]]),
(3,[[[("{{=}}Radiation-monitoring equipment **faltered** at Japan's Shika nuclear plant","日本志贺核电站的辐射监测设备**出了故障**(faltered)，"),("without any threat","但并未威胁"),("to safety,","安全；")],
     "（at Japan's Shika nuclear plant：地点状语；\nwithout any threat to safety：没有威胁到安全）"],
    [[("and a Pentagon","美国国防部"),("ground system that processes **spy**-satellite data","一套处理**间谍**(spy)卫星数据的地面系统"),("failed.","也曾失灵。")],
     "（Pentagon：五角大楼，美国国防部的代称；\nthat processes…：定语从句修饰 ground system）"]]),
(3,[[[("In February 2000","2000年2月，"),("a Senate committee","美国参议院的一个委员会"),("**concluded**","**得出结论**(concluded)，"),("that the **expenditure**","认定这笔**开支**(expenditure)"),("had been **justified**.","是**合理的**(justified)。")],
     "（that…：宾语从句；\nhad been justified：过去完成时的被动语态）"]]),
(4,[[[("Many","许多人"),("saw it differently:","却不这么看："),("the threat","在他们眼里，这一威胁"),("had been **exaggerated**,","被**夸大了**(exaggerated)，"),("even a **hoax**.","甚至是一场**骗局**(hoax)。")],
     "（see A differently：对 A 看法不同；\neven a hoax：前面省略了 had been）"]]),
(4,[[[("Yet","然而，"),("**calm prevailed**","**局面**(calm prevailed)之所以能**保持平静**(calm prevailed)，"),("**largely** because","**很大程度上**(largely)正是因为"),("so much","大量问题"),("had been fixed.","早已修好。")],
     "（calm prevailed：局面保持平静；\nlargely because…：很大程度上是因为……）"]]),
(4,[[[("This is","这就是"),("the preparedness paradox:","防备悖论：")]],
    [[("when **precautions** work,","**预防措施**(precautions)一旦奏效，"),("the danger they **ward off**","它们所**抵御**(ward off)的危险"),("never","就永远不会"),("appears,","出现，")],
     "（they ward off：定语从句，省略了关系代词，\n修饰 the danger）"],
    [[("so it looks **imaginary**.","于是看起来像是**虚构的**(imaginary)。")],
     "（look＋形容词：看起来……）"]]),
(4,[[[("**Tedious** repairs","那些**枯燥乏味的**(Tedious)修复工作"),("earned **mockery**","换来的是**嘲笑**(mockery)，"),("rather than **gratitude**.","而不是**感激**(gratitude)。")],
     "（A rather than B：是 A 而不是 B）"]]),
(5,[[[("Critics noted","批评者指出，"),("that Italy","意大利"),("and South Korea","和韩国"),("spent","花得"),("far less","少得多，"),("yet","结果"),("fared no worse.","也不比别国差。")],
     "（that…：宾语从句；\nfare no worse：情况不比别人差）"]]),
(5,[[[("The **comparison**","但这种**比较**(comparison)"),("**misleads**:","**具有误导性**(misleads)："),("those","那些"),("low","低"),("figures","支出数字"),("often **omitted**","往往**遗漏了**(omitted)"),("what firms","企业自己"),("spent,","的花费，")],
     "（what firms spent：what 引导宾语从句，\n企业花的钱）"],
    [[("and much of","而且很大一部分"),("the **remedial** work","**补救**(remedial)工作"),("replaced","替换的是"),("**obsolete** systems **overdue for** upgrading.","**早该**(overdue for)升级的**过时**(obsolete)系统。")],
     "（overdue for upgrading：后置定语修饰 systems，\n早该升级的）"]]),
(5,[[[("Nobody can say","谁也说不清"),("which dollars were **essential**","哪些钱是**必不可少的**(essential)，"),("and which **excessive**.","哪些是**过度的**(excessive)。")],
     "（and which excessive：省略了 dollars were）"]]),
(5,[[[("**Prevention** that works","奏效的**预防**(Prevention)"),("may leave","留下的可能"),("nothing but","只有"),("an **invoice**,","一张**账单**(invoice)，")],
     "（that works：定语从句修饰 Prevention；\nnothing but：只有）"],
    [[("to be weighed against a **catastrophe** that might have been.","留待与一场本可能发生的**灾难**(catastrophe)相权衡。")],
     "（be weighed against A：与 A 相权衡；\nthat might have been：本可能发生的）\n"
     "（简述：早年内存和硬件昂贵，程序员只用两位数字记年份，\n"
     "“00”可能被读成1900年。1998年2月，克林顿设立委员会协调应对，\n"
     "美国商务部估计美国要花约1,000亿美元。1999年12月31日午夜过后，\n"
     "只出了零星的轻微故障，2000年2月参议院委员会认定开支合理。\n"
     "许多人却说威胁被夸大，这就是防备悖论：预防奏效，危险就不出现，\n"
     "看起来像是虚构的。意大利、韩国花得少也没出事，但这种比较有误导性。）"]]),
]
CONF={
"合组":{
 "S3 might read \"00\" as 1900":"对齐不了：read A as B 中文“把 A 读成 B”，把字结构让宾语提到动词前，拆开语序就乱",
 "S3 calculations of interest, ages, or deadlines":"对齐不了：calculations of A 中文“A 的计算”，of 结构语序必须倒过来",
 "S6 and patched faulty date logic":"对齐不了：patch A 中文“给 A 打上补丁”（文章定稿），宾语 faulty date logic 必须放到“打上补丁”前面",
 "S7 projections of the global bill":"对齐不了：projections of A 中文“对 A 的预测”，of 结构语序必须倒过来",
 "S7 hundreds of billions":"对齐不了：hundreds of billions 是一个数量“数千亿”，拆开不通",
 "S8 midnight struck on 31 December 1999":"对齐不了：on 31 December 1999 是时间状语，中文“1999年12月31日的午夜钟声敲响”时间必须提前",
 "S8 went wrong":"对齐不了：go wrong 是固定说法“出问题”",
 "S9 Glitches that did crop up":"对齐不了：that did crop up 是定语从句修饰 Glitches，中文“确实冒出来的故障”从句必须提前",
 "S10 Radiation-monitoring equipment faltered at Japan's Shika nuclear plant":"对齐不了：at Japan's Shika nuclear plant 是地点状语，中文“日本志贺核电站的辐射监测设备”地点必须提到主语前",
 "S10 without any threat":"对齐不了：without any threat 中文“并未威胁”，介词结构译成动词，拆开不通",
 "S10 ground system that processes spy-satellite data":"对齐不了：that processes spy-satellite data 是定语从句修饰 ground system，中文“处理间谍卫星数据的地面系统”从句必须提前",
 "S12 saw it differently":"对齐不了：see it differently 是固定说法，中文“不这么看”",
 "S14 the preparedness paradox":"对齐不了：preparedness paradox 是一个术语“防备悖论”，拆开不通",
 "S2 stored years":"对齐不了：store A as B 中文“把 A 存成 B”，把字结构，years 和“存成”拆不开",
 "S16 far less":"对齐不了：far less 中文“少得多”，修饰比较级的 far 译成后面的“得多”",
 "S16 fared no worse":"对齐不了：fare no worse 中文“不比别国差”，比较结构拆开不通",
 "S17 obsolete systems overdue for upgrading":"对齐不了：overdue for upgrading 是后置定语修饰 systems，中文“早该升级的过时系统”必须提前",
 "S19 to be weighed against a catastrophe that might have been":"对齐不了：be weighed against A 中文“与 A 相权衡”，A 必须放到“相权衡”前面；that might have been 是定语从句修饰 catastrophe，中文“本可能发生的”必须提前"},
"对齐":{
 "S3-2 might read \"00\" as 1900,":"read A as B 中文“把 A 读成 B”，把字结构语序必须倒过来",
 "S3-3 calculations of interest, ages":"calculations of A 中文“A 的计算”，of 结构语序必须倒过来",
 "S6-2 and patched faulty date logic.":"patch A 中文“给 A 打上补丁”，宾语必须放到动词前",
 "S7-2 projections of the global bill":"projections of A 中文“对 A 的预测”，of 结构语序必须倒过来",
 "S8-1 midnight struck on 31 December":"on 31 December 1999 是时间状语，中文时间必须提前",
 "S9-1 Glitches that did crop up":"that did crop up 是定语从句修饰 Glitches，中文从句必须提前",
 "S10-1 Radiation-monitoring equipment":"at Japan's Shika nuclear plant 是地点状语，中文地点必须提到主语前",
 "S10-2 ground system that processes s":"定语从句修饰 ground system，中文从句必须提前",
 "S14-2 the danger they ward off":"they ward off 是省略关系代词的定语从句，修饰 the danger，中文“它们所抵御的危险”从句必须提前",
 "S17-2 obsolete systems overdue for u":"overdue for upgrading 是后置定语修饰 systems，中文必须提前",
 "S19-1 Prevention that works":"that works 是定语从句修饰 Prevention，中文“奏效的预防”从句必须提前",
 "S19-2 to be weighed against a catast":"be weighed against A 中文“与 A 相权衡”，A 必须放到动词前；定语从句 that might have been 中文必须提前"},
"们":{"S6-1 **(Consultants)们**":"Consultants 是复数，“们”表复数，文章定稿就是“顾问们”"},
"同词异译":{"braced for：严阵以待/准备迎接":"S4 brace for“严阵以待，准备迎接”是同一个意思的两部分（T22/T23 被隔开的每处都标），不是两种译法","calm prevailed：保持平静/局面":"S13 calm prevailed“局面……保持平静”被“之所以能”隔开，是同一个意思的两部分（T22/T23），不是两种译法"},
"短语":{"S3 corrupting … of":"不是搭配：of 属于 calculations of interest，和 corrupting 无关",
 "S7 projections … of":"不是搭配：of 只引出预测的对象（the global bill），projections 单独就是“预测”，速查表 sales projections 也不带 of",
 "S10 faltered … to":"不是搭配：to 属于 threat to safety，和 faltered 无关",
 "S17 omitted … of":"不是搭配：of 属于后一分句 much of the remedial work，和 omitted 无关"},
"是的":{"S9-1 是**零星的**":"文章定稿“也是零星的，而且大多轻微”（铁律：定稿中文意思不改）；were sporadic 判断句",
 "S11-1 是**合理的**":"文章定稿“认定这笔开支是合理的”（铁律：定稿中文意思不改）；had been justified 判断",
 "S14-3 是**虚构的**":"文章定稿“看起来像是虚构的”（铁律：定稿中文意思不改）；looks imaginary 系表结构",
 "S18-1 是**必不可少的**":"文章定稿“哪些钱是必不可少的，哪些是过度的”（铁律）；were essential 判断句，两项对举，去掉“是……的”不通",
 "S18-1 是**过度的**":"文章定稿“哪些是过度的”（铁律）；和前面“是必不可少的”对举"}}
CONF["停顿位置"]={"S1 bug, / or @1.380":"2026-11-03 逐 2.5 ms 看声音（配音指纹 ba906853eb76）：bug 的 /g/ 浊音到 1.275，除阻 1.2775–1.31（重心 2.6–3.7 kHz），1.31–1.35 除阻后的弱元音尾逐渐降到 -49 dB，1.3525–1.383 静音（-55～-62 dB、周期 ≤0.35），1.385 起 or 的元音（1.3925 -13.5 dB、重心 0.9 kHz）；1.380 是两词之间的静音（-60.7 dB），插在这里不切前后词",
 "S14 appears, / so @6.655":"2026-11-03 S14 合成标点 appears; so 重新合成后逐 2.5 ms 看声音：appears 的 /z/ 6.38 收尾（6.39 -53 dB），吸气 6.395–6.6525 由 非人声区间 删掉，6.6525–6.6575 静音 -58～-59 dB，so 的 /s/ 6.66 起；6.655 是两词之间的静音（-58.1 dB），不切前后词",
 "S1 bug, / began @2.440":"2026-11-03 逐 10 ms 看声音：bug 的 /g/ 除阻 2.39–2.43（重心 3.4–4 kHz），2.44 降到 -53.3 dB；之后 2.445–2.675 的吸气声和孤立低频团由 非人声区间 删掉，began 的 /b/ 2.68 起（2.69 -22.9 dB）；2.440 在 /g/ 除阻之后，不切词"}
CONF["非人声"]={"S14 6.3975–6.6525":"2026-11-03 S14 合成标点 appears; so 重新合成后逐 2.5 ms 实测：appears 的 /z/ 6.30–6.38（重心 4–6 kHz）到 6.39 降到 -53 dB，6.395 -57.0 dB；6.4125–6.635 -43～-52 dB、重心 2.5–3 kHz、低频 -5～-21 dB、周期 ≤0.23，是吸气声（A19）；6.6375–6.6575 -55～-59 dB 静音，6.66 起 so 的 /s/ 起音（6.675 -32.9 dB、重心 5.2 kHz），保留","S1 2.433–2.6725（左头紧贴 bug 的 /g/ 除阻尾，落在过零点 2.433；右头 2.6725 -64.6 dB）":"2026-11-03 逐 2.5 ms 实测：/g/ 除阻尾 2.425–2.43 -47 dB，2.4325 低谷 -52.3 dB；2.46–2.59 平稳 -42～-49 dB、重心 2.2–2.7 kHz、低频 -8～-24 dB、周期 0.11–0.37，是吸气声（A19）；2.60–2.62 -38～-45 dB 低频占优的一小团，和 began 之间隔着 2.63–2.67 的静音（-58～-63 dB），不连着词；began 的 /b/ 2.68 起（重心 3.8 kHz）。左头 2.44 -53.3 dB 在 /g/ 除阻之后，右头 2.675 在静音里"}
# 非人声区间新加 2026-11-03 依据（配音指纹 752414198735，dossier 逐 2.5 ms 实测）：
#  S3 [2.595,2.785]、S5 [2.405,2.52]、S7 [2.135458,2.24] 是草稿声音.sh 自动切点找的（程序可定），一并写在这里，免得被这一句的新区间覆盖
#  S3 6.9275–6.9575：hundred, 之后、corrupting 的 /k/ 除阻（6.98）之前，6.935–6.94 孤立 10 ms 一下（-37.9 dB、重心 3.4 kHz、周期 0），两边 -57～-72 dB 静音隔开，不连词，是咔哒
#  S5 2.20–2.26：eight 的 /t/ 除阻 2.09–2.145 之后，2.22–2.24 孤立一团 -38～-50 dB（重心 2.3–2.7 kHz、低频 -12～-20、周期 0.33），两边 -54～-70 dB 静音，不连词
#  S5 2.5425–2.62：2.545–2.58 一团低频 -42～-57 dB（低频 -0～-1），和 President 的 /p/（2.635）隔着 2.59–2.63 的 -62～-73 dB 静音，不连词
#  S6 2.13–2.375083（右头紧贴 and 起音前的低频团，落在过零点 2.375083）：systems 的 /z/ 2.11 收尾后 2.14–2.37 平稳 -47～-56 dB、重心 1.8–2.8 kHz、低频 -9～-19、周期 0.19，是吸气（A19）；2.38–2.43 低频团紧连 and（2.44）保留
#  S7 6.6475–6.9675：enterprises 的 /z/ 6.62 收尾，6.66–6.95 平稳 -39～-45 dB、重心 2.4–3.3 kHz、低频 -13～-27、周期 0.20，是吸气（无标点处）；6.98–7.00 低频团紧连 would 保留
#  S13 1.785–2.02：largely 1.76 收尾，1.81–1.95 -47～-52 dB、重心 1.9–2.6 kHz、低频 -8～-17、周期 0.18，是吸气；1.96–1.98 低频团和 because 的 /b/（2.03）隔着 1.99–2.02 的 -62～-69 dB 静音，不连词
#  S15 1.855208–1.935（左头紧贴 mockery 的元音尾，落在过零点 1.855208）：1.8575–1.92 -49～-58 dB、重心 2.0–2.6 kHz、低频 -10～-22、周期 0.15，是气声；1.935 -64 dB
#  S18 2.625–2.9175：essential 的 /l/ 2.60 收尾，2.65–2.85 -49～-56 dB、重心 2.0–2.3 kHz、低频 -6～-20、周期 0.15–0.19，是吸气；2.86 一下 -48 dB 4 kHz 和 and（2.93）隔着 2.87–2.92 的 -54～-67 dB 静音
out={"no":"39","title_en":"Y2K: The Crisis That Success Erased","title_zh":"千年虫：被成功抹去的危机","title_fx":{"hl":["Crisis","Erased"],"ghost":[]},"sentences":[],"核对确认":CONF,"结尾解说":"简述",
     "说明放宽特批":{"S19":{"倍数":"整屏","依据":"用户 2026-10-25 看 25 简述截图：“以后以后一定要合理的安排，不要压缩成这个样子……这个地方特批一下”（用户同意记录：原话适用以后各篇，26 起沿用）"}},
     "非人声区间":{"S1":[[2.433,2.6725,"紧贴词尾"]],"S3":[[2.595,2.785],[6.9275,6.9575]],"S5":[[2.2,2.26],[2.405,2.52],[2.5425,2.62]],"S6":[[2.13,2.375083,"紧贴词头"]],"S7":[[2.135458,2.24,"紧贴词尾"],[6.6475,6.9675]],"S13":[[1.785,2.02]],"S14":[[6.3975,6.6525]],"S15":[[1.855208,1.935,"紧贴词尾"]],"S18":[[2.625,2.9175]]},
     "合成标点":{"S14":[["appears, so","appears; so"]]},
     "高亮按实际开口":True,"高亮开口门槛":40,
     "术语":{"Clinton":"克林顿","Commerce Department":"美国商务部","Japan":"日本","Shika":"志贺","Pentagon":"美国国防部","Senate":"美国参议院","Italy":"意大利","South Korea":"韩国","America":"美国"}}
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 核对 import 生成并核对
生成并核对(S, out)
