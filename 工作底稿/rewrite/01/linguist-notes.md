# 第01篇 · 语言学家说明（重点词、译文、速查表）

> 成稿：`final.md`。英文 271 词，6 段；重点词 **55 个**；`draft_check.py` 硬性全过，只剩 3 条 △ 提醒，逐条说明见下。
> 英文另抽出来单独跑了 `en_check.py`：271 词，无长句，无视频问题。

---

## 一、为什么是 55 个

合稿里有 61 个候选词。我逐个按四条标准筛：

1. 分档在可用范围内（✓；△ 要有充分理由）；
2. 文中用的是最值得考的义项；
3. 搭配地道；
4. 考研生读到它真能学到东西，而不是早就会了。

结果是留 54 个，删 7 个，另因英文改动新增 1 个（reportedly），共 55 个。落在用户建议的 55–60 区间。没有为凑数加任何弱词。全库 70 篇共用词池，把 pump、distant 这类义项平平的词留给能用出更好义项的文章，比在这里占掉更划算。

### 删掉的 7 个（已取消加粗）

| 词 | 删的理由 |
|---|---|
| instantly | 由 instant 派生，考研生都认识，学不到新东西 |
| pump | 文中只是「水泵」的字面义；最值得考的是动词义 pump money into（大量注资），留给更合适的文章 |
| parish | 不在考试词表；文中又是「地方行政单位」这个容易误读的历史义项，性价比低。译文写作「教区官员」 |
| poison | 基础词 |
| brewery | 考试价值低，专指性强 |
| distant | 文中是字面义「遥远的」，考研生都会 |
| drinkers | 由基础词 drink 派生，工具判为 ✓派生，但实际没有学习价值 |

### 两个 △ 词：都保留，理由如下

- **suspected**（Zipf 4.51，刚过 4.5 的线）
  - 词形人人认识，但 suspect that（觉得很可能）和 doubt that（觉得不太可能）方向相反，是考研阅读和翻译的经典陷阱。
  - 文中「怀疑那口泵有问题」正是 suspect 最典型的用法。
  - 速查表把这组对照写出来了，这个格子占得值。
- **register**（Zipf 4.59）
  - 学生大多只知道动词「注册」。文中是名词「登记簿、名册」（register of deaths），这个义项多数人不熟。
  - 速查表另给了动词义「（仪表）显示」「流露（情绪）」和语言学的「语域」，都是阅读里会碰到的。

### 保留的几个需要说明的词

- **inmates**：分档是 ✓常用。牛津词典的核心定义是「被关在某个机构（监狱、医院等）里的人」，济贫院的收容者正属此义，并非偏义。速查表先给「被收容者」，再给当代最常见的「囚犯」。
- **claiming**：文中是 claim lives（夺去生命）。这是新闻高频搭配，也是 claim 在考研阅读中最容易读错的义项。速查表也给了「声称」「索取」。
- **maintained / contending**：意思相近（都是「坚持说」）。两个都留，因为 maintain that 和 contend that 是考研写作、阅读的核心动词。译文严格区分：maintained 译「坚称」，contending 译「声称」。
- **declined**（拒绝，不是「下降」）、**observed**（评论说）、**isolated**（isolate A from B，分离）、**chart**（动词，标绘）：都用的是考研最爱考的「非第一反应义项」。速查表先给文中义，再给常见义。
- **At his urging / upwards of / a mere**：这三个短语本身就是要学的搭配，所以整体加粗。

### 各段分布：15／9／9／9／6／7

draft_check 提示分布不均（最多段比最少段多 9 个）。我看过，保留现状，理由有二：

- 第 1 段交代两种医学理论，概念词天然密集（attributed, epidemics, orthodox, maintained, inhaled…），删哪个都是在删好词。
- 第 5 段讲寡妇和侄女，基本是叙事和亲属称谓，好词本来就少。为了平均分布而硬加或硬删，都违背「不为凑数加弱词」的原则。

---

## 二、英文改动（共 3 处，只改确有必要的）

