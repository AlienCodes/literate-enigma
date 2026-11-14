#!/usr/bin/env python3
# Pure data frozen from the current approved JSON; shared helper/checkers unchanged.
import os
import sys

S = [(1,
  [[[('On 26 April 1956', '1956年4月26日，'),
     ('a', '一艘'),
     ('**converted**', '**改造过的**(converted)'),
     ('Second World War', '二战'),
     ('**tanker**,', '**油轮**(tanker)'),
     ('the Ideal X,', '“理想X号”，')],
    '（a converted…tanker：主语；the Ideal X：同位语，补充说明 tanker）'],
   [[('**slipped out of**', '**悄然驶离**(slipped out of)'),
     ('Port Newark, New Jersey,', '新泽西州纽瓦克港，'),
     ('for Houston.', '开往休斯敦。')],
    '（slip out of：悄悄离开；for：表示去向，开往）']]),
 (1,
  [[[('**Clamped**', '**固定**(clamped)'),
     ('to her deck', '在她甲板上的'),
     ('were', '是'),
     ('58', '58个'),
     ('**containers**,', '**集装箱**(containers)，')],
    '（倒装句：表语 Clamped to her deck 提前，主语是 58 containers；\nclamp A to B：把 A 固定在 B 上；her 指船）'],
   [[('**trailer** bodies **detached from** their **wheels** and **chassis**.',
      '其实就是**从**(detached from)**车轮**(wheels)和**底盘**(chassis)**上拆卸下来的**(detached from)**挂车**(trailer)车厢。')],
    '（trailer bodies 挂车车厢：同位语，补充说明 containers；\n'
    'detached from…：过去分词短语作后置定语，修饰 bodies；\n'
    'detach from：指将某物从原本附着、连接或所属的主体上分离或拆卸下来）']]),
 (1,
  [[[('Few', '极少数'),
     ('**spectators**', '**旁观者**(spectators)'),
     ('would have taken', '会把'),
     ('so', '一批如此'),
     ('**unremarkable**', '**平淡无奇的**(unremarkable)'),
     ('a **cargo**', '**货物**(cargo)'),
     ('for a **landmark**.', '当作一个**里程碑**(landmark)。')],
    '（take A for B：把 A 当作 B；\nso＋形容词＋a＋名词：这样……的一个；\nwould have done：对过去情况的推测）']]),
 (2,
  [[[('At the time,', '那时，'),
     ('**freight**', '**货物**(freight)'),
     ('travelled **loose**.', '都是**散装**(loose)运输。')],
    '（travelled loose：loose 作补语，\n说明货物运输时的状态）']]),
 (2,
  [[[('**Gangs**', '一**帮**(gangs)'),
     ('of twenty or more', '二十多名或更多的'),
     ('**dockworkers**', '**码头工人**(dockworkers)，')],
    '（of twenty or more dockworkers：of 结构作后置定语，修饰 Gangs）'],
   [[('carried', '一件件地搬运'),
     ('**sacks**,', '**麻袋**(sacks)、'),
     ('**barrels**,', '**桶**(barrels)'),
     ('and **crates** piece by piece.', '和**板条箱**(crates)。')],
    '（piece by piece：一件一件地）']]),
 (2,
  [[[('It was', '这是'), ('**strenuous**', '**繁重的/费力的**(strenuous)'), ('**drudgery**.', '**苦差事**(drudgery)。')],
    '（strenuous：\n'
    '形容需要耗费大量体力或精力的，\n'
    '多用于体力活、运动或努力，\n'
    '如 strenuous work 繁重的工作、\n'
    'strenuous exercise 剧烈运动、\n'
    'make strenuous efforts 尽力）']]),
 (2,
  [[[('Ships', '船舶'),
     ('could', '可能会'),
     ('spend', '花'),
     ('**up to**', '**多达**(up to)'),
     ('half their time', '一半的时间'),
     ('**berthed**,', '**停泊**(berthed)在港，')],
    '（spend time＋过去分词：花时间处于……状态；up to：多达）'],
   [[('and', '而且'), ('**theft**', '**偷窃**(theft)'), ('was **rampant**.', '**猖獗**(rampant)。')]]]),
 (2,
  [[[('In 1956', '1956年，'),
     ('**loading**', '**装载**(loading)'),
     ('loose cargo', '散货'),
     ('cost about $5.83 a ton;', '每吨花费约5.83美元；')],
    '（loading loose cargo：动名词短语作主语）'],
   [[("loading the Ideal X cost, **by** the company's **reckoning**,",
      '**据**(by reckoning)公司**估算**(by reckoning)，装载理想X号花费'),
     ('about 16 cents.', '约16美分。')],
    "（by one's reckoning：根据某人的估算；\nby the company's reckoning 是插入语）"]]),
 (3, [[[('Containers', '集装箱'), ('were not new.', '并不新鲜。')]]]),
 (3,
  [[[('The **hurdle**', '**障碍**(hurdle)'), ('was **consensus**:', '在于**共识**(consensus)：')]],
   [[('**rival**', '**竞争对手**(rival)'),
     ("firms'", '公司的'),
     ('boxes', '箱子'),
     ('had', '有'),
     ('**incompatible**', '**互不兼容的**(incompatible)'),
     ('**dimensions**', '**尺寸**(dimensions)'),
     ('and', '和'),
     ('**latches**.', '**门闩/锁扣**(latches)。')]]]),
 (3,
  [[[('An', '1961年，一个'),
     ('**international standards**', '**国际标准**(international standards)'),
     ('committee', '委员会'),
     ('formed in 1961.', '成立。')],
    '（form：（组织）成立）']]),
 (3,
  [[[('In January 1963', '1963年1月，'),
     ('Sea-Land,', '海陆公司，'),
     ("the Ideal X's", '即理想X号'),
     ('renamed', '更名后的'),
     ('operator,', '运营方，')]],
   [[('let', '允许'),
     ('the committee', '该委员会'),
     ('use', '使用'),
     ('its **patents**', '其**专利**(patents)，'),
     ('free of', '不收取'),
     ('**royalties**,', '**专利费**(royalties)，')],
    '（let sb do：让某人做；free of：免除，不收）'],
   [[('including', '包括'),
     ('those on corner **fittings** for **hoisting**.', '用于**吊装**(hoisting)的角**配件**(fittings)上的那些专利。')],
    '（corner fittings：集装箱八个角上的金属件，\n专门用来让吊车吊起箱子，\n并把箱子上下左右死死锁在一起）']]),
 (3,
  [[[('Lifted by **crane**,', '由**吊机**(crane)吊起，'), ('a box', '一只箱子')], '（Lifted by crane：过去分词短语作状语）'],
   [[('could be', '便能'),
     ('**transferred** **smoothly** between ship, **lorry**, and train.',
      '在船舶、**卡车**(lorry)和火车之间**顺畅地**(smoothly)**转运**(transferred)。')],
    '（between A, B, and C：在 A、B 和 C 之间，中文状语提前）']]),
 (4,
  [[[('This **efficiency**', '这种**效率**(efficiency)'),
     ('came **at the expense of** **livelihoods**.',
      '是**以**(at the expense of)**生计**(livelihoods)**为代价**(at the expense of)换来的。')],
    '（come at the expense of：以……为代价换来；\n'
    'at the expense of：以牺牲……为代价，后面接付出代价的人或物，\n'
    '用于“得到了一样东西，却损害了另一样”，\n'
    '如 at the expense of quality 以牺牲质量为代价、\n'
    'at the expense of others 让别人受损）']]),
 (4,
  [[[("New York's", '纽约'),
     ('**waterfront**', '**海滨区**(waterfront)的'),
     ('**employment**', '**就业人数**(employment)'),
     ('**shrank**', '在1963年至1976年间**缩减了**(shrank)'),
     ('by about three quarters between 1963 and 1976.', '约四分之三。')],
    '（shrink by：缩减了（幅度）；between 1963 and 1976：中文时间状语提前）']]),
 (4,
  [[[('Much of the cargo', '大量货物'), ('crossed', '穿过'), ('the harbour', '港湾，')]],
   [[('to', '前往'),
     ('a new **terminal** at Elizabeth, **inaugurated** in August 1962.',
      '伊丽莎白一处于1962年8月**启用**(inaugurated)的新**码头/港区**(terminal)。')],
    '（inaugurated in August 1962：过去分词短语作后置定语，\n修饰 terminal）']]),
 (4,
  [[[("Most of London's", '1967年到1980年，伦敦'),
     ('**historic**', '**历史悠久的**(historic)'),
     ('**docks**', '**码头**(docks)'),
     ('closed one after another from 1967 to 1980,', '一个接一个地关闭，')],
    '（one after another：一个接一个地；from 1967 to 1980：中文时间状语提前）'],
   [[('while', '而'),
     ('Felixstowe, on the Suffolk coast,', '位于萨福克海岸的费利克斯托'),
     ('**expanded**.', '则**扩张了**(expanded)。')],
    '（while：表示对比，而；on the Suffolk coast：插入语，补充说明 Felixstowe）']]),
 (5, [[[('The **rewards**', '**回报**(rewards)'), ('were **substantial**.', '相当**可观**(substantial)。')]]]),
 (5,
  [[[('A study published in the Journal of International **Economics** in 2016',
      '一项2016年发表于《国际**经济学**(Economics)杂志》的研究'),
     ('estimated', '估计，')],
    '（published in…：过去分词短语作后置定语，修饰 study）'],
   [[('that containerisation', '集装箱化在20年间'),
     ('had lifted trade between', '使'),
     ('**industrialised**', '**工业化**(industrialised)'),
     ('countries', '国家之间的贸易'),
     ('by a **cumulative**', '提高了**累计**(cumulative)'),
     ('700 per cent over 20 years.', '700%。')],
    '（that…：宾语从句；lift A by B：使 A 增长 B；over 20 years：20年间）']]),
 (5,
  [[[('**Tireless**', '如今，**不知疲倦的**(tireless)'),
     ('cranes now', '吊机'),
     ('lift', '把'),
     ('**identical**', '**一模一样的**(identical)'),
     ('containers', '集装箱吊起，'),
     ('into', '码成'),
     ('**orderly**,', '**整齐的**(orderly)、'),
     ('**immense**', '**巨大的**(immense)'),
     ('**stacks**.', '**箱垛**(stacks)。')],
    '（lift A into B：把 A 吊起码成 B）\n'
    '（简述：▸启航：过去码头逐件搬散货，船常久停；1956年，理想X号载58个集装箱启航。▸降本：据运营方估算，该船每吨装船费约0.16美元，远低于当时散货的5.83美元。▸互通：各家箱型原不兼容；运营方海陆公司免费开放专利，推动标准统一，箱子可在船、卡车和火车间转运。▸转移：货运转向新港，老码头和工人生计受冲击；1963至1976年，纽约滨水区就业缩减约四分之三。▸回报：2016年一项研究估计，集装箱化在20年间使工业化国家间贸易累计增加约700%。）']])]

