# 第40篇 · 总编辑约稿单

> 致：母语作者、剑桥毕业生、报社撰稿人；语言学家 ｜ 总编辑 ｜ 2026-10-02
> **用户要求（反复强调）：尽全力写到最好。** 开头抓人、悬念、两手棋的对称是全文骨架；零夸张；交稿前逐句自审三遍，对照第 4、5、8 节。
> 事实只取第 3 节；材料：`rewrite/40/src/sources_excerpts.md`（S1–S6，检索摘要，**不得直接引用原文**）。
> 人名：Lee Sedol（a South Korean Go master / one of the game's greatest players）必写；AlphaGo 必写；DeepMind 可写（Google's DeepMind）；樊麾、李昌镐、David Silver 不写名（可写 the European champion）。**直接引语：0**（"creative and beautiful""God's touch""cannot be defeated"一律改写为间接叙述，不加引号）。
> **选词：优先用第 7 节"已测可用"（按段分组）；任何其他词写进稿子之前先用 `bash $S/wt.sh 词1 词2…` 测**（输出 OK/OCC/BAD/TRI，OK 才可加粗）。自检 `quality/en_check.py`；合稿后 `quality/draft_check.py`。**准确地道优先；重点词下限 50，目标 54。**

## 0 摘要
围棋局面数比宇宙原子还多，长期被视为 AI 难以攻克 → 2015 年 10 月 AlphaGo 5:0 胜欧洲冠军，首次不让子胜职业棋手 → 2016 年 3 月首尔五番棋，对手李世石（18 个国际冠军）→ 3 月 10 日第二局第 37 手：第五线肩冲，解说觉得奇怪、有人以为是失误；李世石离开对局室十余分钟；AlphaGo 自己估算人类下这一手的概率仅万分之一；李世石后来称它有创造性、很美 → AlphaGo 先学强业余棋手对局，再自我对弈数千万盘 → 3 月 13 日第四局李世石第 78 手被誉为"神之一手"，AlphaGo 估算人类下出的概率同样约万分之一，李世石赢下唯一一局 → 总比分 4:1 → 2019 年 11 月李世石退役，称 AI 已无法被击败。
- **论点/骨架**：两手各"万分之一"的棋——机器下出了人类想不到的一手，人类也下出了机器没算到的一手。
- **规格**：5 段，**252–268 词**（上限 271），**重点词 54（下限 50），每段 ≥10，专名不加粗**。英式拼写。

## 标题
**Move 37** ／ **《第37手》**。标题词 move（同族 moves/moved）与 37 不得进结尾。注意正文可写 move 37、move 78，但**结尾句不得出现 move**。

## 2 分段
| 段 | 内容 | 词数 |
|---|---|---|
| P1 背景 | 围棋之难（局面数>原子）；October 2015 胜欧洲冠军；March 2016 首尔对李世石、18 个国际冠军（T1–T3） | 50–56 |
| P2 第37手 | 10 March 2016 第二局；第五线肩冲；解说称怪、疑为失误；李世石离席十余分钟（T4） | 50–56 |
| P3 万分之一 | AlphaGo 估算人类下此手概率万分之一；它如何学：业余对局→自我对弈数千万盘；李后来称其有创造性、美（间接）（T5–T6） | 50–56 |
| P4 第78手 | 13 March 2016 第四局；李世石第 78 手被誉为神之一手；机器同样估算约万分之一；唯一一胜；总比分 4:1（T7） | 50–56 |
| P5 退役·收束 | November 2019 退役，称 AI 无法被击败（间接）；结尾（T8） | 44–52 |

## 3 核准史实表
| # | 可写（措辞上限） | 状态 |
|---|---|---|
| T1★ | Go is said to allow more possible positions than there are atoms in the universe | ✓ S6（写 is said to / reportedly，一处对冲） |
| T2★ | in October 2015 AlphaGo, built by Google's DeepMind, beat the European champion 5–0, the first time a program had beaten a professional on a full board without a handicap | ✓ S1 |
| T3★ | in March 2016, in Seoul, it played a five-game match against Lee Sedol, a South Korean master with 18 international titles | ✓ S2 |
| T4★ | in the second game, on 10 March 2016, AlphaGo's 37th move was a shoulder hit on the fifth line; commentators called it very strange, and one thought it a mistake; Lee left the room and took more than ten minutes to reply | ✓ S3（离席时长各说不一：**写 more than ten minutes / some minutes**，不写 15） |
| T5★ | AlphaGo had estimated the chance of a human playing that move at one in 10,000; Lee later described it as creative and beautiful | ✓ S3（间接叙述，不加引号） |
| T6★ | AlphaGo first learned from games by strong amateurs online, then played tens of millions of games against itself | ✓ S1 |
| T7★ | in the fourth game, on 13 March 2016, Lee's 78th move turned the game; many professionals called it a divine move; DeepMind said a human professional would play it with a probability of about one in 10,000; it gave Lee his only win; AlphaGo won the match 4–1 | ✓ S4（"概率"写法：the team estimated…；不写"AlphaGo 因此崩溃"之类细节） |
| T8★ | in November 2019 Lee retired, saying that AI had become an entity that could not be defeated | ✓ S5（间接叙述） |
| ✗ | 直接引语；李世石离席确切分钟；奖金与捐款（未核）；AlphaGo 第四局"崩溃"细节；李昌镐；AlphaGo Zero 等后续 | drop |