改动后 271 词，在 249–271 以内。en_check 已复跑。

| 段 | 合稿原文 | 改为 | 理由 |
|---|---|---|---|
| 1 | In ten days from 31 August 1854 | Within ten days of 31 August 1854 | 词数不变。in ten days from 31 August 可以读成「从 8 月 31 日算起第十天」这一天，有歧义；within ten days of 是英国报刊指一段时间的地道说法 |
| 4 | Near the pump, a brewery lost none of its 70-odd labourers, who drank their beer allowance instead. | A Broad Street brewery lost none of its 70-odd labourers, who **reportedly** drank their beer allowance instead. | 词数不变。史实问题：约稿单 G2 明令「只喝啤酒」不得当作史实写，这是老板的看法（Mr. Huggins believes they do not drink water at all）。合稿说明也写了要把「不喝水」归给雇主，但成句里漏了。加 reportedly 补上归属。A Broad Street brewery 与原文 "a Brewery in Broad Street, near to the pump" 一字不差，同时省出一个词 |
| 6 | A map could chart where people died; only the living could say what they drank. | A map could chart where people died, **but** only the living could say what they drank. | 多一个词。约稿单 §6.3 明令收尾不许「分号连接的两句格言」，改成一句转折。only 在这里是字面陈述（死者无法开口），不是全称推广，符合 §6.1(3)。如果总编辑更想要分号的节奏，改回来即可，词数回到 270 |

注意：成稿正好 271 词，没有余量。母语作者和报社撰稿人润色时如果要加词，最安全的可删词是第 3 段的 **later**：its cluster 已经指向 12 月公布的地图，时间顺序不会因此丢失。

---

## 三、译文要点

- **对齐**：每句英文对应一句中文，都以「。」收束。英文句内有分号的（第 2 段第 2 句、第 5 段第 2 句），中文也在同一句内处理。全文没有用冒号或分号把两句英文并成一句。
- **一词一译**：55 个中文译法两两不同。容易撞车的几对都区分开了：
  - maintained 坚称／contending 声称／observed 指出／demonstrated 证明；
  - renowned 著名／reputation 声誉；
  - fatal 致命／perished 丧命；
  - plunged 骤降／declined 拒绝。
- **加粗落点**：只加粗真正对应的汉字。
  - upwards of → 「逾」（逾五百人）
  - a mere → 「区区」
  - At his urging → 「在他的敦促下」（短语整体对应）
  - abundant → 「比比皆是」：so abundant that 在中文里最自然的说法。速查表给的是词典义「大量的，丰富的，充裕的」。
- **术语与专名**
  - miasma 译「瘴气」，紧跟同位语「即从污秽中产生的污浊空气」，与英文一样当场解释。
  - workhouse 译「济贫院」，并有「专收贫民」作交代。
  - parish officials 译「教区官员」。「官员」两字表明是地方行政人员；是否加注由总编辑定。
  - niece 统一译「侄女」，速查表两义都给（侄女；外甥女）。
- **引语**："a high and healthy part of Islington" 译作 “伊斯灵顿地势高爽、有益健康的一带”。「高爽」对 high，暗含瘴气说「地势高就安全」的反讽，但没有替原文加话。
- **收尾**：「地图可以标出人死在哪里，但他们喝了什么，只有活着的人才说得出来。」前半句对应标题前半，后半句对应标题后半，与标题《死在哪里，喝了什么》首尾呼应。
- **标题**：沿用《死在哪里，喝了什么》，9 字。我考虑过更文的《死于何处，饮自何方》，但不如现题口语有力，也不如现题贴合英文标题的平实。

---

## 四、速查表体例

- 每条先给词性。
- 屈折形式在括号里注原形，例如 v. (claim)。
- 先给文中义，再给最常考的其他义项。能配搭配的配搭配（attribute A to B、decline to do、contend that/for/with、make allowance for）。
- 易混词顺带点出（physician／physicist、suspect／doubt、widow／widower、niece／nephew）。
