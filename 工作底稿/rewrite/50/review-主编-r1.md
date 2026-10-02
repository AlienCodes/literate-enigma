# 第 50 篇评审 · 英文总编辑 · 第 1 轮

## 总分：98 / 100（无硬伤）

| 项 | 满分 | 得分 |
|---|---|---|
| 1 史实准确 | 15 | 14.5 |
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
`en_check.py`：段落词数 [52, 45, 57, 55, 53]，合计 262 ✓；候选 51 个全部 ✓；**无“已被占用”行** ✓；各段加粗 11/10/10/10/10 ✓。
`wt.sh` 实测：OK coolness、reluctance；OCC muted；BAD tepid、lukewarm、reticence、hesitancy。

## 逐句史实核对（对照约稿单 §3 与 S1–S9）
- P1：1968 年 3M 科学家西尔弗想做超强黏合剂，做出低黏、可揭可重贴的胶 ✓（S1）；tiny spheres 对应来源的 microspheres ✓。**To an inventor chasing strength, the formulation was a setback**：目标是超强、结果是弱黏，从目标与结果的落差直接推出，限定在“对追求强度的发明者而言”，成立 ✓。
- P2：五年、公司内部、非正式交流与研讨会推介 ✓；无产品 ✓。
  - **His own summary called it a solution without a problem**：约稿单 T2 已核准“describing it as a solution without a problem”的转述；正文未加引号、以间接转述呈现，不算直接引语 ✓。但 a summary called it 让“概括”当主语去“称呼”，略别扭（问题 3）。
  - **His perseverance met indifference**：五年无人采用（S2）可推出“反应冷淡”，indifference 分寸合适 ✓。
- P3：1974 年、听过研讨会的同事弗莱、唱诗班赞美诗集的纸书签总掉、想到用这种胶做不伤书页的书签 ✓（S3）。
- P4：1977 年 Press 'n Peel 四城试销、反应平平 ✓（S4）；1978 年博伊西免费派样、超过 90% 表示会买 ✓（S5）。
  - **After the apathy came a turnaround**：S4 是 lukewarm（不温不火），apathy 是“漠不关心”，语气重于来源；且与 P2 indifference 近义重复。见问题 1。
- P5：1980-04-06 以 Post-it Notes 全美上市、1981 年加拿大和欧洲 ✓（S6）；西尔弗 2021-05-08 去世、80 岁 ✓（S9）；黄色出于偶然、隔壁实验室只有黄色废纸 ✓（S7）。

## 结尾
The **stationery** **staple** owes its **signature** **canary** **tone** to an **unplanned** choice. The laboratory next door had only **leftover** yellow paper.
- 事实：S7 原意即“偶然选定，隔壁实验室只有黄色废纸”，leftover 对应 scrap ✓；两句先断言、后给出事实，修辞成立 ✓。
- §5（就末句与末两句整体）：≤26 ✓；无 glue／failed／fail／failure ✓；不以时间状语、What／Yet／Every／Behind／But／Admirers 开头 ✓；无 for／since 原因从句、无 being 独立主格（避开 48、49 结构）✓；无 still、never、apparently 等 ✓；无冒号分号破折号 ✓。
- 同构：与 44–49 各结尾均不同（44 had hidden … so…；45 had begun on …, exactly a year before；46 went …, to a … still convinced；47 Behind glass … testifies；48 …, for by 1969 …；49 …, the originals being …）✓。

## 其他
- 代词跨段：P2 For five years Silver、P3 In 1974 Art Fry、P4 In 1977 the notes、P5 the pads——无跨段代词 ✓。
- 同义堆叠：annoyance／frustration 分处两句，一为“烦心事”一为“懊恼的心情”，可接受但略近（问题 4）；indifference／apathy 见问题 1。

## 逐条问题

**1.（该改）第 1 项 −0.5**
- 原文：After the **apathy** came a **turnaround**.
- 改法：After the **coolness** came a **turnaround**.（0 词；coolness ✓ OK，准确对应 lukewarm，并消除与 P2 indifference 的近义重复）
- 中文：**冷遇**(coolness)之后，迎来了**转机**(turnaround)。
- 已实测：262 词，加粗 51，无占用行 ✓

**2.（可改）第 2 项 −0.5**
- P5 次序：上市 → 西尔弗 2021 年去世 → 黄色由来（1977–80 年间的事），时间跳到 2021 再折回。可把 Silver died… 一句移到 Canada and Europe followed in 1981 之后保持现状亦可；若想更顺，可将死讯并入结尾前的过渡，但不强求。

**3.（可改）第 3 项 −0.5**
- 原文：His own **summary** called it a solution without a problem.
- 问题：summary 作主语“称呼”略拟人；P2 加粗恰 10，保留。

**4.（可改）第 3 项 −0.5**：**annoyance**／**frustration** 两句相邻，略近义。

## 必改
无。

## 改后词数
262 +0 = 262 ✓

## 达标判断
≥95、零硬伤，按我这一票通过；落实问题 1 即为 98.5。

会签：同意定稿

总分 = 各项之和 已核（14.5+9.5+14+5+12+8+10+10+10+5 = 98）
