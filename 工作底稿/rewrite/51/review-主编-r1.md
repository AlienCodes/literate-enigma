# 第 51 篇评审 · 英文总编辑 · 第 1 轮

## 总分：98 / 100（无硬伤）

| 项 | 满分 | 得分 |
|---|---|---|
| 1 史实准确 | 15 | 15 |
| 2 论证与结构 | 10 | 9.5 |
| 3 语言质量 | 15 | 13.5 |
| 4 适配读者 | 5 | 5 |
| 5 学习价值 | 12 | 12 |
| 6 用法典型 | 8 | 8 |
| 7 速查表释义 | 10 | 10 |
| 8 忠实 | 10 | 10 |
| 9 通顺地道 | 10 | 10 |
| 10 重点词对应 | 5 | 5 |

## 机检（英文单独抽出，逐行读，未过滤）
`en_check.py`：段落词数 [46, 59, 51, 58, 43]，合计 257 ✓（余 14 词）；候选 50 个全部 ✓；**无“已被占用”行** ✓；各段加粗恰 10 ✓。
`wt.sh` 实测：OK unpredictable、differing；OCC variable、inconsistent。

## 逐句史实核对（对照约稿单 §3 与 S1–S6）
- P1：1840 年前按页数和距离计费、通常收信人送达时付 ✓（S1）。**Each letter thus carried a fluctuating price**：fluctuating 本义是“随时间起伏波动”，这里指“因信而异”，用法偏离（问题 2）。
- P2：1837 年希尔小册子 ✓；1839 年议会立法 ✓；1840-01-10 统一便士邮资：半盎司一便士、全国任何目的地、寄信人预付 ✓（S2）。
- P3：1840-05-01 发行、05-06 起有效 ✓；**a youthful likeness of Queen Victoria, the reigning monarch**：S3 为“年轻维多利亚女王侧像”，youthful likeness 准确且未写确切年龄 ✓；1840 年她确为在位君主 ✓；68,808,000 枚 ✓；无齿孔、剪刀剪开 ✓。
- P4：1839 约 8 千万 → 1840 逾 1.69 亿、约翻倍 ✓（S4，roughly 一处对冲）；红色注销戳在黑票上不显眼、红墨可擦、可重复使用 ✓；1841 年 2 月换红便士、黑墨注销 ✓（S5）。**arrived to deter tampering and fraud**：S5 说红墨可擦致重复使用，随即改用红票黑墨——“为防篡改与欺诈”是由前因直接推出的目的，成立 ✓。
- P5：首创者、不印国名、君主头像依国际协议即可 ✓（S6）。

## 结尾
By international agreement, the **sovereign**'s head **suffices** for **identification**, an **implicit** **designation** that other countries spell out in print.（20 词）
- 事实：S6“依协议君主头像即足以识别”✓；其他国家邮票印国名，是 S6 中 the only country 的反面，成立 ✓。
- 同构：By international agreement 为方式状语，非时间状语；“主句 + 同位名词短语 + 关系从句”与 44–50（so they could not；exactly a year before；to a … still convinced；Behind glass … testifies；, for by 1969；, the originals being；X next door had only Y）均不同 ✓。
- 其余 §5：无 stamp／changed／change／post ✓；无 for／since 原因从句、being 独立主格、still、never 等 ✓；无冒号分号破折号、最高级 ✓。

## 其他
- 代词跨段：P5 Its stamps 的 Its 指同段 Britain ✓；其余段首均为名词 ✓。
- 同义堆叠：initiator／precedent、identification／designation（问题 1、3）。

## 逐条问题

**1.（可改）第 2 项 −0.5**
- 原文：As the **initiator** of postage stamps, Britain set a **precedent** that brought an **exemption**.
- 问题：“开创先例 → 带来豁免”因果牵强（豁免来自它是首创者，而非“先例”本身）；initiator 与 precedent 意义相叠。可改：As the **initiator** of postage stamps, Britain earned an **exemption** that set a **precedent**…（意思反转亦不妥）——较稳妥的是 As the **initiator** of postage stamps, Britain enjoys an **exemption**, a **precedent** of sorts.（加粗不变，词数 0）。不强求。

**2.（可改）第 3 项 −0.5**
- 原文：Each letter thus carried a **fluctuating** price.
- 问题：fluctuating 指随时间波动；这里是“因信而异”。可用 **differing**（✓ OK，0 词）：Each letter thus carried a **differing** price——略生硬；或 Prices thus varied from letter to letter（失去加粗，P1 跌破 10）。保留亦可。

**3.（可改）第 3 项 −1（两处）**
- Its stamps are **nameless**——邮票各有名称（Penny Black 等），nameless 易误解为“无名”；with no country inscribed 已说清，nameless 略多余，P5 加粗恰 10，保留。
- **identification**, an **implicit** **designation**——identification 与 designation 近义，抽象名词连用；保留。

## 必改
无。

## 改后词数
英文不变：257 ✓（余量 14 词；问题 1 改法 0 词）

## 达标判断
≥95、零硬伤，按我这一票通过。

会签：同意定稿

总分 = 各项之和 已核（15+9.5+13.5+5+12+8+10+10+10+5 = 98）
