# 评审-英文总编辑-17（第 1 轮）·《The Crowded Heavens / 拥挤的苍穹》

**总分：97 / 100（达标线 95 · 零硬伤）**　draft_check（不加 --claim）：267 词、57 重点词、硬性全过；各段词数 [50, 46, 51, 55, 65]；工具提示"各段重点词 [7, 11, 13, 14, 12] 分布不均"，只是提示，不算硬性项，也不扣分。

本评审结论：**达标**。下面 4 处该改／可改都已实测；连同 1 处不扣分的建议一起改完是 269 词（上限 271），draft_check 硬性全过。比对稿放在 `rewrite/17/_rv-主编-r1.md`，只供参考，不是定稿。

| 项 | 满分 | 得分 | 扣分点 |
|---|---|---|---|
| 1 史实准确 | 15 | 14 | 问题 1：the encounter was not among the week's closest 字面上不成立（实际那次交会就是直接相撞）−1 |
| 2 论证与结构 | 10 | 10 | 因果链完整，三处对冲都在，结尾有正文支撑 |
| 3 语言质量 | 15 | 15 | 时间规则全部合规；标题合格 |
| 4 适配读者 | 5 | 5 | 专名、术语首次出现都有交代 |
| 5 学习价值 | 12 | 12 | 57 个词全在 ✓ 档（复跑 `word_tier.tier` 抽查 17 个，全部 ✓） |
| 6 用法典型 | 8 | 8 | 搭配都典型（mitigate 的用法见不扣分建议 a） |
| 7 速查表 | 10 | 10 | 词典义加搭配，首义和正文译法对得上 |
| 8 忠实 | 10 | 9 | 问题 2："此后多年"把时间锚点移到了 2022 年 −1 |
| 9 通顺地道 | 10 | 9.5 | 问题 3："散播碎片"搭配不当 −0.5 |
| 10 重点词对应 | 5 | 4.5 | 问题 4：加粗的 **碎片**(splinters) 和全文没加粗的 fragments 共用"碎片" −0.5 |
| **合计** | 100 | **97** | |

## 一、史实复核（WebSearch，2026-10-01；celestrak.org、agi.com 被出口代理拦截，改用 Kelso 论文的检索摘要交叉核对）

