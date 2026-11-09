import json,re,glob,os
# 第68篇初稿（逐词对照）：S = [(段, [chunk, ...])]，chunk = ([(英文组, 中文组), ...], 可选 note)
# 2026-11-08 重点词中文沿用文章定稿（铁律）；中英尽量对齐、标色优先；不用破折号（T36）；三项并列加牛津逗号（T18）；形容词“的”并进粗体（T38）。
S=[
(1,[[[("In 1936","1936年，"),("the **colossal** Hindenburg","**巨大的**(colossal)兴登堡号"),("made 17 Atlantic round trips,","完成了17次跨大西洋往返飞行，")]],
    [[("a **marvel** of **luxury** and **glamour**.","是**奢华**(luxury)与**魅力**(glamour)的**奇观**(marvel)。")],
     "（a marvel of…：同位语，补充说明前面整句）"]]),
(1,[[[("Its **amenities**","它的**设施**(amenities)"),("included","包括"),("a **lounge**","一间**休息厅**(lounge)，"),("and, that year,","那一年还有"),("a grand piano.","一架三角钢琴。")],
     "（that year：插入语，指1936年）"]]),
(1,[[[("An American **embargo** on **helium** **export**","美国对**氦气**(helium)**出口**(export)实行**禁运**(embargo)，")],
     "（embargo on…：对……的禁运）"],
    [[("had left the ship relying on hydrogen.","这艘飞艇只能依靠氢气。")],
     "（leave sb doing：使某人处于某种状态；had left：过去完成时）"]]),
(1,[[[("Because that gas was **combustible**,","由于氢气**易燃**(combustible)，")],
     "（Because 引导原因状语从句；that gas 指 hydrogen）"],
    [[("smokers","吸烟者"),("sat behind an airlock","只能坐在一道气闸后面，"),("with one electric lighter.","那里只有一个电点火器。")]]]),
(2,[[[("The airship left Frankfurt on 3 May 1937.","1937年5月3日，飞艇离开法兰克福。")]]]),
(2,[[[("Hours behind its **timetable**,","它比**时刻表**(timetable)晚了几个小时，")],
     "（Hours behind its timetable：形容词短语作状语）"],
    [[("it met **thunderstorms** at Lakehurst","在莱克赫斯特遇到**雷暴**(thunderstorms)，"),("and circled for over an hour","盘旋了一个多小时，")]],
    [[("before its **descent** towards the **mooring** **mast**.","才开始向**系留**(mooring)**塔架**(mast)**下降**(descent)。")],
     "（towards the mooring mast：介词短语，修饰 descent）"]]),
(2,[[[("At about 7:25 pm on 6 May,","5月6日晚约7时25分，"),("**flames** appeared near the **stern**.","飞艇**尾部**(stern)附近出现了**火焰**(flames)。")]]]),
(2,[[[("The **inferno**","这场**烈火**(inferno)"),("**incinerated** the ship in about half a minute,","在约半分钟内把飞艇**焚毁**(incinerated)，")]],
    [[("leaving","只留下"),("a **crumpled** **frame**.","一副**扭曲变形的**(crumpled)**骨架**(frame)。")],
     "（leaving…：现在分词短语作结果状语）"]]),
(3,[[[("Of the 97 aboard, 62 survived,","艇上97人中有62人生还，")],
     "（Of the 97 aboard：97人之中；aboard 作后置定语）"],
    [[("a **proportion**","**比例**(proportion)"),("close to **two-thirds**,","接近**三分之二**(two-thirds)；")],
     "（a proportion close to two-thirds：同位语，\n补充说明前面的数字）"],
    [[("while a **minority** of 35 died,","遇难的35人是**少数**(minority)，")],
     "（while：表示对比）"],
    [[("as did one man on the ground.","地面上另有一名男子丧生。")],
     "（as did…：倒装，did 代替 died）"]]),
(3,[[[("A 14-year-old cabin boy","一名14岁的侍应生"),("was **drenched** by a **deluge** from a **burst** water tank,","被一个**破裂**(burst)水箱**倾泻**(deluge)而下的水**浇透**(drenched)，")],
     "（was drenched by…：被动语态）"],
    [[("and the **soaking**","正是这一身**湿透**(soaking)"),("saved him.","救了他。")]]]),
(3,[[[("He dropped through a **hatch**","他从一个**舱口**(hatch)钻下去，"),("and **scrambled** clear,","**连滚带爬地**(scrambled)逃开，")],
     "（scramble clear：迅速爬开、脱身）"],
    [[("escaping only **narrowly**.","**侥幸**(narrowly)逃过一劫。")],
     "（escaping…：现在分词短语作结果状语）"]]),
(4,[[[("Newsreel cameras","新闻纪录片摄影机"),("and **photographers**","和**摄影师**(photographers)"),("caught the disaster.","拍下了这场灾难。")]]]),
(4,[[[("A radio **correspondent**'s","一位电台**通讯员**(correspondent)的"),("**eyewitness** **commentary**","**目击**(eyewitness)**解说**(commentary)"),("was not live;","并不是直播，")]],
    [[("**audiences**","**听众**(audiences)"),("heard it the next day.","第二天才听到。")],
     "（it 指 commentary）"]]),
(4,[[[("The cause","起火原因"),("has not been **definitively** established,","至今没有**确切**(definitively)查明，")],
     "（has not been established：现在完成时的被动语态）"],
    [[("but **static** electricity igniting **leaking** hydrogen is the leading explanation.","但最主要的解释是**静电**(static)点燃了**泄漏的**(leaking)氢气。")],
     "（igniting leaking hydrogen：现在分词短语作后置定语，\n修饰 static electricity）"]]),
(4,[[[("A theory blaming the **doped** **fabric**","一种归咎于**上过涂料的**(doped)**蒙皮织物**(fabric)的说法"),("has been rejected.","已被否定。")],
     "（blaming…：现在分词短语作后置定语，修饰 theory）"]]),
(5,[[[("The 1933 crash of USS Akron","1933年阿克伦号失事"),("killed 73","造成73人死亡，"),("yet won less **notoriety**.","**恶名**(notoriety)却没那么大。")],
     "（USS：United States Ship，美国海军舰艇名前缀）"]]),
(5,[[[("The filmed fire","被拍下的大火"),("left a **fateful** **image**","留下了一幅**影响深远的**(fateful)**画面**(image)，")]],
    [[("that **abruptly** wrecked **confidence**.","**骤然**(abruptly)摧毁了人们的**信心**(confidence)。")],
     "（that 引导定语从句，修饰 image）"]]),
(5,[[[("As public **perception** soured,","公众**观感**(perception)变差后，")],
     "（As 引导时间状语从句）"],
    [[("Graf Zeppelin was withdrawn,","格拉夫·齐柏林号退役，"),("later **scrapped**,","后来被**拆毁**(scrapped)，")],
     "（later scrapped：省略了 was）"],
    [[("and a **glamorous** **epoch** of **aviation** closed.","**航空**(aviation)史上一个**光彩夺目的**(glamorous)**时代**(epoch)就此结束。")],
     "（of aviation：介词短语作后置定语，修饰 epoch）"]]),
(5,[[[("The doomed airship's","这艘终将毁于大火的飞艇"),("first journey to North America","首次飞往北美的航程"),("had begun on 6 May 1936,","始于1936年5月6日，")],
     "（had begun：过去完成时）"],
    [[("exactly a year before the fire.","恰好在那场大火的一年前。")],
     "（简述：1936年，兴登堡号完成17次大西洋往返，艇上设施奢华；美国禁止向它出口氦气，它只能用易燃的氢气。\n"
     "1937年5月3日，它从法兰克福出发，5月6日晚在莱克赫斯特降落前尾部起火，约半分钟就被烧毁。\n"
     "艇上97人中62人生还，一名14岁的侍应生被破裂水箱的水浇透，从舱口逃生。\n"
     "起火原因至今没有确切查明，主流解释是静电点燃了泄漏的氢气。\n"
     "被拍下的大火摧毁了公众的信心，格拉夫·齐柏林号随后退役、拆毁，客运飞艇的时代就此结束。）"]]),
]
G={}
DZ={}
CONF={"合组":G,"对齐":DZ}
out={"no":"68","title_en":"The Last Flight of the Hindenburg","title_zh":"兴登堡号的 34 秒","title_fx":{"hl":["Hindenburg"],"ghost":[]},"sentences":[],"核对确认":CONF,"结尾解说":"简述",
     "高亮按实际开口":True,"高亮开口门槛":40,
     "术语":{"Hindenburg":"兴登堡号","Atlantic":"大西洋","Frankfurt":"法兰克福","Lakehurst":"莱克赫斯特","USS Akron":"阿克伦号","Graf Zeppelin":"格拉夫·齐柏林号","North America":"北美","American":"美国"}}
