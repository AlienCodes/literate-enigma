#!/usr/bin/env python3
# Pure data frozen from the current approved JSON; shared helper/checkers unchanged.
import os
import sys

S = [(1,
  [[[('**Smallpox**,', '**天花**(Smallpox)，'),
     ('a **contagious**', '一种**传染性的**(contagious)'),
     ('**affliction**,', '**疾病**(affliction)，')],
    '（a contagious affliction：同位语，补充说明 Smallpox）'],
   [[('killed', '夺去了'),
     ('about', '约'),
     ('three in ten', '三成'),
     ('of its **sufferers**', '**患者**(sufferers)的生命，'),
     ('and', '并且'),
     ('an estimated', '估计有'),
     ('300 million', '3亿人'),
     ('in the 20th century.', '在20世纪丧命。')],
    '（three in ten：十分之三，即约三成；\nkilled 的宾语有两个：three in ten of its sufferers 和 300 million）']]),
 (1,
  [[[('An early', '一种早期的'),
     ('**safeguard**,', '**防护手段**(safeguard)，'),
     ('**deliberately**', '是**有意**(deliberately)'),
     ('**implanting** **matter** from its **sores** in the healthy,',
      '把天花**脓疮**(sores)中的**物质**(matter)**植入**(implanting)健康人体内，')],
    '（deliberately implanting…：现在分词短语作同位语，\n说明 safeguard 的内容；\nimplant A in B：把 A 植入 B；the healthy：健康的人）'],
   [[('was **practised** in China by the 16th century', '到16世纪，中国已在**施行**(practised)这种方法，'),
     ('and reached England in 1721.', '1721年又传入英国。')],
    '（by the 16th century：到16世纪时（已经））']]),
 (1,
  [[[('The **procedure**', '这种**做法**(procedure)'),
     ('itself', '本身'),
     ('could cause', '可能导致'),
     ('**grave**', '**严重的**(grave)'),
     ('**sickness**', '**疾病**(sickness)'),
     ('or death,', '或死亡，')]],
   [[('if less', '尽管不如'), ('**frequently** than natural smallpox.', '自然天花那样**频繁**(frequently)。')],
    '（if less frequently than…：= though less frequently than…，\n虽然不如……频繁）']]),
 (2,
  [[[('**Rustic**', '**乡间**(Rustic)'), ('**lore**', '**传说**(lore)'), ('held that', '认为，')],
    '（hold that…：认为……）'],
   [[('milkmaids', '挤奶女工'),
     ('with cowpox,', '若得过牛痘'),
     ('a **mild** **ailment** of **livestock**,',
      '这种**牲畜**(livestock)的**轻微**(mild)**病症**(ailment)，\n{{（一般指牛的牛痘，轻微病症）|ailment}}'),
     ('were **immune to** smallpox.', '就**对**(immune to)天花**免疫**(immune to)。')],
    '（a mild ailment of livestock：同位语，补充说明 cowpox）']]),
 (2,
  [[[('In 1774', '1774年，'), ('Benjamin Jesty,', '本杰明·杰斯蒂，'), ('a Dorset', '一位多塞特郡'), ('farmer,', '农夫，')],
    '（a Dorset farmer：同位语，补充说明 Benjamin Jesty；\nDorset：多塞特郡，在英格兰西南部）'],
   [[('**employed**', '**使用**(employed)'),
     ('cowpox', '牛痘'),
     ('to protect', '来保护'),
     ('his wife', '他的妻子'),
     ('and', '和'),
     ('two sons.', '两个儿子。')]]]),
 (2,
  [[[('On 14 May 1796', '1796年5月14日，'),
     ('Edward Jenner,', '爱德华·詹纳，'),
     ('a **provincial**', '一位**地方**(provincial)'),
     ('**practitioner**,', '**执业医师**(practitioner)，')],
    '（a provincial practitioner：同位语，补充说明 Edward Jenner）'],
   [[("**inserted** **fluid** from a milkmaid's cowpox sore", '将取自一名挤奶女工牛痘疮的**液体**(fluid)，**注入**(inserted)'),
     ('into a **scratch** on eight-year-old James Phipps.', '8岁的詹姆斯·菲普斯的一道**划痕**(scratch)中。')],
    '（insert A into B：把 A 注入 B；\non eight-year-old James Phipps：后置定语，修饰 scratch）']]),
 (3,
  [[[('On 1 July 1796', '1796年7月1日，'),
     ('Jenner', '詹纳'),
     ('**exposed** the boy **to** smallpox;', '**让**(exposed to)这个男孩**接触**(exposed to)天花；')],
    '（expose A to B：使 A 接触 B）'],
   [[('no **symptoms**', '任何**症状**(symptoms)都没有'), ('**ensued**.', '**随之出现**(ensued)。')]]]),
 (3,
  [[[('In 1797', '1797年，'),
     ('the Royal Society', '皇家学会'),
     ('declined', '拒绝'),
     ('to', '去'),
     ('**publish**', '**发表**(publish)'),
     ('his paper,', '他的论文，')]],
   [[('judging', '认为'), ('his evidence', '他的证据'), ('**unconvincing**.', '**缺乏说服力**(unconvincing)。')],
    '（judging his evidence unconvincing：现在分词短语作原因状语；\njudge＋宾语＋形容词：认为……）']]),
 (3,
  [[[('In June 1798', '1798年6月，'),
     ('he', '他'),
     ('**privately**', '**私人**(privately)'),
     ('**funded**', '**出资**(funded)出版了'),
     ('his book,', '他的著作'),
     ('the Inquiry,', '《探究》，')],
    '（the Inquiry：同位语，补充说明 his book，\n全名《关于牛痘的原因与效果的探究》）'],
   [[('with', '书中附上了'), ('**supplementary**', '**补充**(supplementary)'), ('cases.', '病例。')]]]),
 (3,
  [[[('The word **vaccine**', '表示**疫苗**(vaccine)的英文词'),
     ('**derives from**', '**源自**(derives from)'),
     ('the **Latin**', '**拉丁语**(Latin)的'),
     ('vacca,', 'vacca，'),
     ('cow.', '意思是牛。')],
    '（vacca, cow：cow 是 vacca 的同位语，说明词义）']]),
 (4,
  [[[('Jenner', '詹纳'),
     ('was not', '并不是'),
     ("the idea's", '这一想法的'),
     ('**originator**.', '**首创者**(originator)。')]]]),
 (4,
  [[[('His contribution', '他的贡献'),
     ('was', '是'),
     ('a test,', '一项试验，'),
     ('with results', '其结果'),
     ('**accessible** in print,', '在已出版的书籍中**可以获得**(accessible)，')],
    '（with results accessible in print：with 复合结构，\n结果印成书、人人可以查阅）'],
   [[('so', '以便'),
     ('other', '其他'),
     ('doctors', '医生'),
     ('could **replicate**', '能够**复制**(replicate)'),
     ('and **disseminate**', '并**传播**(disseminate)'),
     ('the **technique**.', '这项**技术**(technique)。')]]]),
 (4,
  [[[('By', '按'),
     ("today's", '今天的'),
     ('standards,', '标准，'),
     ('**experimentation** on a child', '拿孩子做**实验**(experimentation)'),
     ('without', '在没有取得'),
     ('**informed**', '**知情**(informed)'),
     ('**consent**', '**同意**(consent)的情况下，')],
    '（informed consent：知情同意，医学伦理术语）'],
   [[('would be', '属于'), ('**unethical**.', '**不道德**(unethical)行为。')]]]),
 (4,
  [[[('Jenner', '詹纳'), ('died on 26 January 1823,', '于1823年1月26日去世，')]],
   [[('with smallpox', '那时天花'), ('far from', '还远未被'), ('**eliminated**.', '**消除**(eliminated)。')],
    '（with smallpox far from eliminated：\nwith 复合结构作伴随状语；\nfar from…：远未……）']]),
 (5,
  [[[('In 1967', '1967年，'),
     ('the WHO', '世界卫生组织'),
     ('launched', '发起了'),
     ('an **intensified**,', '一场**强化**(intensified)、'),
     ('**concerted**', '**共同筹划的**(concerted)'),
     ('campaign', '运动，'),
     ('to **eradicate**', '要**根除**(eradicate)'),
     ('smallpox.', '天花。')]]]),
 (5,
  [[[('The last', '最后一例'),
     ('**naturally**', '**自然**(naturally)'),
     ('**occurring**', '**发生**(occurring)的'),
     ('case', '病例')],
    '（naturally occurring：自然发生的，\n区别于后来的实验室感染）'],
   [[('was **diagnosed** in Somalia on 26 October 1977.', '于1977年10月26日在索马里**确诊**(diagnosed)。')]]]),
 (5,
  [[[('On 8 May 1980', '1980年5月8日，'),
     ('the World Health Assembly', '世界卫生大会'),
     ('**formally**', '**正式**(formally)'),
     ('declared', '宣布'),
     ('the world', '全世界'),
     ('free of', '已摆脱'),
     ('smallpox,', '天花，')],
    '（declare A free of B：宣布 A 已摆脱 B）'],
   [[('the only human disease ever **wiped out**.', '天花也成为迄今唯一被**彻底消灭**(wiped out)的人类疾病。')],
    '（the only human disease ever wiped out：\n同位语，补充说明 smallpox；wipe out：彻底消灭）']]),
 (5,
  [[[('That **pronouncement**', '那一**宣告**(pronouncement)，'),
     ('came', '出现在'),
     ('almost 184 years after Phipps was **vaccinated**.', '菲普斯**接种疫苗**(vaccinated)之后的近184年。')],
    '（after Phipps was vaccinated：时间状语从句）\n'
    '（简述：▸背景：天花约致三成患者死亡；早期人痘术把天花疮中物质接种给健康人作预防，风险虽低于自然染病，仍可能致重病或死亡。▸先例：乡间传牛痘可防天花；农夫杰斯蒂1774年已用牛痘保护家人，詹纳并非首创。▸试验：詹纳1796年给男孩种牛痘，再让他接触天花而未发病；无知情同意的儿童试验按今天标准不合伦理。▸推广：皇家学会嫌证据不足拒稿后，詹纳自费公布试验和补充病例，使其他医生能够重复验证、传播技术。▸根除：世卫1967年强化行动，1977年出现最后自然病例；1980年世界卫生大会宣布根除天花，迄今唯一被根除的人类疾病。）']])]