| # | 正文写法 | 结论 | 来源 |
|---|---|---|---|
| 1 | On 10 February 2009, nearly 790 kilometres above Siberia … about 42,000 kilometres an hour | ✓ 16:56 UTC，泰梅尔半岛上空 789 km；相对速度 11.7 km/s，约合 42,120 km/h。"nearly 790"和"about 42,000"都准确 | https://en.wikipedia.org/wiki/2009_satellite_collision ；https://en.wikipedia.org/wiki/Iridium_33 |
| 2 | Kosmos 2251, a Russian military satellite, had been derelict since about 1995 | ✓ Strela-2M 军用通信卫星，1993 年 6 月 16 日发射；俄方称 1995 年停止工作，查不到月份，about 1995 处理得当 | https://en.wikipedia.org/wiki/Kosmos_2251 ；https://russianforces.org/blog/2009/02/collision_in_space.shtml |
| 3 | The Russian hulk, lacking propulsion, could not | ✓ 这一型号没有推进系统 | 同 #2 |
| 4 | the first accidental collision between two intact satellites | ✓ "first known accidental collision between two intact satellites"；accidental 和 intact 两个限定都保留了（1996 年 Cerise 被火箭碎片击中那次不是两颗完整卫星相撞） | 同 #1；https://www.guinnessworldrecords.com/world-records/605473-first-satellite-collision |
| 5 | forecast a narrow miss of about 584 metres, yet the encounter was not among the week's closest; such warnings were frequent and imprecise | ✓ 史实方面：SOCRATES 在 2 月 10 日 15:02 UTC 的报告里预测 584 m；这次交会既不是该期报告的第一名，也不是当周任何一颗铱星的第一名。Kelso 的论文说，相撞前一周 14 期报告每期都列了这次交会，但没有一期进前十，撞时总排名第 152。依据的是 TLE（两行轨道根数），精度有限。措辞问题见问题 1 | https://celestrak.org/events/collision/ ；https://celestrak.org/publications/AAS/09-368/AAS-09-368.pdf ；https://celestrak.org/publications/AMOS/2009/AMOS-2009.pdf |
| 6 | more than 2,000 catalogued fragments and a multitude too small to pinpoint | ✓ 2011 年 7 月已编目超过 2,000 块；到 2016 年合计约 2,300 块（宇宙 1,668 块，铱星 628 块）；更小的碎片无法逐一跟踪 | https://ntrs.nasa.gov/api/citations/20150003820/downloads/20150003820.pdf ；https://ntrs.nasa.gov/api/citations/20090017680/downloads/20090017680.pdf |
| 7 | many would linger for decades | ✓ NASA：两星都有部分碎片会在轨道上留到本世纪末 | 同 #6 |
| 8 | In January 2012 the International Space Station fired its thrusters to dodge an Iridium 33 remnant | ✓ 2012 年 1 月 13 日推进器点火 54 秒，轨道抬高约 300 m，避开一块约 10 cm 的铱星33号碎片 | https://www.csmonitor.com/Science/2012/0113/Space-station-moves-to-avoid-space-junk-in-orbit ；https://www.nbcnews.com/news/amp/wbna45987968 |
| 9 | In June 1978 two NASA scientists envisaged a vicious spiral, later named the Kessler syndrome | ✓ Kessler 和 Cour-Palais 在 1978 年 6 月 1 日出版的 JGR 第 83 卷 A6 期发表论文：碰撞产生碎片，碎片又提高再撞的概率，最终形成碎片带。"Kessler syndrome"这个名字是后来才有的 | https://ntrs.nasa.gov/citations/19780057167 ；https://en.wikipedia.org/wiki/Donald_J._Kessler |
| 10 | By the end of 2024 … about 40,000 objects, only about 11,000 of them functional | ✓ ESA《2025 年空间环境报告》（数据截至 2024 年底）：约 40,000 个被跟踪物体，其中约 11,000 个是在用航天器 | https://www.esa.int/Space_Safety/Space_Debris/ESA_Space_Environment_Report_2025 ；https://heise.de/-10348061 |
| 11 | In September 2022 America's Federal Communications Commission … mandated disposal of low-orbit craft within five years of retirement, scrapping a 25-year guideline | ✓ 2022 年 9 月 29 日以 4:0 通过；2,000 km 以下的卫星任务结束后最迟 5 年离轨，取代 25 年准则；有两年过渡期。补充说明：IADC 和联合国的国际准则仍然是 25 年。正文的主语是"美国的 FCC"，所以 scrapping 只在 FCC 的监管范围内成立，读者不会理解成全球废除，不扣分（见三·c） | https://www.satellitetoday.com/government-military/2022/09/30/fcc-adopts-5-year-rule-for-deorbiting-satellites/ ；https://nextgov.com/policy/2022/09/fcc-adopts-new-5-year-rule-orbital-debris-despite-pushback/377876 ；https://orbitalradar.com/glossary/25-year-rule |
| 12 | Operators now routinely manoeuvre satellites out of harm's way | ✓ 空间站自 1999 年起累计避让碎片 39 次以上（到 2024 年 11 月）；还有大量商业卫星例行避让 | https://livescience.com/space/space-exploration/iss-dodges-its-39th-piece-of-potentially-hazardous-space-junk-experts-say-it-wont-be-the-last |
| 13 | 结尾 For years, spacecraft … kept swerving around its splinters | ✓ 没有新增事实。除了 2012 年 1 月这次，2014 年 10 月空间站又借对接的 ATV 货运飞船点火，避开一块宇宙2251号碎片；2015 年还有两次避让 | https://sma.nasa.gov/news/articles/newsitem/2015/11/23/two-more-collision-avoidance-maneuvers-for-the-international-space-station ；https://www.smithsonianmag.com/smart-news/international-space-station-just-avoided-gravity-disaster-180953265/ |

**时间规则（10-01 细则）**：关键事件都写到了月或日：10 February 2009、June 1978、January 2012、September 2022、by the end of 2024。about 1995 是"查不到月份"的次要事实，任务书和"史实与来源"都注明了。for decades、over decades、for years、within five years 都是相对时间，用来补充，没有代替月份。正文没有只写年份的关键事件。

## 二、逐条问题

