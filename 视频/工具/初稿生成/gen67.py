import json,re,glob,os
# 第67篇初稿（逐词对照）：S = [(段, [chunk, ...])]，chunk = ([(英文组, 中文组), ...], 可选 note)
# 2026-11-08 重点词中文沿用文章定稿（铁律）；中英尽量对齐；不用破折号（T36）；三项并列加牛津逗号（T18）。
S=[
(1,[[[("Marcel Ravidat, 18,","18岁的马塞尔·拉维达")],
     "（18：插入语，补充说明年龄）"],
    [[("was on a **woodland** **stroll** near Montignac with Robot, his **canine** companion,","带着他的**犬类**(canine)伙伴罗伯特在蒙蒂尼亚克附近的**林地**(woodland)里**散步**(stroll)，")],
     "（his canine companion：同位语，补充说明 Robot）"],
    [[("when","这时"),("it began","罗伯特开始"),("**sniffing** at a **hollow** left by a **toppled** tree.","在一棵**倒伏**(toppled)的树留下的**坑洞**(hollow)边**嗅来嗅去**(sniffing)。")],
     "（it 指 Robot；\nleft by a toppled tree：过去分词短语作后置定语，修饰 hollow）"]]),
(1,[[[("On 12 September 1940","1940年9月12日，"),("he","他"),("came back with three other boys","带着另外三个男孩回到这里，")]],
    [[("for","来了一次"),("an **adventurous**","**富于冒险的**(adventurous)"),("**excursion**,","**出游**(excursion)，")],
     "（for：表示目的）"],
    [[("and the four","四个"),("**explorers**","**探险者**(explorers)"),("climbed down into","爬进了"),("the **darkness**.","**黑暗**(darkness)之中。")]]]),
(2,[[[("In later","在后来的"),("**retellings**,","**复述**(retellings)中，")]],
    [[("Ravidat","拉维达"),("**embroidered** his **anecdote**","给这段**轶事**(anecdote)**添油加醋**(embroidered)，"),("with a","加入了一个"),("**dramatic**","**戏剧性的**(dramatic)"),("twist.","转折。")],
     "（embroider A with B：用 B 给 A 添油加醋）"]]),
(2,[[[("Robot, he said,","他说，罗伯特"),("had fallen into","掉进了"),("the cave.","洞里。")],
     "（he said：插入语；\nhad fallen：过去完成时，掉洞在讲述之前）"]]),
(2,[[[("That **fanciful**","这个**离奇**(fanciful)的"),("**mishap**","**意外**(mishap)"),("is a","纯属"),("**fabrication**.","**编造**(fabrication)。")]]]),
(2,[[[("The animal","那只狗"),("only","只是"),("nosed about the hole,","在洞口嗅了嗅，")],
     "（nose about：到处嗅）"],
    [[("and the **pivotal**","**关键的**(pivotal)"),("**initiative**","**主动行动**(initiative)"),("was the boys' own.","完全出自几个男孩。")],
     "（the boys' own：男孩们自己的，own 后省略了 initiative）"]]),
(2,[[[("**Ironically**,","**讽刺的是**(Ironically)，"),("the invented","虚构的"),("fall","那一跤"),("made","让"),("the dog","狗"),("the hero of the story.","成了故事的主角。")],
     "（make A B：使 A 成为 B）"]]),
(3,[[[("Some 680","约680个"),("painted figures","彩绘形象"),("and","和"),("1,500 **engravings**","1,500幅**雕刻图案**(engravings)"),("cover","布满"),("the rock.","岩壁。")],
     "（some：大约，用在数字前）"]]),
(3,[[[("The **artwork**","这些**艺术作品**(artwork)"),("is usually","通常"),("dated to","被认为"),("between 17,000","距今1.7万"),("and 22,000 years ago;","至2.2万年；")],
     "（be dated to：年代被断定为）"],
    [[("its","它们的"),("**creators**,","**创作者**(creators)"),("our distant","是我们遥远的"),("**ancestors**,","**祖先**(ancestors)，"),("lived in","生活在"),("**antiquity**.","**远古**(antiquity)时代。")],
     "（our distant ancestors：同位语，补充说明 creators）"]]),
(3,[[[("Horses,","马、"),("**bulls**,","**公牛**(bulls)"),("and stags","和雄鹿"),("are among the animals **depicted** in **pigments** on the **murals**.","都是**壁画**(murals)上用**颜料**(pigments)**描绘**(depicted)的动物。")],
     "（be among：是……之一；\ndepicted in pigments on the murals：\n过去分词短语作后置定语，修饰 animals）"]]),
(3,[[[("The paintings'","这些画作的"),("**fragility**","**脆弱**(fragility)"),("soon","很快就"),("became clear.","显现出来。")]]]),
(4,[[[("Lascaux opened to the public on 14 July 1948,","1948年7月14日，拉斯科向公众开放，")]],
    [[("and **tourism**","**旅游业**(tourism)"),("brought","带来了"),("an **influx** of about 1,200 visitors a day.","每天约1,200名游客的**涌入**(influx)。")],
     "（an influx of A：A 的涌入）"]]),
(4,[[[("The **throng**","**人群**(throng)"),("**exhaled**","**呼出**(exhaled)"),("carbon **dioxide**","**二氧化碳**(dioxide)，")]],
    [[("and added","带来"),("heat,","热量、"),("**humidity**,","**湿气**(humidity)"),("and","和"),("**contaminants**,","**污染物**(contaminants)，")]],
    [[("and the **deterioration** of the paintings","壁画的**退化**(deterioration)"),("became","变得"),("plain to see.","肉眼可见。")],
     "（plain to see：一眼就能看到）"]]),
(4,[[[("In 1963","1963年，"),("the site","洞穴"),("closed to the public,","对公众关闭，")]],
    [[("followed by","随后进行了"),("**restoration**","**修复**(restoration)，"),("and daily","并开始每日"),("**inspection**.","**检查**(inspection)。")],
     "（followed by…：过去分词短语，表示随后发生的事）"]]),
(5,[[[("Lascaux joined UNESCO's World Heritage List in 1979,","1979年，拉斯科被列入联合国教科文组织《世界遗产名录》；")]],
    [[("and Lascaux II, a **meticulously**","1983年，**精心**(meticulously)"),("made","制作的"),("**partial**","**局部**(partial)"),("**facsimile**, opened in 1983.","**复制品**(facsimile)拉斯科二号开放。")],
     "（a meticulously made partial facsimile：同位语，\n补充说明 Lascaux II）"]]),
(5,[[[("A white **fungus** **invaded** the walls in a 2001 **outbreak**,","2001年，一种白色**真菌**(fungus)**爆发**(outbreak)，**侵入**(invaded)洞壁；")],
     "（in a 2001 outbreak：在2001年的一次爆发中）"],
    [[("and black **stains** spread after chemical treatment.","化学处理后，黑色**污斑**(stains)蔓延开来。")]]]),
(5,[[[("Lascaux IV opened in December 2016.","2016年12月，拉斯科四号开放。")]]]),
(5,[[[("**Admirers** now","如今**仰慕者**(Admirers)"),("meet the bulls only in a **recreation**,","只能在**复原品**(recreation)中见到那些公牛，")],
     "（only in…：只在……中）"],
    [[("the originals","原洞"),("being **inaccessible** to them.","对他们来说**无法进入**(inaccessible)。")],
     "（the originals being…：独立主格，补充说明原因）\n"
     "（简述：1940年，18岁的马塞尔·拉维达带狗罗伯特在蒙蒂尼亚克附近散步，狗在倒伏的树留下的坑洞边嗅来嗅去；9月12日，他和另外三个男孩爬进了洞里。\n"
     "拉维达后来说狗掉进了洞里，这是编造，关键的行动出自男孩们。\n"
     "洞里约有680个彩绘形象和1,500幅雕刻，通常认为距今1.7万至2.2万年。\n"
     "拉斯科1948年开放后，每天约1,200名游客带来二氧化碳、热量和湿气，壁画退化，1963年洞穴关闭。\n"
     "1979年拉斯科列入世界遗产，1983年复制品拉斯科二号开放，2001年洞壁爆发白色真菌，2016年拉斯科四号开放，如今游客只能看复制品。）"]]),
]
G={
 "S1 was on a woodland stroll near Montignac with Robot, his canine companion":"对齐不了：伴随状语 with Robot, his canine companion 中文“带着他的犬类伙伴罗伯特”必须放到前面；地点状语 near Montignac 中文“在蒙蒂尼亚克附近”放到动词前；be on a stroll 中文“散步”放最后",
 "S1 sniffing at a hollow left by a toppled tree":"对齐不了：left by a toppled tree 是后置定语，修饰 hollow，中文“一棵倒伏的树留下的坑洞”必须提前；at a hollow 中文“在……边”放到“嗅来嗅去”前",
 "S2 came back with three other boys":"对齐不了：伴随状语 with three other boys 中文“带着另外三个男孩”必须放到动词“回到这里”前",
 "S6 nosed about the hole":"对齐不了：地点 the hole 中文“在洞口”必须放到“嗅了嗅”前；nose about 是一个说法，拆开不通",
 "S6 was the boys' own":"对齐不了：be the boys' own 意思是“是男孩们自己的”，中文“完全出自几个男孩”是整体说法，拆开不通",
 "S7 the hero of the story":"对齐不了：the hero of the story 中文“故事的主角”必须倒过来",
 "S8 painted figures":"对齐不了：painted figures 中文“彩绘形象”是一个词组，拆开不通",
 "S9 and 22,000 years ago":"对齐不了：between A and B years ago 中文“距今 A 至 B 年”，“距今”(ago) 必须提前；数字中文写作“1.7万”“2.2万”，不能拆",
 "S10 are among the animals depicted in pigments on the murals":"对齐不了：depicted in pigments on the murals 是后置定语，修饰 animals，中文“壁画上用颜料描绘的动物”必须提前；be among 中文“都是”",
 "S11 became clear":"对齐不了：become clear 中文“显现出来”是一个说法，拆开不通",
 "S12 Lascaux opened to the public on 14 July 1948":"对齐不了：时间状语 on 14 July 1948 中文“1948年7月14日”必须放到句首；to the public 中文“向公众”放到动词“开放”前",
 "S12 an influx of about 1,200 visitors a day":"对齐不了：an influx of A 中文“A 的涌入”必须倒过来；a day 中文“每天”必须提前",
 "S13 plain to see":"对齐不了：plain to see 是固定说法，中文“肉眼可见”拆开不通",
 "S14 closed to the public":"对齐不了：to the public 中文“对公众”必须放到动词“关闭”前",
 "S15 and Lascaux II, a meticulously":"对齐不了：时间状语 in 1983 中文“1983年”必须放到句首；专名 Lascaux II 中文“拉斯科二号”放在同位语后面",
 "S15 facsimile, opened in 1983":"对齐不了：Lascaux II 是同位语 a … facsimile 的中心词，中文“复制品拉斯科二号”放在一起；时间“1983年”已提到句首",
 "S16 A white fungus invaded the walls in a 2001 outbreak":"对齐不了：时间状语 in a 2001 outbreak 中文“2001年”必须放到句首，“爆发”放到“侵入”前（先爆发、后侵入）",
 "S16 and black stains spread after chemical treatment":"对齐不了：时间状语 after chemical treatment 中文“化学处理后”必须放到句首",
 "S17 Lascaux IV opened in December 2016":"对齐不了：时间状语 in December 2016 中文“2016年12月”必须放到句首",
 "S18 meet the bulls only in a recreation":"对齐不了：地点 in a recreation 中文“在复原品中”必须放到动词“见到”前",
}
DZ={}
CONF={"合组":G,"对齐":DZ}
out={"no":"67","title_en":"The Cave Found by a Dog","title_zh":"几个少年和一只狗发现的洞穴","title_fx":{"hl":["Cave","Dog"],"ghost":[]},"sentences":[],"核对确认":CONF,"结尾解说":"简述",
     "高亮按实际开口":True,"高亮开口门槛":40,
     "术语":{"Marcel Ravidat":"马塞尔·拉维达","Ravidat":"拉维达","Montignac":"蒙蒂尼亚克","Robot":"罗伯特","Lascaux":"拉斯科","UNESCO":"联合国教科文组织","World Heritage List":"世界遗产名录","Lascaux II":"拉斯科二号","Lascaux IV":"拉斯科四号"}}
