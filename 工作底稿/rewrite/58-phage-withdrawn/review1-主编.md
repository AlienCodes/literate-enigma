# 第 58 篇评审 · 英文总编辑 · 第 1 轮

## 总分：92.5 / 100（无硬伤；未达 95）

| 项 | 满分 | 得分 |
|---|---|---|
| 1 史实准确 | 15 | 14 |
| 2 论证与结构 | 10 | 9 |
| 3 语言质量 | 15 | 12.5 |
| 4 适配读者 | 5 | 5 |
| 5 学习价值 | 12 | 11 |
| 6 用法典型 | 8 | 8 |
| 7 速查表释义 | 10 | 10 |
| 8 忠实 | 10 | 9.5 |
| 9 通顺地道 | 10 | 8.5 |
| 10 重点词对应 | 5 | 5 |

> 按用户新要求：重点词 31 个（低于 50）与 bacteriophage 冷僻均**不扣分**；只判断每个加粗词是否放得自然，以及是否违反台账。

## 机检（英文单独抽出，逐行读，未过滤）
`en_check.py`：段落词数 [55, 49, 58, 62, 44]，合计 268 ✓（已到约稿单硬上限 268）；候选 31 个；✗冷僻 bacteriophage（用户已认可）、△短语 over the counter；无“已被占用”行。
**但**：**psychiatry**、**bacterium** 两词列在约稿单第 7 节“同根／已占勿加粗”名单里（台账已有 psychology、bacteria），en_check 没拦住，必须去粗（问题 1）。

## 逐句核对（对照约稿单 §3 与 S1–S5）

**P1**
- In late 2015 … 69-year-old psychiatry professor at UC San Diego, fell ill in Egypt ✓（S1）。
- The bacterium responsible … **shrugged** off every available **antibiotic**：生动，但 S1 是“多重耐药菌株**后来变得**对所有可用抗生素耐药”，shrugged off every… 写成一开始就全不怕，压缩了“逐步失效”这一层（可改，见问题 6）。
- After he was flown home, a **surgical** drain slipped and **spilled** the **germs** into his **abdomen** and bloodstream ✓。
- Septic shock followed, and he lay **unresponsive** in a **coma**：unresponsive 与 coma 同义叠用（昏迷即无反应），且全篇已顶 268 词，删 unresponsive 正好腾出一词（问题 3）。

**P2**
- Help came from a **century-old** idea ✓ 过渡利落。
- 1917、巴斯德研究所、痢疾病人样本、发现一种**捕食**细菌的病毒 ✓；He named it the **bacteriophage**, **literally** "bacteria-eater" ✓。
- proposed it as an **antidote**：antidote 是“解毒剂”（针对毒物），细菌感染不是中毒，用词错位（问题 2）。
- Frederick Twort had reported a similar agent in 1915 ✓ 公允（未把德埃雷勒写成唯一发现者）。

**P3**
- After the Second World War, penicillin became medicine's **cornerstone**, early preparations proved less reliable, and phages became a Western **outcast**：**early preparations** 紧跟 penicillin，读者会理解为“早期青霉素制剂不可靠”，正好与事实相反——S3 说的是早期**噬菌体**制剂不可靠。逻辑断口（问题 2）。
- Phage therapy found a **haven** in Soviet Georgia ✓；Eliava 1923 年建所、德埃雷勒 1933–35 在那里工作 ✓。
- Eliava was shot in Stalin's **purge** of 1937：S3 只写 executed；Stalin's purge 是公认史实背景，可接受，但 shot（行刑方式）属来源外细节，又贴近约稿单 ✗“政治细节展开”。建议 executed（可改，见问题 6）。
- yet phage **cocktails** were even sold **over the counter** ✓（S3），yet 的转折（创始人被杀、疗法照旧普及）成立。

**P4**
- 妻子、流行病学家斯特拉斯迪四处求噬菌体 ✓。
- Teams at Texas A&M and the US Navy, whose collection drew partly on **sewage**, found matches：whose 可指 the US Navy，也可指 Teams（两队），S4 只说海军的藏品来自污水，指代宜收紧（问题 4）。
- 2016 年 3 月、美国首位静脉输注噬菌体治疗全身性多重耐药感染 ✓；约三天后苏醒 ✓；8 月 12 日出院 ✓。

**P5**
- 抗生素耐药日益严重、带动噬菌体疗法重获关注 ✓（S5，只写概括）。
- One recovery cannot prove phages will replace antibiotics, but it suggests … deserves a second look：分寸好，主动排除“取代抗生素”的过度推论 ✓。
- **结尾** Ninety-nine years separated d'Hérelle's discovery from Patterson's first treatment.
  - 算术：1917 → 2016 = 99 ✓；句首拼写数字，非阿拉伯数字 ✓；无 virus／saved／life ✓；非 51–57 已用结构，也非 44–57 其他结尾 ✓；无禁用词与标点 ✓。
  - **first treatment** 有歧义：读成“他第一次接受治疗”（他 2015 年底就开始治疗了），应是“第一剂噬菌体”（问题 5）。

