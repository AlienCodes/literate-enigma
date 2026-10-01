# 评审-语言学教授-18-r2 · 《The Web Beneath the Woods / 林下之网》

**总分：99 / 100（通过，无硬伤）**

**算术核对**：15 + 10 + 14.5 + 5 + 12 + 8 + 10 + 10 + 9.5 + 5 = **99**，跟总分一致。

## 脚本核对

- draft_check（final-v2.md）：**271 词（正好是上限 271）**，54 个重点词，密度 19.9%，**硬性全过**。分档为 ✓四六级 1、✓常用 7、✓派生 8、✓短语 1、✓考研 15、✓雅思 10、✓高中中上 12，没有 △ 档和 ✗ 档的词。各段重点词依次为 11、11、9、16、7 个（「分布不均」只是提醒，不扣分）。各段词数依次为 59、48、42、68、54。
- **速查表顺序和段号**：用脚本比对，英文加粗 54 个，速查表 54 条，两者的顺序和段号逐条一致。中文括注也是 54 个，段号全对；中文里有两处语序跟英文不同（「氮等养分」对 nutrients including nitrogen；第 5 段「输送……发掘……传奇的魅力」对 unearthed…allure…saga…convey），这是汉语语序的正常调整，速查表按英文顺序排是对的。
- 没有两个不同的英文重点词译成同一个中文词的情况。
- 对照 used_words.json：54 个词都不在台账里；第 1 轮提出的 mere 重复已经取消加粗，re-examined 已经换成 combed through。
- 我建议的改法都套在一份临时副本上（`polish-tmp/18-r2-test.md`）复跑过：**仍是 271 词、54 个重点词，硬性全过**。改法**没有增加任何英文词**，英文只加了一个逗号。

## 第 1 轮问题的落实情况

| 第 1 轮问题 | 落实 |
|---|---|
| 1. mere 重复（项5） | 已改。英文干脆删掉了 mere，这样比只取消加粗多省出 1 个词，供 2025 年那一句用。中文残留问题见下文可改 C |
| 2. re-examined → combed through（项5） | 已改。英文、中文「梳理」、速查表三处一致 |
| 3. inconsistent →「互不一致」（项8） | 已改。中文和速查表都改了 |
| 4. nurture →「照料」（项9） | 已改。速查表的 nurture 释义也换成了新的 |

## 逐条核对本轮的改动

**英文**
- **In a Canadian forest, researchers…**：成立。作者里有一半在美国机构，写 Canadian researchers 不准；把「加拿大」移到地点上，事实更稳，句子也自然。
- **bathed each species in carbon dioxide laced with a different tracer**：成立。实验是互换标记，两种幼苗各用一种同位素，a different tracer 的分配读法（每种各一种）很清楚。tracer 从主语位置挪到 laced with 的宾语位置，正好是它最典型的用法（a radioactive tracer，be labelled with a tracer）。bathe 的宾语是 species 而不是 seedlings，属于科技写作里常见的转喻，可以接受。
- **Carbon shuttled both ways**：成立，比上一稿的 The tracer shuttled 直白。
- **nutrients including nitrogen, swapping them for plant sugars**：成立。plant sugars 把糖的来源交代清楚了，比光说 sugars 好。
- **knit plants into a shared network**：成立。删掉 two or more 后，knit A into B 结构不受影响，plants 用复数，network 本身就隐含「不止一株」。
- **年份后加逗号**：Between 2015 and 2021, 和 In February 2023, 两处都加对了。但同一类结构第 5 段漏了一处（问题 1）。
- **Yet the 1997 trees were seedlings, not elderly mothers.**：成立。删掉 mere 之后，靠 Yet 和 X, not Y 的对照仍然能表达「只是幼苗」的意思。
- **…, and in January 2025 defenders faulted the critique's methods.**：结构和用词都成立。fault 作动词表示「挑……的毛病」（fault sb's methods/reasoning）是地道用法；the critics → the critique 前后呼应，指的是 2023 年那篇综述；defenders 不带宾语，但上下文是批评方和拥护方对举，读者看得懂。时间写到了月，符合时间规则。事实跟「史实与来源」T21 一致（非主责，没有另外核）。

