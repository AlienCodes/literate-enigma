# 第 30 篇评审 · 英文总编辑 · 第 1 轮

## 总分：92 / 100（无硬伤，未达 95）

| 项 | 满分 | 得分 |
|---|---|---|
| 1 史实准确 | 15 | 14.5 |
| 2 论证与结构 | 10 | 9 |
| 3 语言质量 | 15 | 12 |
| 4 适配读者 | 5 | 5 |
| 5 学习价值 | 12 | 12 |
| 6 用法典型 | 8 | 6 |
| 7 速查表释义 | 10 | 10 |
| 8 忠实 | 10 | 10 |
| 9 通顺地道 | 10 | 8.5 |
| 10 重点词对应 | 5 | 5 |

## 机检
`en_check.py`（标题 + 英文正文）：段落词数 [60, 56, 50, 48, 56]，合计 270 ✓（上限 271，只剩 1 词余量）；加粗 54 个全部 ✓ 档、无占用；各段加粗 12/11/11/10/10，均 ≥10 ✓。

## 史实核对（逐条）
与任务书核准表及常见权威来源（CDC、WHO、Jenner Museum、Royal College of Physicians）一致：
- 致死约三成 ✓（about 保留）；20 世纪估计 3 亿 ✓（an estimated 保留）
- 人痘：中国 16 世纪 ✓；1721 年传入英国 ✓；未写百分比 ✓
- 1774 年杰斯蒂、多塞特农夫、妻子和两个儿子 ✓
- 1796 年 5 月 14 日詹纳给 8 岁菲普斯接种牛痘 ✓；1796 年 7 月 1 日天花复验未发病 ✓
- 1797 年皇家学会 declined to publish ✓（未写嘲笑／驳回）；1798 年 6 月自费出版《探究》✓；vacca 只写词源 ✓
- 1823 年 1 月 26 日去世 ✓；1967 年 WHO 强化运动 ✓（年份，月份无可靠来源，合规）
- 1977 年 10 月 26 日索马里最后一例自然病例 ✓（naturally occurring 保留）；1980 年 5 月 8 日世界卫生大会宣布 ✓；唯一被根除的人类疾病 ✓
- almost 184 years：1796-05-14 → 1980-05-08，差 6 天满 184 年，“almost” 准确 ✓
- 公允：写明詹纳非首创（Jesty + not the idea's originator）✓；未写詹纳根除 ✓；伦理标 by today's standards ✓；无挤奶女工传说 ✓
- 结尾：13 词，无 first / shot / smallpox，无禁用结构，不新增事实（184 年为自算）✓
- 时间顺序：P4 1823 → P5 1967，均标年，清楚 ✓

## 逐条问题

**1.（该改）第 1 项 −0.5**
- 原文：The **procedure** itself could cause **grave** **sickness** or death, if less **frequently** than smallpox.
- 问题：人痘接种本身就是让人得天花，“比天花少”逻辑上自相比较；任务书原意是“比自然感染的天花少”。
- 改法：The **procedure** itself could cause **grave** **sickness** or death, if less **frequently** than natural smallpox.（+1 词）

**2.（该改）第 6 项 −1**
- 原文：milkmaids with cowpox, a **mild** **ailment** of cattle, were **exempt** from smallpox.
- 问题：exempt from 是法律／税务用语（exempt from tax），说疾病不地道；词的典型用法没教到。
- 改法：were **immune** to smallpox.（0 词；immune 已测 ✓ 未占用；速查表改为 immune  adj. 免疫的；不受影响的（immune to measles；the immune system）；中文“就能**免于**(exempt)感染天花”改为“就对天花**免疫**(immune)”）

**3.（该改）第 6 项 −1**
- 原文：had **employed** cowpox on his wife and two sons.
- 问题：employ sth on sb 不是母语搭配（employ 接 method/technique，不接“用在某人身上”）；也没交代目的。
- 改法：had **employed** cowpox to protect his wife and two sons.（+2 词；中文“已在妻子和两个儿子身上**使用**(employed)过牛痘”改为“已**使用**(employed)牛痘保护妻子和两个儿子”）