out.update({"非人声区间":{"S1":[[1.465042,1.662542,"紧贴两头"]],"S2":[[1.922958,2.207708,"紧贴词头"]],"S5":[[1.515,1.74]],"S6":[[4.535,4.762125]],"S8":[[3.235542,3.610542,"紧贴词头"]],"S9":[[3.110083,3.441,"紧贴词头"],[5.49,5.80]],"S18":[[1.762667,1.945],[4.792583,5.000417,"紧贴词头"]]},
            "停顿插入点":{"S2":{"1":[2.345958,"交界"]}}})   # 2026-11-09 逐 2.5/10 ms 实测（w 秒）：纯人声核对 dossier_68：S1 thirty-six 的 /s/ 到 1.45，1.47–1.66 吸气（-41～-50 dB、重心 2.2–2.6 kHz、低频 -10～-21），1.665–1.70 低频浊音（低频 -0～-2）试删后 1936|the 无标点停顿超 0.22 s，是 the 的浊音前导，保留；S17 image 后 2.55–2.585 的低频浊音试删后 image|that 无标点停顿变成 0.26 s，是 dʒ 连到 that 的浊音，保留；S5 Frankfurt 后 1.52–1.69 吸气（低频 -7～-25、重心 2 kHz）连同 1.695–1.73 一下 150 Hz 以下的噗声（低频 -1～-2），两头 -56/-60 dB；S6 Lakehurst 后 4.555–4.71 吸气（低频 -10～-24）连同 4.715–4.75 噗声（低频 -0～-3），4.78 起 and；S18 soured 后 1.785–1.935 吸气（低频 -7～-25）；S8 延到 leaving 的 l 前 3.6105（3.555–3.61 -50～-61 dB 杂声）；S9 延到 a 前 3.441（3.405–3.44 -48 dB 噗声）。S2 lounge 的 ʒ 到 1.91，1.92–2.16 吸气（-50～-55 dB、重心 2.3 kHz、低频 -10～-22 dB），2.21 起 and；配音把停顿放在 lounge|and，删掉吸气，标准停顿插到 and 的 d（到 2.343）与 that 的 ð（2.345 起 3–4 kHz）之间。S8 minute 的 /t/ 到 3.21，3.30–3.55 吸气（-45～-55、重心 2.2 kHz、低频 -10～-22），3.55 一下 5 kHz 咔声一起删，3.615 起 leaving。S9 survived 后 3.12–3.39 吸气（低频 -10～-28），3.40 起 a 的浊音；two-thirds 的 /z/ 到 5.45，5.50–5.79 吸气，5.80–5.85 while 的 /w/ 浊音前导（低频 -1～-5）保留。S18 scrapped 的 /t/ 除阻 4.60–4.64 保留，4.80–4.99 吸气，5.00–5.03 and 的浊音前导保留