**中文**
- 「研究人员在加拿大的一片森林里，把……罩进袋里，再让两种幼苗分别**沐浴**(bathed)在**掺有**(laced)不同**示踪物**(tracer)的二氧化碳中」：忠实、通顺。each species 译成「两种幼苗分别」，a different tracer 译成「不同示踪物」，分配义保住了。加粗落点准。
- 「碳在两种树之间双向**穿梭**(shuttled)」：准确。
- 「出现了碳的**小幅**(slight)**盈余**(surplus)」：加上「碳的」是合理的显化，英文 surplus 的「碳」靠上下文补出，中文需要明说。不算增意。
- 「**氮**(nitrogen)等**养分**(nutrients)」对 nutrients including nitrogen：including 跟 such as 一样，都可以对应「等」。准确。
- 「再拿去**换取**(swapping)植物的糖分」：准确。
- 「单个真菌就能把多株植物**编织**(knit)进同一张共享网络」：「多株」对 plants（复数），没有增意。准确。
- 「照料自己的**亲族**(kin)」：成立。「亲族」是集合名词，跟 kin 的集合义（统称、作复数）对得上，比「亲属」更贴近原词。「照料亲族」的搭配不如「照料子女」那么常见，但「母树」语境下读得通，不扣分。
- 「2025年1月，共享网络说的拥护者则指摘这篇批评的方法有缺陷」：意思忠实。把 defenders 显化成「共享网络说的拥护者」是必要的补足；「则」跟上文「批评者也承认」构成对照，符合英文的对举。表达上有两处不顺（问题 2）。

**速查表**
- **tracer**：词典义「示踪物，示踪剂」和搭配都对，「本文指」也改成跟新英文一致。只是「两种幼苗各用一种的标记碳」的「的」字结构绕口（可改 A）。
- **kin**：「亲族，亲属」作第一义可以；「next of kin 近亲」「kin selection 亲缘选择」都是准确的对应；「本文指树木自己的后代与近亲」跟原文 mother trees nurture their kin 一致。上一稿「统称，作复数」的语法提示被删掉了，这对学生有用（不能说 *kins，要说 his kin are…），建议加回去（可改 B）。
- 其余 52 条没有改动，第 1 轮已经核过。

## 各项得分

| 项 | 满分 | 得分 | 说明 |
|---|---|---|---|
| 1 史实准确 | 15 | 15 | （非主责）In a Canadian forest、each species…a different tracer（互换标记）、plants into a network、2025 年 1 月拥护方回应，都跟「史实与来源」一致。来源笔记里有三处说明没跟着正文更新（见「来源笔记」），不影响正文，不扣分 |
| 2 论证与结构 | 10 | 10 | （非主责）新加的 2025 年那一句让「争论未决」从暗示变成明写，跟下一句 must settle 衔接得更紧，首尾呼应不受影响 |
| 3 语言质量 | 15 | 14.5 | in January 2025 defenders 漏了逗号，跟本轮刚加的两处年份逗号不一致，而且数字紧挨名词，容易先读成「2025 名拥护者」（问题 1，−0.5） |
| 4 适配读者 | 5 | 5 | critique、defenders、tracer 的意思都靠上下文就能看懂；tracer 在速查表里有交代 |
| 5 学习价值 | 12 | 12 | 54 个词都落在 ✓ 档，没有重复；mere 和 re-examined 两个问题都解决了 |
| 6 用法典型 | 8 | 8 | laced with a tracer、knit plants into、fault the critique's methods、shuttled 等用的都是最该学的意思，搭配地道 |
| 7 速查表 | 10 | 10 | tracer、kin 两条新释义都是词典义加搭配，没有错误，也没有误导；可改 A、B 只是写得更好的问题 |
| 8 忠实 | 10 | 10 | 新改的中文都没有增删意思。「只不过」那一处见可改 C，属于把隐含义说出来，在翻译允许的范围内 |
| 9 通顺地道 | 10 | 9.5 | 「指摘这篇批评的方法有缺陷」：「批评」直接当作「一篇文章」用，而且「指摘」跟「有缺陷」意思重复（问题 2，−0.5） |
| 10 重点词对应 | 5 | 5 | 示踪物(tracer)、穿梭(shuttled)、小幅(slight)、盈余(surplus)、编织(knit)、亲族(kin) 的加粗落点都准，速查表的顺序和段号都对 |

## 逐条问题

