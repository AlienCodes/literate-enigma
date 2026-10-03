# 第 56 篇评审 · 英文总编辑 · 第 1 轮

## 总分：95.5 / 100（无硬伤）

| 项 | 满分 | 得分 |
|---|---|---|
| 1 史实准确 | 15 | 13.5 |
| 2 论证与结构 | 10 | 10 |
| 3 语言质量 | 15 | 12.5 |
| 4 适配读者 | 5 | 4.5 |
| 5 学习价值 | 12 | 12 |
| 6 用法典型 | 8 | 8 |
| 7 速查表释义 | 10 | 10 |
| 8 忠实 | 10 | 10 |
| 9 通顺地道 | 10 | 10 |
| 10 重点词对应 | 5 | 5 |

## 机检（英文单独抽出，逐行读，未过滤）
`en_check.py`：段落词数 [54, 46, 54, 59, 53]，合计 266 ✓；候选 50 个全部 ✓；**无“已被占用”行** ✓；各段加粗恰 10 ✓。
**台账抽查**：toaster、gadget、cumbersome、heavyweight、cassette、staffers、superiors、cash-cow、franchise、analogue、shrinkage、apex、creditors、sapped、consortium、once-mighty、streamlined、refocused、laurels、commending 逐个过 en_check／wt.sh，均无占用行；同族核查（restructuring／structure、reorganisation／organised 等）未见与台账已占词同词根重复 ✓。
`wt.sh` 另测：OK dismissive、indifferent；OCC honours、distinction；BAD unenthusiastic。

## 逐句史实核对（对照约稿单 §3 与 S1–S7）
- P1：1975 年、柯达工程师萨松、首台数码相机 ✓；烤面包机大小、约八磅 ✓；同年 12 月首张照片、1 万像素黑白 ✓；录磁带 23 秒、回放装置在电视上显示 ✓（S1）。hardly portable 属评述，8 磅的机器“谈不上便携”可接受。
- P2：技术人员喜欢、不用胶卷 ✓；管理层“挺可爱、别声张”（转述，By Sasson's recollection 归属到位）✓；柯达靠卖胶卷 ✓；1978 年专利、从未投产 ✓（S2）。
  - **superiors were unimpressed**：来源原意是“可爱但别说出去”——是“压下不提”，不是“没被打动”（cute 反倒是一点好感）。unimpressed 偏离一层；dismissive（✓ OK，0 词）更贴（问题 4）。
  - **Kodak's revenues showed its dependence on film**：S2 “柯达的生意靠卖胶卷”，以营收说明依赖是合理转述，不超出来源 ✓；但 a **profitable** **cash-cow** and the **pillar** of its **franchise** 中 profitable／cash-cow 为常识性评价（来源未言利润），franchise 作“主营业务”是美式商业义，偏生（问题 5）。
- P3：数码颠覆 ✓；2009 年 6 月宣布停产 Kodachrome、因数码时代需求下降 ✓（S5）。
  - **Since 2003 layoffs had slashed 47,000 jobs…**：**时间参照错位**。S3 的 47,000／13 家工厂／约 130 个冲印室都是“截至 2012 年 1 月申请破产时”的累计数；原句紧跟“2009 年 6 月”，又用过去完成时，读者自然理解为“到 2009 年已裁 4.7 万”，与来源不符（问题 1）。
  - 同句 about 145,000 与 about 130 两个对冲，违反“每句至多一个”（随问题 1 一并解决）。
- P4：2012-01-19、131 年、第 11 章 ✓；养老金与多年数码迟缓（多因，未写单一因果）✓；花旗 9.5 亿美元 ✓；同年 12 月约 1,100 项数字成像专利、约 5.25 亿美元、12 家买方、含苹果谷歌 ✓（S4）。同句两个 about（问题 2）。
- P5：2013 年 9 月、19 个月后走出破产、缩成商业印刷 ✓（S7）；2009-11 奥巴马授奖 ✓（S6）。
  - **national laurels**：laurels 是“桂冠、荣誉”的比喻，national laurels 没说出是什么奖——国家技术与创新奖章是这一句的信息核心，被修辞吞掉了；**commending the digital camera** 让奖章“表彰相机”，而 S6 是“表彰他发明数码相机”（问题 3）。

