# 第 31 篇评审 · 英文总编辑 · 第 1 轮

## 总分：94 / 100（无硬伤，未达 95）

| 项 | 满分 | 得分 |
|---|---|---|
| 1 史实准确 | 15 | 13 |
| 2 论证与结构 | 10 | 10 |
| 3 语言质量 | 15 | 13 |
| 4 适配读者 | 5 | 5 |
| 5 学习价值 | 12 | 12 |
| 6 用法典型 | 8 | 7.5 |
| 7 速查表释义 | 10 | 10 |
| 8 忠实 | 10 | 10 |
| 9 通顺地道 | 10 | 8.5 |
| 10 重点词对应 | 5 | 5 |

## 机检（英文单独抽出，未过滤任何行）
`en_check.py`：段落词数 [41, 60, 49, 63, 58]，合计 271 ✓（已到上限，零余量）；候选 54 个，**无任何“已被占用”行** ✓；各段加粗 10/11/11/12/10 ✓。
△ 两个：electronics、origins（Zipf 4.55，与 variety 同层），须语言学家判定。若 electronics 被判不达标，总数降到 53、P2 降到 10，须另补一个（我试过的替补 hardware、devised、ingenious、myth、folklore 均已占用，gifted／designed 为基础词，single-handedly 冷僻；可用未占用的 genesis、mythical、anecdote、malignant、inception，但都不顺，故倾向保留 electronics）。

## 史实核对（逐条，对照任务书 §3）
- 1985 年 5 月董事会支持斯卡利、30 岁、剥夺 managerial duties ✓；未直陈 fired，用 stripped／ousted ✓；1985 年 9 月辞职 ✓
- Rewind three decades：1985 → 1955，正好三十年 ✓；1955-02-24 旧金山出生、新生儿被收养 ✓
- 1976-04-01 与沃兹尼亚克创办 ✓；早期样机归沃兹尼亚克 ✓；车库写成 symbolic，并交代沃兹尼亚克说法 ✓
- 1980-12-12 上市（floated，英式）✓；1984-01-24 Macintosh ✓
- Later in 1985 NeXT ✓（倒叙结束后回到 1985，标得清楚）；1986 年 2 月收购卢卡斯影业图形部门、后成皮克斯 ✓；1995-11-22《玩具总动员》、首部长篇电脑动画 ✓
- 1996-12-20 宣布收购 NeXT ✓；1997 年 8 月微软 1.5 亿美元 ✓；he later said … weeks ✓（归属到位，未写 90 天）
- 2003 年 10 月确诊罕见胰腺肿瘤 ✓；2011 年 8 月 briefly 超越埃克森美孚 ✓；2011-08-24 卸任、2011-10-05 去世、56 岁 ✓
- nearly fourteen years：1997 年 9 月任临时 CEO → 2011 年 8 月卸任 = 13 年 11 个月 ✓
- 公允：未写发明电脑／手机，产品无“他造”字样 ✓；无引语 ✓；无 genius／visionary ✓
- 结尾：He had spent nearly fourteen years at the **helm** of the company that had **ousted** him.（17 词）无 garage／top／world，无禁用结构（非 That+名词+came，非 years after），回环呼应开场“被赶出”，不新增事实 ✓

## 逐条问题

**1.（该改）第 1 项 −1**
- 原文：It began as a **manufacturer** of **specialised** hardware, not an **animation** studio.
- 问题：皮克斯起初主业是卖 Pixar Image Computer，但动画组从一开始就在（1986 年即有《顽皮跳跳灯》Luxo Jr.），“不是动画工作室”说过头。
- 改法：It began as a **manufacturer** of **specialised** hardware, not chiefly an **animation** studio.（+1 词；chiefly 不加粗——已被第 07 篇占用）；中文“而不是**动画**(animation)工作室”改为“主业并不是**动画**(animation)”

