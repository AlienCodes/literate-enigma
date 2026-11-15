#!/usr/bin/env python3
# Pure data frozen from the current approved JSON; shared helper/checkers unchanged.
import os
import sys

S = [(1,
  [[[('In May 1985,', '1985年5月，'),
     ('after', '经过'),
     ('a **bruising**', '一场**十分激烈的**(bruising)'),
     ('**confrontation**,', '**争执/交锋**(confrontation)，')],
    '（after…：介词短语作时间状语）'],
   [[("Apple's **board**", '苹果公司**董事会**(board)'),
     ('**ultimately**', '**最终**(ultimately)'),
     ('backed', '支持'),
     ('chief **executive**', '首席**执行官**(executive)'),
     ('John Sculley.', '约翰·斯卡利。')],
    '（back：支持；chief executive：首席执行官，\n作 John Sculley 的头衔）']]),
 (1,
  [[[('Steve Jobs, 30,', '时年30岁的史蒂夫·乔布斯')], '（30：插入语，说明他当时的年龄）'],
   [[('was **stripped of** his **managerial** duties at the company he had **co-founded**.',
      '在他参与**创办**(co-founded)的公司里被**剥夺了**(stripped of)**管理的**(managerial)职务。')],
    '（be stripped of…：被剥夺……；\nhe had co-founded：定语从句，\n省略了关系代词，修饰 company）']]),
 (1,
  [[[('That September,', '同年9月，'),
     ('**sidelined**', '已被**架空**(sidelined)、'),
     ('and **alienated**,', '**被疏远的**(alienated)'),
     ('he **resigned**.', '乔布斯**辞职了**(resigned)。')],
    '（sidelined and alienated：分词短语作状语，说明他辞职时的处境）\n'
    '（sidelined：指被排挤出核心圈子，剥夺实权、靠边站）\n'
    '（alienated：指感到被疏远、排斥，从而觉得格格不入、失去归属感）']]),
 (2,
  [[[('**Rewind**', '**回溯**(Rewind)'), ('three decades.', '三十年。')],
    '（rewind：本义倒带；\n从1985年往回倒三十年，\n正是乔布斯出生的1955年）']]),
 (2,
  [[[('Born in **San Francisco** on 24 February 1955, Jobs', '1955年2月24日，乔布斯生于**旧金山**(San Francisco)，')],
    '（Born in…：过去分词短语作状语）'],
   [[('was **adopted** as a **newborn**.', '还是**新生儿**(newborn)时就**被收养**(adopted)。')],
    '（as a newborn：作为新生儿，指刚出生不久）']]),
 (2,
  [[[('On 1 April 1976', '1976年4月1日，'),
     ('he', '他'),
     ('**founded** Apple with Steve Wozniak,', '与史蒂夫·沃兹尼亚克**创办了**(founded)苹果公司；')]],
   [[('the', '沃兹尼亚克是'),
     ('**electronics** engineer behind its first **prototypes**.',
      '苹果首批**样机**(prototypes)背后的**电子**(electronics)工程师。')],
    '（the electronics engineer…：同位语，补充说明 Steve Wozniak；\nbehind…：介词短语作后置定语，修饰 engineer）']]),
 (2,
  [[[("Apple's garage **origins**", '苹果的车库**起源**(origins)'),
     ('are largely', '在很大程度上只是具有'),
     ('**symbolic**;', '**象征**(symbolic)意义的；')],
    '（largely：在很大程度上）'],
   [[('Wozniak', '沃兹尼亚克'),
     ('calls', '称'),
     ('their **significance**', '其**意义**(significance)'),
     ('**inflated**.', '被**夸大了**(inflated)。')],
    "（call A B：认为 A 是 B；their 指 Apple's garage origins）"]]),
 (2,
  [[[('Apple **floated** on 12 December 1980;', '1980年12月12日，苹果公司**上市**(floated)；')], '（float：使公司上市）'],
   [[('the', '而'),
     ('**flagship**', '**旗舰**(flagship)'),
     ('Macintosh', '产品 Macintosh'),
     ('**debuted**', '**首次推出**(debuted)'),
     ('on 24 January 1984.', '于1984年1月24号。')],
    '（debut：首次亮相，首次推出）']]),
 (3,
  [[[('**Exile**', '这段**放逐**(Exile)岁月'), ('proved **productive**.', '**成果丰硕**(productive)。')],
    '（prove＋形容词：结果是……，\n事实证明……）']]),
 (3,
  [[[('Later in 1985', '1985年晚些时候，')]],
   [[('Jobs', '乔布斯'), ('**founded** NeXT,', '**创办了**(founded) NeXT，')]],
   [[('a computer **start-up**.', '一家电脑**初创公司**(start-up)。')], '（a computer start-up：同位语，\n补充说明 NeXT）']]),
 (3,
  [[[('In February 1986', '1986年2月，'),
     ('he **acquired**', '他**收购了**(acquired)'),
     ("Lucasfilm's", '卢卡斯影业的'),
     ('computer-**graphics**', '电脑**图形**(graphics)'),
     ('**outfit**,', '**团队**(outfit)，')],
    '（outfit：口语，团队，小机构）'],
   [[('which became **Pixar**.', '这个团队后来成为**皮克斯**(Pixar)。')], '（which…：非限制性定语从句，补充说明 outfit）']]),
 (3,
  [[[('It began as', '皮克斯起初是'),
     ('a **manufacturer**', '一家**制造商**(manufacturer)，'),
     ('of **specialised**', '生产**专用**(specialised)'),
     ('**hardware**,', '**硬件**(hardware)，')],
    '（begin as…：起初是……；\nof specialised hardware：of 结构作后置定语，修饰 manufacturer）'],
   [[('not chiefly', '主要并不是'), ('an **animation**', '**动画**(animation)'), ('**studio**.', '**工作室**(studio)。')],
    '（not chiefly…：主要并不是……，与 a manufacturer 对照）']]),
 (3,
  [[[('Toy Story,', '《玩具总动员》'), ('**released** on 22 November 1995,', '于1995年11月22日**上映**(released)，')],
    '（released on…：过去分词短语作后置定语，补充说明 Toy Story）'],
   [[('was the first', '是第一部'),
     ('**feature-length**', '**长篇**(feature-length)'),
     ('**computer-animated**', '**电脑动画**(computer-animated)'),
     ('film.', '电影。')]]]),
 (4,
  [[[('The **reversal** came on 20 December 1996:', '1996年12月20日，局面出现**彻底转变**(reversal)。')],
    '（冒号后具体说明彻底转变的内容）\n（reversal：局势、决定或状态彻底转向了相反的方向（即：逆转/反转））'],
   [[('Apple', '苹果'), ('agreed', '同意'), ('to buy', '收购'), ('NeXT,', 'NeXT，')], '（agree to do：同意做……）'],
   [[('gaining', '从而获得了'),
     ('the **core** software of the **eventual** Mac OS X', '**最终版**(eventual) Mac OS X 的**核心**(core)软件，')],
    '（gaining… and reuniting…：现在分词短语作结果状语）'],
   [[('and **reuniting with** its **estranged** co-founder.',
      '并**与**(reuniting with)**关系疏远的**(estranged)联合创始人**重聚**(reuniting with)。')],
    '（reunite with…：与……重聚；its estranged co-founder：指乔布斯）']]),
 (4,
  [[[('In August 1997', '1997年8月，'),
     ('Microsoft', '微软'),
     ('**invested** $150 million **in** its **distressed** **competitor**;',
      '**向**(invested in)这个**陷入困境的**(distressed)**竞争对手**(competitor)**投资**(invested in)1.5亿美元；')],
    '（invest A in B：向 B 投资 A）'],
   [[('that September', '同年9月，'),
     ('Jobs', '乔布斯'),
     ('**took the reins**', '**接掌大权**(took the reins)，'),
     ('as **interim** chief.', '出任**临时**(interim)负责人。')],
    '（take the reins：接掌大权，reins 本义缰绳；as：作为）']]),
 (4,
  [[[('Apple, he later said,', '他后来说，苹果当时'), ('had been weeks from **ruin**.', '离**破产**(ruin)只差几周。')],
    '（he later said：插入语；weeks from ruin：离破产只有几周）']]),
 (4,
  [[[('The iMac,', 'iMac、'), ('iPod,', 'iPod'), ('and iPhone', '和 iPhone'), ('followed,', '相继问世，')]],
   [[('the iPhone', 'iPhone'), ('**showcased** on 9 January 2007.', '于2007年1月9日公开**展示**(showcased)。')],
    '（the iPhone showcased…：独立主格结构，补充说明 iPhone）']]),
 (5,
  [[[('In October 2003', '2003年10月，'),
     ('Jobs', '乔布斯'),
     ('received', '收到了'),
     ('a **diagnosis**:', '一份**诊断**(diagnosis)：')],
    '（receive a diagnosis：被诊断出；冒号后说明诊断结果）'],
   [[('an **uncommon**,', '一种**罕见的**(uncommon)'),
     ('**cancerous**', '**恶性**(cancerous)'),
     ('**pancreatic**', '**胰腺**(pancreatic)'),
     ('**tumour**.', '**肿瘤**(tumour)。')]]]),
 (5,
  [[[('In August 2011', '2011年8月，'),
     ('Apple', '苹果公司'),
     ('**briefly**', '**一度**(briefly)'),
     ('**overtook** Exxon Mobil', '**超越**(overtook)埃克森美孚，')]],
   [[('as', '成为'),
     ("the world's", '全球'),
     ('**most valuable**', '**市值最高的**(most valuable)'),
     ('company.', '公司。')],
    '（overtake A as…：超过 A，成为……）']]),
 (5,
  [[[('His **tenure** ended on 24 August 2011;', '2011年8月24日，他的**任期**(tenure)结束；')]],
   [[('he died on 5 October 2011,', '2011年10月5日，他去世，'), ('aged 56.', '终年56岁。')], '（aged 56：作状语，说明去世时的年龄）']]),
 (5,
  [[[('He', '（在他最终离开时）他'),
     ('had spent nearly fourteen years **at the helm of** the company that **ousted** him.',
      '已在那家曾把他**逐出**(ousted)的公司**掌舵**(at the helm of)近十四年。')],
    '（at the helm of…：执掌……，helm 本义船舵；\n'
    'that ousted him：定语从句，修饰 company）\n'
    '（简述：▸创业：1976年，乔布斯与沃兹尼亚克创办苹果，沃兹尼亚克研制首批样机。苹果1980年上市；广为流传的车库创业故事，意义被夸大。▸离开：1985年，董事会支持首席执行官斯卡利，撤掉乔布斯的管理权，乔布斯随后辞职。▸另起：他创办一家电脑公司，又收购后来成为皮克斯的图形部门。皮克斯起初卖专用硬件，1995年推出长篇电脑动画《玩具总动员》。▸回归：1996年，苹果同意收购他的电脑公司，获得日后操作系统的核心软件，他也重回苹果；次年微软注资，乔布斯开始掌舵。▸重振：iMac、iPod、iPhone相继推出，苹果2011年一度市值全球第一。患胰腺恶性肿瘤的乔布斯同年卸任、去世，此前已领导这家曾撤掉他职权的公司近十四年。）']])]