### 1. 【该改·项3 −0.5】第 5 段年份后漏了逗号
- **原文**：`…can **migrate** between trees underground, and in January 2025 defenders faulted the critique's methods.`
- **问题**：本轮已经在 `Between 2015 and 2021,` 和 `In February 2023,` 后面加了逗号，这一处是同一类时间状语，却没加，全文不统一。另外 2025 跟 defenders 紧挨着，前文又多次用到「数字 + 名词」（26 field studies、three researchers），读者容易先把它读成「2025 名拥护者」，再回头改过来。
- **改法**（不增加词，只加一个逗号）：
  - `and in January 2025 defenders faulted the critique's methods.` → `and in January 2025, defenders faulted the critique's methods.`
  - 结果：仍是 271 词

### 2. 【该改·项9 −0.5】「指摘这篇批评的方法有缺陷」表达不顺
- **原文**：`2025年1月，共享网络说的拥护者则指摘这篇批评的方法有缺陷。`
- **问题**：(1)「这篇批评」把「批评」直接当成一篇文章的名称来用，现代汉语里通常说「这篇批评文章」，而且前文的中文从来没出现过「一篇文章」，加上「这篇」两个字会显得突兀。(2)「指摘」的词义就是「挑出错误，加以批评」（《现代汉语词典》），后面再接「有缺陷」意思重复。「指摘 + 名词」最贴近英文 faulted the critique's methods，而且跟「指出」不同，不暗示拥护方说得对，符合来源笔记「不评判谁对」的要求。
- **改法**：
  - `2025年1月，共享网络说的拥护者则指摘这篇批评的方法有缺陷。` → `2025年1月，共享网络说的拥护者则指摘这篇批评文章的方法。`
  - 英文不用动

## 可改（不扣分，供写作组参考）

- **A. 速查表 tracer 的「本文指」不顺**：`本文指两种幼苗各用一种的标记碳` → `本文指掺进二氧化碳的标记碳，两种幼苗各用一种`。整行改为：
  `| tracer | n. 示踪物，示踪剂（a radioactive/chemical tracer；use sth as a tracer，本文指掺进二氧化碳的标记碳，两种幼苗各用一种）；曳光弹 | 1 |`
- **B. 速查表 kin 补回语法提示**（只加中文）：
  `| kin | n. 亲族，亲属（统称，作复数；next of kin 近亲；kin selection 亲缘选择）；本文指树木自己的后代与近亲 | 3 |`
- **C.「只不过」现在没有对应的英文**：英文删掉了 mere，中文「1997年实验里的树只不过是幼苗」还保留着「只不过」。Yet…seedlings, not elderly mothers 本来就有「只是幼苗」的意思，所以不算增意。但学生逐句对照时，可能会以为 seedlings 本身就有「只不过」的意思。建议改成：`然而，1997年实验里的树只不过是幼苗` → `然而，1997年实验里的树都是幼苗`（the 1997 trees 是复数，「都」不增意）
- **D.** 第 1 轮可改 A（In 26 → Across 26）、B（「果然」）、C（「而总体上以中性效应居多」）、D（filaments 先给词典义）、E（allure 的动词义换成 alluring adj.）这次都没有采纳。这些仍然只是建议，不扣分。

## 来源笔记（不在正文里，不扣分，但应该同步）

「史实与来源」里有三处说明还是旧稿的写法，跟正文矛盾，后面的评审可能会被误导：
- 【T1/T2】`正文不写名，写 Canadian researchers）` → `正文不写名，写 In a Canadian forest, researchers）`
- 【T1/T2】`正文写 carbon dioxide laced with traceable carbon，不写同位素名称` → `正文写 carbon dioxide laced with a different tracer，不写同位素名称`
- 【T21·入正文】`此事属实，但正文未写（正文以 None of this disproves… 与批评方 concede 表明争论未决）。` → `此事属实，正文第5段写入一句，与 None of this disproves… 和批评方 concede 一起表明争论未决。`

## 达标与预计

现在是 99 分，已达标，没有硬伤。问题 1、2 改完，预计 **100 分**（项3 回到 15，项9 回到 10）。可改 A–D 和来源笔记的同步都不影响分数。问题 1、2 和可改 A–C 都套在副本 `polish-tmp/18-r2-test.md` 上复跑过 draft_check：271 词、54 个重点词，硬性全过，没有增加英文词。
