# 第 39 篇评审 · 英文总编辑 · 第 1 轮

## 总分：96.5 / 100（无硬伤）

| 项 | 满分 | 得分 |
|---|---|---|
| 1 史实准确 | 15 | 15 |
| 2 论证与结构 | 10 | 8.5 |
| 3 语言质量 | 15 | 13 |
| 4 适配读者 | 5 | 5 |
| 5 学习价值 | 12 | 12 |
| 6 用法典型 | 8 | 8 |
| 7 速查表释义 | 10 | 10 |
| 8 忠实 | 10 | 10 |
| 9 通顺地道 | 10 | 10 |
| 10 重点词对应 | 5 | 5 |

## 机检（英文单独抽出，逐行读，未过滤）
`en_check.py`：段落词数 [58, 45, 51, 58, 59]，合计 271 ✓（零余量）；候选 53 个全部 ✓；**无“已被占用”行** ✓；各段加粗 11/11/11/10/10 ✓。
替补词实测：oblivious、unaware ✓ 未占用；arms 基础词。

## 史实核对（对照任务书 §3 与 S1–S8）
- 2016 年初某夜、员工下班后（after keepers … had left，未写 waited）✓；网罩开口、落地、爬过房间、排水口、约 50 米管道、太平洋 ✓；推断标记 presumably 一处 ✓（S1 称路线由黏液痕迹还原）
- 黏液痕迹还原路线 ✓；2014 年渔民在内皮尔附近龙虾笼中发现 ✓；约三个月后 2016 年 4 月公开、成全球新闻 ✓
- 无骨无壳、唯一硬质是喙、喙能过即可过 ✓；约 5 亿神经元、约三分之二在腕足、腕足能一定程度自主 ✓（未写“九个大脑”）
- 西雅图巨型太平洋章鱼拧罐：起初 15 分钟、后约 2 分钟 ✓
- 2010 年研究：区分喂食者与刺毛棍者；adopting a different hue and posture 与 S6“体色斑纹与动作明显不同”一致 ✓（未写“记仇”）
- 2012 年 7 月剑桥宣言 neurological substrates for conscious awareness ✓（未说证明有意识）；2021 年 11 月英国政府评估报告建议视为有感知 ✓；2022 年 4 月法案纳入 ✓；None of this proves an inner life ✓ 公允
- 用 it 不用 he ✓；无引语、无下落 ✓

## 逐条问题

**1.（必改）第 2 项 −1.5**
- 原文：Inky, somewhere beyond the pipe, lay **wholly** outside the Act's **jurisdiction**.
- 问题：逻辑断口。该法是英国法律，Inky 在新西兰，无论在水箱里还是海里都本就不受其管辖；结尾把“越过管道”写成“脱离管辖”的原因，反讽不成立。
- 改法：Inky, somewhere beyond the pipe, remained **wholly** **oblivious** to the debate.（11 → 11 词，0；oblivious ✓ 未占用，替 jurisdiction，P5 加粗仍 10）
- §5：≤26 ✓；无 octopus／escaped／escape ✓；主语 Inky（建议之一）✓；非时间状语开头；无 lay in、had left、that bears、swept、never、evidently、may／might ✓；不新增事实（the debate 指上文剑桥宣言、评估报告、立法）✓；oblivious 只说它“不知道”，不算拟人过度。
- 速查表：删 jurisdiction，增 oblivious | adj. 未察觉的，浑然不知的（oblivious to the danger/noise） | 5；中文：Inky 身在管道另一头的某个地方，对这场讨论**全然**(wholly)**浑然不觉**(oblivious)。（若“全然”与“浑然”嫌重，作：对这场讨论**完全**(wholly)**一无所知**(oblivious)）

**2.（该改）第 3 项 −0.5**
- 原文：Made public in April 2016, it travelled the **globe**.
- 问题：it 指 breakout，“出逃周游世界”；传遍世界的是消息。
- 改法：Made public in April 2016, the story travelled the **globe**.（+1 词）

**3.（该改）第 3 项 −0.5（配套删词）**
- 原文：compressed its **elastic** body into a drain, whose **hollow** pipe **stretched** some 50 metres to the Pacific.
- 问题：管道本就是空心的，hollow 为凑词赘语。
- 改法：…into a drain, whose pipe **stretched** some 50 metres to the Pacific.（−1 词；P1 加粗 11→10，全篇 53→52，仍 ≥50）；中文删“**中空**(hollow)的”

**4.（该改）第 3 项 −0.5**
- 原文：About two-thirds of its roughly 500 million **neurons** lie in the **limbs**
- 问题：一句两个对冲词（about、roughly），违反任务书禁区 3。
- 改法：Roughly two-thirds of its 500 million **neurons** lie in the **limbs**（−1 词；5 亿本为整数估计，不再重复对冲）；中文“章鱼的5亿个神经元中，约三分之二……”

**5.（该改）第 3 项 −0.5**
- 原文：The **wits** are as **versatile** as the **anatomy**.
- 问题：The wits 泛指不清，应为它的才智。
- 改法：Its **wits** are as **versatile** as its **anatomy**.（0 词）

**其余核查（不扣）**：crept through an aperture（S1 为挤出，crept 属润色可接受）；fugitive／breakout 拟人适度，未写渴望自由 ✓；limbs 指腕足可接受；discriminate between ✓；possessing the neurological substrates ✓；encompassed ✓。中文全篇通顺，“这名逃犯想必随后落到地面”“呈现出不同的体色和姿态”准确。

## 改后词数
271 +1（2）−1（3）−1（4）+0（1、5）= 270 ✓。
已用改后英文实测：段落 [57, 46, 50, 58, 59]，合计 270，加粗 52 全部 ✓，**无“已被占用”行**，各段 10/11/11/10/10 ✓。

## 达标判断
≥95、零硬伤，按我这一票通过；但**问题 1 必须改**（结尾逻辑）。改完 1–5 预计 100。

会签：同意定稿（以落实必改 1 为条件）

总分 = 各项之和 已核（15+8.5+13+5+12+8+10+10+10+5 = 96.5）