### 问题 1【该改 · 第 1 项 −1】"the encounter was not among the week's closest"字面上不成立
- 原文：A public screening service had forecast a **narrow** miss of about 584 metres, yet the **encounter** was not among the week's closest;
- 问题：这里说的是预测的排名，可 the encounter 指的是那次真实的交会，而真实的交会是正面相撞，距离为零，恰恰是当周最近的一次。认真的读者读到这里会停一下：明明撞上了，怎么说"不在最近之列"？加一个 predicted 就能把"预测"和"实际"分开，史实也更准确（Kelso：14 期报告没有一期进前十）。
- 改法：yet the **encounter** → yet the predicted **encounter**（+1 词，267 → 268）
- 中文：但这次**交会**(encounter)并未排进当周最接近的几次之列 → 但在当周的预测中，这次**交会**(encounter)并未排进距离最近的几次之列
- 速查表：不用改。

### 问题 2【该改 · 第 8 项 −1】"此后多年"改变了时间锚点
- 原文：For years, spacecraft whose owners had no part in that crash kept swerving around its **splinters**.
- 译文：此后多年，一些航天器的主人与那次相撞毫无瓜葛，……
- 问题：这句紧跟在"2022年9月……废除了原先的25年准则"后面，"此后"会被读成"2022 年以后的许多年"。这就成了一个英文里没有、而且到 2026 年还无从谈起的说法。英文的 For years 没有锚定在 2022 年，读者自然理解为相撞以后的若干年。
- 改法（英文不变）：此后多年 → 多年间
- 改后全句：多年间，一些航天器的主人与那次相撞毫无瓜葛，这些航天器却仍要一再转向，绕开它留下的**碎屑**(splinters)。（"碎屑"见问题 4）

### 问题 3【可改 · 第 9 项 −0.5】"散播碎片"搭配不当
- 原文：即每次相撞都会**散播**(scatter)碎片
- 问题："散播"后面一般接谣言、种子、病毒，接"碎片"不顺。速查表的首义也写成了"散播"。
- 改法（英文不变）：**散播**(scatter) → **散布**(scatter)
- 速查表：`| scatter | v. 散布，撒；（使）分散，（使）四散（scatter fragments/seeds；the crowd scattered） | 4 |`

### 问题 4【可改 · 第 10 项 −0.5】加粗的 splinters 和不加粗的 fragments 共用"碎片"
- 原文：结尾绕开它留下的**碎片**(splinters)；但正文里 fragments 出现了 3 次（2,000多块已编目的碎片、大量碎片、散布碎片），都译成没有加粗的"碎片"。
- 问题：学生会把"碎片"记成 splinters 的对应词，可全文"碎片"最常对应的是 fragments。两个不同的英文词落到同一个中文上，加粗的对应就失去了区分度。
- 改法（英文不变）：**碎片**(splinters) → **碎屑**(splinters)
- 速查表：`| splinters | n. (splinter) 碎屑，碎片，裂片（splinters of glass/metal/wood）；v. 碎裂；分裂（a splinter group 分裂出来的派别） | 5 |`（首义和正文一致）

### 不扣分的可改项（有余量再改）
- a. **mitigate 的宾语**：the cascade … is not **inevitable**; it can be **mitigated**。这里的 it 指 cascade。mitigate a cascade 不算错，但学生最该学的搭配是 mitigate the risk，速查表的例证也是 mitigate risks。改成 the risk 后，前半句说"并非必然"，后半句说"风险可以缓解"，层次也更清楚。改法：it can be **mitigated** → the risk can be **mitigated**（+1 词，268 → 269）。中文：也可以**加以缓解**(mitigated) → 其风险也可以**加以缓解**(mitigated)。速查表不用改。
- b. **a public screening service**：考研生可能把 screening 读成"放映"，不过后面紧跟着 had forecast a narrow miss，加上中文"碰撞筛查服务"，读得懂，不扣分。如果想更直白，可以写 collision-screening（连字符词按 1 词计，词数不变）。
- c. **scrapping a 25-year guideline**：国际上（IADC、联合国）仍然是 25 年准则。正文主语是美国的 FCC，scrapping 只在 FCC 的监管范围内成立，不扣分。建议在"史实与来源"【T18】里补一句"25 年仍是 IADC 和联合国的国际准则，正文只说美国规则"。
- d. **结尾的事实支撑**：正文唯一具体的例证是国际空间站，而空间站的伙伴里有俄罗斯。说空间站的主人和那次相撞"毫无瓜葛"严格讲不完全成立。不过结尾写的是泛指的 spacecraft whose owners…，另外有 Operators now routinely manoeuvre 撑着，不扣分。建议在"史实与来源"【结尾】里补上 2014 年 10 月空间站借 ATV 点火避开宇宙2251号碎片、2015 年又避让两次（NASA SMA 来源见上表 #13）。
- e. 中文"点燃推进器"可以改成"启动推进器"；"老古董"(relic) 的语气比英文俏皮一些。这两处都可以接受，交语言学家定。

