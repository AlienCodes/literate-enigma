# 第 64 篇（俄罗斯方块）评审 · 英文总编辑 · 第 2 轮

## 总分：99 / 100（无硬伤）

| 项 | 满分 | 得分 |
|---|---|---|
| 1 史实准确 | 15 | 14 |
| 2 论证与结构 | 10 | 10 |
| 3 语言质量 | 15 | 15 |
| 4 适配读者 | 5 | 5 |
| 5 学习价值 | 12 | 12 |
| 6 用法典型 | 8 | 8 |
| 7 速查表释义 | 10 | 10 |
| 8 忠实 | 10 | 10 |
| 9 通顺地道 | 10 | 10 |
| 10 重点词对应 | 5 | 5 |

## 机检（英文单独抽出，逐行读，未过滤）
- `en_check.py`：段落词数 [56, 34, 58, 56, 47, 15]，合计 **266** ✓；候选 **51** 个全部 ✓（≥50）；**无“已被占用”行** ✓。
- **人工复核屈折碰撞**（对 used_words.json 逐词比对前五字母近形）：diversion／diverse、geometric／geometry、communist／community、designer／designate、intellectual／intellect、enterprising／enterprise、ignorance／ignorant、regulating／regulation、legitimately／legitimacy、overlapping／overlook、publisher／publish、console／consortium、expiry／expire——均为派生或不同词，**无同一词的屈折形式** ✓。oversee 已删，r1 的 oversaw 碰撞消除 ✓。brazenly 本身不与台账碰撞 ✓。

## r1 必改落实
oversee → manage ✓；删 when he moved to America ✓（史实注已写明 1991 年已移居）；were in Moscow ✓；Copies **mushroomed** ✓；later helped decide ✓；中文结尾“游戏曾免费流传的那个人，后来参与决定谁能卖它”✓ 不再有“任由”的增义。
其余：built、删 quartet（every geometric piece of four tiles 更清楚）✓、**fusion** ✓、删 utter（In his **ignorance** of Elorg）✓。

## brazenly 是否公允——**不公允（必改）**
- 原文：In his **ignorance** of Elorg, …, he **brazenly** **hawked** rights he did not yet **legitimately** hold.
- 问题：brazenly 是“厚颜无耻地、明知不当仍公然为之”，与同句“他根本不知道 Elorg 存在”自相矛盾；S3 只说他在拿到授权前就卖了版权（他以为能拿到），并无“明知故犯”的依据。对真实人物下了来源外的道德判断。
- 改法：…he **hastily** **hawked** rights he did not yet **legitimately** hold.（0 词；hastily 经 en_check 测为合格、未占用；“操之过急”正是“未获授权先卖”的准确描述）
- 中文：他便**草率**(hastily)地**兜售**(hawked)起……
- 备选：**confidently**（合格；“自信满满地”，对应他以为能拿到授权）。

## 小事（非扣分）
- 史实与来源注 T6 一条仍写“结尾‘如今参与决定谁能卖它’即据此”，与现行中文结尾“后来参与决定”不一致，请同步改为“后来”。

## 结尾复核
The man whose puzzle once spread for nothing later helped decide who could sell it.——字面属实（S2、S6），时态通顺，结构与禁词合规 ✓。

## 必改
1. brazenly → **hastily**（见上，0 词，加粗数不变 51）。

## 达标判断
99 ≥ 95、零硬伤，按我这一票通过；以落实必改 1 为条件，改后 100。

会签：同意定稿（以落实必改 1 为条件）

总分 = 各项之和 已核（14+10+15+5+12+8+10+10+10+5 = 99）
