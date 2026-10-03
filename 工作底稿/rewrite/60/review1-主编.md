# 第 60 篇 The Bread Made from Air《从空气中造面包》评审 · 英文总编辑 · 第 1 轮

## 总分：96 / 100（无硬伤）

| 项 | 满分 | 得分 |
|---|---|---|
| 1 史实准确 | 15 | 14.5 |
| 2 论证与结构 | 10 | 9 |
| 3 语言质量 | 15 | 13.5 |
| 4 适配读者 | 5 | 4.5 |
| 5 学习价值 | 12 | 12 |
| 6 用法典型 | 8 | 8 |
| 7 速查表释义 | 10 | 10 |
| 8 忠实 | 10 | 9.5 |
| 9 通顺地道 | 10 | 10 |
| 10 重点词对应 | 5 | 5 |

## 机检（英文单独抽出，逐行读，未过滤）
- `en_check.py`：段落词数 [49, 47, 48, 47, 45, 34]，合计 **270** ✓；候选 **54** 个全部 ✓；**无“已被占用”行** ✓。
- 按用户新规（9 月 30 日原规则）：同根词允许，只排除完全相同的词及其屈折形式（以 en_check 占用行为准）。本稿无占用行，fertiliser、munitions 等原约稿单“同根勿粗”示例词均合规，**不以 stem.py 为去粗理由** ✓。
- `wt.sh`／en_check 另测：prised、wrested、coaxed、conjured、upscaled 冷僻；industrialised（第 23 篇）、extracted（第 7 篇）、harvested（第 4 篇）已占用。

## 总体评价
开篇极好：1909 年的实验室、矮墩墩的机器、液氨一滴滴落下，一个镜头把“从空气里撬出养分”立住；第二段把意义推到“到 2008 年养活近半人类”；第三段 The same ambition had a sinister side 一句转折干净，毒气写得克制（数量、地点、“首次大规模”，无渲染）；克拉拉一段只陈事实，The next day the widower left for the Eastern Front 以冷峻的并置代替评判，分寸很好；死亡营一句同样只陈事实（relatives of his died），没有煽情。结尾回到“我们体内一半的氮经过他的工厂”，让读者自己体会双重遗产，正合约稿单“不说教”。唯一的败笔是结尾前那句 His gift was twofold, a blessing and a curse——陈词滥调、替读者下结论，而且把毒气说成“馈赠”，见必改 1。

## 逐句史实核对（对照约稿单 §3 与 S1–S6）
- P1：1909 年 7 月、卡尔斯鲁厄、向 BASF 代表演示桌面高压装置、氮氢合成氨、液氨滴出 ✓（S1）；crushing pressure／furnace heat 对应约 200 个大气压、约 500 °C ✓；squat、gleaming、bolted 属不改变事实的叙事润色 ✓。
- P2：博施负责放大、1913 年奥保量产 ✓；“从空气中造面包”的赞誉、1918 年诺贝尔奖 ✓（S2）；到 2008 年养活近半人类 ✓（S3，48%）。
  - **ammonia wards off famine as no manure heap could**：与粪肥的比较来源未载，属作者推断（合理但越出 S3）（可改，见问题 5）。
- P3：合成氨让德国在英国封锁下仍能制造弹药所需硝酸盐 ✓（S5）；哈伯上尉组织化学战 ✓；1915-04-22 伊普尔、约 168 吨氯气、首次大规模毒气攻击 ✓（S4）；greenish 符合氯气黄绿色 ✓。克制 ✓。
- P4：克拉拉为德国首位化学博士女性、反对他的工作 ✓；1915-05-02 庆功聚会后在花园用他的配枪自杀 ✓；次日他赴东线 ✓（S4）。克制，无细节渲染 ✓。
- P5：犹太裔、希特勒上台后离开德国、1934 年死于巴塞尔 ✓；研究所杀虫剂研究产生齐克隆、后来的齐克隆 B 用于纳粹死亡营、亲属在其中遇害 ✓（S6）。克制 ✓。
- P6：人体蛋白质和 DNA 中约一半的氮经过哈伯-博施工厂 ✓（S3）。

