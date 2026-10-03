# 第 49 篇评审 · 英文总编辑 · 第 1 轮

## 总分：97 / 100（无硬伤）

| 项 | 满分 | 得分 |
|---|---|---|
| 1 史实准确 | 15 | 14.5 |
| 2 论证与结构 | 10 | 9 |
| 3 语言质量 | 15 | 13.5 |
| 4 适配读者 | 5 | 5 |
| 5 学习价值 | 12 | 12 |
| 6 用法典型 | 8 | 8 |
| 7 速查表释义 | 10 | 10 |
| 8 忠实 | 10 | 10 |
| 9 通顺地道 | 10 | 10 |
| 10 重点词对应 | 5 | 5 |

## 机检（英文单独抽出，逐行读，未过滤）
`en_check.py`：段落词数 [54, 52, 52, 56, 57]，合计 271 ✓（零余量）；候选 50 个全部 ✓；**无“已被占用”行** ✓；各段加粗恰 10 ✓。

## 逐句史实核对（对照约稿单 §3 与 S1–S6）
- P1：拉维达 18 岁、带狗罗伯特、蒙蒂尼亚克附近、狗在倒树留下的洞口嗅探 ✓；1940-09-12 与另三名少年返回、进洞 ✓。**for an excursion that became an adventure**：属叙事润色，不改变事实（“回来进洞”确是一次探险），可接受 ✓。
- P2：后来复述中加工、说狗掉进洞 ✓（S1 embellished）；fabrication 指“掉进洞”这一添加情节，准确 ✓；狗只在洞口嗅探 ✓。
  - **the pivotal initiative belonged to the boys**：来源只说狗嗅探洞口、少年们几天后回来进洞；“进洞是少年们的主动”可由事实直接推出，成立 ✓，但 pivotal initiative 略堆叠（可改）。
  - **Ironically, the invented fall handed the dog the credit for their decision**：来源没有“功劳归属”的讨论；且狗确实发现了洞口，“把少年们的决定的功劳给了狗”是作者引申，说法偏重。见问题 1——改为“让狗成了故事主角”，既事实自明（传说即以狗为主角），又呼应标题。
- P3：约 680 幅彩绘、1,500 幅刻画（some 统摄两数）✓；距今约 1.7 万–2.2 万年（usually dated）✓；马、公牛、雄鹿 ✓。
  - **a remote antiquity; its creators were our distant ancestors**：its 指 artwork ✓；“我们遥远的祖先”是旧石器时代智人的通行说法，不失实；但 remote antiquity 与 distant ancestors 语义叠加（可改）。
  - **Their fragility**：Their 可指动物、颜料或壁画，指代不清（问题 2）。
- P4：1948-07-14 开放、每天约 1,200 名游客、二氧化碳／热量／湿度／污染物、明显受损 ✓；1963 年关闭、修复、每日监测 ✓。**influx／throng**：一指“涌入的人流”，一指“拥挤的人群”，分处两句、各司其职，不算同义堆叠 ✓。
- P5：1979 年列入世界遗产 ✓；拉斯科二号（高度精确的局部复制品）1983、拉斯科四号 2016 年 12 月 ✓；2001 年白色真菌、化学处理后黑斑扩散 ✓。

## 结尾
原文：**Admirers** now meet the bulls only in a **recreation**, for the originals are **inaccessible** to them.
- 事实：原洞 1963 年起对公众关闭 ✓；公牛厅在拉斯科二号／四号中复制 ✓；to them（仰慕者）限定，排除了研究人员，成立 ✓。
- **同构问题**：48 篇结尾为“主句 …, for + 依据从句”（…faded, for by 1969 … had reverted…）。本句同样以“主句, for + 原因从句”收尾，句式骨架相同，紧挨 48 篇，读者一眼可见。见问题 3。
- 其余 §5：≤26 ✓；无 cave／found／find／dog ✓；Admirers 开头，非禁用开头 ✓；无 still、never、apparently、remained 等 ✓。

## 标题与正文
标题 The Cave Found by a Dog 是传说版本，P2 已纠正。改后 P2 末句 the invented fall made the dog the hero of the story 正面点出“标题所说的是传说”，形成呼应，无须另加 ✓。

## 代词跨段
P2 In later retellings, Ravidat…；P3 Inside…；P4 Lascaux…；P5 Lascaux… ——无跨段代词 ✓。

## 逐条问题

**1.（该改）第 1 项 −0.5**
- 原文：**Ironically**, the invented fall handed the dog the credit for their decision.
- 改法：**Ironically**, the invented fall made the dog the hero of the story.（0 词；呼应标题，事实自明）
- 中文：**讽刺的是**(ironically)，那虚构的一跤反倒让狗成了这个故事的主角。

**2.（该改）第 3 项 −0.5**
- 原文：Their **fragility** would soon become clear.
- 改法：The paintings' **fragility** would soon become clear.（+1 词）
- 中文：这些壁画的**脆弱**(fragility)很快就会显现出来。

**3.（必改）第 2 项 −1**
- 原文：…only in a **recreation**, for the originals are **inaccessible** to them.
- 问题：与 48 篇结尾“…, for + 从句”同构。
- 改法：**Admirers** now meet the bulls only in a **recreation**, the originals being **inaccessible** to them.（−1 词，与问题 2 抵消；独立主格结构，与 05–48 均不同构）
- 中文：如今，**仰慕者**(admirers)只能在**复原品**(recreation)中见到那些公牛，原作对他们已**无法企及**(inaccessible)。

**已实测 1–3**：271 词，段落 [54, 52, 53, 56, 56]，加粗 50，无占用行，各段 10 ✓

**4.（可改）第 3 项 −1（两处）**
- the **pivotal** **initiative** belonged to the boys——两个抽象词叠用，可接受；
- a remote **antiquity**; its **creators** were our distant **ancestors**——remote 与 distant 叠义。
- 均为加粗词、各段恰 10，保留。

## 改后词数
271 +0（1）+1（2）−1（3）= 271 ✓（已实测）

## 达标判断
≥95、零硬伤，按我这一票通过；**问题 3 必须改**（与 48 篇结尾同构）。改完 1–3 预计 99。

会签：同意定稿（以落实必改 3 为条件）

总分 = 各项之和 已核（14.5+9+13.5+5+12+8+10+10+10+5 = 97）