**2.（该改）第 1 项 −1**
- 原文：In August 1997 Microsoft **invested** $150 million in its **distressed** **competitor**, and that September Jobs **regained** control as **interim** chief.
- 问题：regained control 暗示他从前掌过苹果大权；1985 年前他是董事长兼部门主管，从未任 CEO，也谈不上“控制”公司。有夸大之嫌。
- 改法：In August 1997 Microsoft **invested** $150 million in its **distressed** **competitor**; that September Jobs **took the reins** as **interim** chief.（“, and”改分号 −1，regained control → took the reins +1，净 0；took the reins 已测 ✓短语、未占用）；速查表删 regained 行，加 took the reins | phr. (take the reins) 接管，掌权（take the reins of government/the company） | 4；中文“乔布斯**重掌**(regained)大权”改为“乔布斯**接掌大权**(took the reins)”

**3.（可改）第 3 项 −0.5（中文同步）**
- 原文：Its Toy Story, released on 22 November 1995, was…
- 问题：Its Toy Story 生硬（所有格 + 片名），且 It／Its 连续两句开头。
- 改法：Toy Story, released on 22 November 1995, was…（−1 词，抵消问题 1；中文“皮克斯出品的”保留不算增义，因上句已交代）

**4.（该改）第 3 项 −0.5**
- 原文：Its garage **origins** are largely **symbolic**
- 问题：Its 前一个名词是 Wozniak／engineer，指代需回找。
- 改法：Apple's garage **origins** are largely **symbolic**（0 词）

**5.（可改）第 3 项 −1**
- 原文：Jobs received a **diagnosis** of an **uncommon**, **cancerous** **pancreatic** **tumour**.
- 问题：received a diagnosis of 本身是地道医学语体，可留；但四个修饰语堆叠，明显为加粗而排队，读来像病历。P5 加粗恰为 10，删任何一个都不够，故只记可改。
- 改法：词数与加粗允许时，可改为 a rare form of pancreatic cancer（任务书原话）；本轮不强求。

**6.（可改）第 6 项 −0.5**
- 原文：Apple announced a **takeover** of NeXT, **reclaiming** its **estranged** co-founder.
- 问题：takeover 常带“敌意收购”色彩，善意并购母语者多说 purchase／acquisition（acquired 已在 P3 用过）；reclaiming its estranged co-founder 修辞稍浓但不失实（他以顾问身份回归），可保留。
- 改法：保留；若有余量可改 announced it would buy NeXT。

**其余核查（不扣）**：sided with ✓ 地道；sidelined and alienated ✓（alienated 指他本人受冷落，与 sidelined 并列不歧义）；electronics engineer ✓ 搭配地道（仅档位待定）；Rewind three decades ✓；nearly fourteen years ✓；His tenure ended 中 His 指 Jobs，无歧义 ✓。

**7.（该改）第 9 项 −1**
- 原文：2003年10月，乔布斯获得**诊断**(diagnosis)，患有一种……
- 问题：“获得诊断”是英文直译，中文不这么说。
- 改法：2003年10月，乔布斯经**诊断**(diagnosis)患有一种**罕见**(uncommon)的**癌性**(cancerous)**胰腺**(pancreatic)**肿瘤**(tumour)。

**8.（可改）第 9 项 −0.5**
- 原文：时年30岁的史蒂夫·乔布斯被**剥夺**(stripped)了**管理**(managerial)职务，而这家公司由他参与**创办**(co-founded)。
- 问题：“而这家公司由他……”后置补充，欧化。
- 改法：时年30岁的史蒂夫·乔布斯在他参与**创办**(co-founded)的这家公司里被**剥夺**(stripped)了**管理**(managerial)职务。

## 改后词数
271 +1（问题 1）+0（问题 2）−1（问题 3）+0（问题 4）= 271 ✓。已用改后英文实测：en_check 合计 271，加粗 54，无占用行，各段 ≥10；△ 仍为 electronics、origins，待语言学家。

## 达标判断
无硬伤，94 < 95，不通过。改完 1–4、7、8 预计 98.5（剩可改 5、6 共 −1.5）。

总分 = 各项之和 已核（13+10+13+5+12+7.5+10+10+8.5+5 = 94）