out = {'no': '61',
 'title_en': 'The Steel Box That Remade the World',
 'title_zh': '集装箱：重塑世界的铁盒子',
 'title_fx': {'hl': ['Box', 'World'], 'ghost': []},
 'sentences': [],
 '核对确认': {'合组': {'S2 Clamped to her deck': '对齐不了：倒装句，to her deck 中文“甲板上”必须放到“牢牢固定”前',
                 'S3 Few spectators': '对齐不了：Few 中文“恐怕很少”必须放到“旁观者”后作谓语',
                 'S10 had incompatible dimensions and latches': '对齐不了：incompatible 作定语修饰 dimensions and '
                                                                'latches，中文“尺寸和锁扣互不兼容”放到最后作谓语；重点词中文先后与英文相反',
                 'S5 piece by piece': '对齐不了：piece by piece 是固定说法“一件件”，拆开不通',
                 "S12 Sea-Land, the Ideal X's renamed operator": "对齐不了：同位语 the Ideal X's renamed operator "
                                                                 '中文“理想X号的运营方、已更名的”必须提前到“海陆公司”前',
                 'S11 An international standards committee formed in 1961': '对齐不了：in 1961 中文“1961年”必须提前到句首',
                 'S16 to a new terminal at Elizabeth, inaugurated in August 1962': '对齐不了：at Elizabeth 和 '
                                                                                   'inaugurated in August 1962 '
                                                                                   '都是后置定语，修饰 '
                                                                                   'terminal，中文“伊丽莎白港1962年8月启用的新货运站”必须提前；两个重点词中文先后与英文相反',
                 'S2 trailer bodies detached from their wheels and chassis': '对齐不了：detached from their wheels '
                                                                             'and chassis 是后置定语，修饰 '
                                                                             'bodies，中文“从车轮和底盘上拆卸下来的挂车车厢”定语必须提前；detach '
                                                                             'from 被“车轮和底盘”隔开（T23 '
                                                                             '两处都标）；重点词中文先后与英文相反',
                 'S8 cost about $5.83 a ton': '对齐不了：a ton 中文“每吨”必须提前到金额前',
                 "S8 loading the Ideal X cost, by the company's reckoning": "对齐不了：插入语 by the company's "
                                                                            'reckoning 中文“据公司估算”必须提前到句首；by '
                                                                            "one's reckoning 被 the company's "
                                                                            '隔开，“据”“估算”两处都标（T23）',
                 'S5 carried': '对齐不了：piece by piece 中文“一件件地”提前到“搬运”前，只能和 carried 放一组',
                 'S5 and crates piece by piece': '对齐不了：piece by piece 已随“搬运”提前，这里只剩“和板条箱”',
                 'S8 loose cargo': '对齐不了：loose cargo 中文是一个词“散货”，拆开不通',
                 'S15 shrank': '对齐不了：between 1963 and 1976 中文“在1963年至1976年间”必须放到“缩减了”前',
                 'S15 by about three quarters between 1963 and 1976': '对齐不了：between 1963 and 1976 '
                                                                      '中文已提前到“缩减了”前，这里只剩“约四分之三”',
                 'S17 closed one after another from 1967 to 1980': '对齐不了：one after another '
                                                                   '中文“一个接一个地”必须放到“关闭”前，from 1967 to 1980 '
                                                                   '中文提前到句首',
                 'S19 had lifted trade between': '对齐不了：lift A by B 中文“使 A 提高了 B”，lifted 的“提高了”放到 cumulative '
                                                 '下面；trade between… 中文“国家之间的贸易”定语提前，trade 的“贸易”只能放到 countries '
                                                 '下面',
                 'S19 700 per cent over 20 years': '对齐不了：700 per cent 中文“700%”是一个数；over 20 years '
                                                   '中文“在20年间”提前到“使”前（放在 that containerisation 下面）',
                 'S20 cranes now': '对齐不了：now 中文“如今”必须提前到句首（在 Tireless 下面）',
                 'S11 An': '对齐不了：in 1961 中文“1961年”必须提前到句首（放在 An 下面）',
                 'S11 formed in 1961': '对齐不了：in 1961 中文已提前到句首，这里只剩“成立”',
                 'S12 those on corner fittings for hoisting': '对齐不了：for hoisting 是后置定语，修饰 '
                                                              'fittings，中文“用于吊装的角配件上的那些专利”定语必须提前，those '
                                                              '的“那些专利”放到最后；两个重点词中文先后与英文相反',
                 'S13 transferred smoothly between ship, lorry, and train': '对齐不了：between… '
                                                                            '介词短语中文“在船舶、卡车和火车之间”必须提前到动词前，smoothly '
                                                                            '中文“顺畅地”也在“转运”前；重点词中文先后与英文相反',
                 'S14 came at the expense of livelihoods': '对齐不了：come at the expense of B 中文“是以 B '
                                                           '为代价换来的”，被“生计”隔开，只能整组',
                 'S16 a new terminal at Elizabeth, inaugurated in August 1962': '对齐不了：at Elizabeth 和 '
                                                                                'inaugurated in August 1962 '
                                                                                '都是后置定语，修饰 '
                                                                                'terminal，中文“伊丽莎白一处于1962年8月启用的新码头/港区”必须提前；两个重点词中文先后与英文相反',
                 'S17 Felixstowe, on the Suffolk coast': '对齐不了：插入语 on the Suffolk coast 中文“位于萨福克海岸的”作定语必须提前',
                 'S19 A study published in the Journal of International Economics in 2016': '对齐不了：published '
                                                                                            'in… in 2016 '
                                                                                            '是后置定语，修饰 '
                                                                                            'study，中文“一项2016年发表于《国际经济学杂志》的研究”必须提前，刊名不能拆'},
          '对齐': {'S13-2 transferred smoothly between ': 'between… 介词短语中文必须提前到动词前',
                 'S1-1 a converted Second World War t': 'converted 中文“改装而成的”必须放到“油轮”后',
                 'S10-2 had incompatible dimensions an': 'incompatible 中文“互不兼容”放到最后作谓语，重点词中文先后与英文相反',
                 'S11-1 An international standards com': 'in 1961 中文“1961年”必须提前到句首',
                 "S12-1 Sea-Land, the Ideal X's rename": "同位语 the Ideal X's renamed operator "
                                                         '中文“理想X号的运营方、已更名的”必须提前到“海陆公司”前',
                 'S16-2 to a new terminal at Elizabeth': 'at Elizabeth、inaugurated in August 1962 都是后置定语，修饰 '
                                                         'terminal，中文必须提前',
                 'S5-1 Gangs of twenty or more': 'twenty or more 中文“二十多人”必须放到“一帮”前',
                 'S7-1 up to half their time': 'up to half their time 是一个数量意群“多达一半时间”，拆开不通',
                 'S16-2 a new terminal at Elizabeth, ': 'at Elizabeth、inaugurated in August 1962 都是后置定语，修饰 '
                                                        'terminal，中文必须提前',
                 'S5-2 and crates piece by piece.': 'piece by piece 中文“一件件地”已随“搬运”提前（用户 11-08 译法），这里只剩“和板条箱”',
                 'S2-2 trailer bodies detached from t': 'detached from… 是后置定语，修饰 '
                                                        'bodies，中文“从车轮和底盘上拆卸下来的挂车车厢”定语必须提前，重点词中文先后与英文相反',
                 'S8-1 cost about $5.83 a ton;': 'a ton 中文“每吨”必须提前到金额前',
                 'S8-2 loading the Ideal X cost, by t': "插入语 by the company's reckoning 中文“据公司估算”必须提前到句首",
                 'S12-3 those on corner fittings for h': 'for hoisting 是后置定语，修饰 fittings，中文必须提前',
                 'S13-2 transferred smoothly between s': 'between… 介词短语中文必须提前到动词前',
                 'S14-1 came at the expense of livelih': 'come at the expense of B 中文“是以 B '
                                                         '为代价换来的”，被“生计”隔开，只能整组',
                 'S15-1 by about three quarters betwee': 'between 1963 and 1976 中文“在1963年至1976年间”提前到“缩减了”前（放在 '
                                                         'shrank 下面）',
                 'S16-2 a new terminal at Elizabeth, i': 'at Elizabeth、inaugurated in August 1962 都是后置定语，修饰 '
                                                         'terminal，中文必须提前',
                 'S17-1 closed one after another from ': 'from 1967 to 1980 中文“1967年到1980年”提前到句首（放在 Most of '
                                                         "London's 下面）",
                 'S17-2 Felixstowe, on the Suffolk coa': '插入语 on the Suffolk coast 中文作定语必须提前',
                 'S19-1 A study published in the Journ': 'published in… in 2016 是后置定语，修饰 study，中文必须提前，刊名不能拆',
                 'S19-2 700 per cent over 20 years.': 'over 20 years 中文“在20年间”提前（放在 that containerisation 下面）'},
          '引号': {'S1-1 “”': '用户 2026-11-08 原话（converted '
                            '后按用户“意思为改造过的”改成“改造过的”）“1956年4月26日，一艘改装过的二战油轮“理想X号”，悄然驶离新泽西州纽瓦克港，开往休斯敦。”自带引号，照用户原话保留（T10）'},
          '即': {'S12-1 即': '用户 2026-11-08 原话“1963年1月，海陆公司, 即理想X号更名后的运营方, 允许该委员会 使用其专利……”自带“即”，照用户原话（T10）'},
          '中文重复': {'货物': '用户 2026-11-08 原话：S3“极少数旁观者会把一批如此平淡无奇的货物当作一个里程碑。”、S4“那时，货物都是散装运输。”cargo、freight '
                         '都译“货物”，照用户原话（T10）'},
          '是的': {'S6-1 是**繁重的**': '“是”对应 was（这是），“的”是形容词 strenuous 的“的”（T38），不是“是……的”句式；文章定稿原文“这是繁重的苦差事”',
                 'S6-1 是**繁重的/费力的**': '“是”对应 was（这是），“的”是形容词 strenuous 的“的”（T38），不是“是……的”句式；文章定稿原文“这是繁重的苦差事”'},
          '方向': {'S5-1 more→二十多人一**帮**(gangs)': 'or more 是“……多”，中文“二十多人”有“多”，方向一致',
                 'S17-1 after→一个接一个地关闭，': 'one after another 是“一个接一个”，不是时间先后；中文“一个接一个地”，方向一致（用户 11-08 译法）',
                 'S5-1 more→二十多名或更多的': 'or more 是“或更多”，中文“或更多的”，方向一致',
                 'S17-1 after→接连关闭，': 'one after another 是“一个接一个”，不是时间先后；中文“接连”，方向一致'},
          '停顿位置': {'S1 Jersey, / for @9.675': '2026-11-07 逐 2.5 ms 实测（S1 w）：Jersey 的 i 浊音到 9.665（周期 '
                                              '0.47），9.675–9.69 是两词之间的低谷（-39～-40 dB、周期 0.18），9.6975 起 for 的 '
                                              '/f/（重心 4.9–6.4 kHz）；停顿 9.675 落在低谷里，在两词之间',
                   'S5 barrels, / and @3.800': '2026-11-07 逐 2.5 ms 实测（S5 w）：barrels 的 /z/ 擦音到 3.7975（重心 '
                                               '4.7–5.6 kHz），3.80 是低谷（-22.8 dB），3.805 起 and 的元音（周期 0.49、重心 2 '
                                               'kHz 以下）；停顿 3.800 正落在两词之间',
                   'S4 time, / freight @0.643': '2026-11-07 逐 2.5 ms 实测（S4 w）：time 的 m 浊音到 0.6385（周期 '
                                                '0.37–0.41、重心 0.8 kHz），0.641 低谷 -30.6 dB，0.6435 起 freight 的 '
                                                '/f/（重心 2.7→5–7 kHz，到 0.78），0.785 起 r 元音；停顿插入点写在交界过零点 '
                                                '0.642792，在两词之间（离前词末音素起点 +19 ms 是因为 m 本身就短）',
                   'S1 Newark, / New @8.870': '2026-11-07 逐 2.5 ms 实测（S1 w）：Newark 的 /k/ 原声除阻 8.8325–8.845（-27 '
                                              'dB）、送气到 8.865（-39～-45 dB），8.8675–8.8725 低谷（-45.8～-47.8 '
                                              'dB），8.8725 起 New 的 n 起音（周期 0.28→0.38，8.8925 -12.8 dB）；停顿 8.870 '
                                              '落在低谷里，/k/ 除阻送气在前、n 在后，在两词之间',
                   'S13 lorry, / and @4.665': '2026-11-07 逐 2.5 ms 实测（S13 w）：lorry 的 i 与 and 的 æ 浊音连读、没有静音（周期 '
                                              '0.46–0.48 一直连着）；i 的重心 1.5–2.7 kHz 到 4.67，4.675 起降到 0.6–1 '
                                              'kHz（æ）；停顿 4.665 落在两个元音的交界上，在两词之间，同 60 S11 law, / which'},
          '非人声': {'27.32–27.36s': {'配音指纹': '7499cce91ea3',
                                   '依据': 'S3 w 4.59–4.635s：2026-11-07 逐 2.5 ms 实测（疑点清单 dossier_61）：S3 '
                                         'landmark. 的 /k/ 除阻：4.53–4.585 闭塞 -63～-69 dB，4.5925 爆出 -32 dB（重心 3.5 '
                                         'kHz、低频 -20 dB），衰减到 4.64；句末词尾塞音除阻',
                                   '实测': {'最响dB': -32.8, '重心Hz': 3414, '周期': 0.22, '低频dB': -14.0}},
                  '35.06–35.08s': {'配音指纹': '7499cce91ea3',
                                   '依据': 'S5 w 3.25–3.265s：2026-11-07 逐 2.5 ms 实测：S5 barrels 的 /b/ 浊音杠起头（3.25 '
                                         '-42 dB、周期 0.59），15 ms 后 3.265 起 -24 dB、重心 0.3–0.4 kHz 的浊音杠，接 '
                                         'æ；词头的一部分',
                                   '实测': {'最响dB': -38.7, '重心Hz': 1571, '周期': 0.0, '低频dB': -1.9}},
                  '54.44–54.48s': {'配音指纹': '7499cce91ea3',
                                   '依据': 'S8 w 8.63–8.67s：2026-11-07 逐 2.5 ms 实测：S8 cost, 的 /t/ 除阻：/s/ 到 '
                                         '8.60（重心 5.5 kHz），8.6175–8.625 闭塞 -65～-67 dB，8.6325 爆出 -34 dB（重心 3.5 '
                                         'kHz），衰减到 8.665；词尾塞音除阻',
                                   '实测': {'最响dB': -31.9, '重心Hz': 3334, '周期': 0.15, '低频dB': -11.3}},
                  '80.02–80.03s': {'配音指纹': '7499cce91ea3',
                                   '依据': 'S12 w 6.465–6.48s：2026-11-07 逐 2.5 ms 实测：S12 let 起音前 15 ms '
                                         '的气流（-48～-55 dB），6.48 起 /l/（-39.5→-25.9 dB），中间没有低谷；紧贴词头，起音的一部分',
                                   '实测': {'最响dB': -48.1, '重心Hz': 3102, '周期': 0.0, '低频dB': -2.9}},
                  '91.42–91.47s': {'配音指纹': '7499cce91ea3',
                                   '依据': 'S13 w 3.955–3.995s：2026-11-07 逐 2.5 ms 实测：S13 ship, 的 /p/ '
                                         '除阻：3.89–3.95 闭塞 -55～-68 dB，3.9575 爆出 -40.6 dB（重心 2.6→1.2 kHz），衰减到 '
                                         '3.99；词尾塞音除阻',
                                   '实测': {'最响dB': -30.5, '重心Hz': 2007, '周期': 0.31, '低频dB': -9.4}},
                  '103.84–103.88s': {'配音指纹': '7499cce91ea3',
                                     '依据': 'S15 w 5.71–5.74s：2026-11-07 逐 2.5 ms 实测：S15 and 的浊音起头（-40～-43 '
                                           'dB、低频 -0.2～-0.9 dB、周期 0.46），5.75 起 -26 dB 元音；前面的吸气已删到 '
                                           '5.7125；词头的一部分',
                                     '实测': {'最响dB': -41.0, '重心Hz': 2531, '周期': 0.35, '低频dB': -0.5}},
                  '121.16–121.20s': {'配音指纹': '7499cce91ea3',
                                     '依据': 'S17 w 6.51–6.555s：2026-11-07 逐 2.5 ms 实测：S17 while 的 /w/ '
                                           '浊音起头（-41～-47 dB、低频 -0.4～-1.3 dB、周期 0.2–0.36），6.56 起 -27.5 dB、重心 '
                                           '0.8 kHz；前面的吸气删到 6.51 低谷；词头的一部分',
                                     '实测': {'最响dB': -42.3, '重心Hz': 1918, '周期': 0.37, '低频dB': -0.5}},
                  '123.83–123.88s': {'配音指纹': '7499cce91ea3',
                                     '依据': 'S17 w 8.85–8.90s：2026-11-07 逐 2.5 ms 实测：S17 coast, 的 /t/ 除阻：/s/ 到 '
                                           '8.82，8.83–8.845 闭塞 -56～-62 dB，8.8525 爆出 -33 dB（重心 3.1 kHz），衰减到 '
                                           '8.89；词尾塞音除阻',
                                     '实测': {'最响dB': -30.2, '重心Hz': 3329, '周期': 0.18, '低频dB': -12.7}},
                  '142.91–143.07s': {'配音指纹': '7499cce91ea3',
                                     '依据': 'S19 w 14.675–14.835s：2026-11-07 逐 2.5 ms 实测：S19 years. 词内：ɹ 元音到 '
                                           '14.67（-20～-30 dB），14.68–14.81 是 -37～-56 dB、重心 1–2 kHz、低频 -2～-10 dB '
                                           '的浊音过渡，14.8125 起 /z/ 擦音（3.5–5.5 kHz）；在 ɹ 和 z 之间，词的一部分',
                                     '实测': {'最响dB': -35.3, '重心Hz': 1767, '周期': 0.19, '低频dB': -2.5}},
                  '142.98–143.00s': {'配音指纹': '7499cce91ea3',
                                     '依据': 'S19 w 14.74–14.755s：同上，years. 的 ɹ→z 浊音过渡中间一帧（-43 dB、低频 -1.3 '
                                           'dB），词的一部分',
                                     '实测': {'最响dB': -43.4, '重心Hz': 1358, '周期': 0.0, '低频dB': -1.3}}},
          '机器复听': {'S2': {'配音指纹': '7499cce91ea3',
                          '依据': '2026-11-07：Clamped to her deck，clamped 的 /t/ 与后面 to 的 /t/ '
                                '连读成一个闭塞（正常连读），small.en 拼成 clamp；parakeet 听对。读音按词典，非读错'},
                   'S8': {'配音指纹': '7499cce91ea3',
                          '依据': '2026-11-07：$5.83 按 spoken() 读 five dollars eighty-three cents（数字读法清单已核），脚本原文是 '
                                '$5.83 符号，比对时“dollars”“cents”算多出/对不上；两个识别器都听到 dollars，读法正确'},
                   'S12': {'配音指纹': '7499cce91ea3',
                           '依据': "2026-11-07：the Ideal X's renamed operator，X's 的 /ɪz/ 连到 renamed 的 "
                                 '/ɹɪ/，small.en 断成 X were named；parakeet 听对 renamed。整句音标 ˈɛksᵻz '
                                 'ɹᵻnˈeɪmd，读音正确'}},
          '删除段': {'S13 raw 1.1150-1.3636': {'类型': '紧贴词头的非人声',
                                            '配音指纹': '7499cce91ea3',
                                            '依据': '2026-11-07 S13 crane, 后停顿里的吸气（自动切点 非人声区间 S13 [1.12, '
                                                  '1.353625, 紧贴词头]，删掉最响 -38.3 dB、无周期），一直贴到 a 的起音，词头切在过零点，a '
                                                  '本身不动'},
                  'S15 raw 5.5100-5.7224': {'类型': '紧贴词头的非人声',
                                            '配音指纹': '7499cce91ea3',
                                            '依据': '2026-11-07 逐 2.5 ms 实测（S15 w）：sixty-three 与 and '
                                                  '之间（无标点）5.51–5.705 约 200 ms -43～-50 dB、周期 0.15–0.26、重心 2.3–3 '
                                                  'kHz 的吸气（删掉最响 -37.3 dB 即此）；5.72 起 and 的浊音起头，紧贴词头切在过零点 '
                                                  '5.7125'},
                  'S17 raw 6.1350-6.5301': {'类型': '紧贴词头的非人声',
                                            '配音指纹': '7499cce91ea3',
                                            '依据': '2026-11-07 逐 2.5 ms 实测（S17 w）：1980, 后停顿里的吸气（-40～-45 dB、低频 '
                                                  '-17～-22 dB，删掉最响 -39.4 dB 即此）到 6.505，6.51 是 -54.6 dB '
                                                  '低谷，6.515 起 while 的 /w/ 浊音起头；终点在过零点 6.510167，/w/ 不动'},
                  'S19 raw 5.0312-5.5400': {'类型': '紧贴词尾的非人声',
                                            '配音指纹': '7499cce91ea3',
                                            '依据': '2026-11-07 逐 2.5 ms 实测（S19 w）：2016 的 n 到 5.02 收尾，5.04 一下 '
                                                  '-47.5 dB 残声，5.25–5.455 约 210 ms -44～-56 dB、重心 2.0–2.9 kHz '
                                                  '的吸气（删掉最响 -41.3 dB 即此），5.47 一帧 -59 dB 残声，5.545 起 '
                                                  'estimated；起点在过零点 5.03125 紧贴 2016 词尾，终点外侧 5 ms < -55 dB'},
                  'S12 raw 3.1700-3.5850': '2026-11-07 逐 2.5 ms 实测（S12 w）：Sea-Land, 后停顿：3.17–3.19 -61 dB '
                                           '静音，3.21–3.53 -42～-54 dB 的吸气（删掉最响 -39.5 dB 即此），3.55–3.57 -60～-61 '
                                           'dB，3.59 起 the（-31 dB）；两侧 -55.2/-61.6 dB 已衰减干净，删掉的是停顿中间的换气声',
                  'S19 raw 10.8450-11.2300': '2026-11-07 逐 2.5 ms 实测（S19 w）：countries 后、by 前：10.85 -60 '
                                             'dB，10.87–11.15 -44～-53 dB 的吸气，11.17 一下 -37.7 dB 声门噪声，11.21–11.23 '
                                             '-64～-68 dB；两侧 -63.1/-61.4 dB 已衰减干净，删掉的是换气声'},
          '同词异译': {'detached from：上拆卸下来的/从': '不是两种译法：detach from '
                                             '的意思“从……上拆卸下来”被“车轮和底盘”隔开，“从”和“上拆卸下来的”是同一个意思的两部分（T23）',
                   'by reckoning：估算/据': "不是两种译法：by one's reckoning 的意思“据……估算”被“公司”隔开，“据”和“估算”是同一个意思的两部分（T23）",
                   'at the expense of：为代价/以': '不是两种译法：at the expense of '
                                              '的意思“以……为代价”被“生计”隔开，“以”和“为代价”是同一个意思的两部分（T23）'},
          '短语': {'S2 detached … from': '不是搭配：from their wheels and chassis 只表示从哪里拆下，detach 单独就是“拆下”，同 60 S11 '
                                       'ejects … from',
                 'S10 rival firms': '不是搭配：rival 是形容词“竞争对手（的）”，修饰 firms；用户 2026-11-08 原话译“竞争对手公司的箱子”，firms '
                                    '单独就是“公司”',
                 'S1 slipped … for': '不是搭配：for Houston 只表示去向（开往休斯敦），slip out of 已整体标',
                 'S2 Clamped … to': '不是搭配：to her deck 只表示固定的位置（甲板上），clamp 单独就是“固定”，同 60 S2 observed … from',
                 'S5 Gangs … of': '不是搭配：of twenty or more dockworkers 只说明是什么人的一帮，gang 单独就是“（工人）一帮”',
                 'S12 patents … on': '不是搭配：on 属于 those on corner fittings（关于角配件的那些专利），和 patents 本身无关',
                 'S12 royalties … on': '不是搭配：on 属于 those on corner fittings，和 royalties 无关',
                 'S13 by … crane': '不是搭配：by crane 是 by＋工具（用吊机），和 by lorry、by hand 一样是普通用法，不像 in flocks '
                                   '那样有独立意思；crane 单独就是“吊机”，“由”已译出 by',
                 'S15 shrank … by': '不是搭配：by about three quarters 只表示幅度（缩减了约四分之三），shrink 单独就是“缩减”',
                 'S16 inaugurated … in': '不是搭配：in August 1962 只表示时间'},
          '高亮': {'S1 第2块': {'开始读': 10.85,
                            '配音指纹': '7499cce91ea3',
                            '依据': '2026-11-14只读原源重放诊断：G72母素材与原producer/clean、原调平JSON重建完整a.wav，全SHA与run43543967031原failedproof一致(1eb3f76a4b859fdde5b0646f3a077999a786f0a8767510f784974d98894d297c)，原AF后的整轨ADTS亦与failed/oldaccepted一致(09a13bc5853b6edbe832580796961247f5aea94c00b81be8e645314bd69d23da)。实际原生a.wav的10.85s原G45确认可收=true，前30ms最大-53.868dB、后40ms最大-20.616dB；此为程序实际测量，非用户听审。保留原失败报告和旧稿；本条记录当前原配音的真实开口测量，正式出片仍由原完整门复验。 '
                                  '原生实证报告SHA256=6e53358c7c4d2df735e7bc755f741c07d46042d99c3dfdf29fa68217d755b15b。'}}},
 '结尾解说': '简述',
 'allow_clash': ['converted', 'crates', 'identical'],
 '高亮按实际开口': True,
 '高亮开口门槛': 40,
 '术语': {'Second World War': '二战',
        'Ideal X': '理想X号',
        'Port Newark': '纽瓦克港',
        'New Jersey': '新泽西州',
        'Houston': '休斯敦',
        'Sea-Land': '海陆公司',
        'New York': '纽约',
        'Elizabeth': '伊丽莎白',
        'London': '伦敦',
        'Felixstowe': '费利克斯托',
        'Suffolk': '萨福克',
        'Journal of International Economics': '《国际经济学杂志》'},
 '停顿插入点': {'S4': {'1': [0.642792, '交界']}},
 '停顿删除区间': {'S7': {'1': [2.3725, 2.6625]}},
 '除阻加强': {'S3': {'句末': [4.59, 4.64, 6.0]}, 'S1': {'3': [8.8325, 8.8475, 4.5]}},
 '句子增益dB': {'S9': -0.3, 'S6': -0.5, 'S18': -0.5},
 '高亮开始': {'S19 第2块': 134.64},
 '段内渐变dB': {'S12': {'2': [0, 3]}},
 '非人声区间': {'S5': [[2.97, 3.22]],
           'S13': [[1.12, 1.353625, '紧贴词头']],
           'S1': [[5.535, 5.83]],
           'S15': [[5.5, 5.7125, '紧贴词头']],
           'S16': [[7.310625, 7.3925, '紧贴词尾']],
           'S17': [[6.245, 6.510167, '紧贴词头']],
           'S19': [[5.03125, 5.54, '紧贴词尾'], [10.855, 11.195]]},
 '结尾句': {'S20': {'前段语速': 0.9,
                 '最后一段语速': 0.78,
                 '最后一段前停顿': 0.7,
                 '接点': [102420, 129780],
                 '依据': '全篇结尾句按 07 定下的标准（用户 2026-10-10 同意并要求所有视频统一）：前段 0.9、最后一段“immense stacks.” 0.78、前面停 0.7 '
                       '秒。接点由 结尾句接点.py 自动找：0.9 那遍最后一个标点后最长静音（45 ms）的正中 4.268 s，0.78 那遍（75 ms）的正中 5.407 '
                       's，所在帧和两侧各 5 ms 都低于 -55 dB（程序以 08 校准：与人工核实的接点落在同一段静音里）'}},
 '词尾除阻': {'S7': {'句末': [3.945, 't']}},
 '区间声音指纹': {'S1': '3d76025116ad',
            'S3': '940ccb3c070e',
            'S4': '38af787d0550',
            'S5': '5df196d6b64d',
            'S7': 'd41c54e13002',
            'S13': '0c0e8c0af523',
            'S15': 'cdb5bb029ef2',
            'S16': '4c4bdd0a6f8f',
            'S17': 'b5c236daeee4',
            'S19': '56a838333bf6'},
 '换行变更记录': [{'日期': '2026-11-08',
             'S10': '上面的这个英文和它下面这个中文意思尽可能对齐……优先对齐标色的……其他的那种没有标色的能对齐的尽量对齐（用户 '
                    '2026-11-07，篇“61-65”，对齐需要改换行算已同意）；2026-11-08 用户逐句改稿',
             'S11': '上面的这个英文和它下面这个中文意思尽可能对齐……优先对齐标色的……其他的那种没有标色的能对齐的尽量对齐（用户 '
                    '2026-11-07，篇“61-65”，对齐需要改换行算已同意）；2026-11-08 用户逐句改稿',
             'S12': '上面的这个英文和它下面这个中文意思尽可能对齐……优先对齐标色的……其他的那种没有标色的能对齐的尽量对齐（用户 '
                    '2026-11-07，篇“61-65”，对齐需要改换行算已同意）；2026-11-08 用户逐句改稿',
             'S16': '上面的这个英文和它下面这个中文意思尽可能对齐……优先对齐标色的……其他的那种没有标色的能对齐的尽量对齐（用户 '
                    '2026-11-07，篇“61-65”，对齐需要改换行算已同意）；2026-11-08 用户逐句改稿'}]}

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 核对 import 生成并核对
生成并核对(S, out)
