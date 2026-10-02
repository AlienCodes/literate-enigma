# 第 41 篇评审 · 英文总编辑 · 第 1 轮

## 总分：98.5 / 100（无硬伤）

| 项 | 满分 | 得分 |
|---|---|---|
| 1 史实准确 | 15 | 15 |
| 2 论证与结构 | 10 | 10 |
| 3 语言质量 | 15 | 13.5 |
| 4 适配读者 | 5 | 5 |
| 5 学习价值 | 12 | 12 |
| 6 用法典型 | 8 | 8 |
| 7 速查表释义 | 10 | 10 |
| 8 忠实 | 10 | 10 |
| 9 通顺地道 | 10 | 10 |
| 10 重点词对应 | 5 | 5 |

## 机检（英文单独抽出，逐行读，未过滤）
`en_check.py`：段落词数 [54, 48, 43, 52, 64]，合计 261 ✓；候选 50 个全部 ✓；**无“已被占用”行** ✓；各段加粗恰 10 ✓。

## 史实核对（对照任务书 §3 与 S1–S6）
- 2018-06-23、12 名 11–16 岁少年队员、25 岁助理教练、睡美人洞、泰国北部 ✓；季风雨、水位上涨被困 ✓（S3 称季风）
- 九天下落不明（6-23 → 7-02）✓；7-02 两名英国潜水员、约 4 公里、被淹洞室、泥土高台、全员生还 ✓
- 出路：数公里狭窄凶险通道 ✓
- 2018-07-06 萨曼·古南（前海豹队员）布放氧气瓶时失去知觉死亡 ✓
- 7-08 起、镇静、担架、潜水员接力、沿途医护、分批；7-10 最后四人与教练 ✓
- 约 1 万人、100 多名潜水员、2,000 士兵、900 警察 ✓（Some 一处对冲）
- 2019 年 12 月另一名海豹队员死于救援中感染的血液感染 ✓
- 时间顺序 23 June → 2 July → 6 July → 8–10 July → December 2019 ✓；无引语、无冥想、无“不会游泳”、无药名 ✓；无“奇迹／英雄”✓

### 协调人点名三处
1. **stockpiling** oxygen **cylinders** along the route：S4 为“沿被淹通道布放氧气瓶”。stockpile 指“储备、囤积以备后用”，潜水救援正是在沿线分段预置气瓶供后续往返使用，along the route 交代了“沿途分布”，下句 while laying them 又落实了“布放”动作，二者合起来与来源一致，**不越界** ✓。（若求最贴字面可作 began **positioning** …，但无必要。）
2. many of them **navigable** only with **scuba** gear：来源说通道被淹（S5、T3 flooded），被淹段落只能潜水通过是直接推论，且限定为 many of them，未说全程，**不越出来源** ✓。顺带也补上了 T3 的 flooded 含义。
3. **结尾** Every boy came home alive, and two rescuers were **mourned**.（11 词）
   - 事实：12 名男孩全部生还 ✓；死者两人（萨曼 2018-07-06、Beirut Pakbara 2019-12）✓；“回家”前先住院，但全部出院回家，概括成立 ✓；every boy 未含教练，但不失实。
   - 对照修辞成立，与论点“13 人全生还，代价两名救援者”一致 ✓。
   - §5：≤26 ✓；无 cave／thirteen ✓；主语 every boy（建议之一）✓；非 Yet／时间状语／What 开头；无 came from、remained、never、had left 等 ✓；无冒号分号破折号、最高级 ✓；不鸡汤 ✓。

## 逐条问题

**1.（该改）第 3 项 −0.5**
- 原文：On 10 July the last four **footballers** followed their **teammates** out, their coach **escorted** with them.
- 问题：独立主格 their coach escorted with them 生硬，escorted with 不地道。
- 改法：On 10 July the last four **footballers** and their coach were **escorted** out after their **teammates**.（0 词，实测 P4 仍 52 词；加粗不变）
- 中文：7月10日，最后四名**小球员**(footballers)和教练在**队友**(teammates)之后被**护送**(escorted)出洞。

**2.（该改）第 3 项 −0.5**
- 原文：including a **contingent** of more than 100 divers, 2,000 soldiers and 900 **policemen**
- 问题：a contingent of 管到了士兵和警察，变成“一支由潜水员、士兵和警察组成的分队”，逻辑不清。
- 改法：including a **contingent** of more than 100 divers, plus 2,000 soldiers and 900 **policemen**（+1 词）

**3.（可改）第 3 项 −0.5**
- 原文：They entered Tham Luang … to **explore** its **darkness**.
- 问题：to explore its darkness 带文学渲染、略像替男孩设动机；来源为“探洞”。P1 加粗恰 10，保留。

**其余核查（不扣）**：whereabouts、huddled／perched、inundated、treacherous、batches、doses of sedative、sobering postscript 均地道；policemen 英式可接受。中文全篇通顺，“一个不少，全都活着”“令人沉重的尾声”自然。

## 改后词数
261 +0（1）+1（2）= 262 ✓（已实测：段落 [54, 48, 43, 52, 65]，加粗 50，无占用行，各段 10）

## 达标判断
≥95、零硬伤，按我这一票通过；落实 1、2 即为 99.5。

会签：同意定稿

总分 = 各项之和 已核（15+10+13.5+5+12+8+10+10+10+5 = 98.5）