CONF["停顿位置"]={
 "S2 and, / that @2.346":"2026-11-09 逐 2.5 ms 实测（S2 w）：and 的 æn 2.23–2.34（-8～-18 dB、周期 0.5–0.6），d 浊音到 2.343（-20 dB、重心 1.3 kHz），2.345 起 that 的 ð（重心 3.3→4.4 kHz、周期降到 0.2–0.35）；插入点 2.346 正好在 and 与 that 之间（DTW 把 that 开头放到 2.400 晚了 54 ms）",
 "S8 minute, / leaving @3.280":"2026-11-09 逐 2.5 ms 实测（S8 w）：minute 的 /t/ 除阻到 3.21（-55 dB），3.215–3.30 数字静音级（-57～-70 dB），3.30–3.55 吸气已删（非人声区间），3.615 起 leaving 的 l（-32→-16 dB）；删静音 3.280–3.555 整段落在 minute 与 leaving 之间，没碰到两个词（DTW 把 minute 末音素起点放到 3.480 是对齐误差）",
 "S9 aboard, / 62 @1.465":"2026-11-09 逐 5 ms 实测（S9 w）：aboard 的 ɹ 到 1.44，d 浊音 1.445–1.46（-37～-45 dB、低频 -1.5～-3.5），1.465 低谷 -52 dB，1.47 起 sixty 的 /s/（重心 2.8→6 kHz）；插入点 1.465 正好在两词之间",
 "S18 withdrawn, / later @3.865":"2026-11-09 逐 10 ms 实测（S18 w）：withdrawn 的 n 3.76–3.86（-24 dB、低频 -1～-2 鼻音），3.87 起 later 的 l（-10.8 dB）；插入点 3.865 正好在两词之间"}
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 核对 import 生成并核对
生成并核对(S, out)
