# 第 44 篇评审 · 英文总编辑 · 第 1 轮

## 总分：96.5 / 100（无硬伤）

| 项 | 满分 | 得分 |
|---|---|---|
| 1 史实准确 | 15 | 15 |
| 2 论证与结构 | 10 | 8.5 |
| 3 语言质量 | 15 | 13.5 |
| 4 适配读者 | 5 | 5 |
| 5 学习价值 | 12 | 12 |
| 6 用法典型 | 8 | 8 |
| 7 速查表释义 | 10 | 10 |
| 8 忠实 | 10 | 10 |
| 9 通顺地道 | 10 | 9.5 |
| 10 重点词对应 | 5 | 5 |

## 机检（英文单独抽出，逐行读，未过滤）
`en_check.py`：段落词数 [44, 58, 63, 52, 54]，合计 271 ✓（零余量）；候选 52 个全部 ✓；**无“已被占用”行** ✓；各段加粗 10/10/12/10/10 ✓。
`wt.sh` 实测：OK quantify、grasp、ardent、thorough、U-turn；OCC gauge、register、detect、devoted、cherished、reversal、painstaking、meticulous、exhaustive；BAD fathom、weigh、staunch、treasured；△ appreciate。

## 史实核对（对照任务书 §3 与 S1–S6）
- 百事挑战：全美购物中心摊位、两杯不标品牌、说出偏好、各地不一、一般更常选百事 ✓（无份额数字）
- 近 20 万次盲测、更甜配方一贯胜出 ✓；1985-04-23 宣布替换 99 年配方、公众称新可乐 ✓；a year short of its centenary（1886 → 1985）为推算，成立 ✓
- 热线约 400 → 约 1,500、几乎全是投诉 ✓；抗议团体、囤货 ✓；1985 年 6 月马林斯诉讼、一周后驳回 ✓（class-action 省略可接受）
- 百事 CEO 放假、视为认输（concession）✓；1985-07-11、79 天、Classic ✓；ABC 打断肥皂剧、两大电视网新闻头条 ✓
- 无阴谋论、无回归后销量、无高管姓名、无引语 ✓

## 协调人点名三处

### 一、P1／P5 评述是否越出来源
- P1 Each stall doubled as **publicity**, letting **consumers** judge by **palate** alone.：百事挑战本是营销活动，“兼作宣传”是常识性定性；“只凭味觉判断”正是盲测的定义（S2 不标品牌）。不越界 ✓。
- P2 the **concoction** was **risky**：事后评价，但下文反弹即其证据，属评述，可接受（见问题 4）。
- P5 Coca-Cola had **misjudged** what the tests measured. They captured a single **mouthful**, not the **emotional** **attachment** …：任务书禁区 2 允许在末段以评述呈现，未说成研究结论 ✓；nearly a century（99 年）✓；To many, the old taste carried **nostalgia** ✓ 有限定。
- **问题在结尾**，见下。

### 二、结尾修辞（必改）
原文：The tests had hidden the label from every taster, and the label was what **loyal** drinkers fought **fiercely** to defend.
- 前半句成立：盲测遮住品牌 ✓。
- **后半句不成立**：新可乐照样印着 Coca-Cola 的名字和标签，标签从未被拿走；抗议者争的是**原配方那瓶饮料**（S3 囤积原版、S6 原配方回归），马林斯的诉讼针对的是新可乐**沿用原版样式包装**（S4）——他们反而是反对把这个标签给新可乐。“人们拼命捍卫的是标签”与事实相反，反讽落空。（任务书 §5.4 的建议本身也有此漏洞。）
- 见问题 1 改法。

### 三、对冲与跨段代词
- 对冲：Figures varied by region, but tasters generally… ✓；about 400／about 1,500 同句两处 about 属数字约数，非两个对冲词叠加观点，可接受 ✓。
- 代词：P2 Its sweetness（承 New Coke）✓；P3 Its dismissal（承 lawsuit）✓；P5 They captured（承 the tests）✓；无跨段代词 ✓。

## 逐条问题

**1.（必改）第 2 项 −1.5**
- 原文：The tests had hidden the label from every taster, and the label was what **loyal** drinkers fought **fiercely** to defend.
- 改法：The tests had hidden the brand from every taster, so they could not **quantify** what it meant to **loyal** drinkers.（20 → 20 词，0；quantify ✓ OK 未占用，替 fiercely，P5 加粗仍 10）
- 事实：盲测设计上就不显示品牌 ✓；品牌对忠实饮用者意味着什么，正由正文的热线、抗议、回归来体现 ✓；与 P5 首句“误判测试衡量的是什么”一脉相承 ✓；it 指 the brand，无歧义 ✓
- §5：≤26 ✓；无 79／days／new／New Coke ✓；The tests 主语（建议之一），非时间状语／What／Yet／Every 开头 ✓；无 never（用 could not）、while … has none、still carries 等 ✓；无冒号分号破折号、最高级 ✓；不新增事实 ✓
- 速查表：删 fiercely，增 quantify | v. 量化，用数量表示（quantify the risks/benefits） | 5
- 中文：测试对每位品尝者都遮住了品牌，所以无法**量化**(quantify)这个品牌对**忠诚**(loyal)饮用者意味着什么。

**2.（该改）第 3 项 −0.5**
- 原文：Coca-Cola's own testing was **deliberate**.
- 问题：deliberate 指“故意的／从容的”，形容测试“周密”不典型。
- 改法：Coca-Cola's own testing was **thorough**.（0 词；thorough ✓ OK）；中文“则十分**周密**(thorough)”

**3.（该改）第 3 项 −0.5**
- 原文：The **u-turn** was a vindication…
- 问题：拼写应为 U-turn（大写 U）。
- 改法：The **U-turn** was…（0 词；U-turn ✓ OK）；中文“**大转弯**(U-turn)”替“回头”

**4.（可改）第 3 项 −0.5**
- 原文：but the **concoction** was **risky**——事后评断略武断，可作 proved **risky**（+1 词，须另删一词）；P2 加粗恰 10，保留亦可。

**5.（该改）第 9 项 −0.5**：中文“这次回头(u-turn)”→“这次**大转弯**(U-turn)”（随问题 3）。

**已实测 1–3**：271 词，加粗 52 全部 ✓，**无“已被占用”行**，各段 10/10/12/10/10 ✓。

## 改后词数
271 +0 +0 +0 = 271 ✓

## 达标判断
≥95、零硬伤，按我这一票通过；但**问题 1 必须改**（结尾事实不成立）。改完 1–3、5 预计 99.5。

会签：同意定稿（以落实必改 1 为条件）

总分 = 各项之和 已核（15+8.5+13.5+5+12+8+10+10+9.5+5 = 96.5）
