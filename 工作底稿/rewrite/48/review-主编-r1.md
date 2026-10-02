# 第 48 篇评审 · 英文总编辑 · 第 1 轮

## 总分：96 / 100（无硬伤）

| 项 | 满分 | 得分 |
|---|---|---|
| 1 史实准确 | 15 | 13.5 |
| 2 论证与结构 | 10 | 9.5 |
| 3 语言质量 | 15 | 13.5 |
| 4 适配读者 | 5 | 5 |
| 5 学习价值 | 12 | 12 |
| 6 用法典型 | 8 | 8 |
| 7 速查表释义 | 10 | 10 |
| 8 忠实 | 10 | 10 |
| 9 通顺地道 | 10 | 9.5 |
| 10 重点词对应 | 5 | 5 |

## 机检（英文单独抽出，逐行读，未过滤）
`en_check.py`：段落词数 [49, 54, 61, 60, 46]，合计 270 ✓；候选 51 个全部 ✓；**无“已被占用”行** ✓；各段加粗 11/10/10/10/10 ✓。
`wt.sh` 实测：OK sentiment、equipped；OCC verdict、publicity、outfitted；BAD popular、opinion、wishes、campaign、carriageways、roads。

## 逐句史实核对（对照约稿单 §3 与 S1–S6）
- P1：1955 年公投约 83% 要保留靠左 ✓；1963-05-10 议会批准 1967 年起改右 ✓。**whose resistance had made the plan unpopular**：“抵制”无来源，且“抵制使计划不得人心”是循环论证（问题 1）。
- P2：挪威、芬兰靠右、每年约 500 万车次过境 ✓；约 90% 左舵车、窄双车道超车致迎面相撞 ✓。“孤立、不便”是由过境量推出的合理概括 ✓。**highways** 指窄路：英式 highway 指主干公路，与 narrow two-lane 搭配略矛盾（问题 4）。
- P3：国家委员会、H 加箭头标志 ✓；电视歌曲比赛、劝人靠右、排行榜第五 ✓；约 36 万块路牌 ✓；千余辆右侧开门新公交 ✓。
  - **propaganda**：中性语境（政府公众宣传）在英国史语境下可用，但现代读者多读出贬义；与正文中立语气略不合（问题 4）。
  - **a massive fleet … was procured with right-hand doors**：with right-hand doors 挂在 procured 后，读成“用右侧车门采购”，修饰错位（问题 3）。
- P4：1967-09-03 星期日 ✓；1–6 点禁非必要车辆、4:50 全停换边、5:00 再走 ✓；**crawled** across：来源为“小心换边”，crawled（缓慢挪动）是合理润色 ✓；before dawn ✓（斯德哥尔摩 9 月初日出约 6 点）；斯德哥尔摩、马尔默周六上午至周日下午封闭改路口 ✓。flipped roads 略俏皮，可接受。
- P5：随后周一 125 起 vs 此前 130–198 ✓；归因于谨慎驾驶（put down to，带归属）✓；1969 年事故率与死亡率回到改前水平 ✓。**But the nervousness subsided, prudent habits faded**：前两分句是对 S5 的推断，被写成事实（问题 2）。冰岛未写，可接受。

## 结尾
- 原文：But the **nervousness** **subsided**, **prudent** **habits** **faded**, and by 1969 accident and fatality rates had **reverted** to their **baseline**.
- 协调人拟改：The **nervousness** apparently **subsided** and **prudent** **habits** **faded**, for by 1969 accident and fatality rates had **reverted** to their **baseline**.
- **评估：同意，这是最佳方案。** apparently 一处对冲，作用于并列谓语 subsided and faded，标明这两点是推断；for 引出依据（1969 年回到原水平，S5），逻辑方向正确（由结果推原因，并明示是推断）；与上句 put down to the heightened care 前后呼应，论点“小心会褪去”由事实撑住 ✓。
- §5：≤26 ✓；无 night／Sweden／Swedish／switch／side(s) ✓；The nervousness 开头，非时间状语／What／Yet／Every／Behind ✓；无 still、never、remained、had left、came from、may／might、冒号分号破折号、最高级 ✓。
- 同构：47 为“地点状语 + 物主名词 + plainly testifies to”，46 为“X went, on …, to a … still convinced …”，45 为“had begun on …, exactly a year before …”，44 为“had hidden …, so they could not …”；本句为“名词 + apparently + 并列谓语, for + 时间 + 过去完成时”，均不同构 ✓。
- 实测：P5 47 词、全篇 270、加粗不变 ✓。

## 逐条问题

**1.（必改）第 1 项 −1；第 2 项 −0.5**
- 原文：…approving right-hand traffic from 1967 in **defiance** of a **populace** whose **resistance** had made the plan **unpopular**.
- 问题：“抵制”无来源；“抵制使其不得人心”循环。
- **最佳措辞**：…approving right-hand traffic from 1967 in **defiance** of a **populace** among whom the plan was **unpopular**.（12 → 11 词，−1；去掉 resistance，P1 加粗 11→10 ✓；unpopular 由上句 83% 直接支持，不循环）
- 备选（若嫌与 overruled the electorate 重复）：…approving right-hand traffic from 1967 in **defiance** of public **sentiment**.（−7 词；sentiment ✓ OK；但 P1 加粗降为 9，须另补一词，不推荐）
- 中文：……批准从1967年起改为靠右行驶，**不顾**(defiance)这一计划在**民众**(populace)中**不得人心**(unpopular)。

**2.（必改）第 1 项 −0.5**：结尾采用协调人方案（见上），0 词（实测 P5 46→47，因 But/and 与 apparently/for 计数差 1；全篇仍 270）。

**3.（该改）第 3 项 −0.5**
- 原文：…and a **massive** **fleet** of over 1,000 new buses was **procured** with right-hand doors.
- 改法：…and a **massive** **fleet** of over 1,000 new buses with right-hand doors was **procured**.（0 词）

**4.（可改）第 3 项 −1（两处）**
- **propaganda**：带贬义色彩，替换词 campaign 为基础词、publicity 已占用，保留；中文译“宣传”已中和。
- narrow two-**lane** **highways**：英式 highway 多指干道；roads／carriageways 不可加粗，保留。

**5.（该改）第 9 项 −0.5**：P1 中文“这是不顾民众的抵制，而这种抵制已让这一计划不得人心”随问题 1 改写（见上）。

**已实测 1+2+3**：270 词，段落 [48, 54, 61, 60, 47]，加粗 50，无占用行，各段 10 ✓

## 达标判断
≥95、零硬伤，按我这一票通过；**问题 1、2 必须改**。改完 1–3、5 预计 99。

会签：同意定稿（以落实必改 1、2 为条件）

总分 = 各项之和 已核（13.5+9.5+13.5+5+12+8+10+10+9.5+5 = 96）
