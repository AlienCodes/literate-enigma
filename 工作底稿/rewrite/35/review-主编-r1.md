# 第 35 篇评审 · 英文总编辑 · 第 1 轮

## 总分：92.5 / 100（无硬伤，未达 95）

| 项 | 满分 | 得分 |
|---|---|---|
| 1 史实准确 | 15 | 14 |
| 2 论证与结构 | 10 | 10 |
| 3 语言质量 | 15 | 9.5 |
| 4 适配读者 | 5 | 5 |
| 5 学习价值 | 12 | 12 |
| 6 用法典型 | 8 | 8 |
| 7 速查表释义 | 10 | 10 |
| 8 忠实 | 10 | 10 |
| 9 通顺地道 | 10 | 9 |
| 10 重点词对应 | 5 | 5 |

## 机检（英文单独抽出，逐行读，未过滤）
`en_check.py`：段落词数 [47, 49, 52, 63, 59]，合计 270 ✓；候选 54 个全部 ✓；**无“已被占用”行** ✓；各段加粗 11/10/12/10/11 ✓。
替补词实测（本题词库极挤）：**未占用可用** determination、glare、collaborated、nullified、reservations、irregular、unfair、renewed、undone、erased；**已占用** restore、classified、reinstate(d)、posthumously、colleagues、yield、renowned、eminent、cautioned、revived、endured、lingered、recruited、explosion、enlisted、blast、tapped、summoned；**冷僻** annulled、rescinded、quashed、outlived、outlasted、unease、detonation；**基础** ruling、finding、staff、professor、advised、material；△ opposed、decades、appointed、selected。

## 史实核对（对照任务书 §3）
- 1904-04-22 纽约 ✓；理论物理学家、伯克利与加州理工 ✓（lecturer 见问题 7）
- 1943 年 4 月洛斯阿拉莫斯、数千人共同完成 ✓；oversaw = led，未写独自造弹 ✓；T2 1942 年 10 月格罗夫斯受命一事未写（任务书标 ★，但词数零余量、Recruited／tapped／enlisted 均已占用，记可改）
- 1945-07-16 三位一体、roughly 20 kilotons ✓
- 1945-08-06／09 广岛长崎 ✓；well over 100,000 / about 70,000 带对冲 ✓
- 1945 年 10 月辞职、1947 年起主持高等研究院 ✓
- 1949 年 10 月顾问委员会一致反对 crash programme ✓（未写反对一切核武）
- 1953 年 12 月总统指令切断接触机密 ✓
- 1954-04-12 至 05-06 安全听证，明写 administrative proceeding, not a criminal prosecution ✓
- 1954-06-29、4 比 1、合同到期前两天 ✓；did not find him disloyal ✓；character and associates ✓
- 1963-12-02 约翰逊授费米奖、肯尼迪生前批准 ✓；1967-02-18 去世、62 岁 ✓
- 2022-12-16 能源部长撤销 ✓；55 年：1967 → 2022 ✓
- 无间谍说、无引语 ✓

## 逐条问题

**1.（该改）第 3 项 −1**
- 原文：From April 1943 he **oversaw** a **secretive** **weapons** laboratory at Los Alamos, whose bombs were the **collaborative** **creation** of a **thousands-strong** **workforce** he **supervised**.
- 问题：oversaw 与 he supervised 同义重复，句尾拖沓。
- 改法：From April 1943 he **oversaw** a **secretive** **weapons** laboratory at Los Alamos, whose bombs were the **collaborative** **creation** of a **thousands-strong** **workforce**.（−2 词；P1 加粗 11→10，总数由问题 2 补回）
- 中文：从1943年4月起，他**主管**(oversaw)洛斯阿拉莫斯的一座**秘密**(secretive)**武器**(weapons)实验室；那里的炸弹由**数千人**(thousands-strong)的**员工队伍**(workforce)**协作**(collaborative)造出，是集体的**成果**(creation)。（删 supervised 加粗）

