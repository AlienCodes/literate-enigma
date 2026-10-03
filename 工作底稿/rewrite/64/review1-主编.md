# 第 64 篇 The Game That Escaped the Soviet Union（俄罗斯方块）评审 · 英文总编辑 · 第 1 轮

## 总分：96 / 100（无硬伤）

| 项 | 满分 | 得分 |
|---|---|---|
| 1 史实准确 | 15 | 14 |
| 2 论证与结构 | 10 | 9.5 |
| 3 语言质量 | 15 | 14 |
| 4 适配读者 | 5 | 5 |
| 5 学习价值 | 12 | 11 |
| 6 用法典型 | 8 | 8 |
| 7 速查表释义 | 10 | 10 |
| 8 忠实 | 10 | 9.5 |
| 9 通顺地道 | 10 | 10 |
| 10 重点词对应 | 5 | 5 |

## 机检（英文单独抽出，逐行读，未过滤）
- `en_check.py`：段落词数 [57, 35, 57, 55, 52, 15]，合计 **271** ✓；候选 **55** 个；无“已被占用”行。
- **人工复核不规则变化（对 used_words.json 逐词比对）**：
  - **oversee ↔ oversaw（第 35 篇已占用）**——oversaw 是 oversee 的不规则过去式，属**同一个词的屈折形式**，en_check 漏报。**必须处理**（必改 1）。
  - 其余近形词均为派生或不同词：concocted／concoction(44)、geometric／geometry(55)、communist／community(61)、enterprising／enterprise(13)、utter／utterly(21)、ignorance／ignorant(46)、regulating／regulation(11)、legitimately／legitimacy(38)、expiry／expire(35)、intellectual／intellect(26)、publisher／publish(30) 等，按规则允许 ✓。
  - 另测替换词：administer（27）、govern（03）已占用；manage、police 基础词。

## 逐项核查（协调人点名）
| 词／句 | 判断 |
|---|---|
| **hectic** week of negotiations | S4 只说三方“同一周恰好都在莫斯科争夺版权”；三路人马同城角逐，“忙乱的一周”是合理的叙事润色，不改变事实 ✓ |
| Nintendo **scooped** the handheld rights | scoop = 抢先拿到；Elorg 把掌机版权给了任天堂，而其他人同场竞争，用法准确 ✓ |
| copies **mushroomed** freely | mushroom = 迅速蔓延，对应 S2“在莫斯科和东欧免费流传”✓ |
| a **resourceful** Dutch-born publisher | 持旅游签证闯到莫斯科、自己找到 Elorg（S4），resourceful 有事实支撑 ✓ |
| In **utter** **ignorance** of Elorg | S3“从没听说过 Elorg”——utter ignorance 正是“完全不知其存在”，不过度 ✓ |
| **around 1995, when he moved to America** | **有误**。S6 的表述是“1995 年协议到期／移居美国后开始拿版税”，并未说他 1995 年移居；when he moved to America 把移居钉在 1995 年前后（帕基特诺夫实际 1991 年已移居美国）。必改 2 |
| Stein and Kevin Maxwell … were **there** | 紧跟 found his way to Elorg，there 会被读成“在 Elorg 办公室”；S4 是“同一周也在莫斯科”。必改 3 |
| **Duplicated** copies | copies 本身就是复制品，duplicated 叠义（该改 4）|

## 其余史实（T1–T6）
1984 年 6 月、29 岁、Elektronika 60 只能显示文字、方块由字符组成 ✓；tetra- ＋ tennis ✓；国家所有、本人无权 ✓；软盘在东欧自由流传 ✓；1986 年斯坦因在匈牙利看到、不知 Elorg、未获授权先卖 ✓；版权在西方公司间层层转卖、其一属马克斯韦尔 ✓；1989 年 2 月罗杰斯持旅游签证到莫斯科、找到 Elorg ✓；帕基特诺夫喜欢罗杰斯、任天堂先得掌机版权后得全球主机版权 ✓；捆绑 Game Boy、出货超 3,500 万份 ✓；多年分文未得、1995 年前后协议到期后才有收入 ✓；1996 年共同成立俄罗斯方块公司 ✓。

## 结尾
原文：The man whose puzzle once spread for nothing now helped decide who could sell it.（15 词）
- 字面：1996 年起他与罗杰斯共同管理版权，“参与决定谁能卖它”✓；“曾免费流传”✓。
- 结构核查：不在禁用清单内（不是“主句, + 名词短语”、极短判词、The year … saw、倒装、In effect、partly … has yet to、At that pace、so each of us carries、Its builders were not、A haven built against、The X that … was the one …）；以 The man 开头不在禁用开头里 ✓；无冒号分号破折号、最高级、may／might、never、still 等 ✓。提醒：“The + 名词 + 关系从句 + 谓语”与第 33 篇“The boy who had seemed to … would …”有几分相似，但无 who had、无 would + 插入语，可放行。
- **时态问题**：now 与过去式 helped 搭配别扭（now 指“如今”，而 helped 是过去），见必改 5。
- 中文“那个当年**任由**自己的游戏免费流传的人”——“任由”给了他主动放任的意思，英文只说 puzzle spread（被动流传，且他本无权利阻止），属增义（必改 6）。

## 必改（已实测）

**1. 第 5 项 −1：屈折形式重复**
- 原文：…founded The Tetris Company to **oversee** the rights.
- 改法：…founded The Tetris Company to manage the rights.（0 词；manage 为基础词不加粗；加粗 −1）

**2. 第 1 项 −1：移居时间**
- 原文：His **earnings** began only after his arrangement's **expiry** around 1995, when he moved to America.
- 改法：His **earnings** began only after his arrangement's **expiry** around 1995.（−4 词）
- 中文：直到1995年前后他的协议**到期**(expiry)之后，他才开始有**收入**(earnings)。（删“他移居美国”）

**3. 第 3 项 −0.5：there 指代**
- 原文：Stein and Kevin Maxwell, the magnate's son, were there that same **hectic** week…
- 改法：…were in Moscow that same **hectic** week…（+1 词）
- 中文“也在那里”→“也在莫斯科”。

**4.（该改，随必改一并落实）第 3 项 −0.5：叠义**
- 原文：**Duplicated** copies **mushroomed** freely…
- 改法：Copies **mushroomed** freely…（−1 词；加粗 −1）
- 中文“复制出来的拷贝”→“拷贝”。

**5. 第 2 项 −0.5：结尾时态**
- 原文：The man whose puzzle once spread for nothing now helped decide who could sell it.
- 改法：The man whose puzzle once spread for nothing later helped decide who could sell it.（0 词）

**6. 第 8 项 −0.5：中文增义**
- 原文：那个当年任由自己的游戏免费流传的人，如今参与决定谁能卖它。
- 改法：那个人的游戏当年曾免费流传，后来他却参与决定由谁来卖它。（或：游戏曾免费流传的那个人，后来参与决定谁能卖它。）

**已实测 1–5**：段落词数 [57, 34, 57, 56, 47, 15]，合计 **266** ✓；候选 **53** 个全部 ✓；**无“已被占用”行** ✓。余 5 词。

## 可改
- 余下 5 词可用来为罗伯特·马克斯韦尔一句或帕基特诺夫多年无收入一句补一点画面，但须避免来源外事实；不补亦可。

## 达标判断
96 ≥ 95、零硬伤，按我这一票通过；以落实必改 1–3、5、6 为条件。改完预计 100。

会签：同意定稿（以落实必改为条件）

总分 = 各项之和 已核（14+9.5+14+5+11+8+10+9.5+10+5 = 96）
