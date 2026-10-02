# 第 57 篇评审 · 英文总编辑 · 第 1 轮

## 总分：97.5 / 100（无硬伤）

| 项 | 满分 | 得分 |
|---|---|---|
| 1 史实准确 | 15 | 15 |
| 2 论证与结构 | 10 | 9.5 |
| 3 语言质量 | 15 | 13.5 |
| 4 适配读者 | 5 | 5 |
| 5 学习价值 | 12 | 11.5 |
| 6 用法典型 | 8 | 8 |
| 7 速查表释义 | 10 | 10 |
| 8 忠实 | 10 | 10 |
| 9 通顺地道 | 10 | 10 |
| 10 重点词对应 | 5 | 5 |

## 机检（英文单独抽出，逐行读，未过滤）
`en_check.py`：段落词数 [54, 55, 48, 47, 63]，合计 267 ✓；候选 50 个全部 ✓；**无“已被占用”行** ✓；各段加粗恰 10 ✓。
`stem.py` 同根扫描：fur／furious、stiff／justify、looms／gloom、mills／millimetre、apparel／apparatus、underdog／underworld、clasp／classify、overran／overrule 均为字形巧合，非同根 ✓；merged／emerge、submerge：merge 与 emerge 同出拉丁 mergere，但英语里是两个独立词，按“同一词根派生”从严可议，建议协调人裁定（我倾向放行）。**真正同根需处理的两处**：
- **trademark** 与台账 trade-off（第 20 篇）共用 trade——复合词共享实词词根，按本轮“同根一律排除”应换（问题 3）；
- **generic** 与台账 generally 同出 gener-（genus），从严亦属同根，提请协调人裁定；如须换，可用词有限（common／everyday 为基础词），建议保留并在台账注明。
`wt.sh` 另测：OK proprietary、brand-name、copyright；OCC patented；BAD catwalk、eponymous。

## 逐句史实核对（对照约稿单 §3 与 S1–S7）
- P1：1941 年、瑞士工程师德·梅斯特拉尔、阿尔卑斯山**打猎**归来（未写遛狗）✓、爱尔兰指示犬 ✓；牛蒡刺果粘衣、缠狗毛 ✓；显微镜下成千上万小钩、钩住布料小环 ✓（S1）。hound 泛指猎犬，指示犬属枪猎犬，严格说不是 hound，但文学用法可接受（可改）。
- P2：起初少有人当真 ✓；里昂、当时的纺织中心、棉样很快磨坏 ✓；与纺织厂合作、改用尼龙、钩子既能扣又能拉开 ✓；约十年 ✓（S2）。**looms and mills**：S2 写“织工／纺织厂”，“在织机旁和工厂里反复试验”是合理具象化，不改变事实 ✓。
- P3：velours（天鹅绒）＋crochet（钩）✓；1955 年美国专利 ✓（S3）；1959 年纽约时装秀、反应不如预期、主要因外观 ✓（S4）。runway 在英式里多指跑道，时装 T 台英式作 catwalk（但 catwalk 为 BAD），可改。
- P4：**underdog**：上段刚写“公众不买账”，称其为“不被看好者”有据，修辞成立 ✓；阿波罗计划、失重中固定物品 ✓；阿波罗 11 号约 3,300 平方英寸 ✓（S5）；**NASA had not invented**：事实正确（S5），但过去完成时没有参照点，应作一般过去时（问题 2）。
- P5：1978 年专利到期、台湾／大陆／韩国廉价仿品涌入 ✓；**went mainstream**：S6“此前是小众产品”，到期后仿品泛滥、走向大众，是对“niche until then”的直接推论，口语但不越界 ✓；2017 年公司请公众把仿品称作 hook and loop、防商标沦为通用词 ✓（S7）。

## 结尾
The firm ended up asking the public to stop using its own name for rivals' products.（16 词）
- 事实：S7 活动正是请公众别再把对手的仿品叫成公司名 ✓，ended up 点出“发明太成功、名字被借走”的反讽 ✓。
- 结构：主谓 + ended up doing，非“主句 + 逗号 + 名词短语”、非超短判断句、非 The year … saw、非倒装 ✓；与 44–56 均不同构 ✓。§5 禁词与标点均无 ✓；不含 burrs／became／Velcro ✓。
- **问题**：与上一句（In 2017 the company asked people to call such mimics hook and loop fasteners…）内容几乎重复，只是换了说法，收束没有新角度（问题 1）。

## 其他
- 代词跨段：各段名词开头 ✓。
- 对冲：每句至多一处 ✓。

## 逐条问题

**1.（可改）第 2 项 −0.5**
- 问题：结尾复述上一句。
- 备选（0 加粗变化，−4 词）：Its own name had turned into the everyday word for rivals' products.——从“为什么要发起这场活动”收束，补上因果一环；但 had turned into 说成“已成通用词”，与上句“防止成为通用词”略有张力（日常用语层面已通用、法律上尚未）。两者择一，现稿亦可接受。

**2.（该改）第 3 项 −0.5**
- 原文：NASA had not invented the nylon **clasp**.
- 改法：NASA did not invent the nylon **clasp**.（0 词）

**3.（该改）第 5 项 −0.5（同根规则）**
- 原文：to stop its **trademark** **melting** into a **generic** **noun**
- 问题：trademark 与第 20 篇 trade-off 共用 trade。
- 改法：to stop its **brand-name** **melting** into a **generic** **noun**（0 词；brand-name ✓ OK）；或协调人裁定复合词不受同根规则约束则保留 trademark（它是法律上最准确的词）。
- 中文：以免它的**品牌名**(brand-name)逐渐**融化**(melting)成……

**4.（可改）第 3 项 −1（两处）**：**hound**（指示犬非猎犬类）；**runway**（英式 T 台作 catwalk，但 catwalk 不可加粗）。

**已实测 2+3（及问题 1 备选）**：263–267 词，加粗 50，无占用行，各段 10 ✓

## 必改
无。

## 改后词数
英文不变 267；采纳 2、3：267 ✓；再采纳问题 1 备选：263 ✓。

## 达标判断
≥95、零硬伤，按我这一票通过。落实 2、3 预计 98.5。

会签：同意定稿

总分 = 各项之和 已核（15+9.5+13.5+5+11.5+8+10+10+10+5 = 97.5）
