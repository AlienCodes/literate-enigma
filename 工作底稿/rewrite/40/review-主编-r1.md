# 第 40 篇评审 · 英文总编辑 · 第 1 轮

## 总分：96.5 / 100（无硬伤）

| 项 | 满分 | 得分 |
|---|---|---|
| 1 史实准确 | 15 | 14 |
| 2 论证与结构 | 10 | 10 |
| 3 语言质量 | 15 | 13 |
| 4 适配读者 | 5 | 5 |
| 5 学习价值 | 12 | 12 |
| 6 用法典型 | 8 | 8 |
| 7 速查表释义 | 10 | 10 |
| 8 忠实 | 10 | 10 |
| 9 通顺地道 | 10 | 9.5 |
| 10 重点词对应 | 5 | 5 |

## 机检（英文单独抽出，逐行读，未过滤）
`en_check.py`：段落词数 [57, 57, 52, 51, 52]，合计 269 ✓；候选 50 个全部 ✓；**无“已被占用”行** ✓；各段加粗恰 10 ✓。
`wt.sh` 实测：OK simulated、rehearsal、virtual；OCC contests、bouts、encounters、hailed、landmark、breakthrough、feat、unprecedented、inaugural；BAD matches、rounds、maestro、virtuoso、prodigy、grandmaster、practice、player 等。

## 史实核对（对照任务书 §3 与 S1–S6）
- 局面数多于宇宙原子，reportedly 一处对冲 ✓
- 2015 年 10 月 5–0 胜欧洲冠军、无让子 ✓；“首次不让子在全尺寸棋盘上胜职业棋手”被压成 the first such milestone，见问题 3
- 2016 年 3 月首尔、李世石、18 个国际冠军 ✓
- 第二局 2016-03-10、第 37 手、第五线肩冲 ✓；解说称怪、一人以为失误 ✓；离席、十多分钟（未写 15）✓
- 概率万分之一由 AlphaGo 估算（诊断工具查询）✓ 写明谁估算 ✓；李后来称赞其独创与美，间接 ✓
- 先学网上强业余、再自我对弈数千万盘：iterations 不准，见问题 1
- 第四局 2016-03-13、第 78 手扭转局势、职业棋手誉为神之一手 ✓；DeepMind 团队估算约万分之一 ✓ 写明谁估算 ✓；唯一胜局、4–1 ✓（en dash）
- 2019 年 11 月退役、称 AI 为无法击败的存在（间接）✓；the summit was beyond him 与 S5“再也不可能成为第一”一致 ✓

## 结尾事实核查（第 39 篇教训）
原文：Yet his one win came from a stone whose odds, by DeepMind's figures, were as slim as those of AlphaGo's audacious shoulder hit.（23 词）
- 两个“万分之一”：37 手由 AlphaGo（经 DeepMind 诊断工具）估算，78 手由 DeepMind 团队估算——by DeepMind's figures 涵盖两者，说法成立 ✓
- as slim as：两者都约万分之一 ✓（78 手为 about，结尾不加对冲，as slim as 本身是约略比较，可接受）
- his one win came from a stone：第 78 手是该局转折点（S4），说胜利“来自”这一手是合理概括，不算夸大 ✓
- 并置成立、无暗含因果错误、不新增事实 ✓
- §5：≤26 ✓；无 move／37 ✓；Yet 开头非时间状语 ✓；无 remained／oblivious／swept／that bears／had left／never／evidently／may／might；无冒号分号破折号、最高级 ✓；不鸡汤、不下判决 ✓

## 逐条问题

**1.（该改）第 1 项 −0.5**
- 原文：then **sharpened** its play over tens of millions of **iterations** against itself.
- 问题：来源说的是“自我对弈数千万盘”；iterations 在机器学习里指训练迭代，不等于对局，读者会误解。
- 改法：then **sharpened** its play over tens of millions of **simulated** games against itself.（+1 词；simulated ✓ OK，P3 加粗仍 10）
- 速查表：删 iterations，增 simulated | adj./v. (simulate) 模拟的；模拟（simulated flight；simulate conditions） | 3；中文：随后通过与自己进行数千万盘**模拟**(simulated)对局来**磨炼**(sharpened)棋艺。
- 已实测：270 词，加粗 50，无占用行，各段 10 ✓

**2.（可改）第 3 项 −0.5**
- 原文：Such an **unexpected** **deviation** from **orthodox** play seemed to **defy** **intuition**.
- 问题：五个加粗词排成一句，意思与前后句重叠（unconventional、bizarre），像为占词。P2 加粗恰 10，删则不足，保留。

**3.（可改）第 1 项 −0.5**
- 原文：beat the European champion 5–0 with no **handicap**, the first such **milestone** against a professional.
- 问题：first such milestone 指代不清，没说清“首次有程序在全尺寸棋盘、不让子的条件下战胜职业棋手”。词数余量仅 1（问题 1 后为 0），保留。

**4.（可改）第 3 项 −1（两处）**
- a **staggering** **rarity**——带感叹色彩，与“对称呈现、不渲染”略冲突；
- a **consolation** amid AlphaGo's **overwhelming** 4–1 victory——consolation 有“安慰奖”的悲情意味，禁区 1 提醒不渲染。均为加粗词，P3／P4 各恰 10，保留。

**5.（可改）第 3 项 −0.5**
- 原文：a South Korean **strategist** with 18 international titles
- 问题：strategist 多指军事／商业战略家，称围棋棋手不典型（专业棋手常说 player／master，均为基础词或已占用）。保留。

**6.（该改）第 9 项 −0.5**
- 原文：这是机器对阵职业棋手时的第一个这样的**里程碑**(milestone)。
- 改法：这是机器首次在对阵职业棋手时取得这样的**里程碑**(milestone)。

## 改后词数
269 +1（1）= 270 ✓（已实测）

## 达标判断
≥95、零硬伤，按我这一票通过；结尾修辞事实成立。落实 1、6 预计 97.5。

会签：同意定稿

总分 = 各项之和 已核（14+10+13+5+12+8+10+10+9.5+5 = 96.5）
