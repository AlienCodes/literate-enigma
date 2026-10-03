# 第 33 篇评审 · 英文总编辑 · 第 1 轮

## 总分：91.5 / 100（无硬伤，未达 95）

| 项 | 满分 | 得分 |
|---|---|---|
| 1 史实准确 | 15 | 14 |
| 2 论证与结构 | 10 | 9 |
| 3 语言质量 | 15 | 10.5 |
| 4 适配读者 | 5 | 5 |
| 5 学习价值 | 12 | 12 |
| 6 用法典型 | 8 | 8 |
| 7 速查表释义 | 10 | 10 |
| 8 忠实 | 10 | 9 |
| 9 通顺地道 | 10 | 9 |
| 10 重点词对应 | 5 | 5 |

## 机检（英文单独抽出，逐行读，未过滤）
`en_check.py`：段落词数 [47, 55, 43, 59, 64]，合计 268 ✓；候选 54 个全部 ✓；**无“已被占用”行** ✓；各段加粗 12/11/10/11/10 ✓。另有提示“4.4 小数”（264.4 hours），属史实原值，不改。
替补词实测：jolted、attentively、exhaustion、ostensibly、underline、lamented 均 ✓ 未占用；apparently、seemingly、rebounded、restless、asserted、chronic、recounted、disclosed、ascribed、attribute 已占用；asleep、slept 等为基础词。

## 史实核对（对照任务书 §3）
- 1963-12-28、17 岁、圣迭戈高中、科学展 ✓（science enthusiast 为润色，可接受）；两个朋友 ✓；获第一名 ✓
- 德门特读报赶来、协助海军研究员罗斯 ✓；未写“从第一天起”✓
- 情绪、注意力、短时记忆、多疑、幻觉 ✓；第四天自认职业橄榄球运动员 ✓
- 1964-01-08、264.4 小时、about 11 days and 25 minutes ✓（非 24 分）
- about 14 hours ✓；woke apparently refreshed ✓（apparently 保留）
- 1965 论文、微睡眠释义 ✓；may have ✓
- 1997 吉尼斯因健康风险停止监测 ✓；他人声称更久（professed，未写人名时长，自带存疑）✓
- 2017 采访、约十年严重失眠、he himself pinned it on the experiment ✓（因果只归他本人）
- 小问题：noting **each** fluctuation 略夸大（德门特并非全程在场），见问题 4；原结尾 bounced back 未带对冲、grew into 暗含因果，见问题 8。

## 逐条问题

**1.（该改）第 3 项 −1**
- 原文：Two **companions** **diligently** **roused** him whenever his **alertness** **waned**
- 问题：rouse 指把睡着的人叫醒；他自始没睡，用词与事实相抵。
- 改法：Two **companions** **diligently** **jolted** him awake whenever his **alertness** **waned**（+1 词；jolted ✓ 未占用）；速查表 jolted | v. (jolt) 使猛然一震；使惊醒（jolt sb awake；jolt sb out of complacency） | 1；中文“就把他**叫醒**(roused)”改为“就把他**摇醒**(jolted)，让他保持清醒”——更简：“就**猛推**(jolted)他一把，让他清醒过来”

**2.（该改）第 3 项 −0.5**
- 原文：The **voluntary** **endeavour** went on to take first place.
- 问题：“尝试”本身去拿第一名，主语错位；获奖的是科学展项目。
- 改法：The project, a **voluntary** **endeavour**, went on to take first place.（+2 词）；中文“这个项目是一次**自愿**(voluntary)的**尝试**(endeavour)，后来获得了第一名。”

**3.（可改）第 3 项 −0.5**
- 原文：set out to **forgo** **slumber**
- 问题：forgo sleep 可说，slumber 文学腔，二者叠用略做作；但两词均加粗、P1 改动代价大，保留。中文“舍弃睡眠”见问题 10。

