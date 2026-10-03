# 第58篇（重写：鸟类导航）· 总编辑约稿单
> 致：母语作者、剑桥毕业生、报社撰稿人 ｜ 2026-10-02
> **用户原话：一定要尽全力，把这篇写成全世界最好的英语文章；从第一稿起就要顶级水平。用户硬标准只有两条：全文 ≤271 词、重点词 ≥50；其余一切服务于写成最好的文章。**
> 题材来自用户素材库第 4 篇《鸟类的导航系统》，但用户素材有事实错误（把 Oldenburg 的实验写成 Oxford），**事实只取本约稿单第 3 节史实表**。

## 1 用户的硬性标准（只有两条，任何一条不达标即退稿）
- **全文英文 ≤271 词**（以 en_check 合计为准；建议 255–271，给重点词留空间）。
- **重点词 ≥50 个**（目标 54–58，留出评审删词的余量）。
- 用户原话：除这两条外"其他都无所谓，但一定要写得非常自然、非常完美"。**段落数不强制**（4–6 段皆可，按叙事最佳节奏定）；**每段重点词数不强制**，但分布要自然，不要某段堆砌。
- 词库规则（第56篇起，继续执行）：每个重点词必须
  1. 出自第 6 节"已测词池"，或自己用 `bash $S/wt.sh 词…` 测为 OK **且** `python3 $S/stem.py 词…` 无真同根冲突（字母巧合可忽略，须注明）；
  2. 在句中自然、准确、不可替换——**宁可改写句子让好词自然出现，也绝不硬塞**；
  3. 同族词同篇只加粗一个形式。
## 1b 本社写作规范（总编辑制定，服务于质量）
- 英式拼写；句长 ≤32 词；每句最多 1 个对冲词；代词不跨段指代（每段首次提到人/鸟用名词）；无问号、叹号；句首无阿拉伯数字；**零直接引语**。
- 专名不加粗（Skokholm, Wales, Boston, Atlantic, Gustav Kramer, Stephen Emlen, Wiltschko, Klaus Schulten, Oldenburg, Henrik Mouritsen, Manx shearwater, European robin, indigo bunting 等）。
- 已占/同根勿加粗（示例）：compass(encompass) horizon(horizontal) planetarium(planetary) migrant/migrate/migration navigation orientation/orient/disoriented magnetism 以外的 magnet 家族只选一 rotation(rotate) sensitivity(sensitive) reaction(reactive) colony(colonial) wooden(woodland) internal(internally) correction calibrate shore marvellous boundless intuition metre longitude location inhabit mariner occupants breed dive electrical broadband spectrum disrupt insulate misled.

## 3 史实表（只用这些事实；来源见 src/sources_excerpts.md S1–S7）
| # | 史实 |
|---|---|
| T1 | 1952 年，Rosario Mazzeo 从威尔士外海 Skokholm 岛带走一只大西洋鹱（Manx shearwater，环号 AX6587），先火车到伦敦，再飞机到波士顿；6 月 3 日上午 8:15 在 Logan 机场放飞；6 月 16 日它已回到 Skokholm 的巢穴：约 3,200 英里开阔大西洋，12.5 天；他放飞后立刻从波士顿寄信，信比鸟晚到；Ronald Lockley 起初以为鸟是在伦敦就放了。当时是有记录的最长归巢飞行。 |
| T2 | 1950 年代，Gustav Kramer 把椋鸟关在圆形笼里，用镜子改变太阳的视位置，鸟的朝向随之改变；鸟把太阳当罗盘，并能补偿太阳一天中的移动。 |
| T3 | 1960 年代，Stephen Emlen 在天文馆里研究靛蓝彩鹀，遮掉部分星星后发现它们靠北极星周围的星座（天空旋转的中心）定向。 |
| T4 | 1972 年，法兰克福的 Wiltschko 证明欧亚鸲（知更鸟）利用地磁场；它的罗盘读的是磁力线的倾角，而不是南北极性。 |
| T5 | 1978 年，物理学家 Klaus Schulten 提出：光触发的化学反应可让鸟感知磁场；2000 年提出视网膜里的感光蛋白隐花色素（cryptochrome）是关键分子；2021 年实验室中知更鸟的隐花色素4 对磁场敏感，且比鸡、鸽子的更敏感。**仍是主流假说，未在活鸟体内完全证实。** |
| T6 | 2014 年（Nature），德国奥尔登堡大学：校园里未屏蔽的木屋中，知更鸟用不了磁罗盘；在接地的铝皮屏蔽木屋里恢复定向；拆掉接地或在屋内加噪声，又再次失灵；双盲实验；噪声来自日常电子设备，强度远低于世卫组织安全限值。 |
| T7 | 鸟如何知道"自己在哪里"（地图感）至今未完全弄清。 |

## 2 质量要求（"全世界最好"的具体含义）
- **开篇即抓人**：第一句就是具体场景，不要泛泛的"Twice a year, billions of birds…"。
- **每一段一个清晰的推进**（段落数自定）：悬念 → 线索一（太阳、星星）→ 线索二（磁场与眼睛里的化学）→ 现代转折（人类电子噪声让鸟迷路）→ 尚未解开的谜 + 有力结尾。
- 动词精准有画面；句子长短交错；不用空洞形容词，不加来源没有的心理描写和夸张。
- 科学表述必须准确且克制：磁感受的分子机制是**主流假说、证据增强但未完全证实**；"地图感"仍未解开。
- 考研价值：重点词以考研/六级/雅思层级的实用词为主，搭配地道。

## 4 结尾规则
- 不得含标题词（bird / beat / letter / home）；必须字面属实。
- 不得重复已用结尾结构："主句, + 名词短语"（51/52/54）；极短判词句（55）；"The year…saw"（56）；倒装；"In effect…"（57）；"X cannot prove…, but it suggests…"（58旧版）。
- 不得以时间状语、What、Yet、Every、Behind、But、Admirers 开头。
- 禁用：冒号、分号、破折号、最高级、may/might、never、remained、still、had left、came from、apparently、for/since 原因从句、独立主格 being、exactly、to the day。

## 6 已测词池（均已过 wt.sh 与 stem.py；见 pool-final.txt）
airliner unpacked courier detour doorstep homecoming homesick burrow(s) dwelling/dweller den cliff(s) lighthouse archipelago westward odyssey epic prodigious astounding endless nonstop stamina traveller wander/wanderer astray feathered chick(s) pigeon(s) robin(s) sparrow reptile salmon claws yolk flap glide skim dusk twilight sunrise sunset nocturnal celestial canopy vault twinkle shimmer gleam glimmer whirl spokes pole(s)/pole-star axis magnet/magnetic/magnetism(选一) inclination/incline(选一) needle pointer dial arrow tick retina eyesight protein(s) instinct/instinctive(选一) imprint interference voltage wavelength antenna appliances hut(s) foil blanket cloak smother sabotage meddle disturbance latent hint(s) decode unravel crack unanswered slippery sailor tiller atlas latitude proximity bearings confused/confusion jumble chatter din racket buzz peek awe bewildering eerie spooky enchanted flawless naive novice self-taught upbringing first-timer apprentice cooped hallmark unambiguous reclaim swivel tune/tuned
**词池不够时自行测词，必须两项工具都过。**

## 标题（暂定）The Bird That Beat the Letter Home ／《比信先到家的鸟》

## 5 中文要求
- 自然优美的中文，不是逐词直译；每个英文重点词对应一个**整词**中文加粗，写作 **中文**(english)；不得单字加粗；两个加粗词不得紧贴；不得添加英文没有的释义或信息。
