# 第 42 篇评审 · 英文总编辑 · 第 1 轮

## 总分：98 / 100（无硬伤）

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
| 9 通顺地道 | 10 | 10 |
| 10 重点词对应 | 5 | 5 |

## 机检（英文单独抽出，逐行读，未过滤）
`en_check.py`：段落词数 [49, 49, 58, 57, 58]，合计 271 ✓（零余量）；候选 50 个全部 ✓；**无“已被占用”行** ✓；各段加粗恰 10 ✓。“1.5／2.2／1.3 小数”为视频稿提示，属史实原值，不改。

## 史实核对（对照任务书 §3 与 S1–S6）
- 1990-04-24 发现号送入轨道、约 15 亿美元 ✓（未写“最清晰”类夸张）
- 1990 年 6 月宣布主镜缺陷 ✓；外缘磨平约 2.2 微米、约头发丝宽度五十分之一 ✓
- 检测装置中一块透镜偏约 1.3 毫米 ✓；珀金-埃尔默另一台独立测试结果不同，工程师与 NASA 管理人员认为不可靠、未追查 ✓（S3）
- 主镜无法在轨修复 ✓；COSTAR 冰箱大小、可动机械臂上的小镜子在光到达仪器前截住并矫正 ✓；新主相机 ✓（未写其自带矫正，遵 T5）
- 1993-12-02 奋进号、7 名宇航员、5 次太空行走、约 35.5 小时、装 COSTAR 与新相机、恢复视力 ✓

## “眼镜”比喻与结尾核查
- 比喻：prescribed **tailored** glasses → COSTAR 截住光线、抵消主镜畸变，**The mirror itself would stay untouched** 明确交代主镜未修——符合禁区 4“矫正装置，主镜没被修” ✓。比喻准确：眼镜矫正的是进入眼睛之前的光，不改眼球；COSTAR 矫正的是进入仪器之前的光，不改主镜。
- 结尾：The mirror still carries that 2.2-micrometre flaw, and the light it **gathers** is corrected only after leaving it.（20 词）
  - 主镜至今带着误差：S6 明载哈勃从未返回地面、主镜始终带着误差 ✓；still 用现在时，哈勃至今在轨运行 ✓
  - 光离开主镜之后才被矫正：1993–2009 由 COSTAR／新相机内部光学完成，2009 年 COSTAR 拆除后由各仪器自带矫正光学完成（S6），任何时期矫正都发生在光离开主镜之后 ✓。结尾措辞不提 COSTAR，因此 2009 年拆除并不使其失实 ✓
  - §5：≤26 ✓；无 telescope／glasses／needed 及同族 ✓；非 What／Yet／Every／时间状语开头 ✓；无 came from、remained、mourned、never、had left、evidently、may/might、冒号分号破折号、最高级 ✓。后半句“and + 名词 + is + 过去分词”与 41 篇后半句同为被动，但主语、动词、整体结构不同，不算同构 ✓
  - 不新增事实（2.2 微米与“矫正在镜后”正文已有）✓；不下判决 ✓

## 逐条问题

**1.（该改）第 3 项 −0.5**
- 原文：its outer **rim** had been **flattened** by about 2.2 micrometres, roughly a fiftieth of the **width** of a hair.
- 问题：一句两个对冲词（about、roughly），违反禁区 2。
- 改法：…**flattened** by 2.2 micrometres, roughly a fiftieth of the **width** of a hair.（−1 词）；中文“磨平了2.2微米，大约相当于……”

**2.（该改）第 3 项 −0.5**
- 原文：…**compensated** for the **imperfect** mirror's **distortion** before it reached the instruments.
- 问题：it 可指 distortion 或 light，指代不清。
- 改法：…before the light reached the instruments.（+1 词，与问题 1 抵消）
- 已实测 1+2：271 词，加粗 50，无占用行，各段 10 ✓

**3.（可改）第 3 项 −0.5**
- 原文：came back **blurred** and **fuzzy**——近义叠用；P2 加粗恰 10，保留。

**4.（可改）第 3 项 −0.5**
- 原文：they worked in **tandem** across five spacewalks
- 问题：来源为“两人一组”，in tandem 是“协同、并肩”，不必然是两人一组；不失实但不如 in pairs 准确。in pairs 为基础词、P5 加粗恰 10，保留。

**其余核查（不扣）**：lofted、cradled in the payload bay、lavish investment、prescribed tailored glasses、intercepted、rendezvous、crisp 均地道；calibration 概括“检测装置设置错误”可接受。中文全篇通顺，“开出了一副量身定制的眼镜”“主镜将保持原封不动”自然准确。

## 改后词数
271 −1（1）+1（2）= 271 ✓（已实测）

## 达标判断
≥95、零硬伤，按我这一票通过；结尾与比喻事实成立。落实 1、2 即为 99。

会签：同意定稿

总分 = 各项之和 已核（15+10+13+5+12+8+10+10+10+5 = 98）