out = {'no': '58',
 'allow_clash': ['exposed to', 'matter'],
 'title_en': 'From a Scratch to a World Without Smallpox',
 'title_zh': '从一道划痕到天花绝迹',
 'title_fx': {'hl': ['Scratch', 'Smallpox'], 'ghost': []},
 'sentences': [],
 '核对确认': {'非人声': {'15.81–15.84s': {'配音指纹': 'f770d56e54c4',
                                   '依据': '2026-11-07 逐 2.5 ms 实测（dossier_58，配音指纹 f770d56e54c4）：S2 w '
                                         '1.705–1.735：deliberately 的 /d/ 浊音前导，-50→-31 dB 连续升高，低频占 0～-1 '
                                         'dB（浊音横杠），1.74 起 /d/ 除阻，中间无低谷，是词头的一部分',
                                   '词头': True,
                                   '实测': {'最响dB': -34.0, '重心Hz': 999, '周期': 0.45, '低频dB': -0.1}},
                  '47.35–47.37s': {'配音指纹': 'f770d56e54c4',
                                   '依据': '2026-11-07 逐 2.5 ms 实测（dossier_58，配音指纹 f770d56e54c4）：S5 w '
                                         '4.825–4.84：farmer, 停顿之后、employed 开口前，-45～-57 dB、低频占 0 dB（浊音），4.86 起 '
                                         '/ɛ/ 元音（-19 dB），连续无低谷，是元音的浊音起音',
                                   '词头': True,
                                   '实测': {'最响dB': -46.7, '重心Hz': 2692, '周期': 0.0, '低频dB': -0.3}},
                  '68.36–68.39s': {'配音指纹': 'f770d56e54c4',
                                   '依据': '2026-11-07 逐 2.5 ms 实测（dossier_58，配音指纹 f770d56e54c4）：S7 w '
                                         '3.71–3.73：exposed 的 /z/（3.66 重心 6–7 kHz）衰减后，/d/ 除阻 -42→-30 dB、重心 4–5 '
                                         'kHz，3.735 起直接接 the 的 /ð/，连续无低谷，是 /d/ 除阻',
                                   '词尾': True,
                                   '实测': {'最响dB': -34.4, '重心Hz': 5124, '周期': 0.38, '低频dB': -1.6}},
                  '69.36–69.38s': {'配音指纹': 'f770d56e54c4',
                                   '依据': '2026-11-07 逐 2.5 ms 实测（dossier_58，配音指纹 f770d56e54c4）：S7 w '
                                         '4.705–4.72：smallpox 的 /p/ 闭塞段（4.68–4.725，-50～-67 dB），低频占 0～-2 dB '
                                         '是闭塞里的残余浊音，4.73 起 /p/ 除阻（-19 dB），是词内的一部分',
                                   '词尾': True,
                                   '实测': {'最响dB': -51.7, '重心Hz': 2080, '周期': 0.0, '低频dB': -0.5}},
                  '80.31–80.33s': {'配音指纹': 'f770d56e54c4',
                                   '依据': '2026-11-07 逐 2.5 ms 实测（dossier_58，配音指纹 f770d56e54c4）：S8 w '
                                         '7.54–7.625：unconvincing. 句末 /ŋ/（7.49–7.535 -19～-34 dB 鼻音）连续衰减到 -54 '
                                         'dB，低频占 -2～-13 dB、重心 1–3 kHz，无低谷，是词尾鼻音的衰减尾',
                                   '词尾': True,
                                   '实测': {'最响dB': -35.2, '重心Hz': 1370, '周期': 0.33, '低频dB': -1.6}},
                  '85.55–85.56s': {'配音指纹': 'f770d56e54c4',
                                   '依据': '2026-11-07 逐 2.5 ms 实测（dossier_58，配音指纹 f770d56e54c4）：S9 w '
                                         '3.80–3.815：book, 停顿之后 -46→-29 dB 连续升高，低频占 -1～-2 dB、周期 '
                                         '0.4–0.5（浊音），一直升到 3.855 -14 dB 的 the，无低谷，是 /ð/ 的起音',
                                   '词头': True,
                                   '实测': {'最响dB': -31.3, '重心Hz': 844, '周期': 0.0, '低频dB': -2.4}},
                  '86.77–86.78s': {'配音指纹': 'f770d56e54c4',
                                   '依据': '2026-11-07 逐 2.5 ms 实测（dossier_58，配音指纹 f770d56e54c4）：S9 w '
                                         '4.835–4.855：Inquiry, 停顿之后、with 开口前，-48～-62 dB、低频占 0～-2 dB（浊音），4.875 '
                                         '起 /w/（-35→-11 dB），连续无低谷，是 /w/ 的浊音起音',
                                   '词头': True,
                                   '实测': {'最响dB': -48.0, '重心Hz': 2379, '周期': 0.23, '低频dB': -0.2}},
                  '99.19–99.25s': {'配音指纹': 'f770d56e54c4',
                                   '依据': '2026-11-07 逐 2.5 ms 实测（dossier_58，配音指纹 f770d56e54c4）：S12 w '
                                         '1.875–1.93：test, 的 /s/（1.825–1.85 重心 5 kHz）后闭塞 1.855–1.87（-56～-66 '
                                         'dB），1.875 /t/ 除阻 -37 dB、重心 3–4 kHz，送气衰减到 1.93，是 /t/ 的除阻送气',
                                   '词尾': True,
                                   '实测': {'最响dB': -33.0, '重心Hz': 3361, '周期': 0.13, '低频dB': -13.4}},
                  '105.55–105.61s': {'配音指纹': 'f770d56e54c4',
                                     '依据': '2026-11-07 逐 2.5 ms 实测（dossier_58，配音指纹 f770d56e54c4）：S12 w '
                                           '8.145–8.215：technique. 的 /k/ 闭塞 8.105–8.14（-64～-69 dB），8.15 除阻 -28 '
                                           'dB、重心 4.4 kHz，送气衰减到 8.215 -63 dB，是句末 /k/ 的除阻送气',
                                     '词尾': True,
                                     '实测': {'最响dB': -31.5, '重心Hz': 4219, '周期': 0.21, '低频dB': -16.3}},
                  '132.97–133.00s': {'配音指纹': 'f770d56e54c4',
                                     '依据': '2026-11-07 逐 2.5 ms 实测（dossier_58，配音指纹 f770d56e54c4）：S16 w '
                                           '2.325–2.355：was 开口前，-48～-57 dB、低频占 0～-1 dB（浊音），2.377 起 /w/（-35→-11 '
                                           'dB），连续无低谷，是 /w/ 的浊音起音（前面 case 后的吸气声已切）',
                                     '词头': True,
                                     '实测': {'最响dB': -48.3, '重心Hz': 2405, '周期': 0.27, '低频dB': -0.2}},
                  '138.09–138.17s': {'配音指纹': 'f770d56e54c4',
                                     '依据': '2026-11-07 逐 2.5 ms 实测（dossier_58，配音指纹 f770d56e54c4）：S16 w '
                                           '7.69–7.77：seventy-seven. 句末 /n/（7.64–7.69 -26～-35 dB）连续衰减到 7.78 '
                                           '-57 dB，低频占 -2～-7 dB（浊音），无低谷，是词尾鼻音的衰减尾',
                                     '词尾': True,
                                     '实测': {'最响dB': -35.8, '重心Hz': 1559, '周期': 0.3, '低频dB': -3.1}},
                  '154.97–155.09s': {'配音指纹': 'f770d56e54c4',
                                     '依据': '2026-11-07 逐 2.5 ms 实测（dossier_58，配音指纹 f770d56e54c4）：S18 w '
                                           '5.39–5.505：vaccinated. 句末 /d/：5.395–5.47 -36～-51 dB、低频占 -1～-3 dB 是 '
                                           '/d/ 闭塞浊音，5.48 小除阻 -33 dB，衰减到 5.51 -68 dB，无低谷，是词尾 /d/',
                                     '词尾': True,
                                     '实测': {'最响dB': -35.4, '重心Hz': 1838, '周期': 0.2, '低频dB': -1.2}},
                  '155.00–155.05s': {'配音指纹': 'f770d56e54c4',
                                     '依据': '2026-11-07 逐 2.5 ms 实测（dossier_58，配音指纹 f770d56e54c4）：S18 w '
                                           '5.42–5.47：同上一段 vaccinated. 句末 /d/ 闭塞浊音（-37～-50 dB、低频占 0～-2 dB），是词尾',
                                     '词尾': True,
                                     '实测': {'最响dB': -35.4, '重心Hz': 1127, '周期': 0.36, '低频dB': -0.8}},
                  '80.25–80.34s': {'配音指纹': 'f770d56e54c4',
                                   '依据': '2026-11-07 逐 2.5 ms 实测（dossier_58，配音指纹 f770d56e54c4）：S8 w '
                                         '7.54–7.625：unconvincing. 句末 /ŋ/（7.49–7.535 -19～-34 dB 鼻音）连续衰减到 -54 '
                                         'dB，低频占 -2～-13 dB、重心 1–3 kHz，无低谷，是词尾鼻音的衰减尾',
                                   '词尾': True,
                                   '实测': {'最响dB': -35.2, '重心Hz': 2904, '周期': 0.27, '低频dB': -4.3}},
                  '80.35–80.37s': {'配音指纹': 'f770d56e54c4',
                                   '依据': '2026-11-07 逐 2.5 ms 实测（dossier_58，配音指纹 f770d56e54c4）：S8 w '
                                         '7.635–7.655：unconvincing. 句末 /ŋ/ 衰减尾（-42～-54 dB、低频占 -1～-3 dB 浊音），接在 '
                                         '7.54–7.62 那段后面，7.66 起淡出到 -70 dB 以下，是词尾鼻音的衰减尾',
                                   '词尾': True}},
          '删除段': {'S12 raw 4.3900-4.7000': '2026-10-15 删除段对应 非人声区间 [[4.4, 4.68]]（w 秒）：自动切点.py '
                                           '用实际声音按规则判定是吸气声/噗声（听得见的部分七成以上重心 1.8–3.8 kHz、低频 < -10 dB、周期 < '
                                           "0.35，没有连续 20 ms >4 kHz 的擦音），贴词一侧切在紧挨词 40 ms 内最安静处的过零点；复核报 ['lost'] "
                                           '是删掉的呼吸声本身偏响（-34～-47 dB），不是词',
                  'S9 raw 3.8500-3.8950': {'类型': '紧贴词尾的非人声',
                                           '配音指纹': 'f770d56e54c4',
                                           '依据': '2026-11-07 逐 2.5 ms 实测（dossier_58，配音指纹 f770d56e54c4）：S9 '
                                                 'book, 停顿处（停顿处除阻 k）删掉的 45 ms 是 /k/ 闭塞里的静音，删掉部分最响 -55.2 '
                                                 'dB（听不见），前侧最低 -55.0 dB 正卡在 -55 门槛上，没有切到词的声音'},
                  'S1 raw 5.2650-5.6011': {'类型': '紧贴词头的非人声',
                                           '配音指纹': 'f770d56e54c4',
                                           '依据': "2026-10-15 删除段对应 非人声区间 [[5.255, 5.591125, '紧贴词头']]（w "
                                                 '秒）：自动切点.py 用实际声音按规则判定是吸气声/噗声（听得见的部分七成以上重心 1.8–3.8 kHz、低频 < '
                                                 '-10 dB、周期 < 0.35，没有连续 20 ms >4 kHz 的擦音），贴词一侧切在紧挨词 40 ms '
                                                 "内最安静处的过零点；复核报 ['lost', 'post'] 是删掉的呼吸声本身偏响（-34～-47 dB），不是词"},
                  'S2 raw 5.2300-5.6307': {'类型': '紧贴词头的非人声',
                                           '配音指纹': 'f770d56e54c4',
                                           '依据': "2026-10-15 删除段对应 非人声区间 [[5.225, 5.610708, '紧贴词头']]（w "
                                                 '秒）：自动切点.py 用实际声音按规则判定是吸气声/噗声（听得见的部分七成以上重心 1.8–3.8 kHz、低频 < '
                                                 '-10 dB、周期 < 0.35，没有连续 20 ms >4 kHz 的擦音），贴词一侧切在紧挨词 40 ms '
                                                 "内最安静处的过零点；复核报 ['lost', 'post'] 是删掉的呼吸声本身偏响（-34～-47 dB），不是词"},
                  'S2 raw 8.5250-8.8662': {'类型': '紧贴词头的非人声',
                                           '配音指纹': 'f770d56e54c4',
                                           '依据': "2026-10-15 删除段对应 非人声区间 [[8.55, 8.846208, '紧贴词头']]（w "
                                                 '秒）：自动切点.py 用实际声音按规则判定是吸气声/噗声（听得见的部分七成以上重心 1.8–3.8 kHz、低频 < '
                                                 '-10 dB、周期 < 0.35，没有连续 20 ms >4 kHz 的擦音），贴词一侧切在紧挨词 40 ms '
                                                 "内最安静处的过零点；复核报 ['lost', 'post'] 是删掉的呼吸声本身偏响（-34～-47 dB），不是词"},
                  'S3 raw 3.5100-3.9161': {'类型': '紧贴词头的非人声',
                                           '配音指纹': 'f770d56e54c4',
                                           '依据': "2026-10-15 删除段对应 非人声区间 [[3.685125, 3.896167, '紧贴词头']]（w "
                                                 '秒）：自动切点.py 用实际声音按规则判定是吸气声/噗声（听得见的部分七成以上重心 1.8–3.8 kHz、低频 < '
                                                 '-10 dB、周期 < 0.35，没有连续 20 ms >4 kHz 的擦音），贴词一侧切在紧挨词 40 ms '
                                                 "内最安静处的过零点；复核报 ['post'] 是删掉的呼吸声本身偏响（-34～-47 dB），不是词"},
                  'S5 raw 4.5550-4.8339': {'类型': '紧贴词头的非人声',
                                           '配音指纹': 'f770d56e54c4',
                                           '依据': "2026-10-15 删除段对应 非人声区间 [[4.55, 4.823917, '紧贴词头']]（w "
                                                 '秒）：自动切点.py 用实际声音按规则判定是吸气声/噗声（听得见的部分七成以上重心 1.8–3.8 kHz、低频 < '
                                                 '-10 dB、周期 < 0.35，没有连续 20 ms >4 kHz 的擦音），贴词一侧切在紧挨词 40 ms '
                                                 "内最安静处的过零点；复核报 ['post'] 是删掉的呼吸声本身偏响（-34～-47 dB），不是词"},
                  'S8 raw 1.7015-1.9000': {'类型': '紧贴词尾的非人声',
                                           '配音指纹': 'f770d56e54c4',
                                           '依据': "2026-10-15 删除段对应 非人声区间 [[1.6815, 1.85, '紧贴词尾']]（w 秒）：自动切点.py "
                                                 '用实际声音按规则判定是吸气声/噗声（听得见的部分七成以上重心 1.8–3.8 kHz、低频 < -10 dB、周期 < '
                                                 '0.35，没有连续 20 ms >4 kHz 的擦音），贴词一侧切在紧挨词 40 ms 内最安静处的过零点；复核报 '
                                                 "['pre'] 是删掉的呼吸声本身偏响（-34～-47 dB），不是词"},
                  'S16 raw 2.1100-2.3235': {'类型': '紧贴两头的非人声',
                                            '配音指纹': 'f770d56e54c4',
                                            '依据': "2026-10-15 删除段对应 非人声区间 [[2.110042, 2.3235, '紧贴两头']]（w "
                                                  '秒）：自动切点.py 用实际声音按规则判定是吸气声/噗声（听得见的部分七成以上重心 1.8–3.8 kHz、低频 < '
                                                  '-10 dB、周期 < 0.35，没有连续 20 ms >4 kHz 的擦音），贴词一侧切在紧挨词 40 ms '
                                                  "内最安静处的过零点；复核报 ['pre'] 是删掉的呼吸声本身偏响（-34～-47 dB），不是词"},
                  'S18 raw 3.7525-3.8553': {'类型': '紧贴两头的非人声',
                                            '配音指纹': 'f770d56e54c4',
                                            '依据': "2026-10-15 删除段对应 非人声区间 [[3.7325, 3.835292, '紧贴两头']]（w "
                                                  '秒）：自动切点.py 用实际声音按规则判定是吸气声/噗声（听得见的部分七成以上重心 1.8–3.8 kHz、低频 < '
                                                  '-10 dB、周期 < 0.35，没有连续 20 ms >4 kHz 的擦音），贴词一侧切在紧挨词 40 ms '
                                                  "内最安静处的过零点；复核报 ['lost', 'post', 'pre'] 是删掉的呼吸声本身偏响（-34～-47 "
                                                  'dB），不是词'}},
          '机器复听': {'S10': {'配音指纹': 'f770d56e54c4',
                           '依据': '2026-11-07 逐 2.5 ms 实测（dossier_58，配音指纹 f770d56e54c4）：vacca 配音注音 vˈækə（与 CMU '
                                 '词典 V AE1 K AH0 一致，拉丁词英语读法）；两路识别器拼成 vaca 是生僻拉丁词的拼写猜测，不是读错'},
                   'S2': {'配音指纹': 'f770d56e54c4',
                          '依据': '2026-11-07 逐 2.5 ms 实测（dossier_58，配音指纹 f770d56e54c4）：sores 只有 parakeet 一路听成 '
                                'source，small.en 听对；配音 sˈɔːɹz，w 4.41–4.47 词尾 /z/ 周期 0.15–0.23、低频占 -13～-16 '
                                'dB，浊化偏弱（接 in 前），前面 ɔːɹ 长约 170 ms，交用户听'}},
          '合组': {'S2 implanting matter from its sores in the healthy': '对齐不了：implant A in B 中文“把 A 植入 B”，from '
                                                                       'its sores '
                                                                       '是后置定语，中文“天花脓疮中的物质”定语必须提前，植入放到宾语后',
                 'S2 was practised in China by the 16th century': '对齐不了：by the 16th century '
                                                                  '是时间状语，中文“到16世纪，中国已在施行这种方法”时间必须提前，被动 was '
                                                                  'practised in China 化成主动“中国已在施行”',
                 'S2 and reached England in 1721': '对齐不了：in 1721 是时间状语，中文“1721年又传入英国”时间必须提前',
                 'S3 if less frequently than natural smallpox': '对齐不了：if less frequently than… '
                                                                '是比较结构，中文“虽然不像自然感染的天花那样频繁”比较对象必须提前，频繁放最后',
                 'S4 a mild ailment of livestock': '对齐不了：a mild ailment of livestock 是 of '
                                                   '结构，中文“牲畜的轻微病症”语序必须倒过来',
                 "S6 inserted fluid from a milkmaid's cowpox sore": "对齐不了：from a milkmaid's cowpox sore "
                                                                    '是后置定语，修饰 '
                                                                    'fluid，中文沿用文章定稿“从一名挤奶女工的牛痘疮中取出液体，注入”，来源必须提前',
                 'S6 into a scratch on eight-year-old James Phipps': '对齐不了：on eight-year-old James Phipps '
                                                                     '是后置定语，修饰 '
                                                                     'scratch，中文“8岁的詹姆斯·菲普斯身上的一道划痕”定语必须提前',
                 'S7 exposed the boy to smallpox': '对齐不了：expose A to B 中文“让 A 接触 B”，to 化成“接触”，拆开不通',
                 'S12 with results accessible in print': '对齐不了：with 复合结构 with results accessible in '
                                                         'print，中文沿用文章定稿“并把结果付印，供人查阅”，in print 化成“付印”提前',
                 'S14 died on 26 January 1823': '对齐不了：on 26 January 1823 是时间状语，中文“于1823年1月26日去世”时间必须放到动词前',
                 'S16 was diagnosed in Somalia on 26 October 1977': '对齐不了：in Somalia、on 26 October 1977 '
                                                                    '是地点、时间状语，中文“于1977年10月26日在索马里确诊”必须放到动词前',
                 'S17 the only human disease ever wiped out': '对齐不了：ever wiped out 是后置定语，修饰 '
                                                              'disease，中文“迄今唯一被消灭的人类疾病”定语必须提前',
                 'S18 came almost 184 years after Phipps was vaccinated': '对齐不了：after Phipps was vaccinated '
                                                                          '是时间状语从句，中文“距菲普斯接种已近184年”，after '
                                                                          '化成“距”放最前，came 化成“已”',
                 'S3 frequently than natural smallpox': '对齐不了：less frequently than… '
                                                        '比较结构，中文“尽管不如自然天花那样频繁”，比较对象“自然天花那样”必须放在“频繁”前面（用户 '
                                                        '2026-11-07 给的译文）',
                 'S18 almost 184 years after Phipps was vaccinated': '对齐不了：after '
                                                                     '引导的时间状语，中文“菲普斯接种疫苗之后的近184年”，时间“之后”必须放在“近184年”前面（用户 '
                                                                     '2026-11-07 给的译文）'},
          '对齐': {'S18-1 almost 184 years after Phipps': 'after Phipps was vaccinated '
                                                        '是时间状语从句，中文“菲普斯接种疫苗之后的近184年”（用户 2026-11-07 '
                                                        '给的译文），“之后”必须在“近184年”前面，语序倒过来',
                 'S2-1 implanting matter from its sor': 'implant A in B，from its sores '
                                                        '是后置定语，中文“把天花脓疮中的物质植入健康人体内”语序必须倒过来',
                 'S2-2 was practised in China by the ': 'by the 16th century 时间状语，中文时间必须提前',
                 'S2-2 and reached England in 1721.': 'in 1721 时间状语，中文时间必须提前',
                 'S3-2 if less frequently than natura': '比较结构，中文比较对象必须提前',
                 'S4-2 a mild ailment of livestock,': 'of 结构，中文“牲畜的轻微病症”语序必须倒过来',
                 'S6-2 inserted fluid from a milkmaid': "后置定语 from a milkmaid's cowpox sore，中文来源必须提前",
                 'S6-2 into a scratch on eight-year-o': '后置定语 on eight-year-old James Phipps，中文定语必须提前',
                 'S7-1 exposed the boy to smallpox;': 'expose A to B 中文“让 A 接触 B”',
                 'S12-1 with results accessible in pri': 'with 复合结构，中文沿用文章定稿“并把结果付印，供人查阅”',
                 'S14-1 died on 26 January 1823,': '时间状语，中文时间必须放到动词前',
                 'S16-2 was diagnosed in Somalia on 26': '地点、时间状语，中文必须放到动词前',
                 'S17-2 the only human disease ever wi': '后置定语 ever wiped out，中文定语必须提前',
                 'S18-1 came almost 184 years after Ph': '时间状语从句，中文“距菲普斯接种已近184年”语序必须倒过来',
                 'S18-1 almost 184 years after Phipps ': 'after Phipps was vaccinated '
                                                         '是时间状语从句，中文“菲普斯接种疫苗之后的近184年”（用户 2026-11-07 '
                                                         '给的译文），“之后”必须在“近184年”前面，语序倒过来'},
          '短语': {'S2 implanting … from': '不是搭配：from 属于 matter from its sores（后置定语），implant 单独就是“植入”',
                 'S2 implanting … in': '不是搭配：implant 本身就是“植入”，in 只引出植入的位置（健康人体内），中文“植入……体内”已译出',
                 'S4 ailment … of': '不是搭配：of livestock 是后置定语，说明是谁的病症，ailment 单独就是“病症”',
                 'S5 employed … to': '不是搭配：to protect 是目的不定式，employ 单独就是“使用”',
                 'S6 inserted … from': "不是搭配：from 属于 fluid from a milkmaid's cowpox sore（后置定语），insert 单独就是“注入”",
                 'S6 inserted … into': '不是搭配：insert 本身就是“注入”，into 只引出注入的位置（划痕），中文“注入……划痕”已译出',
                 'S6 inserted … on': '不是搭配：on 属于 a scratch on eight-year-old James Phipps，和 inserted 无关',
                 'S6 scratch … on': '不是搭配：on eight-year-old James Phipps 是后置定语，说明划痕在谁身上，scratch 单独就是“划痕”',
                 'S9 funded … with': '不是搭配：with supplementary cases 说明书里附带的内容，和 funded 无关',
                 'S12 accessible … in': '不是搭配：in print 是方式（以印成书的形式），accessible 单独就是“可查阅的”',
                 'S16 occurring … on': '不是搭配：on 26 October 1977 是 diagnosed 的时间状语，和 occurring 无关',
                 'S16 diagnosed … on': '不是搭配：on 26 October 1977 是时间状语，diagnose 单独就是“确诊”'},
          '中文意思': {'S9 funded': '不是被隔开的两处：本文“私人出资出版了他的著作”，funded 只对应“出资”，宾语 his book 接在“出版了”后，没有“为……”',
                   'S18 vaccinated': '不是被隔开的两处：本文“距菲普斯接种”，被动 was vaccinated 只对应“接种”，没有“给……”'},
          '方向': {'S8-1 declined→不予发表': 'decline 本文是“拒绝，不予”，中文“不予发表”，不是方向（下降）义',
                 'S8-1 declined→不予': 'decline 本文是“拒绝，不予”，中文“不予发表”，不是方向（下降）义',
                 'S3-2 less→虽然不像自然感染的天花那': 'less frequently than… 是比较结构，中文“不像……那样频繁”，less 化成“不像……那样”，不是方向词',
                 'S8-1 declined→拒绝': 'decline 本文是“拒绝”，中文“拒绝去发表”，不是方向（下降）义',
                 'S18-1 after→距菲普斯接种已近184年': 'after 化成“距……已近”，中文“距菲普斯接种已近184年”就是“在那之后近184年”，方向一致',
                 'S3-2 less→尽管不如': 'less frequently than… 是比较结构，less 化成“不如”，中文“尽管不如自然天花那样频繁”，方向一致（较少）'},
          '同词异译': {'immune to：免疫/对': '不是两种译法：S4 be immune to 的意思“对……免疫”被“天花”隔开，“对”和“免疫”是同一个意思的两部分（T23）',
                   'exposed to：接触/让': '不是两种译法：S7 expose A to B 的意思“让……接触”被“这个男孩”隔开，“让”和“接触”是同一个意思的两部分（T23）'},
          '数字': {'S1-2 300': '300 million 中文写作“3亿”，数值相同（300百万 = 3亿）；英文读 three hundred million'},
          '数字写法': {'S1-2 three': 'three in ten 中文写作“三成”（十分之三），数值相同',
                   'S6-2 eight': 'eight-year-old 中文按文章定稿写作“8岁”，数值相同（eight = 8）'},
          '中文重复': {'疾病': '用户 2026-11-07 原话（问 S1 affliction 与 S3 sickness 都译“疾病”怎么处理）：“疾病都保留”；两处都指天花这类病，S1 '
                         '是天花本身，S3 是接种可能引起的病'}},
 '结尾解说': '简述',
 '高亮按实际开口': True,
 '高亮开口门槛': 40,
 '术语': {'Benjamin Jesty': '本杰明·杰斯蒂',
        'Dorset': '多塞特郡',
        'Edward Jenner': '爱德华·詹纳',
        'Jenner': '詹纳',
        'James Phipps': '詹姆斯·菲普斯',
        'Phipps': '菲普斯',
        'Royal Society': '皇家学会',
        'Inquiry': '《探究》',
        'WHO': '世界卫生组织',
        'Somalia': '索马里',
        'World Health Assembly': '世界卫生大会',
        'China': '中国',
        'England': '英国',
        'Latin': '拉丁语'},
 '非人声区间': {'S1': [[5.255, 5.591125, '紧贴词头']],
           'S2': [[5.225, 5.610708, '紧贴词头'], [8.55, 8.846208, '紧贴词头']],
           'S3': [[3.685125, 3.896167, '紧贴词头']],
           'S5': [[4.55, 4.823917, '紧贴词头']],
           'S6': [[5.615, 5.895]],
           'S7': [[5.36, 5.587833, '紧贴词头']],
           'S8': [[1.6815, 1.85, '紧贴词尾']],
           'S9': [[1.885, 2.065]],
           'S11': [[2.355208, 2.4375, '紧贴词尾']],
           'S12': [[4.4, 4.68]],
           'S14': [[3.93, 4.166792, '紧贴词头']],
           'S15': [[1.565, 1.8]],
           'S16': [[2.110042, 2.3235, '紧贴两头'], [4.52, 4.758708, '紧贴词头']],
           'S17': [[2.015, 2.275]],
           'S18': [[3.7325, 3.835292, '紧贴两头']]},
 '词尾除阻': {},
 '除阻加强': {'S17': {'句末': [9.53, 9.565, 6.0]}, 'S4': {'2': [5.13, 5.18, 5.5]}},
 '停顿处除阻': {'S9': {'1': [3.745, 3.75, 'k']}},
 '区间声音指纹': {'S1': '7cbd31ec04da',
            'S2': 'b4feb574164e',
            'S3': 'b8a1ca6062fd',
            'S4': 'a035ae63d913',
            'S5': '8f24deffaa87',
            'S6': '6b3820918e56',
            'S7': '25e57da0b7c0',
            'S8': '89183a669101',
            'S9': 'eb2729f53a92',
            'S11': '518d777463a9',
            'S12': 'c714969a7120',
            'S14': 'f1fd7cb97f5e',
            'S15': 'a6662cbdf714',
            'S16': '26b4b478396f',
            'S17': 'cb0d61e689a4',
            'S18': '6331d449a5f9'},
 '分段增益dB': {'S9': {'1': -2.0}},
 '句子增益dB': {'S10': 0.5},
 '换行变更记录': [{'日期': '2026-11-07',
             'S1': '用户 2026-11-07：“尽量对齐能懂吗？就是说上面是英文下面它的英文，它下面它的中文意思尽量能够跟这个英文对齐。”',
             'S3': '用户 2026-11-07：“尽量对齐能懂吗？就是说上面是英文下面它的英文，它下面它的中文意思尽量能够跟这个英文对齐。”',
             'S5': '用户 2026-11-07：“尽量对齐能懂吗？就是说上面是英文下面它的英文，它下面它的中文意思尽量能够跟这个英文对齐。”',
             'S9': '用户 2026-11-07：“尽量对齐能懂吗？就是说上面是英文下面它的英文，它下面它的中文意思尽量能够跟这个英文对齐。”',
             'S12': '用户 2026-11-07：“尽量对齐能懂吗？就是说上面是英文下面它的英文，它下面它的中文意思尽量能够跟这个英文对齐。”',
             'S15': '用户 2026-11-07：“尽量对齐能懂吗？就是说上面是英文下面它的英文，它下面它的中文意思尽量能够跟这个英文对齐。”',
             'S4': '用户 2026-11-07：“中文这个中文翻译的正下方加上：一般指牛的牛痘，轻微病症。”',
             'S18': '用户 2026-11-07：“那一宣告，出现在菲普斯接种疫苗之后的近184年。”；“4K 定稿”'}]}

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 核对 import 生成并核对
生成并核对(S, out)
