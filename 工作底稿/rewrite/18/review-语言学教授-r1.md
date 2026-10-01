# 评审-语言学教授-18-r1 · 《The Web Beneath the Woods / 林下之网》

**总分：97.5 / 100（通过，无硬伤）**

**算术核对**：15 + 10 + 15 + 5 + 10.5 + 8 + 10 + 9.5 + 9.5 + 5 = **97.5**，跟总分一致。

draft_check（不带 --claim）结果：262 词（上限 271），55 个重点词，密度 21.0%，硬性全过。分档为 ✓四六级 1、✓常用 8、✓派生 8、✓考研 16、✓雅思 10、✓高中中上 12，没有 △ 档和 ✗ 档的词。各段重点词依次为 11、11、10、16、7 个（脚本提示分布不均，只是提醒，不扣分）。各段词数依次为 56、51、43、67、45。

**脚本核对**
- 英文加粗、中文 `**中文**(english)` 括注、速查表三者的顺序和段号逐条一致（用脚本比对过，55 = 55 = 55）。
- 中文括注一律用小写（`(unsupported)` 对 `**Unsupported**`），跟全库第 01 篇 `(amid)` 对 `**Amid**` 的做法一致，不扣分。
- 没有两个不同的英文重点词译成同一个中文词的情况。
- 用 used_words.json 按词元比对：55 个词的字面都不在台账里。但 **mere 跟第 01 篇的 a mere 实际上是同一个词**（问题 1）。apparently/apparent(11)、assertions/assert(14)、ambiguous/ambiguity(13)、enclosed/enclosure(05)、tracer/trace(09) 都是派生关系，按评分表「派生词算不同的词」可以用，不算重复。
- 按问题 1–4 改完后复跑 draft_check：**263 词，54 个重点词，各段 [11, 11, 9, 16, 7]，硬性全过**。改好的稿子见 `rewrite/18/_rv-语言学教授-r1.md`。

| 项 | 满分 | 得分 | 说明 |
|---|---|---|---|
| 1 史实准确 | 15 | 15 | （非主责）1997 年 8 月 7 日《自然》第 388 卷、纸桦和花旗松、塑料袋、双向转移、花旗松净得、遮荫越重净得越多、封面造出 wood-wide web、2015–2021 年三本书、2023 年 2 月三位研究者、26 项野外研究、同行评审、25 年翻倍，都跟「史实与来源」一致。apparently 和 told readers that 两处把推断和书中说法跟事实隔开了 |
| 2 论证与结构 | 10 | 10 | （非主责）塑料袋实验 → 机制 → 造词 → 比喻走红 → 2023 年复核 → 不否认网络存在、只要求证据。首句的 romantic 和末句的 allure of a family saga 首尾呼应；末段 unearthed 跟标题 Beneath 形成双关 |
| 3 语言质量 | 15 | 15 | 英式拼写全文统一（harbour、favouring、towards）。没有语法错误（见下文「语法」）。In 26 field studies 和 such fungi…such as 只是可改，不扣分 |
| 4 适配读者 | 5 | 5 | tracer、wood-wide web、peer-reviewed、mother trees 在上下文或速查表里都有交代 |
| 5 学习价值 | 12 | 10.5 | 选词质量高：一组「研究与证据」词（tracer、demonstrate、sparse、inconsistent、ambiguous、peer-reviewed、assertions、citations、skewed、disproves、concede）正好是考研阅读科技文的核心词；一组「拟人化叙事」词（romantic、metaphor、converse、nurture、kin、elderly、saga、allure）对照鲜明。扣分：mere 跟第 01 篇的 a mere 重复（问题 1，−1）；re-examined 是基础词 examine 加透明前缀，学不到新东西（问题 2，−0.5） |
| 6 用法典型 | 8 | 8 | 委托方点名的六处搭配逐条核过，都成立（见下文「搭配逐条核对」）。apparently 用的正是考研最常考的「看来，据说」，不是「显然」 |
| 7 速查表 | 10 | 10 | 每条都给了词典义和常用搭配，「本文义」单独标出。converse 给了动词和形容词、名词的重音差别；apparently 提醒了不要译成「显然」；surplus、tracer、migrate 都写了本文指什么。inconsistent 和 nurture 两条的释义随问题 3、4 一起改，不在这里重复扣分 |
| 8 忠实 | 10 | 9.5 | 每一处 hedge 都保留了（见下文清单）。只有 inconsistent 译成「前后不一」，意思偏了（问题 3，−0.5） |
| 9 通顺地道 | 10 | 9.5 | 「养育自己的亲属」动宾搭配不顺（问题 4，−0.5） |
| 10 重点词对应 | 5 | 5 | 罩(enclosed)、栖居着(harbour)、搜寻(forage)、妨碍(hindered)、居多(predominating)、偏向(skewed)、发掘(unearthed) 的加粗落点都准确。harbour 译成「栖居着」，主语从植物换成了真菌，这是汉语的正常转换，不扣分 |