**4.（该改）第 3 项 −1**
- 原文：In June 1798 he **privately** **funded** and issued his Inquiry, with **supplementary** cases.
- 问题：privately 同时修饰 issued，读作“私下发行／内部流通”，与“公开出版、让方法传播”的论点相反；funded and issued 并列也生硬。
- 改法：In June 1798 he **privately** **funded** his Inquiry's publication, with **supplementary** cases.（−1 词；publication 不加粗，已被 29 篇占用；中文不变）

**5.（该改）第 2 项 −0.5**
- 原文：In 1967 the WHO launched an **intensified**, **concerted** campaign to **eradicate** it.
- 问题：段首代词 it 跨段回指上段末的 smallpox，读者要回头找；且中间隔着 1823 年。
- 改法：…campaign to **eradicate** smallpox.（0 词）

**6.（该改）第 2 项 −0.5**
- 原文：By today's standards, **experimentation** … would be **unethical**. Jenner was not the idea's **originator**. His contribution was a test…
- 问题：伦理 → 非首创 → 贡献，三拍跳跃；“非首创”与“贡献”是一组反转，被伦理句插在前面削弱了。不改词也可调句序。
- 改法：把伦理句移到段末死亡句之前：Jenner was not the idea's **originator**. His contribution was a test, … the **technique**. By today's standards, **experimentation** on a child without **informed** **consent** would be **unethical**. He died on 26 January 1823, with smallpox far from **eliminated**.（0 词，句序调换；中文同步调序）

**7.（可改）第 3 项 −1.5（三处合计）**
- (a) 原文：judging the **proof** **deficient** — 母语者说 judging the evidence insufficient；proof deficient 读作“证明有缺陷”。evidence／insufficient 均不可用（基础词／被 03 篇占用），故只记可改 −0.5，不强求。
- (b) 原文：the only human disease ever **vanquished** — 文学腔，且技术上应是 eradicated；stamped out 为 △ 短语需语言学家判定。可改 −0.5：若语言学家判 stamped out 达标，改为 ever **stamped out**（+1 词，须另删 1 词，见下）。
- (c) 原文：**Rustic** **lore** / a **provincial** **practitioner** — rustic 多指家具风格，provincial 带“土气”贬义；country doctor 更准，但 country／doctor 都是基础词。可改 −0.5，保留亦可。

**8.（可改）第 3 项 −0.5（词数中性）**
- 原文：a **scratch** on James Phipps, aged 8.
- 改法：a **scratch** on eight-year-old James Phipps.（−1 词，给问题 3 腾出余量）

**9.（该改）第 9 项 −1**
- 原文：**地方**(provincial)**医生**(practitioner)爱德华·詹纳**注入**(inserted)取自一名挤奶女工牛痘疮的**液体**(fluid)，注入的位置是8岁的詹姆斯·菲普斯身上的一道**划痕**(scratch)。
- 问题：“注入……注入的位置是”重复、欧化。
- 改法：**地方**(provincial)**医生**(practitioner)爱德华·詹纳从一名挤奶女工的牛痘疮中取出**液体**(fluid)，**注入**(inserted)8岁的詹姆斯·菲普斯身上的一道**划痕**(scratch)。

**10.（可改）第 9 项 −0.5**
- 原文：此后任何**症状**(symptoms)都没有**随之出现**(ensued)。
- 问题：“此后”与“随之”语义重复。
- 改法：“任何**症状**(symptoms)都没有**随之出现**(ensued)。”（删“此后”）

## 改后词数
270 +1（问题 1）+0（问题 2）+2（问题 3）−1（问题 4）+0（问题 5、6）−1（问题 8）= 271 ✓。
已用改后全文实测：`en_check.py` 合计 271，加粗 54 个全部 ✓、无占用，各段 ≥10。问题 7(b) 若采用 stamped out 将到 272，需再删 1 词（如 In 1797, however, 中删 however 不可取——宁可不改 7(b)）。

## 达标判断
无硬伤，但 92 < 95，不通过。改完 1–6、8、9、10 后预计 98.5（剩可改 7 的 −1.5）。

总分 = 各项之和 已核（14.5+9+12+5+12+6+10+10+8.5+5 = 92）
