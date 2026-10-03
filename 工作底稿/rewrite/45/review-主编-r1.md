# 第 45 篇评审 · 英文总编辑 · 第 1 轮

## 总分：97.5 / 100（无硬伤）

| 项 | 满分 | 得分 |
|---|---|---|
| 1 史实准确 | 15 | 15 |
| 2 论证与结构 | 10 | 10 |
| 3 语言质量 | 15 | 13 |
| 4 适配读者 | 5 | 5 |
| 5 学习价值 | 12 | 12 |
| 6 用法典型 | 8 | 8 |
| 7 速查表释义 | 10 | 10 |
| 8 忠实 | 10 | 10 |
| 9 通顺地道 | 10 | 9.5 |
| 10 重点词对应 | 5 | 5 |

## 机检（英文单独抽出，逐行读，未过滤）
`en_check.py`：段落词数 [54, 56, 54, 47, 58]，合计 269 ✓；候选 53 个全部 ✓；**无“已被占用”行** ✓；各段加粗 11/11/10/11/10 ✓。

## 逐句史实核对（对照约稿单 §3 与 S1–S9）
- P1：1936 年 17 次往返 ✓（S6）；休息厅、当年有三角钢琴 ✓（that year 限定得当，1937 年已撤，S5）；吸烟室气闸、唯一电点火器 ✓；美国禁止向德出口氦气、只能用氢 ✓（embargo 概括 1927 法，可接受）
- P2：1937-05-03 离开法兰克福 ✓；晚点数小时、雷暴、盘旋一小时以上 ✓；1937-05-06 约 7:25 pm 尾部见火 ✓；约半分钟烧毁 ✓（未写 34 秒定数）；**crumpled frame** ✓——照片所见正是扭曲倒塌的铝骨架，不夸张；全篇未把燃烧写成“爆炸”✓
- P3：97 人中 62 人生还、近三分之二（63.9%）✓；艇上 35 人＋地面 1 人遇难 ✓；14 岁侍应生被破裂水箱浇透、从舱口落下逃生 ✓；**the soaking saved him** ✓——S7 原意即“saved by a soaking from a burst water tank”，有来源支持
- P4：新闻片摄影机与摄影师在场 ✓；电台记者目击录音非直播、次日播出 ✓；原因未确证（一处对冲）、主流解释静电点燃泄漏氢气 ✓；涂料说被否 ✓（doped fabric 指涂过涂料的蒙皮，准确）
- P5：
  - **Akron 比较**：1933 年 Akron 73 人遇难 ✓（S8），兴登堡 36 人在 P3 已交代，读者自然得出“Akron 更惨”；**won less notoriety** 有 S8“被遗忘的飞艇灾难”支持 ✓。暗示方向正确：未说兴登堡“最致命”，而是说更致命的 Akron 反而不出名。小提醒：Akron 是海军飞艇、无乘客，比较对象是“飞艇失事”而非“客运”，原文未混淆 ✓。
  - **Fire on camera** left a **fateful** **image**：镜头确实拍下大火（P4）✓；fateful 指“后果深远”，不是“命中注定”，用法正确 ✓（但中文译法见问题 4）
  - Graf Zeppelin 退役、后被拆 ✓（S9 1937 退役、1940 拆）；**a glamorous epoch of aviation closed**：a 限定为“航空史上的一个时代”（即载客飞艇时代），未说整个航空业结束 ✓，符合 T11
- **结尾**：The ship's first journey to North America had begun on 6 May 1936, exactly a year before the fire.（19 词）
  - 事实：S6 首次北美航程 1936-05-06 自法兰克福出发 ✓；与失事日 1937-05-06 恰好一年 ✓；修辞成立
  - 标题词：无 last／flight／Hindenburg ✓（journey 替 flight，ship 替 Hindenburg）
  - 同构检查：非时间状语开头（主语 The ship's first journey）✓；不同于 30 篇“That pronouncement came almost N years after”（无 That+名词、无 came、无 years after）✓；不同于 44 篇“The tests had hidden…, so they could not…” ✓；不同于 38 篇“The discoverer's ashes swept past…”（同为 The + 名词's 开头，但谓语与结构不同）✓；无 What／Yet／Every 开头、最高级、问句、冒号分号破折号、may／might、never、remained、had left、came from ✓
  - 不新增事实之外的判断 ✓

## 其余检查
- 对冲：about 7:25、about half a minute 分在两句；has not been definitively established 一处 ✓；全篇每句至多一个 ✓
- 代词跨段：P2 以 The airship 开头、P3 以 Sixty-two 开头、P5 以 The 1933 crash 开头，无跨段代词 ✓
- 同义堆叠：见问题 3

## 逐条问题

**1.（该改）第 3 项 −0.5**
- 原文：Sixty-two of the 97 aboard survived, a **proportion** of almost **two-thirds**, while a **minority** died: 35 aboard and one man on the ground.
- 问题：“少数死亡”指的是 97 人中的少数，冒号后却把地面上的一人也算进去，口径混杂。
- 改法：…while a **minority** of 35 died, as did one man on the ground.（+1 词，270；P3 加粗不变）
- 中文：……遇难的是**少数**(minority)，共35人，地面上另有一名男子遇难。
- 已实测：270 词，加粗 53，无占用行 ✓

**2.（可改）第 3 项 −0.5**
- 原文：…one electric lighter, for the gas was **combustible**. An American **embargo** on **helium** **export** had left the ship relying on hydrogen.
- 问题：the gas 先于 hydrogen 出现，读者要读到下一句才知是什么气；两句互换顺序即可（0 词）。

**3.（可改）第 3 项 −0.5**
- 原文：He dropped through a **hatch** and **scrambled** clear, **narrowly** escaping.
- 问题：scrambled clear 与 narrowly escaping 意思重叠，且上句已说 the soaking saved him。P3 加粗恰 10，保留。

**4.（可改）第 3 项 −0.5**
- 原文：**Fire on camera** left a **fateful** **image**…
- 问题：无冠词的标题式名词短语作主语，略像新闻标题；可作 The fire on camera…（+1 词）。

**5.（该改）第 9 项 −0.5**
- 原文：**静止**(static)**电荷**(electricity)
- 问题：static electricity 中文是“静电”，拆成“静止电荷”不是通行说法。
- 改法：**静**(static)**电**(electricity)——或“**静电**(static electricity)”整词对应（须与速查表一致）
- 另：命中注定(fateful)般的画面——fateful 此处是“后果重大”，建议改“影响深远的画面”（可改，不另扣）

## 改后词数
269 +1（1）= 270 ✓（若同时采纳 4，271 ✓）

## 达标判断
≥95、零硬伤，按我这一票通过；无必改项。结尾修辞事实成立，未与 05–44 同构，未含标题词。落实 1、5 预计 98.5。

会签：同意定稿

总分 = 各项之和 已核（15+10+13+5+12+8+10+10+9.5+5 = 97.5）
