# 第 32 篇评审 · 英文总编辑 · 第 1 轮

## 总分：90 / 100（无硬伤，未达 95）

| 项 | 满分 | 得分 |
|---|---|---|
| 1 史实准确 | 15 | 13 |
| 2 论证与结构 | 10 | 9.5 |
| 3 语言质量 | 15 | 10 |
| 4 适配读者 | 5 | 5 |
| 5 学习价值 | 12 | 12 |
| 6 用法典型 | 8 | 8 |
| 7 速查表释义 | 10 | 10 |
| 8 忠实 | 10 | 10 |
| 9 通顺地道 | 10 | 8 |
| 10 重点词对应 | 5 | 4.5 |

## 机检（英文单独抽出，逐行读，未过滤）
`en_check.py`：段落词数 [51, 57, 47, 57, 59]，合计 271 ✓（零余量）；候选 54 个，全部 ✓；**无“已被占用”行** ✓；各段加粗 10/10/11/12/11 ✓。
替补词实测（我试过）：markers、layout、differentiated、promptly、genetic、tip-off 均 ✓ 未占用；patterns △；sole、solitary、culprit、arrangement、sequences、disproved、refuted、discredited、subsequently 均已占用；single、cleared、matched 基础词。

## 史实核对（对照任务书 §3 与 sources 末尾 Updated verdicts）
- 1983 年 11 月纳伯勒、1986 年夏恩德比附近，两名 15 岁少女 ✓；未写姓名、无暴力细节 ✓（slain 属中性新闻用语，不算渲染）
- 17 岁当地青年供认第二起 ✓
- 两年前：1984 年 9 月 10 日（距 1986 年供认约两年）✓；《自然》1985 年 3 月 ✓
- 青年非凶手、两案同一人 ✓；the first person known to be cleared by DNA evidence ✓（known to be 保留）
- 1987 年 1 月首次大规模筛查、more than 5,000 men、三个村、血或唾液 ✓；无精确数、无年龄段 ✓
- 面包师让同事冒名送样 ✓；1987 年 8 月 someone overheard ✓（无性别、无酒馆）
- 1987-09-19 被捕、DNA 吻合 ✓；1988 年 1 月认罪、终身监禁、无刑期年数 ✓；first person convicted of murder on the basis of DNA evidence ✓（无“世界”）
- 筛查没抓住他：not the screening ✓
- 倒叙：P1 停在 1986 年供认 → P2 “two years earlier” 回到 1984 → P3 起顺叙，清楚 ✓
- 结尾：15 词，无 fingerprint／blood，无禁用结构，回扣反转 ✓

## 逐条问题

**1.（该改）第 1 项 −1**
- 原文：a **lone** **attacker** had killed both girls
- 问题：lone = 单独作案，不等于“同一人”；读者会理解为“每起都是一个人干的”，丢掉了检测最关键的结论（两案同一凶手）。
- 改法：the same **attacker** had killed both girls（0 词；lone 失去加粗，见问题 9 补回）；中文“**同一个**(lone)**袭击者**”改为“同一个**袭击者**(attacker)”

**2.（该改）第 1 项 −1**
- 原文：An **informant**, not the screening, had **unmasked** him.
- 问题：informant 指警方线人（常为固定、有偿的消息来源），与“有人偶然听到后报警”不符。
- 改法：A **tip-off**, not the screening, had **unmasked** him.（0 词；tip-off ✓ 未占用）；中文“一名**举报人**(informant)”改为“一条**举报线索**(tip-off)”，速查表改 tip-off | n. 密报，举报线索（an anonymous tip-off；act on a tip-off） | 5

**3.（必改）第 3 项 −1.5**
- 原文：**discerned** on an X-ray film **molecular** **motifs** whose **configuration** **varied** **distinctly** from person to person
- 问题：motif 指图案母题／DNA 中的功能序列基元，用在这里是术语误用；configuration 也堆砌。
- 改法：**discerned** on an X-ray film **molecular** **markers** whose **layout** **varied** **distinctly** from person to person（0 词，加粗数不变）；中文“一些**分子**(molecular)**标记**(markers)的**排布**(layout)因人**各异**(varied)，而且差别**分明**(distinctly)”；速查表 markers | n. (marker) 标记，标志物（a genetic marker；a marker of success）；layout | n. 布局，排布（the layout of a page/house）

