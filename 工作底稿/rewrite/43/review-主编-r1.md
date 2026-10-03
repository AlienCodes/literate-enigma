# 第 43 篇评审 · 英文总编辑 · 第 1 轮

## 总分：98 / 100（无硬伤）

| 项 | 满分 | 得分 |
|---|---|---|
| 1 史实准确 | 15 | 14 |
| 2 论证与结构 | 10 | 10 |
| 3 语言质量 | 15 | 14.5 |
| 4 适配读者 | 5 | 5 |
| 5 学习价值 | 12 | 12 |
| 6 用法典型 | 8 | 8 |
| 7 速查表释义 | 10 | 10 |
| 8 忠实 | 10 | 10 |
| 9 通顺地道 | 10 | 9.5 |
| 10 重点词对应 | 5 | 5 |

## 机检（英文单独抽出，逐行读，未过滤）
`en_check.py`：段落词数 [55, 55, 49, 62, 50]，合计 271 ✓（零余量）；候选 51 个全部 ✓；**无“已被占用”行** ✓；各段加粗 10/11/10/10/10 ✓。

## 史实核对（对照任务书 §3 与 S1–S7）
- 1991-09-19、两名德国徒步者、奥茨塔尔阿尔卑斯、约 3,210 米、奥意边境、山脊 ✓；起初以为当代登山者、冰川偶尔吐出遗体 ✓（未写“露出冰面”）
- 当作新近死亡、风钻撕下左髋皮肉 ✓
- 皮革草衣、铜斧、弓箭 → 史前 ✓；天然木乃伊、约 5,300 年前、公元前 3350–3105 年、称奥茨 ✓
- 2001 年 X 光、左肩燧石箭头、十年前漏掉 ✓；动脉撕裂、大出血、血块、几分钟内死亡、约 46 岁 ✓
- 他人所杀、由伤口深度推断从背后约 30 米射来、很可能出其不意 ✓
- 2018 年研究：干野山羊肉与脂肪、马鹿、单粒小麦 ✓；reportedly 死前两小时内 ✓（S6 为 30 分钟至 2 小时，within two hours 涵盖）
- 文身 61 处、关节脊柱、perhaps 针灸 ✓；博尔扎诺 ✓
- 无发现者姓名、无诅咒、无凶手身份或“逃亡”猜测 ✓；时间顺序 1991 → 鉴定 → 2001 → 2018 ✓

## 协调人点名两处

### 一、凶案推断的对冲
- They concluded that another person killed him.：主语 They 承上句 Researchers，**有归属**，不是叙述者直陈；任务书禁区 1 也把 concluded 列为可用词。但 S5 原意是“认为”（believe），concluded 比来源更笃定，一句话把“他杀”说成已下的结论，略过硬。见问题 1。
- inferred（推断方向与距离）✓、probably（出其不意）✓、Researchers believe（几分钟内死亡）✓、reportedly（进食时间）✓——其余对冲充分。
- 但 Researchers believe he died within minutes, aged about 46. 一句两个对冲（believe、about），违反禁区 3。见问题 2。

### 二、结尾
He has a name, a last meal and a cause of death, while his **anonymous** **killer** has none.（18 词）
- 凶手身份确实不明（S5 只说“被他人杀害”）✓；凶手的最后一餐、死因自然无从知晓 ✓；“他有名字”——Ötzi 是 1991 年后起的名字，但“他现在有一个名字”字面成立，且正文已交代 Known as Ötzi ✓；最后一餐、死因（动脉撕裂、几分钟内死亡）正文均已写 ✓。修辞成立。
- 小瑕疵：anonymous 与 has none（含“无名”）语义重叠，见问题 4。
- killer 一词以“他杀”为前提，前文已以 researchers believe 归属，结尾回用不算新断言 ✓。
- §5：≤26 ✓；无 murder／ice／5,000 及同族 ✓；He 开头，非时间状语／What／Yet／Every ✓；无 still carries、came from、remained、mourned、never、had left 等 ✓；无冒号分号破折号、最高级 ✓；不新增事实 ✓。

## 逐条问题

**1.（该改）第 1 项 −0.5**
- 原文：They concluded that another person killed him.
- 改法：They believe another person killed him.（−1 词；与 S5“认为”一致）
- 中文：“研究者断定，是另一个人杀死了他”改为“研究者认为，是另一个人杀死了他”

**2.（该改）第 3 项 −0.5**
- 原文：Researchers believe he died within minutes, aged about 46.
- 问题：一句两个对冲（believe、about）。
- 改法：Researchers believe he died within minutes. He was about 46.（+2 词）

**3.（该改）配套删词 −1 词**
- 原文：X-rays revealed a small **flint** arrowhead → 改法：X-rays revealed a **flint** arrowhead（small 非来源要点；P3 加粗不变）
- 已实测 1+2+3：270 词，段落 [55, 55, 49, 61, 50]，加粗 51，无占用行，各段 10/11/10/10/10 ✓
- 注意：**不要**用删 on a **trek** 来腾词——P1 加粗只有 10，删 trek 会降到 9（已实测）。

**4.（可改）第 3 项（不另扣，并入 0.5 内）**
- 原文：while his **anonymous** **killer** has none
- 问题：anonymous 已含“无名”，与 has none 略重复；但两词均加粗、P5 恰 10，保留。

**5.（可改）第 1 项 −0.5**
- 原文：a **hearty**, **nourishing** meal
- 问题：来源只列了食物，hearty（丰盛）尚可从“肉、脂肪、谷物”推出，nourishing 属评价性推断；P4 加粗恰 10，保留。

**6.（该改）第 9 项 −0.5**
- 原文：他曾**进食**(dined)干野山羊肉和脂肪……
- 问题：“曾进食”生硬。
- 改法：他最后**吃**(dined)的是干野山羊肉和脂肪、**马鹿**(deer)肉以及单粒小麦……

## 改后词数
271 −1（1）+2（2）−1（3）= 271；**实测 270**（以机检为准）✓

## 达标判断
≥95、零硬伤，按我这一票通过；对冲经问题 1、2 修正后充分，结尾修辞成立。落实 1–3、6 预计 99.5。

会签：同意定稿

总分 = 各项之和 已核（14+10+14.5+5+12+8+10+10+9.5+5 = 98）