**4.（该改）第 3 项 −1；第 1 项 −0.5**
- 原文：…in monitoring the **sleepless** boy **closely**. The two **investigators** kept an **attentive** eye on him, noting each **fluctuation** in his state as the **deprivation** **progressively** **deepened**.
- 问题：monitoring closely 与 kept an attentive eye 同义重复；each 夸大了记录的完整性（德门特中途才到）。
- 改法：The two **investigators** **attentively** noted **fluctuations** in his state as the **deprivation** **progressively** **deepened**.——为保持 ✓ 已测版本，最小改为：The two **investigators** **attentively** noted each **fluctuation** in his state…（−5 词；attentively ✓ 未占用；each 若改为复数 fluctuations 再 −1 词，须语言学家确认 fluctuations 与 fluctuation 同格）。investigators 指研究人员属规范用法，不改。
- 中文：“两位**调查者**(investigators)**细心**(attentively)记下他状态的**波动**(fluctuation)……”

**5.（可改）第 3 项 −0.5**：the **deprivation** **progressively** **deepened**——progressively 与 deepened 语义叠加，三词加粗，保留。

**6.（该改）第 3 项 −0.5**
- 原文：He may have had such **momentary** **bouts** **unawares**.
- 问题：unawares 是古旧书面词，常见只在 catch/take sb unawares 里。
- 改法：He may have had such **momentary** **bouts** without noticing.（+1 词；P4 加粗 11→10，仍达标）；速查表删 unawares 行；中文“他可能在不知不觉中经历过这种**片刻**(momentary)的**发作**(bouts)”（不知不觉不再加粗）

**7.（可改）第 3 项 −0.5**
- 原文：others have since **professed** longer **stints** awake
- 问题：profess 多接信仰／情感／无知（profess ignorance），接“经历”略生硬；好处是自带“自称”的存疑色彩，与 T10 慎用相合。保留。probed、helped **highlight**、**pinned** it on 均为地道用法，不扣。

**8.（必改）第 2 项 −1；第 1 项 −0.5**
- 原文：The teenager who had **bounced** back after a single long rest grew into a man who could **barely** **doze**.
- 问题：① 花园路径：读者在 “rest grew” 处卡住；② bounced back 无对冲，与正文 apparently 不一致；③ grew into 把晚年失眠写成成长的直接结果，暗含因果，超出 T11“只是他的看法”。
- 改法：The man who could **barely** **doze** had, as a boy, seemed to **bounce** back from **exhaustion** with a single long rest.（21 词，+1；exhaustion ✓ 未占用，P5 加粗 10→11；结尾无标题词、无禁用结构：非 had been + 名词 + 关系从句、不以时间状语开头、无 once + 过去分词、无冒号分号破折号）
- 关于 doze：barely doze = 连打个盹都难，语义上足以表达严重失眠，不算轻描淡写；sleep 为标题禁词，保留 doze。
- 中文：那个连**盹**(doze)都**几乎**(barely)打不成的人，少年时似乎只睡了一个长觉，就从**疲惫**(exhaustion)中**恢复**(bounce)了过来。

**9.（该改）第 8 项 −1**
- 原文：就把他**叫醒**(roused)
- 问题：随问题 1，“叫醒”与事实相抵（他未入睡）。改法见问题 1。

**10.（该改）第 9 项 −0.5**
- 原文：开始尝试**舍弃**(forgo)**睡眠**(slumber)
- 改法：开始尝试**放弃**(forgo)**睡眠**(slumber)，挑战不睡觉

**11.（该改）第 9 项 −0.5**
- 原文：两位**调查者**(investigators)
- 问题：“调查者”像警方或记者。
- 改法：两位**研究人员**(investigators)——上文 researcher 未加粗，不冲突。

## 改后词数
手算：268 +1（1）+2（2）−5（4）+1（6）+1（8）= 268；机检实测改后全文为 **269**（以机检为准，差 1 来自原结尾计数），≤271 ✓。
实测结果：段落 [50, 50, 43, 60, 66]，加粗 54 全部 ✓，**无“已被占用”行**，各段 12/11/10/10/11 ✓。

## 达标判断
无硬伤，91.5 < 95，不通过。改完 1、2、4、6、8–11 预计 97.5（剩可改 3、5、7 共 −1.5）。

总分 = 各项之和 已核（14+9+10.5+5+12+8+10+9+9+5 = 91.5）
