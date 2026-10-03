# 第 34 篇评审 · 英文总编辑 · 第 1 轮

## 总分：95 / 100（无硬伤）

| 项 | 满分 | 得分 |
|---|---|---|
| 1 史实准确 | 15 | 13.5 |
| 2 论证与结构 | 10 | 10 |
| 3 语言质量 | 15 | 12 |
| 4 适配读者 | 5 | 5 |
| 5 学习价值 | 12 | 12 |
| 6 用法典型 | 8 | 8 |
| 7 速查表释义 | 10 | 10 |
| 8 忠实 | 10 | 10 |
| 9 通顺地道 | 10 | 9.5 |
| 10 重点词对应 | 5 | 5 |

## 机检（英文单独抽出，逐行读，未过滤）
`en_check.py`：段落词数 [46, 50, 56, 60, 59]，合计 271 ✓（零余量）；候选 54 个全部 ✓；**无“已被占用”行** ✓；各段加粗 10/12/10/10/12 ✓。
替补词实测：penalty、notoriety ✓ 未占用；transformed、conveyed、condemned、verdict、ferried、hauled、acclaim、celebrity 已占用；transported △；renown 冷僻；term、sentence、carried、standing 基础词。

## 史实核对（对照任务书 §3）
- 1911-08-21 周一、闭馆日（customarily closed）✓；次日一位画家发现，未写姓名 ✓；闭馆一周 ✓
- 重开后观众排队看空位 ✓
- 1911-09-07 阿波利奈尔被捕、关押约一周 ✓；毕加索被问讯 ✓（interrogated 语气略重，但不失实）；Both were cleared ✓
- 佩鲁贾、意大利人、曾短期在卢浮宫做玻璃工 ✓；未写玻璃罩 ✓；周日藏身储藏室、白色工作罩衫、画藏衣下 ✓；夹层箱、巴黎住处、more than two years ✓
- 1913 年 12 月联系杰里 ✓；乌菲齐馆长在旅馆鉴定 ✓；1913-12-11 被捕 ✓
- 拿破仑：mistakenly believing 写成误信 ✓；In fact 达·芬奇应弗朗索瓦一世之邀带去 ✓
- 1914-01-04 回到卢浮宫 ✓；1914 年 6 月受审、一年零十五天、about seven months ✓
- 史学家归属：Many historians argue ✓——**但结尾 Its fame began with a bare wall 把这一观点改成了直陈事实**，见问题 1。
- 无 Valfierno、无同伙、无卡夫卡 ✓。
- 叙事润色（quietly、patiently、strode、lurked）属评分表允许的“不改变事实的润色”，不扣第 1 项；其中 patiently 可顺手删以腾词数。

## 逐条问题

**1.（必改）第 1 项 −1.5**
- 原文：Its **fame** began with a **bare** wall.
- 问题：① 上句才把“失窃成就名气”归给史学家，结尾却去掉归属、写成定论，违反任务书公允条款；② 失窃前此画已受推崇，Its fame 不加限定即过头。
- 改法：If so, its **fame** began with a **bare** wall.（+2 词；If so 为条件状语，非时间状语，不触 §5 禁令；无标题词、无禁用结构）
- 中文：若真如此，它的**名气**(fame)始于一面**光秃秃**(bare)的墙。

**2.（该改）第 3 项 −1**
- 原文：In June 1914 a **tribunal** **imposed** a year and 15 days
- 问题：impose 须接 sentence／penalty 作宾语，“impose a year” 不成立。tribunal 用于法国刑事法庭（tribunal correctionnel）可接受，不改。
- 改法：In June 1914 a **tribunal** **imposed** a **penalty** of a year and 15 days（+3 词；penalty ✓ 未占用，P5 加粗 12→13）
- 速查表增：penalty | n. 惩罚，刑罚；罚款（the death penalty；impose a penalty on sb） | 5；中文“**法庭**(tribunal)**判处**(imposed)佩鲁贾一年零十五天的**刑罚**(penalty)”

**3.（该改）删词以守 271（共 −5 词）**
- 原文：In fact Leonardo da Vinci had → 改法：In fact Leonardo had（−2；中文保留全名）
- 原文：The museum then **shuttered** for a week. → 改法：The museum **shuttered** for a week.（−1）
- 原文：**curious** **onlookers** queued **patiently** to **stare** → 改法：**curious** **onlookers** queued to **stare**（−1；patiently 无来源，删去更稳；P2 加粗 12→11）；中文删“**耐心**(patiently)”
- 原文：Having **lurked** in a storeroom on the Sunday → 改法：…in a storeroom on Sunday（−1）
- 已实测改后：271 词，段落 [45, 49, 55, 58, 64]，加粗 54 全部 ✓，无占用行，各段 10/11/10/10/13 ✓。

**4.（可改）第 3 项 −0.5**
- 原文：The museum **shuttered** for a week.
- 问题：shutter 作不及物动词（店铺、企业“关门”）偏美式商业用语；英式更常见 stayed shut。词数已到上限，保留。

**5.（可改）第 3 项 −0.5**
- 原文：the Mona Lisa was **quietly** **plucked** from its wall
- 问题：pluck 暗示轻巧摘取，而画板连框重约数公斤；但“趁闭馆悄然摘走”的画面不失实，保留。

**6.（可改）第 3 项 −0.5**
- 原文：Leonardo had **accompanied** it to France
- 问题：accompany 让画成了旅行主体、人是陪同者，略别扭；transported 为 △、conveyed／ferried 已占用，无合规替换，保留。repatriated 用于文物归还母国是规范说法，不扣。

**7.（可改）第 3 项 −0.5**
- 原文：the **heist** **elevated** one **esteemed** **gem** among many into the world's most **renowned** painting
- 问题：elevate 常接 to（elevate sb to the status of），into 略偏；gem 指画作稍口语。transformed 已占用，保留。

**其余核查（不扣）**：conspicuous gap on the plaster（墙面露出空位，地道）；strode（润色）；was imprisoned for about seven months（自然）；repatriated ✓。

**8.（该改）第 9 项 −0.5**
- 原文：**好奇**(curious)的**围观者**(onlookers)**耐心**(patiently)排队**凝视**(stare)那幅**杰作**(masterpiece)曾经挂过的那块**空荡荡**(vacant)的地方。
- 问题：定语过长，“那幅……的那块……的地方”欧化。
- 改法：**好奇**(curious)的**围观者**(onlookers)排起长队，只为**凝视**(stare)那块**空荡荡**(vacant)的墙面——那幅**杰作**(masterpiece)曾挂在那里。若嫌破折号：……排起长队，**凝视**那幅**杰作**曾经挂过、如今**空荡荡**的位置。

## 改后词数
271 +2（1）+3（2）−5（3）= 271 ✓（已实测）。

## 达标判断
95、零硬伤，按我这一票通过，但**问题 1 必须改**（归属是任务书公允红线）；改完 1–3、8 预计 98（剩可改 4–7 共 −2）。

会签：同意定稿（以落实必改 1 及配套问题 2、3 为条件）

总分 = 各项之和 已核（13.5+10+12+5+12+8+10+10+9.5+5 = 95）