## 搭配逐条核对（委托方点名的几处）

- **grew out of plastic bags**：成立。grow out of 的词典义是「起源于，由……发展而来」（an idea grew out of a conversation）。这里的字面意思是「从塑料袋里长出来」，又暗合袋里的幼苗，一语双关。中文「萌生于塑料袋之中」用「萌生」把双关保住了，译得好。
- **bathed the seedlings in carbon dioxide laced with traceable carbon**：成立。bathe sth in（light/gas/liquid）表示「使笼罩在……之中」，是标准用法。be laced with 表示「掺入少量某物」，最典型的宾语是酒、毒药、药物，用在气体上也说得通；实验里的标记气体确实是在普通空气中加入少量带同位素的二氧化碳。速查表给了 coffee laced with brandy 这个典型例子，处理得当。
- **ran a slight surplus**：成立，而且是本文最有《经济学人》味道的一处。run a surplus/deficit 本来是经济用语（run a budget/trade surplus），这里借来说碳的「收支」，跟生态学里的 carbon budget 一致。速查表在 surplus 下写明了 run a surplus 和「本文指花旗松收到的碳多于送出的碳」，学生不会误解。larger in deeper shade 是紧缩的同位形容词短语，修饰 surplus，母语者读得懂。
- **knit two or more plants into a shared network**：成立。knit 的引申义「使紧密联结」最常见的是 knit together，knit A into B（knit communities into a nation）也是词典收录的结构。速查表两种都给了。
- **with neutral effects predominating**：成立。predominate 是不及物动词，with + 名词 + -ing 的独立结构用得对，语义上也跟前面 about equally often 咬合：有利、不利大致持平，没有影响的最多。
- **with citations skewed towards positive results**：成立。skewed towards/toward 是统计和学术写作的标准搭配（skewed towards younger respondents）。towards 跟全文英式拼写一致。速查表给了英美两种拼法。
- 另外核过的几处：shuttled both ways（shuttle 本身含「往返」，加 both ways 点明是两个物种之间的双向流动，不算赘余）、harbour such fungi（生物学里 harbour microbes/fungi 是中性用法）、forage for water and nutrients（菌丝 foraging 是生态学常用说法）、unveiled the study（新闻英语常见）、proved irresistible、nurture their kin、too sparse…to demonstrate、hindered seedlings、favouring their own offspring、concede that、unearthed evidence、the allure of、how much the networks convey。这些都是地道搭配。

## 语法

没有发现语法错误。its cover offering a catchy coinage 是独立主格结构；had doubled 用过去完成时，表示 2023 年之前 25 年间的变化，时态正确；It is evidence…, not…, that must settle… 是强调句，结构完整；how much the networks convey 里 how much 是 convey 的宾语，及物用法没问题。swapping them for sugars 的逻辑主语是真菌（或菌丝），不构成垂悬分词。

## hedge 逐条核对（中文都保留了）

