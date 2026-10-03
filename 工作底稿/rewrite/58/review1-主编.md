# 第 58 篇（鸟类导航）评审 · 英文总编辑 · 第 1 轮

## 总分：96.5 / 100（无硬伤）

| 项 | 满分 | 得分 |
|---|---|---|
| 1 史实准确 | 15 | 13.5 |
| 2 论证与结构 | 10 | 10 |
| 3 语言质量 | 15 | 14.5 |
| 4 适配读者 | 5 | 4.5 |
| 5 学习价值 | 12 | 11 |
| 6 用法典型 | 8 | 8 |
| 7 速查表释义 | 10 | 10 |
| 8 忠实 | 10 | 10 |
| 9 通顺地道 | 10 | 10 |
| 10 重点词对应 | 5 | 5 |

## 机检（英文单独抽出，逐行读，未过滤）
- `en_check.py`：段落词数 [60, 61, 67, 57, 26]，合计 **271** ✓（≤271，零余量）；候选 **54** 个全部 ✓（≥50）；**无“已被占用”行** ✓。
- `stem.py`（全部 54 个加粗词）：traveller／traverse、arc／archive 等、decode／decorate、protein／protest、retina／retirement、tuned／fortune、reclaimed／reclassify、interference／intercept 等均为字母巧合 ✓。**唯一真同根：front-runner 与台账 frontage（第 55 篇）、frontier 共用 front**——按“同根一律排除”须换（必改 1）。
- `wt.sh` 另测：OK **prime**；△ candidate、suspect（candidate 另与 55 篇 candid 同根，不可用）；BAD blotted。

## 总体评价
这是近十篇里最好的开头之一：第一句就落在具体场景（1952、波士顿、放飞），“信比鸟晚到”的悬念一句收住；全文按“悬念 → 太阳与星星 → 磁场与眼睛里的化学 → 人类电噪声 → 未解之谜”推进，每段一个台阶；动词精准（swivelled、curtained、piping、reclaimed、clad），长短句交错；科学表述大体克制，结尾以“罗盘破解了一部分、地图还没人读懂”收束，扣住开篇那只鹱，干净有力。

## 逐句史实核对（对照约稿单 §3 与 S1–S7）

**P1**
- 1952-06-03、马泽奥在波士顿放飞大西洋鹱 ✓；火车＋飞机从斯科克霍姆岛（威尔士外海）的洞巢带来 ✓；放飞后立刻寄信 ✓（S1）。
- **a 3,200-mile odyssey**：S1 为 about 3,200 miles，正文去掉了约数（问题 3）。
- 十二天半后回到巢 ✓；信随后才到 ✓。

**P2**
- 1950 年代克雷默、椋鸟、笼中、镜子移动太阳视位置、鸟随之转向、并补偿太阳每日移动 ✓（S2；allowing for its daily arc 的 its 指 sun，同句唯一单数名词，无歧义）。
- 1960 年代埃姆伦、天文馆、遮星、依北极星周围星座、北极星为星空旋转中心 ✓（S3）。**curtained off stars** 略别扭——curtain off 多指“用帘子隔出一块空间”，遮星说 blot out 更自然，但 blotted 为 BAD（可改）。

**P3**
- 1972 年维尔奇科、欧亚知更鸟、读倾角不读极性 ✓（S4）；与水手罗盘针对比 ✓。
- 1978 年舒尔滕提出光触发的化学反应 ✓（S5）。
- **by 2000 cryptochrome … was the front-runner**：S5 是 2000 年**刚被提出**为候选分子；“到 2000 年已是领跑者”时间上提前（问题 1，与同根问题一并改）。
- 2021 年实验室中知更鸟的（隐花色素 4）比鸡和鸽子的更敏感 ✓（the robin's 省略得当）；Proof in a living bird is **awaited** ✓ 克制。

**P4**
- 2014 年奥尔登堡、校园未屏蔽木屋中失灵、接地铝屏蔽屋中恢复、拆接地或加噪声再失灵 ✓（S6）；日常电器、远低于世卫限值 ✓。
- **The double-blind result was unambiguous**：S6 只说“双盲实验”；unambiguous（毫不含糊）是评价，来源无此判断（问题 2）。

