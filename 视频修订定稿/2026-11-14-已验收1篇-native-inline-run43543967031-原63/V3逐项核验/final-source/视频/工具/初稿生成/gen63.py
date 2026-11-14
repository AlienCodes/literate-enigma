#!/usr/bin/env python3
# Pure data frozen from the current approved JSON; shared helper/checkers unchanged.
import os
import sys

S = [(1,
  [[[('On 10 February 2009,', '2009年2月10日，'), ('nearly 790 kilometres above Siberia,', '在西伯利亚上空近790公里处，')]],
   [[('two satellites', '两颗卫星'),
     ('**slammed**', '**猛撞**(slammed)'),
     ('together', '在一起，'),
     ('at about 42,000 kilometres an hour.', '时速约42,000公里。')],
    '（at about 42,000 kilometres an hour：表示速度；\nan hour：每小时）']]),
 (1,
  [[[('Iridium 33', '铱星33号'),
     ('**belonged to**', '**属于**(belonged to)'),
     ('an American', '美国的一个'),
     ('satellite-phone', '卫星电话'),
     ('**constellation**;', '**星座**(constellation)；')],
    '（constellation：卫星星座，\n指由多颗协同工作的卫星组成的网络）'],
   [[('Kosmos 2251,', '宇宙2251号'),
     ('a Russian', '是一颗俄罗斯'),
     ('military', '军用'),
     ('satellite,', '卫星，'),
     ('had been **derelict** since about 1995.', '约自1995年起便已**废弃**(derelict)。')],
    '（a Russian military satellite：同位语，补充说明 Kosmos 2251；\nhad been…since：过去完成时，表示一直处于废弃状态）']]),
 (1,
  [[[('Both', '两星双双'), ('**shattered**', '**粉碎**(shattered)，')]],
   [[('in the first', '这是首次有'),
     ('**accidental**', '**意外**(accidental)'),
     ('**collision**', '**相撞**(collision)'),
     ('between', '发生在'),
     ('two', '两颗'),
     ('intact', '完整'),
     ('satellites.', '卫星之间。')],
    '（between two intact satellites：后置定语，\n修饰 collision；\nintact：完好无损的）']]),
 (2, [[[('Neither craft', '两个飞行器都没有'), ('**swerved**.', '**紧急转向避让**(swerved)。')], '（neither：两者都不）']]),
 (2,
  [[[('The Russian', '那个俄罗斯的（卫星）'),
     ('**hulk**,', '**残骸**(hulk)，'),
     ('lacking', '由于缺乏'),
     ('**propulsion**,', '**推进力**(propulsion)，'),
     ('could not.', '无法转向。')],
    '（hulk：本文指失效卫星的残骸；\nlacking propulsion：现在分词短语作原因状语；\ncould not 后省略了 swerve）']]),
 (2,
  [[[('A public', '一项公开的'),
     ('collision-warning', '碰撞预警'),
     ('service', '服务'),
     ('had forecast', '曾预报，'),
     ('a **narrow miss**', '两星将**惊险擦过**(narrow miss)，'),
     ('of about 584 metres,', '相距约584米，')],
    '（a narrow miss：惊险擦过，险些相撞；\nof about 584 metres：后置定语，修饰 miss）'],
   [[('yet', '但'),
     ('the predicted', '预测中的这次'),
     ('**encounter**', '**交会**(encounter)'),
     ('was not among', '并未排进'),
     ("the week's", '当周'),
     ('closest;', '距离最近的几次之列；')],
    "（the week's closest：当周预测中距离最近的几次，\nclosest 后省略了 encounters）"],
   [[('such warnings were', '这类预警既'),
     ('**frequent**', '**频繁**(frequent)'),
     ('and', '又'),
     ('**imprecise**.', '**不精确**(imprecise)。')]]]),
 (2,
  [[[("One owner's", '一方'),
     ('**discarded**', '**弃置的**(discarded)'),
     ('**relic**', '**遗物**(relic)，'),
     ('**demolished**', '**意外毁坏了**(demolished)'),
     ("another's", '另一方'),
     ('working', '仍在工作的'),
     ('**asset**.', '**资产**(asset)。')],
    "（another's：another owner's，省略了 owner）"]]),
 (3,
  [[[('The', '这些'),
     ('**wreckage**,', '**残骸**(wreckage)'),
     ('however,', '却'),
     ('**endangered**', '**危及了**(endangered)'),
     ('everyone', '所有'),
     ('else.', '其他人。')],
    '（however：插入语，表示转折）']]),
 (3,
  [[[('The **impact**', '**撞击**(impact)'),
     ('**flung out**', '**抛出了**(flung out)'),
     ('more than 2,000', '2,000多块'),
     ('**catalogued**', '**已编目的**(catalogued)'),
     ('fragments', '碎片，')],
    '（fling out：猛抛出，flung 是 fling 的过去式）'],
   [[('and', '另有'),
     ('**a multitude of**', '**大量**(a multitude of)'),
     ('others', '碎片'),
     ('too', '太'),
     ('small', '小，'),
     ('to **pinpoint**.', '无法**精确定位**(pinpoint)。')],
    '（a multitude of others：大量其他碎片，others 指 fragments；\ntoo…to…：太……而不能……）']]),
 (3,
  [[[('At that height', '在那个高度，'),
     ('**air drag**', '**空气阻力**(air drag)'),
     ('is **feeble**,', '**微弱**(feeble)，')]],
   [[('so', '因此'), ('many', '许多碎片'), ('would **linger**', '会在轨道上**滞留**(linger)'), ('for decades.', '数十年。')],
    '（many：many fragments，省略了 fragments）']]),
 (3,
  [[[('In January 2012,', '2012年1月，'),
     ('the International', '国际'),
     ('**Space Station**', '**空间站**(Space Station)'),
     ('**fired**', '**点火了**(fired)'),
     ('its', '它的'),
     ('**thrusters**', '**推进器**(thrusters)，')]],
   [[('to', '以'),
     ('**dodge**', '**躲开/避开**(dodge)'),
     ('an Iridium 33', '一块铱星33号的'),
     ('**remnant**.', '**残片**(remnant)。')],
    '（to dodge…：不定式作目的状语）']]),
 (4,
  [[[('In June 1978,', '1978年6月，'),
     ('two NASA scientists', '两位美国国家航空航天局（NASA）的科学家'),
     ('**envisaged**', '**设想了**(envisaged)'),
     ('a', '一种'),
     ('**vicious spiral**,', '**恶性循环**(vicious spiral)，')],
    '（a vicious spiral：恶性循环）'],
   [[('later', '后来'), ('named', '被称为'), ('the Kessler', '凯斯勒'), ('**syndrome**:', '**综合征**(syndrome)：')],
    '（later named…：过去分词短语作后置定语，修饰 spiral；\n冒号后面说明这一设想的内容）'],
   [[('each', '每次'), ('collision', '相撞'), ('would **scatter**', '都会**散布**(scatter)'), ('fragments,', '碎片，')]],
   [[('**raising the odds of**', '**提高了**(raising the odds of)'),
     ('**subsequent**', '**后续**(subsequent)'),
     ('crashes.', '相撞**的几率**(raising the odds of)。')],
    '（raising the odds of…：现在分词短语作结果状语，\n使……更有可能）']]),
 (4,
  [[[('The 2009 crash', '2009年的这次相撞'),
     ('**illustrated**', '**例证了**(illustrated)'),
     ('that **premise**', '这一**前提**(premise)，')]],
   [[('without', '却并未'),
     ('**triggering**', '**引发**(triggering)'),
     ('a **runaway**', '**失控的**(runaway)'),
     ('**chain reaction**.', '**连锁反应**(chain reaction)。')],
    '（without＋动名词：而没有……）\n（2009年那次卫星相撞事件，虽然验证了科学家之前的可怕猜想，\n但万幸的是，它并没有引发那种彻底失控的连环大爆炸。）']]),
 (4,
  [[[('By', '截至'),
     ('the end of 2024,', '2024年底，'),
     ('**surveillance** networks', '太空**监视**(surveillance)网络'),
     ('tracked', '跟踪了'),
     ('about 40,000 objects,', '约40,000个物体，')]],
   [[('only some 11,000 of them', '其中只有约11,000个'), ('**functional**.', '能**正常运行**(functional)。')],
    '（only some 11,000 of them functional：独立主格结构，\n补充说明 objects；some＋数字：大约）']]),
 (5,
  [[[('Such a cascade', '不过，这样的连锁效应'),
     ('would **unfold**', '会逐步**展开**(unfold)，'),
     ('over decades, though,', '历时几十年，')],
    '（though：放在句中，表示转折“不过”）'],
   [[('and is not', '而且并非'),
     ('**inevitable**;', '**不可避免**(inevitable)，'),
     ('the risk', '风险'),
     ('can be **mitigated**.', '也可以**加以缓解**(mitigated)。')],
    '（这就像高速公路上的连环追尾，虽然可怕，但它是个持续几十年的慢动作。\n既然不是瞬间毁灭，我们就有机会去清理垃圾、把风险摁住。）']]),
 (5,
  [[[('Operators', '运营方'),
     ('now', '如今会'),
     ('**routinely**', '**例行**(routinely)'),
     ('**manoeuvre**', '**操纵**(manoeuvre)'),
     ('satellites', '卫星'),
     ("**out of harm's way**.", "**避开危险**(out of harm's way)。")],
    "（manoeuvre A out of harm's way：操纵 A 避开危险）"]]),
 (5,
  [[[('In September 2022,', '2022年9月，'),
     ("{{=}}America's Federal Communications Commission, which licenses satellites,", '负责为卫星发放许可的美国联邦通信委员会')],
    '（which licenses satellites：非限制性定语从句，\n修饰 Commission）'],
   [[('**mandated**', '**强制要求**(mandated)，')]],
   [[('**disposal** of low-orbit craft within five years of **retirement**',
      '低轨航天器须在**退役**(retirement)后五年内**处置**(disposal)，'),
     ('**instead of**', '**而不是**(instead of)'),
     ('25.', '25年。')],
    '（disposal：本文指卫星退役后离轨销毁；\nwithin five years of…：……后五年内；\n25 后省略了 years）']]),
 (5,
  [[[('Years after the crash,', '相撞多年之后，'),
     ('spacecraft whose owners **had no part in** it',
      '那些所有者**与**(had no part in)此事**毫无瓜葛**(had no part in)的航天器，')],
    '（whose owners…：定语从句，修饰 spacecraft；\nhave no part in：与……无关；it 指 the crash）'],
   [[('kept', '仍不得不一再'),
     ('swerving', '转向，'),
     ('around its', '绕开那次相撞留下的'),
     ('**splinters**.', '**碎片**(splinters)。')],
    "（keep doing：一再做……；its 指 the crash's）\n"
    '（简述：▸相撞：2009年，两颗完整卫星首次意外相撞：失效的宇宙2251号撞上仍工作的铱星33号。\n'
    '▸预警：公开预警频繁且不准，预计两星会隔约584米擦过，并非当周最近交会；失效卫星也无法避让。\n'
    '▸碎片：碰撞留下两千多块被登记追踪的碎片；截至2024年底，全球跟踪约4万个在轨物体，只有约1.1万个正常运行。\n'
    '▸风险：高空空气阻力小，碎片能留上数十年，还可能撞出更多碎片；\n'
    '▹此次没有触发失控连锁反应，恶性循环并非必然。\n'
    '▸应对：运营方加强卫星避让；美国联邦通信委员会要求其监管的低轨卫星，\n'
    '▹退役后5年内离轨处置，缩短了原来的25年期限。）']])]