## 结尾
The year of that medal also saw Kodak announce the end of Kodachrome.（13 词）
- 事实：奖章 2009 年 11 月、停产宣布 2009 年 6 月，同年 ✓；并置不暗示因果 ✓。
- 结构：主语 The year of that medal（名词短语作主语，非句首时间状语）+ saw + 宾补；**非“主句 + 逗号 + 名词短语”**，也非 55 篇那种超短判断句 ✓；与 44–55 均不同构 ✓。
- §5：无 company／invented／invent／killer ✓；无禁用词与标点 ✓；≤26 ✓。
- 小注：Kodachrome 停产 P3 已讲，结尾是回扣并置而非新增，可接受。

## 其他
- **代词跨段**：P2 首句 Technical staffers liked it——it 回指 P1 的相机，跨段（问题 2）。
- 同义堆叠：P5 downsized, streamlined and refocused 三连（可改）。

## 逐条问题

**1.（必改）第 1 项 −1（兼 对冲）**
- 原文：Since 2003 **layoffs** had **slashed** 47,000 jobs, part of a **shrinkage** from a 1980s **apex** of about 145,000 staff, alongside the **shutdown** of 13 factories and about 130 labs.
- 改法：By 2012 **layoffs** since 2003 had **slashed** 47,000 jobs, part of a **shrinkage** from a 1980s **apex** of about 145,000 staff. There had also been the **shutdown** of 13 factories and some 130 labs.（+4 词；By 2012 标明累计截止点；拆成两句，各一处对冲；加粗不变）
- 中文：到2012年，自2003年以来的**裁员**(layoffs)已**砍掉**(slashed)4.7万个岗位……此外，13家工厂和约130个冲印室也相继**关闭**(shutdown)。

**2.（该改）第 3 项 −1（两处）**
- 跨段代词：Technical **staffers** liked it → Technical **staffers** liked the camera（+1 词）
- 双重对冲：a **portfolio** of about 1,100 digital imaging patents fetched about $525 million → a **portfolio** of 1,100 digital imaging patents fetched about $525 million（−1 词；1,100 本为整数概数）

**已实测 1+2**：271 词，段落 [54, 47, 59, 58, 53]，加粗 50，无占用行，各段 10 ✓

**3.（该改）第 4 项 −0.5；第 3 项 −0.5**
- 原文：In November 2009 President Barack Obama had **decorated** Sasson with national **laurels**, **commending** the digital camera.
- 问题：national laurels 隐去了奖名；commending the camera 主宾错位。
- 建议（词数已到 271，须 0 增词）：…had **decorated** Sasson with national **laurels**, **commending** his digital camera.（the → his，0 词，至少把“表彰他的发明”落实）；奖名可放中文译文与注释：“国家技术与创新奖章”。

**4.（可改）第 1 项 −0.5**
- 原文：his **superiors** were **unimpressed**
- 改法：his **superiors** were **dismissive**（0 词；dismissive ✓ OK）

**5.（可改）第 3 项 −1（两处）**
- a **profitable** **cash-cow** and the **pillar** of its **franchise**——profitable 与 cash-cow 叠义，franchise 美式商业义偏生；
- **downsized**, **streamlined** and **refocused**——三连近义。
- 加粗约束下保留。

## 必改
问题 1（时间参照错位：4.7 万裁员等为截至 2012 年的累计数）。

## 改后词数
266 +4（1）+1 −1（2）+0（3、4）= 270；实测 271（以机检为准）✓

## 达标判断
95.5、零硬伤，按我这一票通过；**问题 1 必须改**。改完 1–4 预计 99。

会签：同意定稿（以落实必改 1 为条件）

总分 = 各项之和 已核（13.5+10+12.5+4.5+12+8+10+10+10+5 = 95.5）