out.update({"停顿插入点":{"S4":{"1":[0.64375,"交界"]},"S10":{"2":[1.272292,"交界"]},"S13":{"2":[4.566583,"交界"]}},
 "非人声区间":{"S2":[[6.815,6.905375,"紧贴词头"]],"S4":[[0.994667,1.19,"紧贴词尾"]]}})
# 2026-11-09 逐 2.5/1.25 ms 实测（w 秒，看.py）：S4 Robot（ɹoʊbˈoʊ）的 /oʊ/ 浊音一直到 0.640（-12～-15 dB、重心 150–320 Hz），0.645 起 he 的 /h/（重心 0.9→4.3 kHz），原插入点 0.585 在元音中间，改到交界过零 0.64375；
# S10 bulls 的 /z/ 擦音 1.195–1.271（重心 5 kHz），1.2732 起 and 的元音（重心 1.1 kHz→300 Hz），插在交界过零 1.272292，/z/ 整段留在停顿前（K131）；
# S13 humidity 的 /i/ 到 4.559，4.56–4.566 是 and 起音前的弱声（-32～-40 dB），4.5675 起 and 的元音（-17 dB），插在元音前过零 4.566583，避免渐强压住弱起音（K131）；
# S2 excursion, 停顿后 6.815–6.905 吸气（-48～-59 dB、重心 2.3–3.0 kHz、低频 -9～-24 dB），6.905–6.93 低频浊音前导（低频 -2～-4）、6.9325 起 and，保留前导；
# S4 said 的 /d/ 浊音到 0.990（低频 -0.2），0.995–1.19 弱气声（-50～-58 dB、重心 1.0–2.5 kHz、低频 -4～-20），删掉，1.225 起 had 的 /h/ 不动
CONF["停顿位置"]={
 "S4 Robot, / he @0.644":"2026-11-09 逐 2.5 ms 实测（S4 w）：Robot（ɹoʊbˈoʊ）末音节 /oʊ/ 浊音到 0.640（-12～-15 dB、重心 150–320 Hz、低频 -0～-0.5），0.645 起 he 的 /h/（重心 0.9→4.3 kHz）；停顿 0.644 落在两词交界（时长模型把 /oʊ/ 算短了）",
 "S4 said, / had @1.005":"2026-11-09 逐 2.5 ms 实测（S4 w）：said 的 /d/ 浊音到 0.990（低频 -0.2），0.9947–1.19 弱气声已按非人声区间删成静音，1.225 起 had 的 /h/；停顿 1.005–1.21 落在两词之间的静音里",
 "S10 Horses, / bulls, @0.695":"2026-11-09 逐 2.5 ms 实测（S10 w）：Horses 的 /z/ 擦音 0.62–0.675（重心 5 kHz），0.695 是低谷 -43.5 dB，0.70–0.85 是 bulls 的 /b/ 浊音杠（周期 0.45–0.53、重心 220–460 Hz、低频 -0.5～-2）；停顿 0.695 落在两词交界（时长模型没算 /b/ 浊音杠）",
 "S10 bulls, / and @1.272":"2026-11-09 逐 1.25 ms 实测（S10 w）：bulls 的 /z/ 擦音 1.195–1.271（重心 5 kHz），1.2732 起 and 的元音（重心 1.1 kHz→300 Hz）；停顿 1.272292 是交界过零点",
}
CONF["非人声"]={"16.66–16.68s": {"配音指纹": "2859954961e6", "依据": "2026-11-09 逐 2.5 ms 实测（dossier_67 #1）：S2 w 0.945–0.960s：of September 之间，of 的 /v/ 清化收尾、紧接 September 的 /s/（0.985 起 5.7 kHz），在 September 的时长 0.897–1.392 内；词的一部分", "实测": {"最响dB": -34.4, "重心Hz": 3298, "周期": 0.0, "低频dB": -22.9}}, "18.25–18.27s": {"配音指纹": "2859954961e6", "依据": "2026-11-09 逐 2.5 ms 实测（dossier_67 #2）：S2 w 2.615–2.630s：forty 的 /i/ 浊音收尾（周期 0.28、低频 -0.4 dB，词 1.986–2.654 内）；词尾", "实测": {"最响dB": -45.4, "重心Hz": 2346, "周期": 0.0, "低频dB": -0.4}}, "32.02–32.08s": {"配音指纹": "2859954961e6", "依据": "2026-11-09 逐 2.5 ms 实测（dossier_67 #3）：S3 w 4.990–5.045s：twist. 句末 /t/ 除阻（重心 4 kHz、低频 -16 dB，词 4.540–5.089 内）；词尾塞音除阻", "实测": {"最响dB": -36.6, "重心Hz": 4035, "周期": 0.17, "低频dB": -16.6}}, "38.63–38.69s": {"配音指纹": "2859954961e6", "依据": "2026-11-09 逐 2.5 ms 实测（dossier_67 #4）：S5 w 1.370–1.425s：mishap 词内（词 0.913–1.544 内，周期 0.22、低频 -3 dB 浊音）；词的一部分", "实测": {"最响dB": -33.7, "重心Hz": 1611, "周期": 0.19, "低频dB": -3.2}}, "43.92–43.94s": {"配音指纹": "2859954961e6", "依据": "2026-11-09 逐 2.5 ms 实测（dossier_67 #5）：S6 w 2.990–3.005s：the 的元音收尾、接 pivotal 的 /p/ 闭塞（低频 -0.1 dB、周期 0.26）；词的一部分", "实测": {"最响dB": -46.7, "重心Hz": 2057, "周期": 0.0, "低频dB": -0.1}}, "46.30–46.38s": {"配音指纹": "2859954961e6", "依据": "2026-11-09 逐 2.5 ms 实测（dossier_67 #6）：S6 w 5.370–5.455s：own. 句末 /n/ 鼻音收尾（周期 0.31、低频 -8.6 dB，词 5.033–5.515 内）；词尾", "实测": {"最响dB": -38.7, "重心Hz": 1957, "周期": 0.26, "低频dB": -8.6}}, "58.13–58.16s": {"配音指纹": "2859954961e6", "依据": "2026-11-09 逐 2.5 ms 实测（dossier_67 #7）：S8 w 5.415–5.435s：engravings 的 /z/ 擦音残尾（重心 4.8 kHz，-48 dB，紧接词尾 5.412）；词尾", "实测": {"最响dB": -48.4, "重心Hz": 4823, "周期": 0.29, "低频dB": -3.9}}, "72.71–72.72s": {"配音指纹": "2859954961e6", "依据": "2026-11-09 逐 2.5 ms 实测（dossier_67 #8）：S10 w 0.700–0.715s：bulls 的 /b/ 浊音杠开头（周期 0.40、重心 460 Hz、低频 -1.1 dB），停顿插在 0.695 低谷；词头的一部分", "实测": {"最响dB": -32.6, "重心Hz": 460, "周期": 0.0, "低频dB": -1.1}}, "77.34–77.44s": {"配音指纹": "2859954961e6", "依据": "2026-11-09 逐 2.5 ms 实测（dossier_67 #9）：S10 w 5.250–5.345s：murals. 句末 /lz/（词 4.949–5.515 内，周期 0.23、低频 -3.9 dB）；词尾", "实测": {"最响dB": -37.7, "重心Hz": 1657, "周期": 0.23, "低频dB": -3.9}}, "87.54–87.56s": {"配音指纹": "2859954961e6", "依据": "2026-11-09 逐 2.5 ms 实测（dossier_67 #10）：S12 w 5.275–5.295s：and 的浊音起音（周期 0.38、低频 -0.4 dB，紧接非人声区间止点 5.277）；词头的一部分", "实测": {"最响dB": -47.2, "重心Hz": 2506, "周期": 0.38, "低频dB": -0.4}}, "92.57–92.67s": {"配音指纹": "2859954961e6", "依据": "2026-11-09 逐 2.5 ms 实测（dossier_67 #11）：S12 w 10.305–10.405s：day. 句末 /eɪ/ 收尾气化（词 10.084–10.467 内，低频 -5.8 dB）；词尾", "实测": {"最响dB": -35.5, "重心Hz": 3288, "周期": 0.21, "低频dB": -5.8}}, "99.11–99.12s": {"配音指纹": "2859954961e6", "依据": "2026-11-09 逐 2.5 ms 实测（dossier_67 #12）：S13 w 5.375–5.390s：contaminants 词内（词 4.762–5.982 内，低频 -2.8 dB）；词的一部分", "实测": {"最响dB": -33.6, "重心Hz": 1068, "周期": 0.0, "低频dB": -2.8}}, "102.80–102.88s": {"配音指纹": "2859954961e6", "依据": "2026-11-09 逐 2.5 ms 实测（dossier_67 #13）：S13 w 9.285–9.365s：see. 句末 /iː/ 收尾气化（词 9.043–9.408 内，低频 -2.6 dB）；词尾", "实测": {"最响dB": -36.4, "重心Hz": 3223, "周期": 0.26, "低频dB": -2.6}}, "102.83–102.84s": {"配音指纹": "2859954961e6", "依据": "2026-11-09 逐 2.5 ms 实测（dossier_67 #14）：S13 w 9.320–9.335s：see. 句末 /iː/ 收尾（周期 0.34，词内）；词尾", "实测": {"最响dB": -38.5, "重心Hz": 3454, "周期": 0.0, "低频dB": -1.4}}, "105.38–105.47s": {"配音指纹": "2859954961e6", "依据": "2026-11-09 逐 2.5 ms 实测（dossier_67 #15）：S14 w 1.525–1.620s：sixty-three 的 /iː/ 收尾（词 0.825–1.708 内，低频 -6.9 dB）；词尾", "实测": {"最响dB": -37.3, "重心Hz": 2387, "周期": 0.25, "低频dB": -6.9}}, "117.72–117.74s": {"配音指纹": "2859954961e6", "依据": "2026-11-09 逐 2.5 ms 实测（dossier_67 #16）：S15 w 6.155–6.175s：Lascaux two 的 /uː/ 收尾（周期 0.33、低频 -1.2 dB，词 5.865–6.588 内）；词尾", "实测": {"最响dB": -41.6, "重心Hz": 1557, "周期": 0.33, "低频dB": -1.2}}, "122.88–122.97s": {"配音指纹": "2859954961e6", "依据": "2026-11-09 逐 2.5 ms 实测（dossier_67 #17）：S15 w 11.270–11.355s：eighty-three. 句末 /iː/ 收尾气化（词 10.672–11.392 内，低频 -3.5 dB）；词尾", "实测": {"最响dB": -38.5, "重心Hz": 3329, "周期": 0.26, "低频dB": -3.5}}, "128.00–128.06s": {"配音指纹": "2859954961e6", "依据": "2026-11-09 逐 2.5 ms 实测（dossier_67 #18）：S16 w 4.060–4.120s：outbreak, 停顿前 /k/ 除阻（重心 4.5 kHz、低频 -19 dB，词 3.572–4.538 内）；词尾塞音除阻", "实测": {"最响dB": -30.6, "重心Hz": 4491, "周期": 0.16, "低频dB": -19.2}}, "128.46–128.47s": {"配音指纹": "2859954961e6", "依据": "2026-11-09 逐 2.5 ms 实测（dossier_67 #19）：S16 w 4.525–4.540s：and 的浊音起音（低频 -0.3 dB，紧接非人声区间止点 4.5236）；词头的一部分", "实测": {"最响dB": -44.7, "重心Hz": 2243, "周期": 0.0, "低频dB": -0.3}}, "131.28–131.31s": {"配音指纹": "2859954961e6", "依据": "2026-11-09 逐 2.5 ms 实测（dossier_67 #20）：S16 w 7.340–7.370s：treatment. 句末 /t/ 除阻（除阻加强处，词 6.893–7.418 内）；词尾塞音除阻", "实测": {"最响dB": -42.0, "重心Hz": 2665, "周期": 0.15, "低频dB": -10.6}}, "140.21–140.30s": {"配音指纹": "2859954961e6", "依据": "2026-11-09 逐 2.5 ms 实测（dossier_67 #21）：S18 w 3.465–3.555s：recreation, 的 /ʃən/ 鼻音收尾（低频 -2.9 dB、周期 0.25，词 2.727–3.973 内）；词尾", "实测": {"最响dB": -35.2, "重心Hz": 1706, "周期": 0.25, "低频dB": -2.9}}, "141.00–141.03s": {"配音指纹": "2859954961e6", "依据": "2026-11-09 逐 2.5 ms 实测（dossier_67 #22）：S18 w 4.050–4.075s：the 的 /ð/ 浊擦起音（低频 -1.2 dB，紧接 4.080 的 ðɪ）；词头的一部分", "实测": {"最响dB": -31.0, "重心Hz": 4760, "周期": 0.28, "低频dB": -1.2}}, "144.17–144.26s": {"配音指纹": "2859954961e6", "依据": "2026-11-09 逐 2.5 ms 实测（dossier_67 #23）：S18 w 7.215–7.310s：them. 句末 /m/ 鼻音收尾（周期 0.31、低频 -6.2 dB，词 7.022–7.364 内）；词尾", "实测": {"最响dB": -36.3, "重心Hz": 1591, "周期": 0.31, "低频dB": -6.2}}}
CONF["停顿位置"]["S13 humidity, / and @4.567"]="2026-11-09 逐 1.25 ms 实测（S13 w）：humidity 的 /i/ 到 4.559，4.56–4.566 是 and 起音前的弱声（-32～-40 dB），4.5675 起 and 的元音（-17 dB）；停顿 4.566583 落在元音前的过零点"
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 核对 import 生成并核对
生成并核对(S, out)