out = {'no': '63',
 'title_en': 'The Crowded Heavens',
 'title_zh': '拥挤的苍穹',
 'title_fx': {'hl': ['Crowded', 'Heavens'], 'ghost': []},
 'sentences': [],
 '核对确认': {'合组': {'S3 in the first accidental collision between two intact satellites': '对齐不了：between two '
                                                                                       'intact satellites '
                                                                                       '是后置定语，修饰 '
                                                                                       'collision，中文“两颗完整卫星之间的”必须提前；拆开会把“两颗完整卫星之间的首次”说成泛指的首次相撞，意思变了',
                 'S12 raising the odds of subsequent crashes': '对齐不了：raise the odds of A 中文“使 A '
                                                               '更有可能发生”，A（后续撞击）必须放到中间；两个重点词中文先后与英文相反',
                 'S1 nearly 790 kilometres above Siberia': '对齐不了：above Siberia 修饰 790 '
                                                           'kilometres，中文“在西伯利亚上空近790公里处”地点必须提前',
                 'S1 at about 42,000 kilometres an hour': '对齐不了：an hour（每小时）中文“时速”必须放到数字前，拆开不通',
                 'S2 had been derelict since about 1995': '对齐不了：since about 1995 '
                                                          '是时间状语，中文“约自1995年起便已废弃”时间必须放到动词前',
                 'S15 over decades, though': '对齐不了：though 是句中插入的转折词，与上一段转折，中文“不过”必须放在句首（已在 Such a cascade '
                                             '一组），这一组只剩“历时几十年”',
                 'S17 disposal of low-orbit craft within five years of retirement': '对齐不了：用户 11-08 '
                                                                                    '原话语序“低轨航天器须在退役后五年内处置”把“处置”放到最后，disposal '
                                                                                    '与 of low-orbit '
                                                                                    'craft、within…retirement '
                                                                                    '先后相反，只能整组',
                 'S17 within five years of retirement': '对齐不了：within five years of retirement '
                                                        '中文“在退役后五年内”，退役必须提前',
                 "S17 America's Federal Communications Commission, which licenses satellites": '对齐不了：which '
                                                                                               'licenses '
                                                                                               'satellites '
                                                                                               '是非限制性定语从句，中文“负责为卫星发放许可的美国联邦通信委员会”定语必须提前，机构名不能拆',
                 'S18 spacecraft whose owners had no part in it': '对齐不了：whose 引导的定语从句修饰 '
                                                                  'spacecraft，中文“那些主人与此事毫无瓜葛的航天器”定语必须提前',
                 'S18 Years after the crash': '对齐不了：Years after the crash 中文“相撞多年之后”，after 的宾语必须提前'},
          '中文重复': {'残骸': '用户 2026-11-08 原话把 S5 hulk 改成“残骸”（“那个俄罗斯的 (卫星) 残骸，由于缺乏推进力，无法转向。”），与 S8 wreckage '
                         '同中文，按用户原话保留'},
          '对齐': {'S1-1 nearly 790 kilometres above Si': 'above Siberia 修饰 790 '
                                                        'kilometres，中文“在西伯利亚上空近790公里处”地点必须提前',
                 'S1-2 at about 42,000 kilometres an ': 'an hour（每小时）中文“时速”必须放到数字前',
                 'S2-2 had been derelict since about ': 'since about 1995 是时间状语，中文“约自1995年起便已废弃”时间必须放到动词前',
                 'S14-2 only some 11,000 of them': 'only some 11,000 of them functional 是独立主格结构，of them '
                                                   '中文“其中”必须提前',
                 "S17-1 America's Federal Communicatio": 'which licenses satellites 是非限制性定语从句，中文定语必须提前，机构名不能拆',
                 'S17-3 within five years of retiremen': 'within five years of retirement 中文“在退役后五年内”，退役必须提前',
                 'S17-3 disposal of low-orbit craft wi': '用户 11-08 原话语序“低轨航天器须在退役后五年内处置”把“处置”放到最后，disposal '
                                                         '与后面的 of 结构、within…retirement 先后相反，只能整组',
                 'S18-1 spacecraft whose owners had no': 'whose 引导的定语从句修饰 spacecraft，中文定语必须提前'},
          '短语': {'S9 multitude … of': '不是搭配：multitude 本文就是速查表第一个意思“大量，众多”，of 只把 others 连上',
                 'S10 air drag': '不是搭配：drag 本文就是速查表第一个意思“（空气）阻力”，air 单独译“空气”',
                 'S9 flung … of': '不是搭配：of 属于 a multitude of others，和 flung 无关；fling out 已整体标',
                 'S10 linger … for': '不是搭配：for decades 只表示时长，linger 单独就是“滞留”',
                 'S12 scatter … of': '不是搭配：of 属于 raising the odds of，已整体标',
                 'S15 unfold … over': '不是搭配：over decades 只表示时长，unfold 本文就是速查表第一个意思“（事态）逐步展开”',
                 'S17 mandated … of': '不是搭配：of 属于 disposal of low-orbit craft，和 mandated 无关',
                 'S15 unfold over decades': '不是搭配：unfold 本文就是速查表第一个意思“（事态）逐步展开”，over decades 单独译“历时几十年”',
                 'S11 fired … to': '不是搭配：to 是 to dodge 的不定式符号（目的状语），和 fired 无关'},
          '同词异译': {'had no part in：与/毫无瓜葛': '不是两种译法：have no part in '
                                            '的意思“与……毫无瓜葛”被“此事”隔开，“与”和“毫无瓜葛”是同一个意思的两部分（T23，用户 11-08 原话标 had no '
                                            'part in）',
                   'raising the odds of：提高了/的几率': '不是两种译法：raise the odds of '
                                                  '的意思“提高了……的几率”被“后续相撞”隔开，“提高了”和“的几率”是同一个意思的两部分（T23，用户 11-08 '
                                                  '原话“提高了后续相撞的几率”）'},
          '非人声': {'14.31–14.39s': {'实测': {'最响dB': -36.0, '重心Hz': 1588, '周期': 0.28, '低频dB': -9.9},
                                   '配音指纹': '9a06cf68038d',
                                   '依据': '2026-11-08 逐 2.5 ms 实测（疑点清单 dossier_63，S 句 w）：S1 w '
                                         '11.80–11.88s：hour. 的 ɚ 收尾浊音（周期 0.28–0.56、低频 -9～-18 dB）从 -28 dB 连续衰减到 '
                                         '-60 dB，和词之间没有低谷；词尾'},
                  '20.09–20.11s': {'实测': {'最响dB': -39.9, '重心Hz': 1384, '周期': 0.0, '低频dB': -1.6},
                                   '配音指纹': '9a06cf68038d',
                                   '依据': '2026-11-08 逐 2.5 ms 实测（疑点清单 dossier_63，S 句 w）：S2 w '
                                         '4.71–4.725s：constellation 词中（时长 3.92–5.30），-57 dB 后接 -38 dB '
                                         '有周期（0.31）的浊音，是 ʃ 到 ən 的过渡；词的一部分'},
                  '28.91–29.12s': {'实测': {'最响dB': -36.6, '重心Hz': 3277, '周期': 0.22, '低频dB': -5.6},
                                   '配音指纹': '9a06cf68038d',
                                   '依据': '2026-11-08 逐 2.5 ms 实测（疑点清单 dossier_63，S 句 w）：S2 w '
                                         '13.60–13.81s：five. 的 /v/ 浊音（低频 -3～-10 dB、周期 0.2–0.3）到 13.73，接 /v/ '
                                         '清化的唇齿摩擦（重心 4–4.6 kHz，比吸气的 2–2.6 kHz 高）；词尾'},
                  '32.91–32.95s': {'实测': {'最响dB': -42.8, '重心Hz': 1488, '周期': 0.38, '低频dB': -0.4},
                                   '配音指纹': '9a06cf68038d',
                                   '依据': '2026-11-08 逐 2.5 ms 实测（疑点清单 dossier_63，S 句 w）：S3 w '
                                         '2.80–2.845s：between 的 /b/ 浊音杠（低频 0 dB、周期 0.26–0.49），紧接 2.87 起的元音；词头'},
                  '34.80–34.82s': {'实测': {'最响dB': -42.9, '重心Hz': 1861, '周期': 0.0, '低频dB': -2.1},
                                   '配音指纹': '9a06cf68038d',
                                   '依据': '2026-11-08 逐 2.5 ms 实测（疑点清单 dossier_63，S 句 w）：S3 w '
                                         '4.70–4.715s：satellites. 词的时长内（4.24–4.95），-40～-47 dB、低频 -2～-4 '
                                         'dB、有周期，连续衰减到 -70 dB；词尾'},
                  '42.95–42.97s': {'实测': {'最响dB': -51.1, '重心Hz': 1576, '周期': 0.0, '低频dB': -0.2},
                                   '配音指纹': '9a06cf68038d',
                                   '依据': '2026-11-08 逐 2.5 ms 实测（疑点清单 dossier_63，S 句 w）：S6 w 0.135–0.15s：a 与 '
                                         'public 之间 -51～-58 dB、低频 0 dB 的浊音，0.15 起 public 的 /p/ 爆破（-42→-16 '
                                         'dB）；/p/ 的词头'},
                  '48.99–49.09s': {'实测': {'最响dB': -35.5, '重心Hz': 1449, '周期': 0.16, '低频dB': -3.1},
                                   '配音指纹': '9a06cf68038d',
                                   '依据': '2026-11-08 逐 2.5 ms 实测（疑点清单 dossier_63，S 句 w）：S6 w '
                                         '6.17–6.27s：metres, 词中的 ɚ（低频 -2～-6 dB、周期 0.15–0.35、重心 0.7–2 kHz），6.26 '
                                         '起 /z/（3.4–5.6 kHz）；词的一部分'},
                  '49.62–49.63s': {'实测': {'最响dB': -48.3, '重心Hz': 2197, '周期': 0.0, '低频dB': -0.2},
                                   '配音指纹': '9a06cf68038d',
                                   '依据': '2026-11-08 逐 2.5 ms 实测（疑点清单 dossier_63，S 句 w）：S6 w 6.79–6.805s：yet 的 '
                                         '/j/ 起音前的浊音（低频 0 dB、周期 0.5），连到 6.83 的 -31 dB；词头'},
                  '55.98–56.09s': {'实测': {'最响dB': -36.0, '重心Hz': 3157, '周期': 0.18, '低频dB': -3.8},
                                   '配音指纹': '9a06cf68038d',
                                   '依据': '2026-11-08 逐 2.5 ms 实测（疑点清单 dossier_63，S 句 w）：S6 w '
                                         '13.21–13.31s：imprecise. 的 aɪ 气化收尾（重心 2.7–3.9 kHz），直接接 13.30 起的 '
                                         '/s/（4–5.6 kHz），中间没有低谷；词的一部分'},
                  '73.18–73.20s': {'实测': {'最响dB': -50.0, '重心Hz': 2007, '周期': 0.34, '低频dB': -0.3},
                                   '配音指纹': '9a06cf68038d',
                                   '依据': '2026-11-08 逐 2.5 ms 实测（疑点清单 dossier_63，S 句 w）：S9 w '
                                         '6.685–6.705s：pinpoint 的 /p/ 闭塞里的前爆（6.70 -50 dB、低频 -1 dB），6.71 起爆破 '
                                         '-16 dB；词头'},
                  '100.17–100.19s': {'实测': {'最响dB': -49.8, '重心Hz': 2565, '周期': 0.0, '低频dB': -0.8},
                                     '配音指纹': '9a06cf68038d',
                                     '依据': '2026-11-08 逐 2.5 ms 实测（疑点清单 dossier_63，S 句 w）：S12 w '
                                           '10.73–10.745s：raising 的 /ɹ/ 起音（低频 -1～-2 dB），连到 10.76 的 -26 dB；词头'},
                  '105.38–105.43s': {'实测': {'最响dB': -48.1, '重心Hz': 3385, '周期': 0.49, '低频dB': -0.4},
                                     '配音指纹': '9a06cf68038d',
                                     '依据': '2026-11-08 逐 2.5 ms 实测（疑点清单 dossier_63，S 句 w）：S13 w '
                                           '1.535–1.585s：同上，nine 的 /n/ 鼻音尾（周期 0.46–0.55、低频 0 dB）；词尾'},
                  '105.39–105.42s': {'配音指纹': '9a06cf68038d',
                                     '依据': '2026-11-08 逐 2.5 ms 实测（疑点清单 dossier_63，S 句 w）：S13 w '
                                           '1.535–1.585s：nine 的 /n/ 鼻音尾（周期 0.46–0.55、低频 0 dB）；词尾',
                                     '实测': {'最响dB': -48.1, '重心Hz': 2637, '周期': 0.51, '低频dB': -0.2}},
                  '115.11–115.13s': {'实测': {'最响dB': -49.6, '重心Hz': 1750, '周期': 0.0, '低频dB': -0.8},
                                     '配音指纹': '9a06cf68038d',
                                     '依据': '2026-11-08 逐 2.5 ms 实测（疑点清单 dossier_63，S 句 w）：S14 w '
                                           '3.91–3.925s：tracked 词的时长内（3.675–3.997），-47～-53 dB、低频 -1～-2 dB，是 '
                                           '/k/ 与 /t/ 之间的浊音残留；词的一部分'},
                  '124.35–124.36s': {'实测': {'最响dB': -32.9, '重心Hz': 4747, '周期': 0.0, '低频dB': -1.3},
                                     '配音指纹': '9a06cf68038d',
                                     '依据': '2026-11-08 逐 2.5 ms 实测（疑点清单 dossier_63，S 句 w）：S15 w '
                                           '2.875–2.89s：though 的 /ð/ 起音（低频 -1～-2 dB、周期 0.32–0.36、摩擦重心 4–5 '
                                           'kHz），连到 2.92 的元音；词头'},
                  '133.07–133.16s': {'实测': {'最响dB': -36.9, '重心Hz': 3451, '周期': 0.25, '低频dB': -5.1},
                                     '配音指纹': '9a06cf68038d',
                                     '依据': '2026-11-08 逐 2.5 ms 实测（疑点清单 dossier_63，S 句 w）：S16 w '
                                           '4.09–4.185s：way. 的 eɪ 气化收尾（周期 0.16–0.43、低频 -4～-11 dB），连续衰减到 -66 '
                                           'dB，没有低谷；词尾'},
                  '148.25–148.44s': {'实测': {'最响dB': -38.1, '重心Hz': 3576, '周期': 0.23, '低频dB': -7.1},
                                     '配音指纹': '9a06cf68038d',
                                     '依据': '2026-11-08 逐 2.5 ms 实测（疑点清单 dossier_63，S 句 w）：S17 w '
                                           '14.00–14.185s：five. 的 /v/ 浊音（低频 -3～-10 dB）接清化唇齿摩擦（重心 3.4–4.2 '
                                           'kHz），衰减到 -63 dB；词尾'},
                  '139.79–139.81s': {'实测': {'最响dB': -49.6, '重心Hz': 2396, '周期': 0.26, '低频dB': -0.3},
                                     '配音指纹': '9a06cf68038d',
                                     '依据': '2026-11-08 逐 2.5 ms 实测（疑点清单 dossier_63，S 句 w）：S17 w '
                                           '5.545–5.565s：which 的 /w/ 起音前的浊音（低频 -1 dB、周期 0.2–0.3），连到 5.59 的 -39 '
                                           'dB；词头'},
                  '155.20–155.22s': {'实测': {'最响dB': -31.5, '重心Hz': 3406, '周期': 0.0, '低频dB': -21.4},
                                     '配音指纹': '9a06cf68038d',
                                     '依据': '2026-11-08 逐 2.5 ms 实测（疑点清单 dossier_63，S 句 w）：S18 w '
                                           '5.59–5.605s：kept 的 /t/ 除阻（-52～-57 dB、低频 -18～-23 dB、重心 2.2–3.8 '
                                           'kHz），紧跟 kept 之后；词尾除阻'}},
          '删除段': {'S1 raw 9.1402-9.3000': {'类型': '紧贴两头的非人声',
                                           '配音指纹': '9a06cf68038d',
                                           '依据': '2026-11-08 实测（w 秒）：about 的 /t/ 与 forty 的 /f/ 之间的吸气（-42～-54 '
                                                 'dB、重心 2.1–2.6 kHz、低频 -12～-20 dB），非人声区间 S1 [9.060167, 9.22, '
                                                 '紧贴两头]，两头切在过零点'},
                  'S2 raw 8.2450-8.6400': '2026-11-08 实测（w 秒）：2251, 后停顿里的吸气（-42～-64 dB，-60 dB 低谷后逐渐升到 -42 dB '
                                          '再落到 -59 dB），两侧都在低谷里',
                  'S3 raw 2.6837-2.8207': {'类型': '紧贴两头的非人声',
                                           '配音指纹': '9a06cf68038d',
                                           '依据': '2026-11-08 实测（w 秒）：collision 的 /n/ 与 between 的 /b/ '
                                                 '浊音杠之间的吸气（-46～-56 dB、重心 2.0–2.5 kHz），非人声区间 S3 [2.663708, '
                                                 '2.80075, 紧贴两头]，两头切在过零点'},
                  'S9 raw 4.0650-4.3750': '2026-11-08 实测（w 秒）：fragments 与 and 之间的吸气（-41～-54 dB 持续上升又回落，前 '
                                          '-58～-60 dB、后 -44 dB 再接 and），非人声区间 S9 [4.05, 4.355]',
                  'S12 raw 5.4750-5.8137': {'类型': '紧贴两头的非人声',
                                            '配音指纹': '9a06cf68038d',
                                            '依据': '2026-11-08 实测（w 秒）：spiral, 后停顿里的吸气（-37～-55 dB，5.47–5.49 '
                                                  '-55～-61 dB 低谷后升起，5.80–5.81 回落到 -51～-53 dB 接 later），非人声区间 '
                                                  'S12 [5.470833, 5.803708, 紧贴两头]'},
                  'S13 raw 3.5353-3.6700': {'类型': '紧贴词尾的非人声',
                                            '配音指纹': '9a06cf68038d',
                                            '依据': '2026-11-08 实测（w 秒）：premise 的 /s/（6 kHz）衰减到 w 3.515（-55 '
                                                  'dB），3.5175–3.625 是吸气（重心 2.3–3.6 kHz、低频 -5～-22 dB），非人声区间 S13 '
                                                  '[3.515292, 3.63, 紧贴词尾]，/s/ 本身不动'},
                  'S14 raw 2.1800-2.4675': {'类型': '紧贴词头的非人声',
                                            '配音指纹': '9a06cf68038d',
                                            '依据': '2026-11-08 实测（w 秒）：2024, 后停顿里的吸气连同 surveillance 的 /s/ '
                                                  '前一下低频噗声（w 2.44，低频 0 dB），非人声区间 S14 [2.165, 2.4475, '
                                                  '紧贴词头]，/s/（2.45 起 4.3 kHz）切在过零点、本身不动'},
                  'S15 raw 3.1917-3.4750': {'类型': '紧贴词尾的非人声',
                                            '配音指纹': '9a06cf68038d',
                                            '依据': '2026-11-08 实测（w 秒）：though 的元音衰减到 w 3.165，3.20–3.42 '
                                                  '是吸气（-36～-44 dB、重心 2–3.5 kHz），非人声区间 S15 [3.18175, 3.465, '
                                                  '紧贴词尾]，3.475 起 and'},
                  'S17 raw 0.3600-0.4049': '2026-11-08 实测（w 秒）：In 与 September 之间一下孤立杂音（w 0.355–0.365，-46 dB、重心 '
                                           '3.3 kHz，两边 -62/-64 dB），非人声区间 S17 [0.3525, 0.3675]',
                  'S17 raw 2.3188-2.6700': '2026-11-08 实测（w 秒）：2022, 后停顿里的吸气（-37～-50 dB，前 -56 dB、后 -59～-65 dB '
                                           '低谷），非人声区间 S17 [2.29875, 2.62375]',
                  'S11 raw 1.9548-2.4300': {'类型': '紧贴词尾的非人声',
                                            '配音指纹': '9a06cf68038d',
                                            '依据': '2026-11-08 实测（w 秒）：twelve, 的 /v/ 浊音到 1.94，1.945–2.03 '
                                                  '清化气流（纯人声核对判像可闻吸气，G43）连同 2.19–2.42 停顿里的吸气（非人声区间 S11 '
                                                  '[1.944792, 2.03, 紧贴词尾]、[2.19, 2.418708, 紧贴词头]），浊音本身不动'}},
          '机器复听': {'S2': {'配音指纹': '9a06cf68038d',
                          '依据': '2026-11-08：satellite-phone 配音音标 sˈæɾəlˌaɪtfˈoʊn（phone /fˈoʊn/，CMU F OW1 '
                                'N），读对；phone 后紧接 constellation 的 /k/，small.en 一路把 n 听成 m 拼成 '
                                'foam，另一路识别器听对，非读错'}},
          '停顿位置': {'S5 propulsion, / could @2.235': '2026-11-07 逐 2.5 ms 实测（S5 w，句首修剪 10 ms 后的时刻）：propulsion 的 '
                                                    '/n/ 浊音（重心 0.4–0.6 kHz）衰减到 2.2125（-27 dB），2.215–2.245 '
                                                    '是两词交界的低谷（-39～-58 dB），2.2475 起 could 的 /k/ 送气（-20 dB、重心 '
                                                    '4.5 kHz）；停顿 2.235 落在低谷里，在两词之间',
                   'S8 wreckage, / however, @0.555': '2026-11-07 逐 2.5 ms 实测（S8 w，句首修剪 20 ms 后的时刻）：wreckage 的 '
                                                     '/dʒ/ 擦音（重心 4.5–5 kHz）到 0.535 还有 -15 dB，0.54–0.5625 '
                                                     '衰减（-18→-30 dB），0.5675 起 however 的 /h/（重心约 3 kHz）回升，0.615 '
                                                     '起元音；停顿 0.555 落在 /dʒ/ 衰减到 -29 dB 的尾巴和 /h/ 之间的低处，两词之间',
                   'S15 decades, / though, @2.870': '2026-11-07 逐 2.5 ms 实测（S15 w，句首修剪 10 ms 后的时刻）：decades 的 '
                                                    '/z/（重心 6–7.5 kHz）衰减到 2.865（-35 dB），2.8675–2.8725 '
                                                    '是低谷（-38～-39 dB），2.875 起 though 的 /ð/（重心降到 3–5 '
                                                    'kHz）回升，2.9175 起元音；停顿 2.870 落在低谷里，在两词之间',
                   'S15 though, / and @3.190': '2026-11-07 逐 2.5 ms 实测（S15 w，句首修剪 10 ms 后的时刻）：though 的元音衰减到 '
                                               '3.165（-36 dB），3.1725–3.195 低谷（-42～-54 dB），3.20–3.42 '
                                               '是吸气（-36～-44 dB、重心 2–3.5 kHz，非人声区间 S15 [3.18175, '
                                               '3.465]），3.42–3.47 低谷（-44～-56 dB），3.475 起 and（-22 dB）；删静音 '
                                               '3.190–3.460 两头都在低谷里，在两词之间'},
          '高亮': {'S17 第3块': {'开始读': 142.86,
                             '配音指纹': '9a06cf68038d',
                             '依据': '2026-11-08 直接读 work_63/a.wav 逐 10 ms：mandated 的元音到 142.75，142.76–142.85 是 '
                                   'mandated 词尾 /d/ 与 disposal 词头 /d/ 连在一起的浊音闭塞（-22～-31 dB、重心 0.2–0.5 '
                                   'kHz），142.86 起 disposal 的 /d/ 爆破（重心 3.6 kHz），142.88 起元音 -17→-12 dB，142.94 起 '
                                   '/s/（4.3–5.9 kHz）；开始读 142.86，两种办法 142.85/142.86 一致，高亮 143.13 推后 0.28 s'}}},
 '结尾解说': '简述',
 '高亮按实际开口': True,
 '高亮开口门槛': 40,
 '术语': {'Siberia': '西伯利亚',
        'Iridium 33': '铱星33号',
        'Kosmos 2251': '宇宙2251号',
        'Russian': '俄罗斯',
        'American': '美国',
        'International Space Station': '国际空间站',
        'NASA': '美国国家航空航天局',
        'Kessler': '凯斯勒',
        'Federal Communications Commission': '联邦通信委员会',
        'America': '美国'},
 '高亮开始': {'S17 第3块': 142.86},
 '非人声区间': {'S9': [[4.05, 4.355]],
           'S12': [[5.470833, 5.803708, '紧贴两头']],
           'S15': [[3.18175, 3.465, '紧贴词尾']],
           'S16': [[1.135, 1.315]],
           'S5': [[0.925, 1.12]],
           'S1': [[2.465, 2.722792, '紧贴词头'], [9.060167, 9.22, '紧贴两头']],
           'S2': [[13.810125, 13.84, '紧贴词尾']],
           'S3': [[2.663708, 2.80075, '紧贴两头']],
           'S8': [[1.025, 1.185]],
           'S11': [[1.944792, 2.03, '紧贴词尾'], [2.19, 2.418708, '紧贴词头']],
           'S13': [[1.355, 1.53], [3.515292, 3.63, '紧贴词尾']],
           'S14': [[2.165, 2.4475, '紧贴词头']],
           'S17': [[2.29875, 2.62375, '紧贴两头'], [0.3525, 0.3675]]},
 '句子增益dB': {'S4': -1.0},
 '分段增益dB': {'S11': {'2': 1.0}},
 '停顿插入点': {},
 '词尾除阻': {'S2': {'3': [10.395, 't']},
          'S7': {'句末': [3.815, 't']},
          'S12': {'1': [1.855, 't']},
          'S5': {'句末': [2.785, 't']},
          'S6': {'2': [10.17, 't']},
          'S9': {'句末': [7.29, 't']},
          'S11': {'句末': [8.11, 't']}},
 '结尾句': {'S18': {'前段语速': 0.9,
                 '最后一段语速': 0.78,
                 '最后一段前停顿': 0.7,
                 '接点': [44220, 52500],
                 '依据': '全篇结尾句按 07 定下的标准（用户 2026-10-10 同意并要求所有视频统一）：前段 0.9、最后一段“spacecraft whose owners had no '
                       'part in it kept swerving around its splinters.” 0.78、前面停 0.7 秒。接点由 结尾句接点.py 自动找：0.9 '
                       '那遍最后一个标点后最长静音（30 ms）的正中 1.843 s，0.78 那遍（75 ms）的正中 2.188 s，所在帧和两侧各 5 ms 都低于 -55 dB（程序以 '
                       '08 校准：与人工核实的接点落在同一段静音里）'}},
 '区间声音指纹': {'S1': 'a773686f1633',
            'S2': '1a98098e4e8d',
            'S3': 'bb48cd36e64a',
            'S5': 'ac75fbe3ce80',
            'S6': 'c4d4c2ec186f',
            'S7': 'fe064df445d6',
            'S8': '3de2e4e1c82e',
            'S9': 'f39a13358598',
            'S11': 'b033862eff17',
            'S12': '2e94d458517b',
            'S13': 'e02bcb2a839c',
            'S14': '7d6f9d717ff5',
            'S15': 'af8692d95289',
            'S16': '92c647ad9194',
            'S17': 'af6a576b3df1'},
 '换行变更记录': [{'日期': '2026-11-08',
             'S17': '用户 2026-11-08 原话把 S17 整句改为“2022年9月，负责为卫星发放许可的美国联邦通信委员会强制要求，低轨航天器须在退役后五年内处置，而不是25年。”并标 '
                    'instead of，中文语序变了随之换行',
             'S11': '用户 2026-11-08 原话要 S11 整句改为“2012年1月，国际空间站启动了它的推进器，以躲开/避开一块铱星33号的残片。”、fired 标重点词、“space '
                    'station 整体标注重点词汇”，字变多随之换行；另 11-07 原话（篇 61-65）“对齐需要改换行”视为同意'}]}

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 核对 import 生成并核对
生成并核对(S, out)