## 三、论证、结构、对冲、标题、结尾

- **结构**：撞击（第 1 段）→ 为什么没人避让，并点出"一方的弃物毁了另一方的资产"（第 2 段）→ 残骸把风险摊给所有人（第 3 段）→ 1978 年的设想、2009 年只是例证、2024 年底的现状（第 4 段）→ 对冲、对策、收束（第 5 段）。每段都往前推一步，however 和 though 两处转折都站得住。第 5 段 65 词偏长，但每句都有用，不扣分。
- **公平性**：宇宙2251号被叫作 derelict、hulk、discarded relic，贬义略重，但 lacking propulsion, could not 交代了它客观上无法避让。正文全程不点国名、不指责（One owner's … another's），铱星方没有避让，也用"预警既频繁又不精确"作了交代，没有把责任推给任何一方。公平。
- **对冲**：任务书要求的三处对冲都在：第 2 段预警不准（frequent and imprecise），第 4 段首例不等于失控（without triggering a runaway chain reaction），第 5 段风险可以管理（over decades / not inevitable / can be mitigated）。数字都有限定词：nearly 790、about 42,000、about 1995、about 584、more than 2,000、many、about 40,000/11,000。没有夸大，也没有对冲过度。ESA 说"不主动清除，碎片还会增长"，正文没写这句，但正文只说"可以缓解"，没说"已经解决"，所以不算偏向乐观。
- **标题**：The Crowded Heavens /《拥挤的苍穹》。大气、响亮，中英严格对应，不是论点式短语，符合 10-01 的标题规则。"拥挤"在正文里有支撑：预警频繁；撞时那一期报告里有 151 次预测比它更近；约 4 万个被跟踪物体里只有约 1.1 万个在用。它和 08《Saving the Sky》、16《The Sound That Shook the World》的框架都不撞。比任务书推荐的 When Satellites Collide 少了一点事件感，但立意更高，我同意采用，不扣分。
- **结尾**：For years, spacecraft whose owners had no part in that crash kept swerving around its splinters.（16 词）
  - 支撑：第 3 段写了空间站避让，第 5 段写了运营方例行避让，没有新增事实。
  - 呼应：kept swerving 和第 2 段开头的 Neither craft swerved 首尾相扣：当事的两颗卫星都没躲，躲的是一直在躲的局外人。whose owners had no part 落到"公地"论点上，前面的 One owner's … another's 和 endangered everyone else 也都在为它铺垫。
  - 和 05–16 比：05/13 是 may 格言，06 是分号加 it took，07 是分号对举，08 是 began with，09 是 The paradox holds 加冒号，10 是 What…was，11 是 until 加 may，12 是冒号加 may never，14 是 may、if、冒号、破折号，15 是 , but…heaviest，16 是介词三联加 began to glimpse。第 17 篇的结尾是"时间状语 + 具体画面 + 关系从句 + kept V-ing"，句式新；没有冒号、分号、may、began、if/until、最高级、问号、破折号；也没有标题词和 satellite/collide/collision。**和 05–16 都不同，合格。**
  - 小提示：英文的 For years 本身没有歧义，问题出在中文"此后多年"（见问题 2）。

## 四、达标

当前 **97 分**，零硬伤，**本评审达标**。

建议改问题 1–4，词数按顺序累计：267 → 268（问题 1）；问题 2–4 只动中文和速查表，仍是 268。如果再加不扣分项 a，是 **269 词**（上限 271）。改完 57 个重点词，draft_check 硬性全过。比对稿 `rewrite/17/_rv-主编-r1.md` 已经实测（问题 1–4 加 a 项）：269 词，各段词数 [50, 47, 51, 55, 66]。预计 **99–100 分**。
