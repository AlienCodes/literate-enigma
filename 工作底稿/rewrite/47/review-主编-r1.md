# 第 47 篇评审 · 英文总编辑 · 第 1 轮

## 总分：96.5 / 100（无硬伤）

| 项 | 满分 | 得分 |
|---|---|---|
| 1 史实准确 | 15 | 13 |
| 2 论证与结构 | 10 | 9.5 |
| 3 语言质量 | 15 | 14 |
| 4 适配读者 | 5 | 5 |
| 5 学习价值 | 12 | 12 |
| 6 用法典型 | 8 | 8 |
| 7 速查表释义 | 10 | 10 |
| 8 忠实 | 10 | 10 |
| 9 通顺地道 | 10 | 10 |
| 10 重点词对应 | 5 | 5 |

## 机检（英文单独抽出，逐行读，未过滤）
`en_check.py`：段落词数 [58, 57, 50, 58, 48]，合计 271 ✓（零余量）；候选 50 个全部 ✓；**无“已被占用”行** ✓；各段加粗恰 10 ✓。

## 逐句史实核对（对照约稿单 §3 与 S1–S9）
- P1：1996-07-05、罗斯林 ✓；芬兰多塞特母羊乳腺细胞、与去核黑脸羊卵融合、黑脸代孕 ✓（S1 S2）；白脸证明来自供体细胞 ✓；277 次唯一活羔 ✓。**an extraordinary failure rate**：1/277 的算术推论，成立 ✓。genome 严格说是核基因组（线粒体来自卵），概括可接受。
- P2：常被误称第一个克隆体 ✓（论点）；1962 年青蛙核移植、1995 年梅根与莫拉格由胚胎细胞克隆 ✓（S3）；首个成年细胞克隆的哺乳动物 ✓；1997-02-22 公布与论文同时 ✓；以多莉·帕顿命名、乳腺双关 ✓（S1）。
- P3：
  - **Her birth provoked uproar and apprehension**：**与事实不符**。多莉 1996 年 7 月出生时秘而不宣，直到 1997 年 2 月 22 日公布才引起轰动（S1）；引起骚动的是“消息”，不是“出生”。且 Her 跨段紧接上段末的 Dolly Parton，指代也有歧义。见问题 1。
  - uproar／apprehension 本身由 1997 年 3 月克林顿禁令（S4）可推出，属合理概括 ✓。
  - 1997 年 3 月克林顿禁止联邦资金用于人类克隆实验 ✓；1999 年端粒约短 20% ✓（S5）；“生来就老”之忧、推测早衰 ✓。
  - **20% shortened for her age**：S5 为“比同龄羊短约 20%”，shortened for her age 搭配生硬（问题 4）；同句 reported 与 about 两个对冲沿用约稿单 T7 措辞，可接受。
- P4：2003-02-14 六岁安乐死、关节炎、病毒引起的进行性肺病 ✓（S6）；**Indoor housing probably contributed** ✓——S2“被认为是诱因”，probably 对冲到位；2016 年 7 月 13 只克隆羊（4 只同细胞系）正常衰老、无高血压糖尿病 ✓（S7）。
  - **X-rays … showed ordinary arthritis, proving such fears unfounded**：S7 原意是 X 光显示关节炎与自然受孕羊相似、“早发”之忧无据；proving 比来源笃定，且 such fears 指代不清——上文的担忧是“生来就老”，并未提过“克隆导致关节炎提前”。见问题 2。
- P5：自然交配产六羔、首只邦妮 1998 年 4 月 ✓（S8）；2003 年起剥制陈列于苏格兰国家博物馆 ✓（S9）。
  - **a famously debated icon and memorial**：debated 无来源；且同位语紧跟 National Museum of Scotland，读来像是博物馆“富有争议”。见问题 3。
- **结尾** Behind the glass, her white face **plainly** **testifies** to her Finn Dorset **ancestry**.（13 词）
  - 事实：剥制标本保留白脸 ✓；白脸即 P1 所说的供体血统证据 ✓，首尾呼应成立。ancestry 严格说是“遗传来源”（她是供体的克隆而非后代），与 P1 lineage 同义回扣，可接受。
  - 同构：Behind the glass 为地点状语，非时间状语开头；主谓“her white face testifies to …”与 05–46 各结尾均不同（不同于 46 的 X went, on …, to a … still convinced、45 的 had begun on …, exactly a year before、42 的 still carries）✓；无 Dolly／copied／copy／sheep、still、never、remained、came from 等 ✓。

## 其他
- 代词跨段：P3 Her birth（见问题 1）；P5 She bore——上段主语为多莉，女性唯一，无歧义 ✓。
- 同义堆叠：uproar and apprehension、anxiety／speculate 各自分句，可接受。

## 逐条问题

**1.（必改）第 1 项 −1（兼 跨段代词）**
- 原文：Her birth **provoked** **uproar** and **apprehension** about the **ethics** of human cloning.
- 改法：The news **provoked** **uproar** and **apprehension** about the **ethics** of human cloning.（0 词）
- 中文：消息一出，**引发**(provoked)了**轩然大波**(uproar)……

**2.（该改）第 1 项 −0.5；第 2 项 −0.5**
- 原文：…showed ordinary **arthritis**, proving such fears **unfounded**.
- 改法：…showed ordinary **arthritis**, showing early-ageing fears **unfounded**.（0 词；early-ageing 计 1 词）——与上文“早衰”之忧呼应，showing 不再过度断言。若嫌 showed／showing 重复，可作 suggesting early-ageing fears **unfounded**。
- 中文：……证明对她**过早**衰老的担忧**毫无根据**(unfounded)。→ 改为“表明对她早衰的担忧**毫无根据**”。

**3.（该改）第 1 项 −0.5；第 3 项 −0.5**
- 原文：Since 2003 her **stuffed** body has been **encased** in the National Museum of Scotland, a **famously** debated **icon** and **memorial**.
- 改法：Since 2003 her **stuffed** body, now **famously** an **icon** and **memorial**, has been **encased** in the National Museum of Scotland.（0 词；删无来源的 debated，消除同位语误挂）
- 中文：自2003年起，她的**填充标本**(stuffed)——如今已是**著名**(famously)的**标志**(icon)和**纪念**(memorial)——一直**封存**(encased)在苏格兰国家博物馆。（若避破折号：她那如今已**广为人知**的……）

**已实测 1–3**：271 词，加粗 50，无占用行，各段 10 ✓

**4.（可改）第 3 项 −0.5**
- 原文：were reported about 20% **shortened** for her age
- 问题：shortened for her age 生硬；shorter than normal for her age 更自然，但 shorter 为基础词、P3 加粗恰 10，保留。

## 改后词数
271 +0 +0 +0 = 271 ✓（已实测）

## 达标判断
≥95、零硬伤，按我这一票通过；**问题 1 必须改**（出生时秘而不宣，骚动始于公布）。改完 1–3 预计 99.5。

会签：同意定稿（以落实必改 1 为条件）

总分 = 各项之和 已核（13+9.5+14+5+12+8+10+10+10+5 = 96.5）