**2.（该改）第 3 项 −1**
- 原文：Trinity, **illuminated** the **desolate** New Mexico **landscape** with roughly 20 kilotons of **explosive** force.
- 问题：“用 2 万吨的爆炸力照亮”搭配错位，照亮的是光，不是当量。
- 改法：Trinity, **illuminated** the **desolate** New Mexico **landscape** with a blinding **glare**, its **explosive** force roughly 20 kilotons.（+3 词；glare ✓ 未占用，P2 加粗 10→11）
- 速查表增：glare | n. 强光，刺眼的光；怒视（the glare of headlights；in the full glare of publicity） | 2；中文：……以**刺眼**的**强光**(glare)**照亮**(illuminated)了新墨西哥州**荒凉**(desolate)的**大地**(landscape)，其**爆炸**(explosive)威力约合2万吨TNT当量。

**3.（必改）第 3 项 −1（兼及论证一致）**
- 原文：the energy secretary **officially** **vacated** the 1954 **judgement**, deeming the process **defective**…
- 问题：judgement 指法院判决，与上段“非刑事起诉”自相矛盾；deeming 生硬。
- 改法：the energy secretary **officially** **vacated** the 1954 **determination**, calling the process **defective**…（0 词；determination ✓ 未占用，是美国行政机关裁定的规范用语，AEC 当年文件即称 determination）；officially 保留（vacate 本身正式，officially 略冗，但删去会使 P5 降到 10、总数降到 53，不划算）
- 速查表：determination | n. （官方）裁定，决定；决心（a determination by the court/agency；with grim determination） | 5；中文“**裁定**(determination)”不变，“认定”改为“称”。

**4.（该改）第 3 项 −0.5**
- 原文：He resigned in October 1945（P3 段首）
- 问题：P2 无人物，He 要回指到 P1。
- 改法：Oppenheimer resigned in October 1945（0 词）

**5.（可改）第 3 项 −0.5**
- 原文：The **revocation** had **persisted** fifty-five years beyond his **lifetime**.
- 问题：beyond his lifetime 稍绕；但符合 §5：≤26（9 词）、无标题词、主语为 the revocation（非国家／政府）、非时间状语开头、非 years after、无禁用结构、不新增事实（55 年已核）。替换 outlived／outlasted 冷僻，after his death 触“years after”禁令，保留。

**6.（可改）第 3 项 −1（两处）**
- 原文：voicing **misgivings**, **unanimously** **counselled** against…——分词插入略松，counsel against 地道但偏旧，保留。
- 原文：severed his access to **confidential** **documentation**——美国说法为 classified material；classified 已占用、material 基础词，保留。

**7.（可改）第 3 项 −0.5；第 1 项 −0.5**
- 原文：voted 4 to 1 against letting him **regain** his clearance——技术上是“不予恢复”，restore 已占用，regain 不失实，保留。
- 原文：**prominent** **lecturer** at Berkeley and Caltech——他是教授，lecturer 在英式里是低一级职称，易误读；professor 为基础词，保留。

**8.（可改）第 1 项 −0.5**：1942 年 10 月格罗夫斯受命（T2）未写，词数零余量，保留。

**9.（该改）第 9 项 −1**
- 原文：这里造出的炸弹，是他**督导**(supervised)下**数千人**(thousands-strong)的**员工队伍**(workforce)**协作**(collaborative)完成的**成果**(creation)。
- 问题：定语堆叠，欧化。改法见问题 1 中文。

## 改后词数
270 −2（1）+3（2）+0（3、4）= 271 ✓。
已用改后英文实测：段落 [45, 52, 52, 63, 59]，合计 271，加粗 54 全部 ✓，**无“已被占用”行**，各段 10/11/12/10/11 ✓。

## 达标判断
无硬伤，92.5 < 95，不通过。改完 1–4、9 预计 97（剩可改 5–8 共 −3，词库与词数限制下难再压）。

总分 = 各项之和 已核（14+10+9.5+5+12+8+10+10+9+5 = 92.5）