**4.（该改）第 3 项 −1**
- 原文：He called them DNA fingerprints, a way of **differentiating** one person's DNA from another's.
- 问题：同位语 a way of … 挂在 fingerprints（图案）上，图案不是“方法”，逻辑错位。
- 改法：He called them DNA fingerprints, since they **differentiated** one person's DNA from another's.（−1 词）；中文“他把这些标记称为DNA指纹，因为它们能把一个人的DNA与另一个人的**区分**(differentiated)开来”

**5.（该改）第 3 项 −0.5**
- 原文：Nature **duly** carried his paper in March 1985.
- 问题：duly 意为“按预期、按规定地”，暗示理所当然，在此空洞。
- 改法：Nature **promptly** carried his paper in March 1985.（0 词）；中文“1985年3月，《自然》杂志**很快**(promptly)刊登了他的论文”

**6.（必改）第 3 项 −1**
- 原文：The youth was not the **perpetrator**, and a lone attacker had killed both girls. He became the first person known to be cleared…
- 问题：He 最近的男性先行词是 attacker，指代歧义，且事关史实（被洗清的是青年）。
- 改法：…girls. The youth became the first person known to be cleared…（+1 词）；中文“他成为”改为“那名青年成为”

**7.（可改）第 3 项 −0.5**
- 原文：his tests **overturned** the **erroneous** **confession**
- 问题：常用说法是 a false confession；erroneous 指“出错的”，语气偏软。三词均为加粗，替换代价大，保留。

**8.（可改）第 3 项 −0.5**
- 原文：None **corresponded**.
- 问题：correspond 不带宾语单用略悬，常见是 None matched／none corresponded to the killer's profile。词数已到上限，保留。

**9.（该改）第 3 项（并入上项，不另扣）· 补加粗**
- 原文：Police **enlisted** Jeffreys, and his tests **overturned**…
- 改法：Police **enlisted** Jeffreys, and his **genetic** tests **overturned**…（+1 词；genetic ✓ 未占用；补回问题 1 失去的一个加粗）；中文“他的**基因**(genetic)检测”

**10.（该改）删 1 词以守 271**
- 原文：A 17-year-old local youth then **confessed** to the second killing
- 改法：A 17-year-old local youth **confessed** to the second killing（−1 词；第二起案件已标 1986 年夏，then 可省）

**11.（可改）第 2 项 −0.5**
- 原文：P3 末句 The **forensic** **innovation** had freed an **innocent** before it **implicated** anyone. 与结尾 The test's first **beneficiary** had been a **blameless** **juvenile** …
- 问题：两句说同一件事，结尾的反转被提前用掉一半。加粗约束下难删，保留；返修时可考虑把 P3 末句换成别的角度。

**其余核查（不扣）**：elusive killer ✓ 地道；freed an innocent ✓（an innocent 作名词“无辜者”是规范用法）；falsely admitted the offence ✓（英式法律语体 admit the offence 地道；falsely 准确）；induced a co-worker ✓。

**12.（该改）第 9 项 −1**
- 原文：他曾**虚假地**(falsely)承认了这项**罪行**(offence)。
- 问题：“虚假地承认”欧化。
- 改法：他曾**违心**(falsely)认下这项**罪行**(offence)。

**13.（该改）第 9 项 −1**
- 原文：他成为已知第一个因 DNA 证据洗清嫌疑的人。（中文同英文问题 6 的指代歧义）
- 改法：那名青年成为已知第一个因 DNA 证据洗清嫌疑的人。

**14.（该改）第 10 项 −0.5**
- 原文：**同一个**(lone)
- 问题：lone 不是“同一个”，加粗落点错位（随问题 1 一并消失）。

## 改后词数
271 +0（1）+0（2）+0（3）−1（4）+0（5）+1（6）+1（9）−1（10）= 271 ✓。
已用改后英文实测：合计 271，段落 [50, 56, 49, 57, 59]，加粗 54 全部 ✓，无“已被占用”行，各段 10/10/11/12/11 ✓。

## 达标判断
无硬伤，90 < 95，不通过。改完 1–6、9、10、12–14 预计 98.5（剩可改 7、8、11 共 −1.5）。

总分 = 各项之和 已核（13+9.5+10+5+12+8+10+10+8+4.5 = 90）
