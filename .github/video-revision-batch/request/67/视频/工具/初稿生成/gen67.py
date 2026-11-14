#!/usr/bin/env python3
# Pure data frozen from the current approved JSON; shared helper/checkers unchanged.
import os
import sys

S = [(1,
  [[[('Marcel Ravidat,', '马塞尔·拉维达，'), ('18,', '18岁，')], '（18：插入语，补充说明年龄）'],
   [[('was on a', '正在'),
     ('**woodland**', '和罗伯特在蒙蒂尼亚克附近的**林地**(woodland)里'),
     ('**stroll** near Montignac with Robot,', '**散步**(stroll)。'),
     ('his **canine**', '罗伯特是他**犬类的**(canine)小'),
     ('**companion**,', '**伙伴**(companion)。')],
    '（his canine companion：同位语，补充说明 Robot）'],
   [[('when', '这个时候'),
     ('it began', '罗伯特'),
     ('**sniffing** at a **hollow** left by a **toppled** tree.',
      '在一棵**倒下的**(toppled)树留下的（地面）**凹陷处**(hollow)**嗅来嗅去**(sniffing)。')],
    '（it 指 Robot；\nleft by a toppled tree：过去分词短语作后置定语，修饰 hollow）']]),
 (1,
  [[[('On 12 September 1940', '1940年9月12日，'),
     ('he', '他'),
     ('came back with three other boys', '带着另外三个男孩回到这里，')]],
   [[('for', '来了一次'),
     ('an **adventurous**', '**富于冒险的**(adventurous)'),
     ('**excursion**,', '**短途旅行**(excursion)，')],
    '（for：表示目的）'],
   [[('and', '并且'),
     ('the four', '四个'),
     ('**explorers**', '**探险者**(explorers)'),
     ('climbed down into', '爬进了'),
     ('the **darkness**.', '**黑暗**(darkness)之中。')]]]),
 (2,
  [[[('In later', '在后来的'), ('**retellings**,', '**复述**(retellings)中，')]],
   [[('Ravidat', '拉维达'),
     ('**embroidered** his **anecdote**', '给这段**轶事**(anecdote)**添油加醋**(embroidered)，'),
     ('with a', '加入了一个'),
     ('**dramatic**', '**戏剧性的**(dramatic)'),
     ('twist.', '转折。')],
    '（embroider A with B：用 B 给 A 添油加醋）\n（anecdote：关于某人真事的、有趣的小故事\n（趣闻轶事））']]),
 (2,
  [[[('Robot, he said,', '他说，罗伯特'), ('had **fallen into**', '**掉进了**(fallen into)'), ('the cave.', '洞里。')],
    '（he said：插入语；\nhad fallen：过去完成时，掉洞在讲述之前）']]),
 (2,
  [[[('That **fanciful**', '这个**离奇的**(fanciful)'),
     ('**mishap**', '**意外**(mishap)'),
     ('is a', '纯属'),
     ('**fabrication**.', '**编造/虚构**(fabrication)。')]]]),
 (2,
  [[[('The animal', '那只狗'), ('only', '只是'), ('nosed about the hole,', '在洞口嗅了嗅，')], '（nose about：到处嗅）'],
   [[('and the **pivotal**', '**关键的**(pivotal)'),
     ('**initiative**', '**主动行动**(initiative)'),
     ("was the boys' own.", '完全出自几个男孩。')],
    "（the boys' own：男孩们自己的，own 后省略了 initiative）\n（那只狗只是在洞口随便闻了闻，并没有往里钻。\n真正决定往下爬去探险的，完全是那几个男孩自己的主意。）"]]),
 (2,
  [[[('**Ironically**,', '**讽刺的是**(Ironically)，'),
     ('the **invented**', '**虚构的**(invented)'),
     ('fall', '那一跤'),
     ('made', '让'),
     ('the dog', '狗'),
     ('the hero of the story.', '成了故事的主角。')],
    '（make A B：使 A 成为 B）']]),
 (3,
  [[[('Some 680', '约680个'),
     ('**painted figures**', '**彩绘人像**(painted figures)'),
     ('and', '和'),
     ('1,500 **engravings**', '1,500幅**雕刻图案**(engravings)'),
     ('**cover**', '**布满了**(cover)'),
     ('the rock.', '这块岩石。')],
    '（some：大约，用在数字前）\n（几个男孩爬进去一看，好家伙，\n整个岩壁上密密麻麻全都是画！\n大概有680个是用颜料彩绘上去的图案，\n还有1500个是用工具刻上去的图案。）']]),
 (3,
  [[[('The **artwork**', '这些**艺术作品**(artwork)'),
     ('is usually', '通常'),
     ('dated to', '可被追溯到'),
     ('between 17,000', '1.7万'),
     ('and 22,000 years ago;', '至2.2万年之前；')],
    '（be dated to：年代被断定为）'],
   [[('its', '其'),
     ('**creators**,', '**创作者**(creators)，'),
     ('our distant', '是我们遥远的'),
     ('**ancestors**,', '**祖先**(ancestors)，'),
     ('lived in', '生活在'),
     ('**antiquity**.', '**古时代**(antiquity)。')],
    '（our distant ancestors：同位语，补充说明 creators）\n（antiquity：古时代（特别指古埃及、古希腊、古罗马时期））']]),
 (3,
  [[[('Horses,', '马、'),
     ('**bulls**,', '**公牛**(bulls)'),
     ('and stags', '和雄鹿'),
     ('are among the animals **depicted** in **pigments** on the **murals**.',
      '都是**壁画**(murals)上用**颜料**(pigments)**描绘**(depicted)的动物。')],
    '（be among：是……之一；\ndepicted in pigments on the murals：\n过去分词短语作后置定语，修饰 animals）']]),
 (3,
  [[[("The paintings'", '这些画作的'),
     ('**fragility**', '**脆弱性**(fragility)'),
     ('soon', '很快就'),
     ('became clear.', '显现了出来。')]]]),
 (4,
  [[[('Lascaux **opened to the public** on 14 July 1948,', '1948年7月14日，拉斯科**向公众开放**(opened to the public)，')]],
   [[('and **tourism**', '**旅游业**(tourism)'),
     ('brought', '带来了'),
     ('an **influx** of about 1,200 visitors a day.', '每天约1,200名游客的**涌入**(influx)。')],
    '（an influx of A：A 的涌入）']]),
 (4,
  [[[('The **throng**', '**人群**(throng)'),
     ('**exhaled**', '**呼出**(exhaled)'),
     ('**carbon dioxide**', '**二氧化碳**(carbon dioxide)，')]],
   [[('and added', '并增加了'),
     ('heat,', '热量、'),
     ('**humidity**,', '**湿度**(humidity)'),
     ('and', '和'),
     ('**contaminants**,', '**污染物**(contaminants)，')]],
   [[('and the **deterioration** of the paintings', '而壁画的**劣化/恶化**(deterioration)'),
     ('became', '变得'),
     ('**plain to see**.', '**显而易见**(plain to see)。')]]]),
 (4,
  [[[('In 1963', '1963年，'), ('the site', '该遗址'), ('closed to the public,', '对公众关闭，')]],
   [[('followed by', '紧随其后的是'),
     ('**restoration**', '**修复**(restoration)'),
     ('and daily', '和每日'),
     ('**inspection**.', '**检查**(inspection)。')],
    '（followed by…：过去分词短语，表示随后发生的事）']]),
 (5,
  [[[('Lascaux', '拉斯科'), ("joined UNESCO's World Heritage List in 1979,", '于1979年加入了联合国教科文组织的《世界遗产名录》，')]],
   [[('and', '而'),
     ('Lascaux II,', '拉斯科二号，'),
     ('a **meticulously**', '一个**精心**(meticulously)'),
     ('made', '制作的'),
     ('**partial**', '**局部的**(partial)'),
     ('**facsimile**,', '**复制品**(facsimile)，'),
     ('opened in 1983.', '于1983年开放。')],
    '（a meticulously made partial facsimile：同位语，\n补充说明 Lascaux II）\n（meticulously：极其仔细地、一丝不苟地（连一点细节都不放过））']]),
 (5,
  [[[('A white **fungus** **invaded** the walls in a 2001 **outbreak**,',
      '2001年，一种白色**真菌**(fungus)**爆发**(outbreak)，**侵入**(invaded)洞壁；')],
    '（in a 2001 outbreak：在2001年的一次爆发中）'],
   [[('and black **stains** spread after **chemical treatment**.',
      '**化学处理**(chemical treatment)后，黑色**污斑**(stains)蔓延开来。')]]]),
 (5, [[[('Lascaux IV opened in December 2016.', '2016年12月，拉斯科四号开放。')]]]),
 (5,
  [[[('**Admirers** now', '如今**仰慕者**(Admirers)'),
     ('meet the bulls only in a **recreation**,', '只能在**复原品**(recreation)中见到那些公牛，')],
    '（only in…：只在……中）'],
   [[('the originals', '原洞'), ('being **inaccessible** to them.', '对他们来说**无法进入**(inaccessible)。')],
    '（the originals being…：独立主格，补充说明原因）\n'
    '（简述：▸发现：1940年，狗在地洞旁嗅闻引起拉维达注意；他随后与另外三名少年下洞，发现拉斯科史前壁画。▸澄清：后来拉维达把故事说成狗掉进洞里；其实狗只在洞口嗅闻，下洞探险是少年们主动决定的。▸瑰宝：洞内约有680个彩绘形象和1500幅雕刻图案，常被断代为距今约1.7万至2.2万年，描绘马、牛、鹿等动物。▸受损：1948年开放后，游客带来二氧化碳、热量、湿气和污染，壁画退化，1963年闭洞。▸保护：闭洞后仍出现真菌、黑斑；1983年和2016年先后开放复制洞穴，公众如今只能看复制品。）']])]