## 4 禁区
1. 不渲染"人类被机器打败的悲情"；不鸡汤；两手棋对称呈现即可。
2. "万分之一"两处都要说明是**谁估算的**（AlphaGo 自己 / DeepMind 团队）。
3. 对冲每句至多一个。
4. 无引语、无问号叹号、无 &、句首无阿拉伯数字；5–0、4–1 用 en dash 或写 five games to nil / four games to one。

## 5 结尾
1. ≤26 词；不新增事实；不含 move / 37；不鸡汤、不下判决。
2. **不得与 05–39 同构**：39 *Inky, somewhere beyond the pipe, remained wholly oblivious to the debate*（专名 + 插入状语 + remained + 副词 + 形容词 + to the + 名词）；38 *The discoverer's ashes swept past the heart that bears his name*；37 *The legend had left him conspicuously unharmed*；36 *Alice's appetite was evidently shared by millions*；35 *The stigma of … had persisted for … beyond his lifetime*；34 *If so, its fame began with*；33 *The boy who had seemed to … would, decades later*；32 *The test's first beneficiary had been a … who had*；31 *had spent … at the helm*；30 *That pronouncement came almost N years after*；29 *never + 过去式*；28 *retain*；27 *lay in / The essence of*；26 *The country that*；25 *once + 过去分词 + have prompted*；24 *all along*；23 *now + 及物动词 + into*。另禁：时间状语开头、What 开头、最高级、问句、冒号、分号、破折号、may/might、evidently、had left、never、remained、oblivious、swept、that bears。
3. **建议**：用"第 78 手"收——李世石那一手仍是人类在五局里唯一的胜利 / 机器至今没有再输给他。主语可用 **his 78th / that single win / the one game he won / Lee's reply**，须避开 move 一词（可写 his 78th stone / that stone）。

## 6 文风
句长 ≤32；英式拼写；时间：October 2015、March 2016、10 March 2016、13 March 2016、November 2019。

## 7 总编辑已测（2026-10-02，按段分组）
- **P1 背景**：showdown, televised, broadcast, stakes, algorithm, handicap, milestone, opponent, computational, processor, supremacy, dominance, superior, heritage, viewers, atoms, configurations, countless, territory, grid, intersections, strategist
- **P2 第37手**：bizarre, unconventional, unorthodox, stunned, deliberated, pondered, eccentric, unexpected, orthodox, deviate, deviation, defy, defied, foresee, anticipate, scenario, contemplate, awe
- **P3 万分之一**：probability, odds, imitate, mimic, rehearse, simulated, intuition, neural, iterations, reinforcement, self-taught, wager, predecessor, fallible
- **P4 第78手**：wedge, comeback, redemption, confused, consolation, unanswered, unbeaten, triumphant, applause, dignity, graceful, resilience
- **P5 退役**：invincible, entity, humility, inspire, mentor, withdraw, farewell, reflection
- **已占（不可加粗）**：contest, spectators, artificial, unprecedented, contender, baffled, blunder, puzzled, startled, resumed, elegant, hasty, imitation, calculation, combinations, exhaustive, vast, faltered, resigned, sole, solitary, triumph, erratic, retirement, abandoned, legacy, reshaped, rethink, conventional, humbled, concede(d), legendary, glitch, commentators, formidable, prowess, synthetic, sequence, evaluate, assess, baffling, astonish, dazzling, convention, spectacle, obsolete, flawed, overturned, verdict, hindsight, anomaly, successor, prevailed, lone
- **基础/冷僻**：board, ancient, grandmaster, champion, professional, prodigy, titles, creative, shoulder, dismissed, misjudgement, dataset, permutations, network, counterattack, brilliancy, gambit, victory, retired, insurmountable, pupil, tutor, poignant, bittersweet, encircle, stones, adversary, awestruck, dogma, centuries, millennia, jubilant, relinquish, renounce, infallible, frailty, outlandish, revealing, outplayed
- △：audience, programme, decade, universe, defeat, quit

## 8 课程清单（必查）
- [ ] 结尾修辞先过事实逻辑（第 39 篇教训：反讽必须真成立）
- [ ] 两个"万分之一"写清估算者；离席时长不写死
- [ ] 代词：it 指 AlphaGo 还是 the move 须清楚；不跨段
- [ ] 不为凑词牺牲准确；新词先测后写
- [ ] 专名不加粗