**P5**
- 地图感未解 ✓（S7）。
- **结尾** The compass is partly **cracked**, but the **atlas** that steered the shearwater has yet to be read.
  - 字面成立：罗盘（太阳、星星、磁场）已部分弄清，地图感未解 ✓；has yet to be read 准确对应“尚未弄清”。
  - 结构：并列转折句，不是“主句, + 名词短语”、极短判词、The year … saw、倒装、In effect、“cannot prove…, but it suggests…”（后者是“否定证明 + suggests”，本句是“部分破解 + 尚待解读”，骨架不同）✓。
  - 禁词：无 bird／beat／letter／home ✓；无 never、still、remained（上一句的 remains 不在结尾句）✓；无冒号分号破折号、最高级、may／might ✓。

## 其他
- 代词跨段：各段以名词开头 ✓。
- 对冲：每句至多一处 ✓。
- 人物身份：维尔奇科（1972）、舒尔滕（1978）首次出场未交代身份（S4 为法兰克福的鸟类学者、S5 为物理学家）；克雷默、埃姆伦有实验情境可推知（问题 4）。

## 必改（均已实测）

**1.（必改）第 5 项 −1；第 1 项 −0.5：同根＋时间提前**
- 原文：and by 2000 cryptochrome, a **protein** in the **retina**, was the **front-runner**.
- 改法：and in 2000 cryptochrome, a **protein** in the **retina**, became the **prime** suspect.（+1 词；prime ✓ OK、无同根；suspect 不加粗）
- 中文：到2000年，……成了**领跑者**(front-runner) → 2000年，视网膜中的一种**蛋白质**(protein)隐花色素成了**头号**(prime)嫌疑对象。

**2.（必改）第 1 项 −0.5：无源评价，并腾出词数**
- 原文：Removing the grounding, or **piping** noise in, **bewildered** them again. The double-blind result was **unambiguous**.
- 改法：Removing the grounding, or **piping** noise in, **bewildered** them again in double-blind tests.（−2 词；去掉 unambiguous）
- 中文：拆掉接地，或往屋里**灌入**(piping)噪声，在双盲实验中又让它们**晕头转向**(bewildered)。（删“这项双盲实验的结果毫不含糊”）

**3.（必改）第 1 项 −0.5：数字对冲**
- 原文：After a 3,200-mile **odyssey** …
- 改法：After a roughly 3,200-mile **odyssey** …（+1 词）
- 中文：飞越约三千二百英里……

**已实测 1–3**：段落词数 [61, 61, 68, 55, 26]，合计 **271** ✓；加粗 **53** ✓（≥50）；**无“已被占用”行** ✓。

## 可改
**4. 第 4 项 −0.5**：In 1972 Wiltschko → In 1972 the Frankfurt biologist Wiltschko（+3 词）；Klaus Schulten → the physicist Klaus Schulten（+2 词）。字数已满，需另删词才可采纳（例如删 P4 首句的 eerie，或把 P2 的 nightly whirl 改 whirl），否则保留。
**5. 第 3 项 −0.5**：**curtained** off stars → 可接受；如能另测到合规的 masked／hid（须过 wt.sh 与 stem.py），会比 curtained 更自然。

## 中文（整体自然优美，少量随必改同步）
- “**披着羽毛**(feathered)的**旅行者**(traveller)”“回到自家**门口**(doorstep)”“罗盘之谜已**破解**(cracked)了一部分”均好。
- 随必改 1–3 同步修改三处（见上）。

## 达标判断
96.5 ≥ 95、零硬伤，按我这一票通过；以落实必改 1–3 为条件（尤其必改 1 的同根问题）。改完预计 99。

会签：同意定稿（以落实必改 1–3 为条件）

总分 = 各项之和 已核（13.5+10+14.5+4.5+11+8+10+10+10+5 = 96.5）