apparently via fungi → 似乎是经由……真菌；a slight surplus → 小幅盈余；larger in deeper shade → 所受遮荫越重，盈余越大；Most terrestrial plants → 大多数陆生植物；such as nitrogen → 氮等；One fungus can → 单个真菌就能；two or more → 两株乃至更多；told readers that → 向读者讲述（书中说法没有被当成事实）；They judged it → 他们认为；too…to demonstrate → 不足以证明；about equally often → 大致一样多；No peer-reviewed field study showed → 没有任何一项经同行评审的野外研究表明；had doubled over 25 years → 在25年间增加了一倍；None of this disproves → 这一切都不能否定；can migrate → 可以……迁移；must settle → 必须由……来裁定；whether it matters → 这又是否要紧。

## 逐条问题

### 1. 【该改·项5 −1】mere 跟第 01 篇的 a mere 重复
- **原文**：Yet the 1997 trees were **mere** seedlings, not **elderly** mothers.／然而，1997年实验里的树**只不过**(mere)是幼苗……
- **问题**：台账里第 01 篇登记的是短语 a mere，所以脚本没拦下。但 a mere 只是 mere 加上不定冠词，并不是有独立意义的固定短语；第 01 篇速查表的释义写的就是「短语. 仅仅，区区（mere adj. 仅仅的，只不过的）」，已经把形容词 mere 教过了。评分表规定「70 篇全库不重复」，这里实质上是同一个词占了两篇的名额，按「同一个词的不同形态占两格每对 −1」扣分。
- **改法**：只取消加粗，不换词（mere seedlings 句子本身很好，不动）。P3 其他没加粗的词（forester、novel、seedlings、warn 等）要么是透明派生，要么是 ✗档，所以不补。
  - 英文：`were **mere** seedlings` → `were mere seedlings`
  - 中文：`1997年实验里的树**只不过**(mere)是幼苗` → `1997年实验里的树只不过是幼苗`
  - 速查表：删掉 `| mere | adj. 只不过的，仅仅的（…）；merely adv. 仅仅 | 3 |` 这一行
  - 结果：词数 262 不变，重点词 55 → 54，各段 [11, 11, 9, 16, 7]

### 2. 【该改·项5 −0.5】re-examined 是基础词加透明前缀，换成 combed through
- **原文**：In February 2023 three researchers **re-examined** the field evidence.／三位研究者**重新审视**(re-examined)了野外证据
- **问题**：机器把它分到 ✓常用（Zipf 4.14），只是因为带连字符的形式不在词表里。它的词根 examine 本身是 ✗基础（脚本判 examined 为 ✗基础），re- 又是最透明的前缀，考研生一看就懂，占一个名额学不到新东西。按评分表「语言学家可以有理由改判」，改判为太基础。可替换的 scrutinise 机器判 ✗冷僻，scrutiny 已被占用；comb through 没被占用，判 ✓短语。它是阅读里高频的短语动词，最典型的宾语正是 evidence/data/records，又能体现复核了大量研究、逐条梳理的意思，跟中文「梳理」字面、引申义都对得上。
- **改法**（+1 词）：
  - 英文：`three researchers **re-examined** the field evidence` → `three researchers **combed through** the field evidence`
  - 中文：`三位研究者**重新审视**(re-examined)了野外证据` → `三位研究者**梳理**(combed through)了野外证据`
  - 速查表：`| re-examined | v. (re-examine) 重新审视，复查（re-examine the evidence/a case/an assumption）；re-examination n. | 4 |` → `| combed through | v. (comb through) 仔细搜查，逐一梳理（comb through the evidence/data/records/files）；comb n. 梳子 v. 梳（头发） | 4 |`
  - 结果：262 → **263 词**，重点词数不变（跟问题 1 一起改，为 263 词、54 个重点词，复跑硬性全过）
  - 如果写作组想保留原句，退一步的做法是只取消 re-examined 的加粗（262 词、53 个重点词，仍在 52–58 之内），但这样 P4 就少一个好词，不推荐。

