# 第 46 篇评审 · 英文总编辑 · 第 1 轮

## 总分：96 / 100（无硬伤）

| 项 | 满分 | 得分 |
|---|---|---|
| 1 史实准确 | 15 | 13.5 |
| 2 论证与结构 | 10 | 9 |
| 3 语言质量 | 15 | 14 |
| 4 适配读者 | 5 | 5 |
| 5 学习价值 | 12 | 12 |
| 6 用法典型 | 8 | 8 |
| 7 速查表释义 | 10 | 10 |
| 8 忠实 | 10 | 10 |
| 9 通顺地道 | 10 | 9.5 |
| 10 重点词对应 | 5 | 5 |

## 机检（英文单独抽出，逐行读，未过滤）
`en_check.py`：段落词数 [54, 50, 58, 55, 53]，合计 270 ✓；候选 52 个全部 ✓；**无“已被占用”行** ✓；各段加粗 10/12/10/10/10 ✓。

## 逐句史实核对（对照约稿单 §3 与 S1–S6）
- P1：冯·奥斯滕、数学教师、驯马者、柏林、公马汉斯、用蹄敲出算术与日期 ✓；1904 年《纽约时报》报道 ✓；公开表演 ✓（S1）
- P2：13 人委员会及成员构成 ✓；1904 年 9 月结论无诈术 ✓。
  - **looked for trickery, fraud and collusion**：委员会的任务就是查有无诈术，“查找诡计”合理；fraud／collusion 是同义扩展，不越界，但三词近义堆叠（问题 4）。
  - **in effect certifying the act as authentic**：委员会只结论“没有诈术”，in effect 已标明这是叙述者对效果的概括，authentic 指“非作假”而非“马会思考”，可接受 ✓。
- P3：1907 年普丰斯特、隔开围观者、换提问者、眼罩、有时用不知答案的人 ✓。
  - **altering one variable after another**：S2 说他分别改变“能否看见”“是否知道答案”等条件，“逐一改变变量”是准确概括 ✓。
  - **50 in 56／2 in 35**：S2 的 89%／6% 条件是“能否看见提问者”，正文 When Hans could see the questioner…／With that person invisible… 条件对应正确 ✓。但**提问者不知答案时的结果没有交代**——设置了这个变量却不给结果，T5 的另一半（“只有提问者知道答案时才答对”）缺失，见问题 3。
  - 句内 he answered 的 he：同句先出现 Hans，指 Hans，无歧义 ✓。
- P4：渐近答案时紧张、最后一下放松、挺直或头部上扬、开始时前倾 ✓（S3）；subconscious 对应来源 involuntary ✓；无人存心欺骗、主人不知情 ✓（未写 von Osten 是骗子）。
- P5：聪明汉斯效应、预期影响结果、双盲设计、动物认知研究 ✓（S5）。
  - **Hans later passed to**：没交代冯·奥斯滕 1909 年去世，“转手”无前因（问题 2）。
  - **结尾**：In the laboratory, Pfungst took the animal's place and proved equally sensitive to the cues of attentive volunteers.
    - 扮演马、受试者集中想一个数、他读其提示敲出答案 ✓（S4）。
    - **equally**（与汉斯同样敏感）来源无此比较，属过度断言（问题 1）。
    - 时间：实验室测试在 1907 年，紧接 1909 年后的转手句之后，读者可能误以为是后事；In the laboratory 未标时间，属轻微时序跳跃（问题 5）。
    - 同构检查：In the laboratory 为地点状语，非时间状语开头；主谓结构 Pfungst took … and proved … 与 05–45 各结尾均不同（不同于 45 的 had begun … exactly a year before、44 的 had hidden … so they could not、41 的 Every … and two … were）✓；无 horse／count／could ✓；无冒号分号破折号、may／might、never 等 ✓。

## 其他检查
- 代词跨段：P2 A commission、P3 In 1907、P4 The cues、P5 The Clever Hans effect 开头，无跨段代词 ✓
- 对冲：全篇无对冲需求，in effect 一处 ✓
- 同义堆叠：问题 4

## 逐条问题

**1.（必改）第 1 项 −1**
- 原文：Pfungst took the animal's place and proved equally **sensitive** to the cues of **attentive** volunteers.
- 问题：equally（与汉斯同样敏感）无来源，S4 只说他靠读取受试者的提示敲出答案。
- 改法：Pfungst took the animal's place and proved **sensitive** to the cues of **attentive** volunteers.（−1 词；仍 ≤26，修辞成立：人类也能读出这些提示，正说明信号来自提问者）
- 中文：普丰斯特亲自扮演马的角色，结果他也能**敏锐**(sensitive)地捕捉到**专注**(attentive)的志愿者发出的提示。

**2.（该改）第 1 项 −0.5**
- 原文：Hans later passed to a **jeweller** convinced horses could reason.
- 问题：没交代转手原因（冯·奥斯滕 1909 年去世，T9）。
- 改法：Hans passed, on his owner's death, to a **jeweller** convinced horses could reason.（+2 词）
- 中文：主人去世后，汉斯转到了一位**珠宝商**(jeweller)手中……

**配套删词（−1 词）**：**certifying** the act as **authentic** → **certifying** the act **authentic**（P2 加粗不变）
**已实测 1+2+配套**：271 词，段落 [54, 49, 58, 55, 55]，加粗 52，无占用行，各段 10/12/10/10/10 ✓

**3.（可改）第 2 项 −0.5**
- 原文：…sometimes used askers **ignorant** of the answer.（结果未交代）
- 问题：T5 指出汉斯只有在提问者知道答案且看得见提问者时才答对；正文只给了“看得见／看不见”的数字，“不知答案”这条线悬空。词数已满，可在中文或速查表注释中补，不强求。

**4.（可改）第 3 项 −0.5**
- 原文：Its members looked for **trickery**, **fraud** and **collusion**.——三词近义堆叠，P2 加粗 12，可删 fraud（−1 词，P2 降为 11）以腾词数。

**5.（可改）第 2 项 −0.5**
- 结尾回到 1907 年的实验室，紧接 1909 年后的转手句，时序略跳。时间状语不得作结尾句首，可在转手句与结尾之间不作调整，接受扣分；或把转手句移到效应句之前（0 词）。

**6.（可改）第 3 项 −0.5**
- 原文：his **accuracy** fell to a **ratio** of two in 35——accuracy fell to a ratio 搭配生硬；可作 he was right only twice in 35（但会失两个加粗词，P3 跌破 10），保留。

**7.（该改）第 9 项 −0.5**
- 原文：它的**准确率**(accuracy)降到35次中只对2次的**比率**(ratio)。
- 改法：它的**准确率**(accuracy)就降到了35次只对2次的**比例**(ratio)。或更简：……**准确率**降到只有35分之2的**比率**。

## 改后词数
270 −1（1）+2（2）−1（配套）= 270；实测 271（以机检为准）✓

## 达标判断
≥95、零硬伤，按我这一票通过；**问题 1 必须改**（equally 无来源）。改完 1、2、7 预计 98。

会签：同意定稿（以落实必改 1 为条件）

总分 = 各项之和 已核（13.5+9+14+5+12+8+10+10+9.5+5 = 96）