## 结尾
About half the nitrogen in our proteins and DNA has passed through a Haber-Bosch factory, so each of us carries a little of Haber's chemistry.（24 词）
- 字面成立（S3）；each of us carries a little of Haber's chemistry 是对“体内氮经其工艺固定”的合理转述 ✓；不说教，把“养活与杀戮出自同一人”留给读者 ✓。
- §4：无 bread／made／air ✓；不以禁用词或时间状语开头（About half … 为主语）✓；结构“X has passed through …, so each of us …”与 33、51–59 均不同 ✓；无冒号分号破折号、最高级、may／might、never、still、for／since 原因从句 ✓；≤26 ✓。
- 但它前一句 His gift was twofold, a blessing and a curse. 恰是被禁的“主句, + 名词短语”句型（51／52／54），虽不在末句，紧贴结尾仍显同构，且属说教（必改 1）。

## 其他
- **代词跨段**：P4 段首 His wife 回指上段的 Haber；P6 段首 His gift 同理（必改 2，P6 随必改 1 一并解决）。
- 对冲：每句至多一处 ✓。

## 必改

**1.（必改）第 2 项 −1：陈词滥调、说教，且与禁用句型撞型**
- 原文：His gift was **twofold**, a **blessing** and a **curse**. About half the nitrogen …
- 改法：删去首句，P6 只留结尾句：About half the nitrogen in our proteins and DNA has passed through a Haber-Bosch factory, so each of us carries a little of Haber's chemistry.（−9 词；加粗 −3）
- 中文：删“他的馈赠是双重的，既是福祉，也是诅咒。”

**2.（必改）第 3 项 −0.5：段首代词跨段**
- 原文：His wife, Clara Immerwahr, …
- 改法：Haber's wife, Clara Immerwahr, …（0 词）

**3.（必改）第 3 项 −0.5；第 4 项 −0.5：用词与身份**
- 原文：Carl Bosch **enlarged** the method, and from 1913 Oppau **mass-produced** it.
- 问题：enlarge a method 不地道（方法不能“放大”，规模才能）；博施首次出场无身份。
- 改法：Carl Bosch, a BASF engineer, scaled the method up, and from 1913 Oppau **mass-produced** it.（+4 词；enlarged 去粗；industrialised 已被第 23 篇占用不可用）

**已实测 1–3**：段落词数 [49, 51, 48, 47, 45, 25]，合计 **265** ✓；候选 **50** 个全部 ✓（恰好达标）；**无“已被占用”行** ✓。
**提醒**：加粗正好 50，没有余量。如希望留 2–4 个余量，可在 P1 或 P6 另补经 en_check 合格的词（例如在结尾句把 chemistry 换成合格的同义加粗词——须先测），或保留 P6 首句但改写成非套话、非“主句, + 名词短语”的句子（不推荐）。

## 可改

**4. 第 3 项 −0.5**：Haber had **pried** nourishment——pry 作“撬”美式更常见，英式多作 prise；但 prised、wrested、coaxed 均冷僻，extracted、harvested 已占用，保留可接受。

**5. 第 1 项 −0.5**：ammonia **wards** off **famine** as no **manure** **heap** could——与粪肥的比较是推断。若要贴来源，可作 ammonia **wards** off **famine** on a scale no **manure** **heap** could match（+3 词），仍属推断但更具体；或保留。

**6. 第 8 项 −0.5（中文）**：在希特勒政权**随即**夺取权力之后——“随即”英文没有，删去。

## 达标判断
96 ≥ 95、零硬伤，按我这一票通过；以落实必改 1–3 为条件。改完预计 98.5。

会签：同意定稿（以落实必改 1–3 为条件）

总分 = 各项之和 已核（14.5+9+13.5+4.5+12+8+10+9.5+10+5 = 96）