out = {'no': '43',
 'title_en': 'From a Garage to the Top of the World',
 'title_zh': '从车库到世界之巅',
 'title_fx': {'hl': ['Garage', 'Top'], 'ghost': []},
 'sentences': [],
 '核对确认': {'口述': {'S3-1 觉得': '用户 2026-11-03 原话给的释义原样采用：“alienated '
                            '指感到被疏远、排斥，从而觉得格格不入、失去归属感。小字加上这些，小字加上这些。”——“觉得格格不入”是释义本身的意思，不是语音输入多出来的词'},
          '删除段': {'S3 raw 2.5251-2.5526': {'类型': '紧贴两头的非人声',
                                           '配音指纹': '563124cd66fa',
                                           '依据': '2026-11-03 43 逐 2.5/10 ms 实测（逐段看声音，w 秒）：S3 w '
                                                 '2.505083–2.532625：alienated 的 /d/ 衰减尾（2.4775–2.5075 -48～-55 '
                                                 'dB）与 he 的 /h/（2.5375 起 -45 dB、重心 4.0→5.0 kHz 一路升）之间 -49～-56 '
                                                 'dB 的弱噪声，中间没有 -55 dB 低谷可切，两头切在过零点，/d/ 与 /h/ 都不动'},
                  'S6 raw 2.9350-3.2900': {'类型': '紧贴词尾的非人声',
                                           '配音指纹': '563124cd66fa',
                                           '依据': '2026-11-03 43 逐 2.5/10 ms 实测（逐段看声音，w 秒）：S6 w '
                                                 '2.845–3.19（程序自动切点）：seventy-six 的 /s/ 在 2.8375 衰减到 -56 '
                                                 'dB，2.8425 -59.6 dB 低谷后，2.8475–2.85 一下 -42～-45 dB、重心 4.6 kHz '
                                                 '的孤立咔声，再接 2.855 起 -48～-55 dB 吸气；被报的“词尾 5 ms”是这下孤立咔声，前面隔着 '
                                                 '-56～-60 dB 低谷，不是 six 的 /s/'},
                  'S12 raw 3.3800-3.7910': {'类型': '紧贴词头的非人声',
                                            '配音指纹': '563124cd66fa',
                                            '依据': '2026-11-03 43 逐 2.5/10 ms 实测（逐段看声音，w 秒）：S12 w '
                                                  '3.515–3.781（程序自动切点）：hardware, 后 3.53–3.71 吸气（-43～-51 dB、重心 '
                                                  '2.0–2.6 kHz、低频 -8～-23 dB、周期 0.1–0.3），3.73–3.76 -44～-47 dB '
                                                  '低频团后 3.77–3.78 降到 -55～-60 dB，3.79 起 not 的 /n/（3.80 -21 '
                                                  'dB）；切点 3.781 在 /n/ 起音前'},
                  'S14 raw 10.3400-10.6835': {'类型': '紧贴词头的非人声',
                                              '配音指纹': '563124cd66fa',
                                              '依据': '2026-11-03 43 逐 2.5/10 ms 实测（逐段看声音，w 秒）：S14 w '
                                                    '10.32–10.663（程序自动切点）：Mac OS X（ten）后 10.32–10.61 '
                                                    '吸气（-35～-48 dB、重心 2.2–3.6 kHz、低频 -10～-26 dB、周期 '
                                                    '0.15–0.44），删掉的最响 -34.9 dB 是 10.595 的吸气峰；10.6625 -54.6 dB '
                                                    '后 10.67 起 and 的元音（10.685 -16 dB）'},
                  'S15 raw 2.1504-2.3330': {'类型': '紧贴两头的非人声',
                                            '配音指纹': '563124cd66fa',
                                            '依据': '2026-11-03 43 逐 2.5/10 ms 实测（逐段看声音，w 秒）：S15 w '
                                                  '2.140333–2.323：ninety-seven 的 /n/ 在 2.12–2.13 衰减（-34→-46 '
                                                  'dB），2.14 低谷 -57 dB 后 2.15–2.32 吸气（-43～-48 dB、重心 1.7–2.8 '
                                                  'kHz、低频 -10～-22 dB、周期 0.24），2.33 起 Microsoft 的 /m/ 浊音预发声（低频 '
                                                  '0～-3 dB）；句中无标点，两头切在过零点'},
                  'S17 raw 1.7950-2.1629': {'类型': '紧贴词头的非人声',
                                            '配音指纹': '563124cd66fa',
                                            '依据': '2026-11-03 43 逐 2.5/10 ms 实测（逐段看声音，w 秒）：S17 w '
                                                  '1.945–2.142917（合成标点 iPod; and）：1.98–2.14 吸气（-42～-55 dB、重心 '
                                                  '2.0–3.5 kHz、低频 -8～-23 dB、周期 0.12–0.35），直接连到 and '
                                                  '的低频起音（2.15–2.18 -44～-54 dB、低频 0～-2 dB），中间没有 -55 dB 低谷；切点 '
                                                  '2.142917 在过零点，and 的起音和元音（2.19 起）不动'},
                  'S18 raw 1.7727-1.9543': {'类型': '紧贴两头的非人声',
                                            '配音指纹': '563124cd66fa',
                                            '依据': '2026-11-03 43 逐 2.5/10 ms 实测（逐段看声音，w 秒）：S18 w '
                                                  '1.752667–1.934333：three 的 iː 在 1.72–1.75 衰减（-24→-43 dB、低频 '
                                                  '-1 dB），1.7525 -53 dB 后 1.76–1.93 吸气（-39～-52 dB、重心 2.8–3.4 '
                                                  'kHz、低频 -5～-24 dB、周期 0.21），1.94 起 Jobs 的 /dʒ/ 浊音预发声（低频 0～-1 '
                                                  'dB）；删掉的最响 -38.4 dB 是吸气峰，句中无标点，两头切在过零点'}},
          '高亮': {'S14 第4块': {'开始读': 108.54,
                             '配音指纹': '563124cd66fa',
                             '依据': '2026-11-03 直接读 work_43/a.wav 逐 10 ms：Mac OS X 的 ten 的 /n/ 108.32–108.36 '
                                   '衰减（-25→-49 dB），108.37–108.53 是删掉吸气后的数字静音（-240 dB），108.54 -49.3、108.55 '
                                   '-31.4、108.56 -15.1 dB 是 and 开口；高亮 108.53 提前 0.01 秒；甲法 108.35 落在 ten 的收尾'}},
          '机器复听': {'S12': {'配音指纹': '563124cd66fa',
                           '依据': '2026-11-03 实测：S12 not chiefly an animation studio 的 an 在元音前弱读，配音音标 nˌɑːt '
                                 'tʃˈiːfli ɐn ˌænɪmˈeɪʃən（Cambridge an 弱读 /ən/），读音核对 0；parakeet 听成 an，small.en '
                                 '听成 in（ɐn/ɪn 弱读近音），前后 chiefly、animation 两路都对；交用户听'}},
          '非人声': {'14.29–14.39s': {'配音指纹': '563124cd66fa',
                                   '实测': {'最响dB': -30.6, '重心Hz': 0, '周期': 0.0, '低频dB': 0.0},
                                   '依据': '2026-11-03 43 逐 2.5/10 ms 实测（dossier_43、逐段看声音，配音指纹 563124cd66fa）：S2 '
                                         'w 1.19–1.295：Jobs; 停顿后 thirty 的 /θ/：-48→-25 dB、重心 6.2→8.0 kHz、低频 '
                                         '-26～-43 dB（齿间擦音的高频弥散谱），1.32 起 ɜ 元音 -10→+1 dB，中间没有低谷，属于 thirty',
                                   '词头': 'θ'},
                  '15.21–15.24s': {'配音指纹': '563124cd66fa',
                                   '实测': {'最响dB': -48.1, '重心Hz': 2427, '周期': 0.32, '低频dB': -0.2},
                                   '依据': '2026-11-03 43 逐 2.5/10 ms 实测（dossier_43、逐段看声音，配音指纹 563124cd66fa）：S2 '
                                         'w 2.075–2.105：30, 停顿后 was 的 /w/ 浊音预发声（-46～-57 dB、低频 -0～-3 dB 占优、重心 '
                                         '1.8–3.3 kHz），2.12 起 -33→-18 dB 直接升进 /w/，属于 was',
                                   '词头': 'w'},
                  '15.76–15.78s': {'配音指纹': '563124cd66fa',
                                   '实测': {'最响dB': -34.8, '重心Hz': 3053, '周期': 0.0, '低频dB': -19.7},
                                   '依据': '2026-11-03 43 逐 2.5/10 ms 实测（dossier_43、逐段看声音，配音指纹 563124cd66fa）：S2 '
                                         'w 2.62–2.635：stripped 的 /p/ 闭塞中除阻（-50 dB、重心 2.2 kHz、低频 -16 dB，前后 '
                                         '-59～-64 dB 闭塞），2.67 起 of，属于 stripped 的 /pt/',
                                   '词尾': 'p'},
                  '20.17–20.18s': {'配音指纹': '563124cd66fa',
                                   '实测': {'最响dB': -30.3, '重心Hz': 2745, '周期': 0.0, '低频dB': -2.2},
                                   '依据': '2026-11-03 43 逐 2.5/10 ms 实测（dossier_43、逐段看声音，配音指纹 563124cd66fa）：S3 '
                                         'w 0.025–0.04：句首 That 的 /ð/ 浊音起音（低频 -2 dB、-35→-22 dB），0.06 起元音 -9→-1 '
                                         'dB，属于 That',
                                   '词头': 'ð'},
                  '20.53–20.55s': {'配音指纹': '563124cd66fa',
                                   '实测': {'最响dB': -30.8, '重心Hz': 3661, '周期': 0.0, '低频dB': -25.2},
                                   '依据': '2026-11-03 43 逐 2.5/10 ms 实测（dossier_43、逐段看声音，配音指纹 563124cd66fa）：S3 '
                                         'w 0.385–0.40：That 的 /t/ 除阻（0.39 一下 -28 dB、重心 3.7 kHz、低频 -28 dB，前后 '
                                         '-58～-67 dB 闭塞），0.43 起 September 的 /s/（重心 5.6 kHz），属于 That',
                                   '词尾': 't'},
                  '24.07–24.11s': {'配音指纹': '563124cd66fa',
                                   '实测': {'最响dB': -34.3, '重心Hz': 1972, '周期': 0.29, '低频dB': -1.7},
                                   '依据': '2026-11-03 43 逐 2.5/10 ms 实测（dossier_43、逐段看声音，配音指纹 563124cd66fa）：S3 '
                                         'w 3.30–3.335：句末 resigned 的 /d/ 闭塞浊音（-41～-49 dB、低频 -2 dB、重心 1.3–2.2 '
                                         'kHz），3.34 一下 -33 dB 是 /d/ 除阻，属于 resigned',
                                   '词尾': 'd'},
                  '27.73–27.74s': {'配音指纹': '563124cd66fa',
                                   '实测': {'最响dB': -31.7, '重心Hz': 868, '周期': 0.0, '低频dB': -1.0},
                                   '依据': '2026-11-03 43 逐 2.5/10 ms 实测（dossier_43、逐段看声音，配音指纹 563124cd66fa）：S5 '
                                         'w 0.015–0.03：句首 Born 的 /b/ 浊音预发声（低频 -1～-2 dB、重心 0.3 kHz、-48→-31 '
                                         'dB），0.03 起连着 /b/，属于 Born',
                                   '词头': 'b'},
                  '33.98–33.99s': {'配音指纹': '563124cd66fa',
                                   '实测': {'最响dB': -42.2, '重心Hz': 3351, '周期': 0.0, '低频dB': -20.3},
                                   '依据': '2026-11-03 43 逐 2.5/10 ms 实测（dossier_43、逐段看声音，配音指纹 563124cd66fa）：S5 '
                                         'w 6.285–6.295：adopted 的 /p/ 闭塞中除阻（6.29 一下 -41 dB、重心 3.2 kHz、低频 -20 '
                                         'dB，前后 -60～-71 dB），属于 adopted 的 /pt/',
                                   '词尾': 'p'},
                  '39.24–39.26s': {'配音指纹': '563124cd66fa',
                                   '实测': {'最响dB': -49.4, '重心Hz': 2655, '周期': 0.0, '低频dB': -0.6},
                                   '依据': '2026-11-03 43 逐 2.5/10 ms 实测（dossier_43、逐段看声音，配音指纹 563124cd66fa）：S6 '
                                         'w 3.205–3.22：seventy-six 后 he 的起音（-57→-49 dB、低频占优），3.23 起 /h/ 送气 '
                                         '-38→-30 dB、重心 3.8–4.6 kHz 一路连上，中间没有 -55 dB 低谷（K125：不切 /h/），属于 he',
                                   '词头': 'h'},
                  '57.34–57.41s': {'配音指纹': '563124cd66fa',
                                   '实测': {'最响dB': -36.6, '重心Hz': 3367, '周期': 0.23, '低频dB': -2.7},
                                   '依据': '2026-11-03 43 逐 2.5/10 ms 实测（dossier_43、逐段看声音，配音指纹 563124cd66fa）：S8 '
                                         'w 3.025–3.105：eighty; 的 /i/ 元音气声收尾：2.99 -23、3.02 -27 dB 起一路衰减到 3.10 '
                                         '-53、3.11 -58 dB，重心 2.4–4.6 kHz（/i/ 的高第二共振峰）、低频 -2～-13 dB，中间不断，属于 '
                                         'eighty',
                                   '词尾': 'i'},
                  '57.37–57.38s': {'配音指纹': '563124cd66fa',
                                   '实测': {'最响dB': -36.6, '重心Hz': 3370, '周期': 0.0, '低频dB': -2.3},
                                   '依据': '2026-11-03 43 逐 2.5/10 ms 实测（dossier_43、逐段看声音，配音指纹 563124cd66fa）：S8 '
                                         'w 3.055–3.07：同上 eighty 元音收尾衰减段中的一帧（-40～-46 dB），连着前后，属于 eighty',
                                   '词尾': 'i'},
                  '59.41–59.44s': {'配音指纹': '563124cd66fa',
                                   '实测': {'最响dB': -31.0, '重心Hz': 612, '周期': 0.55, '低频dB': -0.1},
                                   '依据': '2026-11-03 43 逐 2.5/10 ms 实测（dossier_43、逐段看声音，配音指纹 563124cd66fa）：S8 '
                                         'w 5.20–5.23：Macintosh 的 /ʃ/ 收尾后 debuted 的 /d/ 浊音预发声（-48→-27 dB、低频 -1 '
                                         'dB、重心 0.3–0.6 kHz、周期 0.55），5.25 起升进 /d/，属于 debuted',
                                   '词头': 'd'},
                  '63.15–63.24s': {'配音指纹': '563124cd66fa',
                                   '实测': {'最响dB': -35.4, '重心Hz': 1609, '周期': 0.25, '低频dB': -9.7},
                                   '依据': '2026-11-03 43 逐 2.5/10 ms 实测（dossier_43、逐段看声音，配音指纹 563124cd66fa）：S8 '
                                         'w 8.94–9.03：句末 eighty-four 的 ɹ 收尾衰减（-30～-45 dB、重心 0.9–2.2 kHz、低频 '
                                         '-6～-19 dB），9.03 起 -60 dB 以下，连着前面的词，属于 four',
                                   '词尾': 'ɹ'},
                  '70.29–70.33s': {'配音指纹': '563124cd66fa',
                                   '实测': {'最响dB': -31.4, '重心Hz': 4035, '周期': 0.2, '低频dB': -14.2},
                                   '依据': '2026-11-03 43 逐 2.5/10 ms 实测（dossier_43、逐段看声音，配音指纹 563124cd66fa）：S10 '
                                         'w 3.305–3.35：NeXT 的 /st/：3.27 /s/（-24 dB、重心 5.8 kHz）、3.29–3.30 闭塞 '
                                         '-58～-63 dB、3.31–3.33 /t/ 除阻送气 -33～-39 dB、重心 3.6–3.9 kHz，属于 NeXT',
                                   '词尾': 't'},
                  '71.94–71.97s': {'配音指纹': '563124cd66fa',
                                   '实测': {'最响dB': -32.2, '重心Hz': 1582, '周期': 0.24, '低频dB': -4.8},
                                   '依据': '2026-11-03 43 逐 2.5/10 ms 实测（dossier_43、逐段看声音，配音指纹 563124cd66fa）：S10 '
                                         'w 4.855–4.895：句末 start-up 的 /p/ 除阻（4.86 -35 dB、重心 1.9 kHz、低频 -14 '
                                         'dB，前面 4.83–4.85 闭塞 -61～-64 dB），属于 start-up',
                                   '词尾': 'p'},
                  '104.61–104.63s': {'配音指纹': '563124cd66fa',
                                     '实测': {'最响dB': -49.5, '重心Hz': 2825, '周期': 0.39, '低频dB': -0.1},
                                     '依据': '2026-11-03 43 逐 2.5/10 ms 实测（dossier_43、逐段看声音，配音指纹 '
                                           '563124cd66fa）：S14 w 6.555–6.58：NeXT, 停顿后 gaining 的 /ɡ/ '
                                           '浊音预发声（-49～-56 dB、低频 0～-2 dB 占优），6.61 起 -28 dB /ɡ/，属于 gaining',
                                     '词头': 'ɡ'},
                  '114.85–114.89s': {'配音指纹': '563124cd66fa',
                                     '实测': {'最响dB': -41.0, '重心Hz': 1349, '周期': 0.41, '低频dB': -0.2},
                                     '依据': '2026-11-03 43 逐 2.5/10 ms 实测（dossier_43、逐段看声音，配音指纹 '
                                           '563124cd66fa）：S15 w 2.325–2.37：ninety-seven 后 Microsoft 的 /m/ '
                                           '浊音预发声（-43～-56 dB、低频 0～-3 dB、周期 0.41），2.40 起 -28→-20 dB /m/；前面 '
                                           '2.14–2.32 的吸气已用非人声区间切掉，属于 Microsoft',
                                     '词头': 'm'},
                  '120.91–120.92s': {'配音指纹': '563124cd66fa',
                                     '实测': {'最响dB': -36.9, '重心Hz': 4061, '周期': 0.0, '低频dB': -20.2},
                                     '依据': '2026-11-03 43 逐 2.5/10 ms 实测（dossier_43、逐段看声音，配音指纹 '
                                           '563124cd66fa）：S15 w 8.485–8.495：that 的 /t/ 除阻（8.49 一下 -44 dB、重心 '
                                           '3.8 kHz、低频 -16 dB，前后 -64～-68 dB 闭塞），8.52 起 September 的 /s/，属于 that',
                                     '词尾': 't'},
                  '122.04–122.06s': {'配音指纹': '563124cd66fa',
                                     '实测': {'最响dB': -37.5, '重心Hz': 3228, '周期': 0.3, '低频dB': -13.7},
                                     '依据': '2026-11-03 43 逐 2.5/10 ms 实测（dossier_43、逐段看声音，配音指纹 '
                                           '563124cd66fa）：S15 w 9.62–9.645：took 的 /k/ 除阻（9.61 闭塞 -64 '
                                           'dB，9.62–9.63 -44～-36 dB、重心 2.8–3.2 kHz 软腭除阻），9.65 起 the，属于 took',
                                     '词尾': 'k'},
                  '123.83–124.09s': {'配音指纹': '563124cd66fa',
                                     '实测': {'最响dB': -31.5, '重心Hz': 0, '周期': 0.0, '低频dB': 0.0},
                                     '依据': '2026-11-03 43 逐 2.5/10 ms 实测（dossier_43、逐段看声音，配音指纹 '
                                           '563124cd66fa）：S15 w 11.41–11.67：句末 chief 的 iː 收尾和 /f/：11.41–11.49 '
                                           '元音收尾 -30～-45 dB，11.50–11.66 /f/ 擦音 -33～-45 dB、重心 4.5–6.1 kHz、低频 '
                                           '-21～-39 dB，11.67 起降到 -57 dB 以下，属于 chief',
                                     '词尾': 'f'},
                  '123.86–123.95s': {'配音指纹': '563124cd66fa',
                                     '实测': {'最响dB': -35.2, '重心Hz': 3814, '周期': 0.2, '低频dB': -12.6},
                                     '依据': '2026-11-03 43 逐 2.5/10 ms 实测（dossier_43、逐段看声音，配音指纹 '
                                           '563124cd66fa）：S15 w 11.435–11.535：chief 的 iː→/f/ 过渡（-30～-45 '
                                           'dB，11.50 起重心升过 4.5 kHz），连着前后，属于 chief',
                                     '词尾': 'f'},
                  '131.34–131.36s': {'配音指纹': '563124cd66fa',
                                     '实测': {'最响dB': -43.9, '重心Hz': 2534, '周期': 0.37, '低频dB': -0.2},
                                     '依据': '2026-11-03 43 逐 2.5/10 ms 实测（dossier_43、逐段看声音，配音指纹 '
                                           '563124cd66fa）：S17 w 2.15–2.175：iPod; 停顿后 and 的浊音起音（-44～-50 dB、低频 '
                                           '0～-8 dB 占优、周期 0.37），2.20 起 -17 dB 元音；前面 1.945–2.143 的吸气已切掉，属于 and',
                                     '词头': 'æ'},
                  '140.24–140.28s': {'配音指纹': '563124cd66fa',
                                     '实测': {'最响dB': -44.1, '重心Hz': 2247, '周期': 0.31, '低频dB': -0.3},
                                     '依据': '2026-11-03 43 逐 2.5/10 ms 实测（dossier_43、逐段看声音，配音指纹 '
                                           '563124cd66fa）：S18 w 1.935–1.98：three 后 Jobs 的 /dʒ/ 浊音预发声（-46～-53 '
                                           'dB、低频 0～-1 dB 占优），2.00 起 -27 dB /dʒ/；前面 1.75–1.93 的吸气已切掉，属于 Jobs',
                                     '词头': 'dʒ'}},
          '停顿位置': {'S16 Apple, / he @0.415': '2026-11-03 S16 合成标点 Apple; he 重新合成后逐 2.5/5 ms 实测（w）：Apple 的 /l/ '
                                             '在 0.34–0.37 收尾（-12～-16 dB、重心 1.4–2.5 kHz），0.375–0.43 衰减成 -18～-23 '
                                             'dB 的过渡段（5 ms 包络 0.385 -19.9、0.395 -21.6、0.415 -23.2 '
                                             '最低）；带时长模型分号格在 0.37–0.442、h 0.442、iː 0.467；0.435 起升到 -17.6、0.4425 '
                                             '-11.2 是 he 的开头。停顿 0.415 落在包络最低点、he 起声之前，是两词之间；原合成 Apple, he '
                                             '两词完全连读，插在 0.460（he 的元音里），已改合成标点',
                   'S3 alienated, / he @2.505': '2026-11-03 逐 2.5/10 ms 看声音实测（S3 w）：alienated 的 /d/ 在 '
                                                '2.46–2.4675 收尾（-32→-38 dB），2.4775–2.5075 衰减到 -48～-55 '
                                                'dB（2.5075 -54.9 dB 低谷）；he 的 /h/ 2.5375 起（-45 dB、重心 4.0→5.0 '
                                                'kHz 一路升），2.6275 起 iː 元音 -21→-11 dB；停顿 2.505 落在 alienated '
                                                '尾音衰减之后、/h/ 之前的低谷里，是两词之间'},
          '合组': {'S6 electronics engineer behind its first prototypes': '对齐不了：behind its first prototypes '
                                                                        '是介词短语作后置定语，修饰 '
                                                                        'engineer，中文“苹果首批样机背后的电子工程师”定语必须整体提前（用户 '
                                                                        '2026-11-03 原话定的译文）',
                 'S2 was stripped of his managerial duties at the company he had co-founded': '对齐不了：at the '
                                                                                              'company '
                                                                                              '是地点状语、he had '
                                                                                              'co-founded '
                                                                                              '是省略关系代词的定语从句，中文“在他参与创办的公司里”必须整体放到动词前（沿用文章定稿语序），duties、company '
                                                                                              '拆开后中文语序全乱',
                 'S16 Apple, he later said': '对齐不了：he later said 是插入语，中文“他后来说”必须放到句首，主语“苹果当时”放在它后面（沿用文章定稿语序）',
                 'S21 had spent nearly fourteen years at the helm of the company that ousted him': '对齐不了：spend '
                                                                                                   '时长 '
                                                                                                   'at…中文“在那家……的公司掌舵近十四年”语序必须倒过来：地点（含定语从句 '
                                                                                                   'that '
                                                                                                   'ousted '
                                                                                                   'him）提前、时长放到最后（沿用文章定稿语序）'},
          '对齐': {'S6-2 electronics engineer behind its': 'behind its first prototypes 是后置定语，修饰 '
                                                         'engineer，中文“苹果首批样机背后的电子工程师”定语必须整体提前（用户原话定的译文）',
                 'S8-2 debuted on 24 January 1984.': 'on 24 January 1984 是时间状语，中文“1984年1月24日，旗舰产品 Macintosh '
                                                     '亮相”时间必须提前，日期放在句首 the 下面',
                 'S6-2 electronics engineer behind it': 'behind its first prototypes 是后置定语，修饰 '
                                                        'engineer，中文“苹果首批样机背后的电子工程师”定语必须整体提前（用户原话定的译文）',
                 'S2-2 was stripped of his managerial': 'at the company he had co-founded '
                                                        '是地点状语加定语从句，中文“在他参与创办的公司里”必须整体提前',
                 'S5-1 Born in San Francisco on 24 Fe': '过去分词短语作状语，日期在中文必须提前（“1955年2月24日，乔布斯生于旧金山”），主语 Jobs '
                                                        '中文放进这一组，沿用文章定稿语序',
                 'S5-2 was adopted as a newborn.': 'as a newborn 是提前的介词短语，中文“还是新生儿时就被人收养”时间必须放到动词前',
                 'S6-1 founded Apple with Steve Wozni': 'with Steve Wozniak '
                                                        '是提前的介词短语，中文“与史蒂夫·沃兹尼亚克创办了苹果公司”必须放到动词前',
                 'S8-1 Apple floated on 12 December 1': 'on 12 December 1980 '
                                                        '是时间状语，中文“1980年12月12日，苹果公司上市”时间必须提前',
                 'S13-1 released on 22 November 1995,': 'released on… 中文“于1995年11月22日上映”时间必须放到动词前',
                 'S14-1 The reversal came on 20 Decemb': 'on 20 December 1996 '
                                                         '是时间状语，中文“1996年12月20日，局面出现转机”时间必须提前',
                 'S14-3 the core software of the event': 'of 结构：中文“日后 Mac OS X 的核心软件”of 后面的部分必须提前',
                 'S14-4 and reuniting with its estrang': 'with its estranged co-founder '
                                                         '是提前的介词短语，中文“并与那位关系疏远的联合创始人重聚”必须放到动词前',
                 'S15-1 invested $150 million in its d': 'in its distressed competitor '
                                                         '是提前的介词短语，中文“向这个陷入困境的竞争对手投资1.5亿美元”必须放到动词前',
                 'S16-1 had been weeks from ruin.': 'from ruin 是提前的介词短语，中文“离破产只差几周”必须放到前面',
                 'S17-2 showcased on 9 January 2007.': 'on 9 January 2007 是时间状语，中文“于2007年1月9日公开展示”时间必须放到动词前',
                 'S20-1 His tenure ended on 24 August ': 'on 24 August 2011 是时间状语，中文“2011年8月24日，他的任期结束”时间必须提前',
                 'S20-2 he died on 5 October 2011,': 'on 5 October 2011 是时间状语，中文“2011年10月5日，他去世”时间必须提前',
                 'S21-1 had spent nearly fourteen year': 'at the helm of the company that ousted him '
                                                         '是提前的介词短语加定语从句，中文地点必须提前、时长放最后'},
          '牛津逗号': {'S3 That September, sidelined and': '不是三项并列：sidelined and alienated 只有两项'},
          '数字': {'S15-1 150': '$150 million 中文写“1.5亿美元”，数值相同（150百万=1.5亿）；英文读 one hundred and fifty million '
                              'dollars'},
          '方向': {'S1-1 after→经过': 'after a bruising confrontation 中文“经过一场激烈的交锋”，“经过”表示在交锋之后，方向一致'},
          '同词异译': {'invested in：向/投资': '不是异译：invest A in B 短语整体标，被隔开的中文“向……投资”两处都标同一个英文（T22/T23）',
                   'reuniting with：与/重聚': '不是异译：reunite with 短语整体标，被隔开的中文“与……重聚”两处都标同一个英文（T22/T23）'},
          '读音': {'X': {'读音': 'tˈɛn',
                       '依据': '2026-11-03 43 S14 Mac OS X：X 是罗马数字10，苹果官方读 '
                             'ten（https://en.wikipedia.org/wiki/MacOS：Mac OS X，X pronounced ten）；按语境读音“Mac OS '
                             'X”换成 tˈɛn，只认这一种读法（关掉按语境读音读回字母 ˈɛks 必须报出）'}},
          '短语': {'S13 released … on': '不是搭配：on 22 November 1995 只引出日期，不是 release on 的固定用法',
                 'S6 founded … with': '不是搭配：with Steve Wozniak 只表示一起创办的人，found 在这里不与 with 构成固定用法',
                 'S5 adopted … as': '不是搭配：as a newborn 表示被收养时的身份（作为新生儿），adopt 在这里不与 as 构成固定用法',
                 'S5 in … San': '不是搭配：born in San Francisco 里 in 只引出出生地点，San Francisco 是地名，不是 in + 名词的固定用法',
                 'S8 floated … on': '不是搭配：on 12 December 1980 只引出日期，不是 float on 的固定用法',
                 'S8 debuted … on': '不是搭配：on 24 January 1984 只引出日期，不是 debut on 的固定用法',
                 'S14 core … of': '不是搭配：of the eventual Mac OS X 只表示所属，core 在这里是形容词修饰 software，不是 core of '
                                  '的固定用法',
                 'S17 showcased … on': '不是搭配：on 9 January 2007 只引出日期，不是 showcase on 的固定用法',
                 'S19 overtook … as': "不是搭配：as the world's most valuable company 表示超越之后的身份（成为……），不是 overtake "
                                      'as 的固定用法'}},
 '结尾解说': '简述',
 'allow_clash': ['adopted', 'founded', 'hardware', 'released'],
 '高亮按实际开口': True,
 '高亮开口门槛': 40,
 '分段增益dB': {'S2': {'1': -2.0, '2': -2.0, '3': -2.5}, 'S16': {'1': -0.5, '2': -0.5}},
 '合成标点': {'S2': [['Jobs, 30', 'Jobs; 30']],
          'S16': [['Apple, he', 'Apple; he']],
          'S17': [['iPod, and', 'iPod; and']]},
 '非人声区间': {'S6': [[2.845, 3.19]],
           'S7': [[3.87, 3.885]],
           'S11': [[2.26, 2.515]],
           'S12': [[3.515, 3.781, '紧贴词头']],
           'S13': [[4.96, 5.255542, '紧贴词头']],
           'S14': [[10.32, 10.663458, '紧贴词头']],
           'S3': [[0.80575, 0.915042, '紧贴两头'], [2.505083, 2.532625, '紧贴两头']],
           'S15': [[2.140333, 2.323, '紧贴两头'], [7.88, 8.098708, '紧贴词头']],
           'S18': [[1.752667, 1.934333, '紧贴两头']],
           'S17': [[1.945, 2.142917, '紧贴词头']],
           'S19': [[2.072792, 2.363833]]},
 '术语': {'Apple': '苹果',
        'John Sculley': '约翰·斯卡利',
        'Sculley': '斯卡利',
        'Steve Jobs': '史蒂夫·乔布斯',
        'Jobs': '乔布斯',
        'San Francisco': '旧金山',
        'Steve Wozniak': '史蒂夫·沃兹尼亚克',
        'Wozniak': '沃兹尼亚克',
        'Macintosh': 'Macintosh',
        'NeXT': 'NeXT',
        'Lucasfilm': '卢卡斯影业',
        'Pixar': '皮克斯',
        'Toy Story': '玩具总动员',
        'Mac OS X': 'Mac OS X',
        'Microsoft': '微软',
        'iMac': 'iMac',
        'iPod': 'iPod',
        'iPhone': 'iPhone',
        'Exxon Mobil': '埃克森美孚'},
 '词尾除阻': {'S6': {'1': [5.73, 'k']}, 'S7': {'1': [3.395, 'k']}, 'S11': {'1': [5.465, 't']}},
 '区间声音指纹': {'S3': '2fb647148bda',
            'S6': '8aa10f0af462',
            'S7': '96278dd0747c',
            'S11': '71cbcfe64edd',
            'S12': 'b81903612615',
            'S13': 'b389c70d273c',
            'S14': 'c1a0fc451e2c',
            'S15': 'fcd47a194e5d',
            'S17': '2b385ca32bf6',
            'S18': 'a7fa8003f511',
            'S19': '7aa95427b232'},
 '换行变更记录': [{'日期': '2026-11-03',
             'S10': '用户原话“这个作为单独单独一行。这个翻译为乔布斯创办了next 一家电脑初创公司。分三行，分成三行，分成三行。”（2026-11-03，S10 分成 Later in 1985 '
                    '/ Jobs founded NeXT, / a computer start-up. 三行）',
             'S8': '用户原话“翻译为 而旗舰产品首次推出于 1984年1月24号。”（2026-11-03，S8 后半句按用户语序改写、用户选“保留 Macintosh”，日期挪到句末，换行随之变）',
             'S6': '用户原话“1976年4月1日，他与史蒂夫·沃兹尼亚克创办了苹果公司；沃兹尼亚克是苹果首批样机背后的电子工程师。”（2026-11-03，S6 '
                   '后半句中文按用户语序改写，后置定语整体提前，换行随之变）'}],
 '字号上限': {'S21': 99}}

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 核对 import 生成并核对
生成并核对(S, out)