out = {'no': '67',
 'title_en': 'The Cave Found by a Dog',
 'title_zh': '几个少年和一只狗发现的洞穴',
 'title_fx': {'hl': ['Cave', 'Dog'], 'ghost': []},
 'sentences': [],
 '核对确认': {'合组': {'S9 dated to between 17,000 and 22,000 years ago': '对齐不了：between A and B years ago 中文“距今 A 至 '
                                                                    'B 年”，“距今”(ago) '
                                                                    '必须提前；数字中文写作“1.7万”“2.2万”，不能拆',
                 'S9 between 17,000 and 22,000 years ago': '对齐不了：between A and B years ago 中文“距今 A 至 B '
                                                           '年”，“距今”(ago) 必须提前；数字中文写作“1.7万”“2.2万”，不能拆',
                 'S1 was on a woodland stroll near Montignac with Robot, his canine companion': '对齐不了：伴随状语 '
                                                                                                'with Robot, '
                                                                                                'his canine '
                                                                                                'companion '
                                                                                                '中文“带着他的犬类伙伴罗伯特”必须放到前面；地点状语 '
                                                                                                'near '
                                                                                                'Montignac '
                                                                                                '中文“在蒙蒂尼亚克附近”放到动词前；be '
                                                                                                'on a stroll '
                                                                                                '中文“散步”放最后',
                 'S13 plain to see': '对齐不了：plain to see 是固定说法，中文“肉眼可见”拆开不通',
                 'S15 and Lascaux II, a meticulously': '对齐不了：时间状语 in 1983 中文“1983年”必须放到句首；专名 Lascaux II '
                                                       '中文“拉斯科二号”放在同位语后面',
                 'S15 facsimile, opened in 1983': '对齐不了：Lascaux II 是同位语 a … facsimile '
                                                  '的中心词，中文“复制品拉斯科二号”放在一起；时间“1983年”已提到句首',
                 'S1 woodland stroll near Montignac with Robot': '对齐不了：伴随状语 with Robot 中文“和罗伯特”、地点状语 near '
                                                                 'Montignac 中文“在蒙蒂尼亚克附近的林地里”都必须放到动词“散步”前（用户 '
                                                                 '2026-11-10 改稿译文）',
                 'S1 his canine companion': '对齐不了：同位语 his canine companion 用户改译成独立一句“罗伯特是他犬类的小伙伴”（用户 '
                                            '2026-11-10 改稿），拆开不通',
                 'S1 woodland': '对齐不了：伴随状语 with Robot 中文“和罗伯特”、地点状语 near Montignac '
                                '中文“在蒙蒂尼亚克附近的”都必须放到“林地里散步”前（用户 2026-11-10 改稿译文）',
                 'S1 stroll near Montignac with Robot': '对齐不了：near Montignac、with Robot 的中文已放到“林地”前（用户 '
                                                        '2026-11-10 改稿译文），这里只剩“散步”',
                 'S1 sniffing at a hollow left by a toppled tree': '对齐不了：left by a toppled tree 是后置定语，修饰 '
                                                                   'hollow，中文“一棵倒伏的树留下的坑洞”必须提前；at a hollow '
                                                                   '中文“在……边”放到“嗅来嗅去”前',
                 'S2 came back with three other boys': '对齐不了：伴随状语 with three other boys '
                                                       '中文“带着另外三个男孩”必须放到动词“回到这里”前',
                 'S6 nosed about the hole': '对齐不了：地点 the hole 中文“在洞口”必须放到“嗅了嗅”前；nose about 是一个说法，拆开不通',
                 "S6 was the boys' own": "对齐不了：be the boys' own 意思是“是男孩们自己的”，中文“完全出自几个男孩”是整体说法，拆开不通",
                 'S7 the hero of the story': '对齐不了：the hero of the story 中文“故事的主角”必须倒过来',
                 'S8 painted figures': '对齐不了：painted figures 中文“彩绘形象”是一个词组，拆开不通',
                 'S9 and 22,000 years ago': '对齐不了：数字中文写作“2.2万”，years ago 中文“年之前”，一个数和单位不能拆',
                 'S10 are among the animals depicted in pigments on the murals': '对齐不了：depicted in pigments on '
                                                                                 'the murals 是后置定语，修饰 '
                                                                                 'animals，中文“壁画上用颜料描绘的动物”必须提前；be '
                                                                                 'among 中文“都是”',
                 'S11 became clear': '对齐不了：become clear 中文“显现出来”是一个说法，拆开不通',
                 'S12 Lascaux opened to the public on 14 July 1948': '对齐不了：时间状语 on 14 July 1948 '
                                                                     '中文“1948年7月14日”必须放到句首；opened to the '
                                                                     'public 中文“向公众开放”是一个说法',
                 'S12 an influx of about 1,200 visitors a day': '对齐不了：an influx of A 中文“A 的涌入”必须倒过来；a day '
                                                                '中文“每天”必须提前',
                 'S14 closed to the public': '对齐不了：to the public 中文“对公众”必须放到动词“关闭”前',
                 "S15 joined UNESCO's World Heritage List in 1979": '对齐不了：时间状语 in 1979 '
                                                                    '中文“于1979年”必须放到动词“加入了”前；机构名、名录名不能拆',
                 'S16 A white fungus invaded the walls in a 2001 outbreak': '对齐不了：时间状语 in a 2001 outbreak '
                                                                            '中文“2001年”必须放到句首，“爆发”放到“侵入”前（先爆发、后侵入）',
                 'S16 and black stains spread after chemical treatment': '对齐不了：时间状语 after chemical treatment '
                                                                         '中文“化学处理后”必须放到句首',
                 'S17 Lascaux IV opened in December 2016': '对齐不了：时间状语 in December 2016 中文“2016年12月”必须放到句首',
                 'S18 meet the bulls only in a recreation': '对齐不了：地点 in a recreation 中文“在复原品中”必须放到动词“见到”前',
                 'S8 1,500 engravings': '对齐不了：1,500 是一个数，中文“1,500幅”带量词，不能拆成“1、500”'},
          '对齐': {'S1-2 stroll near Montignac with Rob': '用户 2026-11-10 改稿译文“和罗伯特在蒙蒂尼亚克附近的林地里散步”：伴随状语 with '
                                                        'Robot、地点状语 near Montignac 中文已放到“林地”前，这一组只剩“散步”',
                 'S1-3 sniffing at a hollow left by a': 'left by a toppled tree 是后置定语，修饰 '
                                                        'hollow，中文“在一棵倒下的树留下的（地面）凹陷处”必须提前，“嗅来嗅去”在最后',
                 'S2-1 came back with three other boy': '伴随状语 with three other boys 中文“带着另外三个男孩”必须放到“回到这里”前',
                 'S7-1 the hero of the story.': 'of 结构 the hero of the story 中文“故事的主角”必须倒过来',
                 'S9-1 and 22,000 years ago;': '数字中文写作“2.2万”，years ago 中文“年之前”，一个数和单位不能拆',
                 'S10-1 are among the animals depicted': 'depicted in pigments on the murals 是后置定语，修饰 '
                                                         'animals，中文“壁画上用颜料描绘的动物”必须提前',
                 'S12-1 Lascaux opened to the public o': '时间状语 on 14 July 1948 中文“1948年7月14日”必须放到句首；opened to '
                                                         'the public 是重点短语“向公众开放”',
                 'S12-2 an influx of about 1,200 visit': 'of 结构 an influx of visitors 中文“游客的涌入”必须倒过来；a day '
                                                         '中文“每天”提前',
                 'S13-3 and the deterioration of the p': 'of 结构 the deterioration of the paintings '
                                                         '中文“壁画的劣化/恶化”必须倒过来',
                 "S15-1 joined UNESCO's World Heritage": '时间状语 in 1979 中文“于1979年”必须放到动词“加入了”前；机构名、名录名不能拆',
                 'S16-1 A white fungus invaded the wal': '时间状语 in a 2001 outbreak 中文“2001年”必须放到句首，“爆发”在“侵入”前',
                 'S16-2 and black stains spread after ': '时间状语 after chemical treatment 中文“化学处理后”必须放到句首',
                 'S17-1 Lascaux IV opened in December ': '时间状语 in December 2016 中文“2016年12月”必须放到句首',
                 'S18-1 meet the bulls only in a recre': '地点状语 in a recreation 中文“在复原品中”必须放到动词“见到”前'},
          '停顿位置': {'S4 Robot, / he @0.644': '2026-11-09 逐 2.5 ms 实测（S4 w）：Robot（ɹoʊbˈoʊ）末音节 /oʊ/ 浊音到 '
                                            '0.640（-12～-15 dB、重心 150–320 Hz、低频 -0～-0.5），0.645 起 he 的 /h/（重心 '
                                            '0.9→4.3 kHz）；停顿 0.644 落在两词交界（时长模型把 /oʊ/ 算短了）',
                   'S4 said, / had @1.005': '2026-11-09 逐 2.5 ms 实测（S4 w）：said 的 /d/ 浊音到 0.990（低频 '
                                            '-0.2），0.9947–1.19 弱气声已按非人声区间删成静音，1.225 起 had 的 /h/；停顿 1.005–1.21 '
                                            '落在两词之间的静音里',
                   'S10 Horses, / bulls, @0.695': '2026-11-09 逐 2.5 ms 实测（S10 w）：Horses 的 /z/ 擦音 0.62–0.675（重心 '
                                                  '5 kHz），0.695 是低谷 -43.5 dB，0.70–0.85 是 bulls 的 /b/ 浊音杠（周期 '
                                                  '0.45–0.53、重心 220–460 Hz、低频 -0.5～-2）；停顿 0.695 落在两词交界（时长模型没算 '
                                                  '/b/ 浊音杠）',
                   'S10 bulls, / and @1.272': '2026-11-09 逐 1.25 ms 实测（S10 w）：bulls 的 /z/ 擦音 1.195–1.271（重心 5 '
                                              'kHz），1.2732 起 and 的元音（重心 1.1 kHz→300 Hz）；停顿 1.272292 是交界过零点',
                   'S13 humidity, / and @4.567': '2026-11-09 逐 1.25 ms 实测（S13 w）：humidity 的 /i/ 到 '
                                                 '4.559，4.56–4.566 是 and 起音前的弱声（-32～-40 dB），4.5675 起 and '
                                                 '的元音（-17 dB）；停顿 4.566583 落在元音前的过零点'},
          '非人声': {'16.66–16.68s': {'配音指纹': 'c34294a522a7',
                                   '依据': '2026-11-09 逐 2.5 ms 实测（dossier_67 #1）：S2 w 0.945–0.960s：of September '
                                         '之间，of 的 /v/ 清化收尾、紧接 September 的 /s/（0.985 起 5.7 kHz），在 September 的时长 '
                                         '0.897–1.392 内；词的一部分',
                                   '实测': {'最响dB': -34.4, '重心Hz': 3298, '周期': 0.0, '低频dB': -22.9}},
                  '18.25–18.27s': {'配音指纹': 'c34294a522a7',
                                   '依据': '2026-11-09 逐 2.5 ms 实测（dossier_67 #2）：S2 w 2.615–2.630s：forty 的 /i/ '
                                         '浊音收尾（周期 0.28、低频 -0.4 dB，词 1.986–2.654 内）；词尾',
                                   '实测': {'最响dB': -45.4, '重心Hz': 2346, '周期': 0.0, '低频dB': -0.4}},
                  '32.02–32.08s': {'配音指纹': 'c34294a522a7',
                                   '依据': '2026-11-09 逐 2.5 ms 实测（dossier_67 #3）：S3 w 4.990–5.045s：twist. 句末 '
                                         '/t/ 除阻（重心 4 kHz、低频 -16 dB，词 4.540–5.089 内）；词尾塞音除阻',
                                   '实测': {'最响dB': -36.6, '重心Hz': 4035, '周期': 0.17, '低频dB': -16.6}},
                  '38.63–38.69s': {'配音指纹': 'c34294a522a7',
                                   '依据': '2026-11-09 逐 2.5 ms 实测（dossier_67 #4）：S5 w 1.370–1.425s：mishap 词内（词 '
                                         '0.913–1.544 内，周期 0.22、低频 -3 dB 浊音）；词的一部分',
                                   '实测': {'最响dB': -33.7, '重心Hz': 1611, '周期': 0.19, '低频dB': -3.2}},
                  '43.92–43.94s': {'配音指纹': 'c34294a522a7',
                                   '依据': '2026-11-09 逐 2.5 ms 实测（dossier_67 #5）：S6 w 2.990–3.005s：the 的元音收尾、接 '
                                         'pivotal 的 /p/ 闭塞（低频 -0.1 dB、周期 0.26）；词的一部分',
                                   '实测': {'最响dB': -46.7, '重心Hz': 2057, '周期': 0.0, '低频dB': -0.1}},
                  '46.30–46.38s': {'配音指纹': 'c34294a522a7',
                                   '依据': '2026-11-09 逐 2.5 ms 实测（dossier_67 #6）：S6 w 5.370–5.455s：own. 句末 /n/ '
                                         '鼻音收尾（周期 0.31、低频 -8.6 dB，词 5.033–5.515 内）；词尾',
                                   '实测': {'最响dB': -38.7, '重心Hz': 1957, '周期': 0.26, '低频dB': -8.6}},
                  '58.13–58.16s': {'配音指纹': 'c34294a522a7',
                                   '依据': '2026-11-09 逐 2.5 ms 实测（dossier_67 #7）：S8 w 5.415–5.435s：engravings 的 '
                                         '/z/ 擦音残尾（重心 4.8 kHz，-48 dB，紧接词尾 5.412）；词尾',
                                   '实测': {'最响dB': -48.4, '重心Hz': 4823, '周期': 0.29, '低频dB': -3.9}},
                  '72.71–72.72s': {'配音指纹': 'c34294a522a7',
                                   '依据': '2026-11-09 逐 2.5 ms 实测（dossier_67 #8）：S10 w 0.700–0.715s：bulls 的 /b/ '
                                         '浊音杠开头（周期 0.40、重心 460 Hz、低频 -1.1 dB），停顿插在 0.695 低谷；词头的一部分',
                                   '实测': {'最响dB': -32.6, '重心Hz': 460, '周期': 0.0, '低频dB': -1.1}},
                  '77.34–77.44s': {'配音指纹': 'c34294a522a7',
                                   '依据': '2026-11-09 逐 2.5 ms 实测（dossier_67 #9）：S10 w 5.250–5.345s：murals. 句末 '
                                         '/lz/（词 4.949–5.515 内，周期 0.23、低频 -3.9 dB）；词尾',
                                   '实测': {'最响dB': -37.7, '重心Hz': 1657, '周期': 0.23, '低频dB': -3.9}},
                  '87.54–87.56s': {'配音指纹': 'c34294a522a7',
                                   '依据': '2026-11-09 逐 2.5 ms 实测（dossier_67 #10）：S12 w 5.275–5.295s：and '
                                         '的浊音起音（周期 0.38、低频 -0.4 dB，紧接非人声区间止点 5.277）；词头的一部分',
                                   '实测': {'最响dB': -47.2, '重心Hz': 2506, '周期': 0.38, '低频dB': -0.4}},
                  '92.57–92.67s': {'配音指纹': 'c34294a522a7',
                                   '依据': '2026-11-09 逐 2.5 ms 实测（dossier_67 #11）：S12 w 10.305–10.405s：day. 句末 '
                                         '/eɪ/ 收尾气化（词 10.084–10.467 内，低频 -5.8 dB）；词尾',
                                   '实测': {'最响dB': -35.5, '重心Hz': 3288, '周期': 0.21, '低频dB': -5.8}},
                  '99.11–99.12s': {'配音指纹': 'c34294a522a7',
                                   '依据': '2026-11-09 逐 2.5 ms 实测（dossier_67 #12）：S13 w '
                                         '5.375–5.390s：contaminants 词内（词 4.762–5.982 内，低频 -2.8 dB）；词的一部分',
                                   '实测': {'最响dB': -33.6, '重心Hz': 1068, '周期': 0.0, '低频dB': -2.8}},
                  '102.80–102.88s': {'配音指纹': 'c34294a522a7',
                                     '依据': '2026-11-09 逐 2.5 ms 实测（dossier_67 #13）：S13 w 9.285–9.365s：see. 句末 '
                                           '/iː/ 收尾气化（词 9.043–9.408 内，低频 -2.6 dB）；词尾',
                                     '实测': {'最响dB': -36.4, '重心Hz': 3223, '周期': 0.26, '低频dB': -2.6}},
                  '102.83–102.84s': {'配音指纹': 'c34294a522a7',
                                     '依据': '2026-11-09 逐 2.5 ms 实测（dossier_67 #14）：S13 w 9.320–9.335s：see. 句末 '
                                           '/iː/ 收尾（周期 0.34，词内）；词尾',
                                     '实测': {'最响dB': -38.5, '重心Hz': 3454, '周期': 0.0, '低频dB': -1.4}},
                  '105.38–105.47s': {'配音指纹': 'c34294a522a7',
                                     '依据': '2026-11-09 逐 2.5 ms 实测（dossier_67 #15）：S14 w '
                                           '1.525–1.620s：sixty-three 的 /iː/ 收尾（词 0.825–1.708 内，低频 -6.9 dB）；词尾',
                                     '实测': {'最响dB': -37.3, '重心Hz': 2387, '周期': 0.25, '低频dB': -6.9}},
                  '117.72–117.74s': {'配音指纹': 'c34294a522a7',
                                     '依据': '2026-11-09 逐 2.5 ms 实测（dossier_67 #16）：S15 w 6.155–6.175s：Lascaux '
                                           'two 的 /uː/ 收尾（周期 0.33、低频 -1.2 dB，词 5.865–6.588 内）；词尾',
                                     '实测': {'最响dB': -41.6, '重心Hz': 1557, '周期': 0.33, '低频dB': -1.2}},
                  '122.88–122.97s': {'配音指纹': 'c34294a522a7',
                                     '依据': '2026-11-09 逐 2.5 ms 实测（dossier_67 #17）：S15 w '
                                           '11.270–11.355s：eighty-three. 句末 /iː/ 收尾气化（词 10.672–11.392 内，低频 '
                                           '-3.5 dB）；词尾',
                                     '实测': {'最响dB': -38.5, '重心Hz': 3329, '周期': 0.26, '低频dB': -3.5}},
                  '128.00–128.06s': {'配音指纹': 'c34294a522a7',
                                     '依据': '2026-11-09 逐 2.5 ms 实测（dossier_67 #18）：S16 w '
                                           '4.060–4.120s：outbreak, 停顿前 /k/ 除阻（重心 4.5 kHz、低频 -19 dB，词 '
                                           '3.572–4.538 内）；词尾塞音除阻',
                                     '实测': {'最响dB': -30.6, '重心Hz': 4491, '周期': 0.16, '低频dB': -19.2}},
                  '128.46–128.47s': {'配音指纹': 'c34294a522a7',
                                     '依据': '2026-11-09 逐 2.5 ms 实测（dossier_67 #19）：S16 w 4.525–4.540s：and '
                                           '的浊音起音（低频 -0.3 dB，紧接非人声区间止点 4.5236）；词头的一部分',
                                     '实测': {'最响dB': -44.7, '重心Hz': 2243, '周期': 0.0, '低频dB': -0.3}},
                  '131.28–131.31s': {'配音指纹': 'c34294a522a7',
                                     '依据': '2026-11-09 逐 2.5 ms 实测（dossier_67 #20）：S16 w '
                                           '7.340–7.370s：treatment. 句末 /t/ 除阻（除阻加强处，词 6.893–7.418 内）；词尾塞音除阻',
                                     '实测': {'最响dB': -42.0, '重心Hz': 2665, '周期': 0.15, '低频dB': -10.6}},
                  '140.21–140.30s': {'配音指纹': 'c34294a522a7',
                                     '依据': '2026-11-09 逐 2.5 ms 实测（dossier_67 #21）：S18 w '
                                           '3.465–3.555s：recreation, 的 /ʃən/ 鼻音收尾（低频 -2.9 dB、周期 0.25，词 '
                                           '2.727–3.973 内）；词尾',
                                     '实测': {'最响dB': -35.2, '重心Hz': 1706, '周期': 0.25, '低频dB': -2.9}},
                  '141.00–141.03s': {'配音指纹': 'c34294a522a7',
                                     '依据': '2026-11-09 逐 2.5 ms 实测（dossier_67 #22）：S18 w 4.050–4.075s：the 的 '
                                           '/ð/ 浊擦起音（低频 -1.2 dB，紧接 4.080 的 ðɪ）；词头的一部分',
                                     '实测': {'最响dB': -31.0, '重心Hz': 4760, '周期': 0.28, '低频dB': -1.2}},
                  '144.17–144.26s': {'配音指纹': 'c34294a522a7',
                                     '依据': '2026-11-09 逐 2.5 ms 实测（dossier_67 #23）：S18 w 7.215–7.310s：them. 句末 '
                                           '/m/ 鼻音收尾（周期 0.31、低频 -6.2 dB，词 7.022–7.364 内）；词尾',
                                     '实测': {'最响dB': -36.3, '重心Hz': 1591, '周期': 0.31, '低频dB': -6.2}},
                  '14.65–14.73s': {'配音指纹': 'c34294a522a7',
                                   '依据': '2026-11-10 逐 10 ms 实测（dossier_67 #1）：S1 w 11.455–11.535s，句末 tree. 的 '
                                         '/iː/ 元音收尾气化（词 11.137–11.595 内，-29→-57 dB 连续衰减、周期 0.2–0.5、低频 -3～-10 '
                                         'dB）；词尾。K134 把 S1 第5段补响后才被报出',
                                   '实测': {'最响dB': -36.5, '重心Hz': 3714, '周期': 0.25, '低频dB': -3.0}},
                  '14.69–14.70s': {'配音指纹': 'c34294a522a7',
                                   '依据': '2026-11-10 逐 10 ms 实测（dossier_67 #2）：S1 w 11.49–11.50s，同上 tree. 的 '
                                         '/iː/ 收尾气化里的一帧（词内）；词尾',
                                   '实测': {'最响dB': -43.6, '重心Hz': 4640, '周期': 0.0, '低频dB': -2.6}}},
          '词尾辅音': {'S8 句末': {'除阻全频': -28.9,
                             '依据': '2026-11-09 主会话按守则22 实测核实：闭塞 6.215–6.29 -60～-70 dB，除阻 6.295–6.35 最响 -28.9 '
                                   'dB、比闭塞高约 30 dB、60 ms、重心 1.3–2.4 kHz，是 /k/ 的除阻'}},
          '删除段': {'S1 raw 7.5600-7.9812': {'类型': '紧贴词头的非人声',
                                           '配音指纹': 'c34294a522a7',
                                           '依据': "2026-11-09 删除段对应 非人声区间 S1 [7.73, 7.971167, '紧贴词头']：自动切点.py "
                                                 '实测是吸气声（重心 1.8–3.8 kHz、低频 < -10 dB、周期 < 0.35），与 when 的词头之间没有 '
                                                 '-55 dB 低谷，只能紧贴词头在过零点切；post 侧 -50.6 dB 是 when 的 /w/ 浊音前导'},
                  'S4 raw 1.0147-1.2350': {'类型': '紧贴词尾的非人声',
                                           '配音指纹': 'c34294a522a7',
                                           '依据': '2026-11-09 逐 2.5 ms 实测（S4 w）：said 的 /d/ 浊音杠到 '
                                                 '0.990，0.9947–1.19 弱气声（-50～-58 dB、重心 1.0–2.5 '
                                                 'kHz）按非人声区间紧贴词尾在过零点删；pre 侧 -49 dB 是 /d/ 浊音的衰减尾'},
                  'S6 raw 2.3501-2.7600': "2026-11-09 删除段对应 非人声区间 S6 [2.475, 2.743625, '紧贴词头']：hole, "
                                          '停顿里的吸气声（自动切点.py 实测重心 1.8–3.8 kHz、低频 < -10 dB），删掉部分最响 -38.7 dB '
                                          '是吸气本身，不是词；两侧 -57/-55.6 dB 已衰减',
                  'S9 raw 8.8250-9.1150': {'类型': '紧贴词尾的非人声',
                                           '配音指纹': 'c34294a522a7',
                                           '依据': '2026-11-09 逐 2.5 ms 实测（S9 w）：ancestors 的 /z/ 擦音衰减到 8.81（-60 '
                                                 'dB 低谷），8.8125–8.8175 是吸气开头的一下（-41.9 dB、重心 3.5 kHz），之后 '
                                                 '-43～-55 dB 吸气，和 /z/ 隔着 -60 dB 低谷；复核报“词尾被切 5 ms”切到的是吸气开头，不是 '
                                                 '/z/'},
                  'S10 raw 2.0650-2.3534': "2026-11-09 删除段对应 非人声区间 S10 [2.06, 2.343417, '紧贴词头']：stags "
                                           '后停顿里的吸气声（自动切点.py 实测），删掉部分最响 -38.9 dB 是吸气本身，两侧 -58.7/-57.8 dB 已衰减',
                  'S12 raw 4.8950-5.3270': {'类型': '紧贴词头的非人声',
                                            '配音指纹': 'c34294a522a7',
                                            '依据': "2026-11-09 删除段对应 非人声区间 S12 [5.055, 5.277, '紧贴词头']：1948, "
                                                  '后停顿里的吸气（自动切点.py 实测），删掉部分最响 -36.0 dB 是吸气；与 and 的浊音起音之间没有 -55 '
                                                  'dB 低谷，紧贴词头在过零点切，post 侧 -50.8 dB 是 and 的浊音前导（dossier_67 #10 '
                                                  '已实测）'},
                  'S13 raw 5.5650-5.9800': '2026-11-09 删除段对应 非人声区间 S13 [5.76, 5.98]：contaminants, '
                                           '后停顿里的吸气声（自动切点.py 实测），删掉部分最响 -38.0 dB 是吸气，两侧 -57.0/-57.8 dB 已衰减',
                  'S15 raw 4.5400-4.9886': {'类型': '紧贴词头的非人声',
                                            '配音指纹': 'c34294a522a7',
                                            '依据': "2026-11-09 删除段对应 非人声区间 S15 [4.72, 4.988708, '紧贴词头']：1979, "
                                                  '后停顿里的吸气（自动切点.py 实测），删掉部分最响 -38.7 dB 是吸气；与 and 的浊音起音之间没有 -55 '
                                                  'dB 低谷，紧贴词头在过零点切，post 侧 -50.9 dB 是 and 的浊音前导'},
                  'S15 raw 9.1750-9.5150': '2026-11-09 删除段对应 非人声区间 S15 [9.195, 9.43]：facsimile, '
                                           '后停顿里的吸气声（自动切点.py 实测），删掉部分最响 -38.9 dB 是吸气，两侧 -57.8/-63.7 dB 已衰减',
                  'S16 raw 4.1950-4.5936': {'类型': '紧贴词头的非人声',
                                            '配音指纹': 'c34294a522a7',
                                            '依据': '2026-11-09 删除段对应 非人声区间 S16 [4.315, 4.523625, '
                                                  "'紧贴词头']：outbreak, 后停顿里的吸气（自动切点.py 实测），删掉部分最响 -38.7 dB 是吸气；与 "
                                                  'and 的浊音起音（dossier_67 #19，低频 -0.3 dB）之间没有 -55 dB '
                                                  '低谷，紧贴词头在过零点切，复核报“词头被切 5 ms”是过零点到起音之间的吸气尾'},
                  'S15 raw 4.5400-4.9887': {'类型': '紧贴词头的非人声',
                                            '配音指纹': 'c34294a522a7',
                                            '依据': "2026-11-09 删除段对应 非人声区间 S15 [4.72, 4.988708, '紧贴词头']：1979, "
                                                  '后停顿里的吸气（自动切点.py 实测），删掉部分最响 -38.7 dB 是吸气；与 and 的浊音起音之间没有 -55 '
                                                  'dB 低谷，紧贴词头在过零点切，post 侧 -50.9 dB 是 and 的浊音前导'},
                  'S1 raw 1.2900-1.4649': {'类型': '紧贴词尾的非人声',
                                           '配音指纹': 'c34294a522a7',
                                           '依据': '2026-11-10 Ravidat, 后标点停顿：Ravidat（ɹˌævidˈɑː，词尾元音，t '
                                                 '不发音）的元音衰减尾巴，被 S1 第1段段内渐变 0→+6 dB（主会话按守则22 '
                                                 '定，用户“上来直接就名字，就直接声音就变小了”）在段尾抬高，停顿前 -50.5 dB；删掉的部分最响 -50.1 '
                                                 'dB，是停顿静音，不是词'}},
          '机器复听': {'S1': {'配音指纹': 'c34294a522a7',
                          '依据': '2026-11-09：Robot 按法语狗名读 ɹoʊbˈoʊ（读音改正表），两路识别器拼成 robeau，正是 roh-BOH；Ravidat 按法语读 '
                                'ɹˌævidˈɑː（词尾 t 不发音），识别器拼成 ravidas/ravida；读音按脚本，非读错'},
                   'S3': {'配音指纹': 'c34294a522a7',
                          '依据': '2026-11-09：Ravidat 读 ɹˌævidˈɑː（词尾 t 不发音），识别器拼成 ravidah/ravida；读音按脚本，非读错'},
                   'S4': {'配音指纹': 'c34294a522a7',
                          '依据': '2026-11-09：Robot 读 ɹoʊbˈoʊ（法语狗名），small.en 拼成 robeau；读音按脚本，非读错'},
                   'S6': {'配音指纹': 'c34294a522a7',
                          '依据': '2026-11-09：only nosed about：nosed 的 /zd/ 与 about 的 /ə/ 连读，small.en 听成 '
                                "knows；the boys' own：boys' 的 /z/ 与 own 连读，small.en 拼成 bar's；parakeet "
                                '两个词都听对；读音按脚本，非读错'},
                   'S15': {'配音指纹': 'c34294a522a7',
                           '依据': '2026-11-09：Lascaux II 按主会话规则读 Lascaux two，small.en 写成“lasko 2”（Lascaux 读 '
                                 'læskˈoʊ、II 读 two）；读音按脚本，非读错'},
                   'S17': {'配音指纹': 'c34294a522a7',
                           '依据': '2026-11-09：Lascaux IV 读 Lascaux four，parakeet 写成“lasko 4”，small.en 把 Lascaux '
                                 "拼成 let's go；读音按脚本，非读错"}},
          '高亮': {'S13 第2块': {'开始读': 96.42,
                             '配音指纹': 'c34294a522a7',
                             '依据': '2026-11-09 直接读 work_67/a.wav 逐 10 ms：dioxide 的 /d/ 到 96.37，96.385–96.415 '
                                   '数字静音，96.42 起 and 的元音（-59.5→-19.5 dB）；开始读 96.42，高亮 96.41 差 0.01 s；办法甲 96.24 '
                                   '落在 dioxide 里'}},
          '数字': {'S9-1 17,000': 'between 17,000 and 22,000 years ago 中文“1.7万至2.2万年之前”，17,000 = 1.7万，读法 '
                                'seventeen thousand',
                 'S9-1 22,000': '22,000 = 2.2万，读法 twenty-two thousand'},
          '牛津逗号': {'S14 closed to the public, followed by restoration and': '不是三项并列：closed to the public '
                                                                            '是主句谓语，followed by restoration and '
                                                                            'daily inspection '
                                                                            '是分词短语，restoration 和 daily '
                                                                            'inspection 只有两项'},
          '词性': {'S1-2 woodland 林地': '林地是名词（树林地带），“地”不是副词标记，与速查表 n. 一致'},
          '短语': {'S3 embroidered … with': '不是搭配：with a dramatic twist 引出添加的内容，embroider 单独就是“添油加醋”，说明里已写 '
                                          'embroider A with B',
                 'S9 in … antiquity': '不是搭配：lived in antiquity 里 in 引出时间（生活在古时代），antiquity 单独就是“古时代”，用户 '
                                      '2026-11-10 改稿只标 antiquity',
                 'S10 depicted … in': '不是搭配：in pigments 表示用什么颜料，depict 单独就是“描绘”',
                 'S10 depicted … on': '不是搭配：on the murals 表示画在哪里，和 depicted 无关',
                 'S10 in … pigments': '不是搭配：in pigments 表示“用颜料”，pigment 单独就是“颜料”',
                 'S10 pigments … on': '不是搭配：on 属于 on the murals，和 pigments 无关',
                 'S12 influx … of': '不是搭配：of 引出涌入的是什么（游客），influx 单独就是“涌入”',
                 'S14 by … restoration': '不是搭配：by 属于 followed by，restoration 单独就是“修复”',
                 'S18 inaccessible … to': '不是搭配：to them 表示对谁来说，inaccessible 单独就是“无法进入的”'}},
 '结尾解说': '简述',
 'allow_clash': ['carbon dioxide', 'companion', 'cover'],
 '高亮按实际开口': True,
 '高亮开口门槛': 40,
 '术语': {'Marcel Ravidat': '马塞尔·拉维达',
        'Ravidat': '拉维达',
        'Montignac': '蒙蒂尼亚克',
        'Robot': '罗伯特',
        'Lascaux': '拉斯科',
        'UNESCO': '联合国教科文组织',
        'World Heritage List': '世界遗产名录',
        'Lascaux II': '拉斯科二号',
        'Lascaux IV': '拉斯科四号'},
 '停顿插入点': {'S4': {'1': [0.64375, '交界']}, 'S10': {'2': [1.272292, '交界']}, 'S13': {'2': [4.566583, '交界']}},
 '非人声区间': {'S1': [[2.08, 2.345708, '紧贴词头'], [7.73, 7.971167, '紧贴词头']],
           'S6': [[2.475, 2.743625, '紧贴词头']],
           'S8': [[2.525, 2.825]],
           'S9': [[7.01, 7.19], [8.815, 9.07]],
           'S10': [[2.06, 2.343417, '紧贴词头']],
           'S12': [[5.055, 5.277, '紧贴词头']],
           'S13': [[5.76, 5.98]],
           'S15': [[4.72, 4.988708, '紧贴词头'], [9.195, 9.43]],
           'S16': [[4.315, 4.523625, '紧贴词头']],
           'S2': [[2.365, 2.605], [6.815, 6.905375, '紧贴词头']],
           'S4': [[0.994667, 1.19, '紧贴词尾']]},
 '分段增益dB': {'S7': {'1': -1.5, '2': 1.5},
            'S9': {'4': 2.5, '3': 1.9},
            'S4': {'3': 1.5, '2': 1.5},
            'S1': {'1': -2.5, '2': -2.0, '4': 2.0}},
 '换行变更已获同意': {'S1': '用户 2026-11-10 Word 文档 67.docx 原话：“这块的翻译改为：正在和Robot 在蒙迪尼亚克附近的林地里散步。his canine companion. '
                    'Robot 是他 犬类的小伙伴。”“翻译不准，上面的翻译不准改成下面这个翻译。这个时候 罗伯特在一棵倒下的树 留下的 (地面)凹陷处  嗅来嗅去。”（S1 '
                    '译文整句换掉，换行随之变）'},
 '重点词颜色': {'woodland': '#F87171',
           'stroll': '#BEF264',
           'canine': '#38BDF8',
           'companion': '#E879F9',
           'sniffing': '#FBBF24',
           'hollow': '#A78BFA',
           'toppled': '#4ADE80'},
 '段内渐变dB': {'S1': {'1': [0.0, 6.0]}},
 '结尾句': {'S18': {'前段语速': 0.9,
                 '最后一段语速': 0.78,
                 '最后一段前停顿': 0.7,
                 '接点': [97980, 122340],
                 '依据': '全篇结尾句按 07 定下的标准（用户 2026-10-10 同意并要求所有视频统一）：前段 0.9、最后一段“the originals being '
                       'inaccessible to them.” 0.78、前面停 0.7 秒。接点由 结尾句接点.py 自动找：0.9 那遍最后一个标点后最长静音（40 ms）的正中 '
                       '4.082 s，0.78 那遍（110 ms）的正中 5.098 s，所在帧和两侧各 5 ms 都低于 -55 dB（程序以 08 '
                       '校准：与人工核实的接点落在同一段静音里）'}},
 '词尾除阻': {'S14': {'1': [3.195, 'k']}},
 '除阻加强': {'S12': {'1': [4.79, 4.84, 6.0]}, 'S13': {'1': [3.44, 3.505, 6.0]}, 'S16': {'句末': [7.34, 7.37, 6.0]}},
 '区间声音指纹': {'S1': '55427a4f0ea4',
            'S2': '230e898e282f',
            'S4': 'f8db5e43a1a6',
            'S6': '5e89f3590345',
            'S8': '89167c2de3a5',
            'S9': 'c939467b2f91',
            'S10': 'd8bf394386ca',
            'S12': 'a351ec08bef7',
            'S13': '3fc04558cc41',
            'S14': '2c5ab703bd20',
            'S15': '75d2fb6fdbbd',
            'S16': '2fbacc429325'},
 '换行变更记录': [{'日期': '2026-11-10',
             'S1': '用户 2026-11-10 Word 文档 67.docx 原话：“这块的翻译改为：正在和Robot 在蒙迪尼亚克附近的林地里散步。his canine companion. '
                   'Robot 是他 犬类的小伙伴。”“翻译不准，上面的翻译不准改成下面这个翻译。这个时候 罗伯特在一棵倒下的树 留下的 (地面)凹陷处  嗅来嗅去。”（S1 '
                   '译文整句换掉，换行随之变）'}]}

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 核对 import 生成并核对
生成并核对(S, out)