## 加粗词是否自然
多数自然：coma、preys、literally、cornerstone、outcast、haven、purge、cocktails、over the counter、sewage、infused、vein、systemic、discharged、resurgence 均为该词最常见的用法。
略牵强者：**shrugged**（拟人）、**antidote**（错位，见问题 2）、**unresponsive**（与 coma 重复）、**threat**（偏基础）、**awakened**（woke 更自然，awakened 稍书面）、**forsaken**（文学色彩重，与 abandoned 相比略做作，但 abandoned 在台账禁区内，可接受）。

## 必改

**1.（必改）第 5 项 −1：台账禁粗词**
- **psychiatry** → 去粗（psychiatry professor 照写）
- **bacterium** → 去粗（The bacterium responsible 照写）
- 中文同步删去两处加粗对应：“精神病学教授”“罪魁祸首是鲍曼不动杆菌”。

**2.（必改）第 2 项 −1；第 3 项 −1：两处语义错位**
- P3：early preparations proved less reliable → **early phage preparations** proved less reliable（+1 词）
- P2：proposed it as an **antidote** → proposed it as a treatment（0 词；antidote 不宜；remedy／cure／therapy 均已占用，treatment 为基础词，不加粗）
- 中文：“提出把它当作一种解药” → “并提出可以用它治疗细菌感染”；“早期的噬菌体制剂又不够可靠”已正确，保持。

**3.（必改，配合字数）第 3 项 −0.5**
- he lay **unresponsive** in a **coma** → he lay in a **coma**（−1 词，抵消问题 2 的 +1；consistent 268）

**已实测 1–3**：268 词，段落 [54, 49, 59, 62, 44]，无占用行 ✓（加粗数降至 28，按用户意见不扣分）。

## 该改

**4. 第 3 项 −0.5**
- 原文：Teams at Texas A&M and the US Navy, whose collection drew partly on **sewage**, found matches.
- 问题：whose 可回指“两支团队”，而 S4 只说海军的藏品部分取自污水。
- 改法：Teams at Texas A&M and the US Navy found matches, the Navy's collection drawing partly on **sewage**.（+1 词）。全文已到 268 上限，须另删一词方可采纳（例如 P5 One recovery cannot prove phages will replace antibiotics 中删 will → cannot prove phages replace antibiotics，语义不变，−1 词）。

**5. 第 3 项 −0.5**
- 结尾 Patterson's first treatment → Patterson's first dose（0 词；承接上段 infused，语义清楚是第一剂噬菌体）
- 中文：“到帕特森接受第一剂噬菌体”。

## 可改

**6. 第 1 项 −1（两处）**
- **shrugged** off every available **antibiotic** → 若字数允许，可作 had come to shrug off every available antibiotic（+3），体现“逐步耐药”；否则保留。
- Eliava was shot in … → Eliava was executed in …（0 词；与来源一致，不展开行刑细节）

## 中文（第 8、9 项）

- 作祟的**菌体**(bacterium)是鲍曼不动杆菌 → **罪魁祸首是鲍曼不动杆菌**（“菌体”不是这里的意思；bacterium 去粗后无需对应）
- 它对所有可用的抗生素都**满不在乎** → 它对所有现有抗生素都**无动于衷**（“满不在乎”太口语、拟人过头）
- 把病菌一下子**泼洒**进他的腹腔和血液 → 病菌随之**流入**他的腹腔和血液（“泼洒”不合医学语境）
- 紧接着是感染性休克，他陷入昏迷，毫无反应 → 随之而来的是感染性休克，他陷入昏迷（随英文删 unresponsive）
- 它**激起**了噬菌体疗法的**复兴热潮** → 它让噬菌体疗法重新**受到关注**（“复兴热潮”夸大了 resurgence of interest，第 8 项 −0.5）
- “噬菌体混合制剂后来甚至可以在柜台直接购买” → “……甚至在药店柜台就能买到”（更自然）
- “从德埃雷勒的发现到帕特森的第一次治疗，中间隔了九十九年” → “从德埃雷勒发现噬菌体，到帕特森接受第一剂噬菌体，中间隔了整整九十九年”

## 达标判断
无硬伤；92.5 < 95，本轮不会签。落实必改 1–3 与该改 4–5、中文各条后，预计 98 左右，可在下轮会签。

总分 = 各项之和 已核（14+9+12.5+5+11+8+10+9.5+8.5+5 = 92.5）