### 3. 【该改·项8 −0.5】inconsistent 译成「前后不一」，意思偏了
- **原文**：They judged it too sparse, **inconsistent** or ambiguous…／这些证据或过于稀少，或**前后不一**(inconsistent)，或含糊不清
- **问题**：「前后不一」说的是同一个人或同一份材料自相矛盾、先后说法不同（证言前后不一、言行前后不一）。这里的 inconsistent 指 26 项野外研究彼此之间的结果不一致（来源里写的是「野外结果差异大」），并没有「自相矛盾」的意思。速查表把「前后不一的」列为第一义，同样有误导。
- **改法**：
  - 中文：`或**前后不一**(inconsistent)` → `或**互不一致**(inconsistent)`（「过于稀少／互不一致／含糊不清」三个四字格并列，节奏不变）
  - 速查表：`| inconsistent | adj. 前后不一的，不一致的（inconsistent results/findings；be inconsistent with 与……不符）；反复无常的 | 4 |` → `| inconsistent | adj. 不一致的，相互矛盾的（inconsistent results/findings 互不一致的结果；be inconsistent with 与……不符）；前后不一的，反复无常的（inconsistent behaviour） | 4 |`
  - 英文不用动；词数不变

### 4. 【可改·项9 −0.5】「养育自己的亲属」动宾搭配不顺
- **原文**：as "mother trees", **nurture** their **kin**／还会作为“母树”**养育**(nurture)自己的**亲属**(kin)
- **问题**：「养育」的宾语一般是子女、后代（养育儿女），「亲属」泛指成年亲戚，「养育亲属」读起来别扭。nurture 的词典核心义是 care for and protect sb/sth while they are growing（OALD），「照料、呵护」正好对上；kin 保留「亲属」，跟速查表一致。
- **改法**：
  - 中文：`还会作为“母树”**养育**(nurture)自己的**亲属**(kin)` → `还会作为“母树”**照料**(nurture)自己的**亲属**(kin)`
  - 速查表：`| nurture | v. 养育，培育，滋养（nurture children/the young/talent）；n. 养育（nature and nurture 先天与后天） | 3 |` → `| nurture | v. 养育，照料，呵护（成长中的人或物）（nurture children/the young/seedlings）；培养，扶植（nurture talent/an idea）；n. 养育（nature and nurture 先天与后天） | 3 |`
  - 英文不用动；词数不变

## 可改（不扣分，供写作组参考）

- A. `In 26 field studies, networks helped…` → `Across 26 field studies, networks helped…`：汇总多项研究时，across 比 in 更地道，也不会被误读成每一项研究里都如此。词数不变。
- B. 「这个比喻**果然**令人难以抗拒」：「果然」带「不出所料」的意思，英文 proved 没有这一层。不过上一句刚说完 catchy，可以理解为顺势承接，所以不扣分。想更贴近原文，可以改成「事实证明，这个**比喻**(metaphor)**令人难以抗拒**(irresistible)」。
- C. 「……有所助益和有所**妨碍**(hindered)的情形大致一样多，而以**中性**(neutral)效应**居多**(predominating)」：「以……居多」的范围靠句首的「在26项野外研究中」撑着，但紧挨着的主语是「助益和妨碍的情形」，细读会以为是在这两类情形里中性居多。可以在「而」后加「总体上」：`而总体上以**中性**(neutral)效应**居多**(predominating)`。
- D. 速查表 filaments 的第一义「（真菌的）菌丝」是本文义，建议调成 `n. (filament) 细丝，丝状物；（灯泡的）灯丝；本文指真菌的菌丝（fungal filaments）`，先给词典义。
- E. 速查表 allure 的动词用法很少见（OALD 只收名词），建议把 `v. 吸引，诱惑` 换成 `alluring adj. 诱人的`，更有用。
- F. bestseller 是透明复合词，但它是「畅销书」的专用词，不能字面理解成「卖得最好的人」，学生写作也用得上，所以保留，不扣分。

## 达标与预计

当前 97.5 分，已达标，没有硬伤。问题 1–4 都改完，预计 **100 分**（项5 回到 12、项8 回到 10、项9 回到 10）；可改 A–F 不影响分数。改后稿 `rewrite/18/_rv-语言学教授-r1.md` 已复跑 draft_check：263 词、54 个重点词（在 52–58 之内）、硬性全过，新词 combed through 不在 used_words.json 里。
