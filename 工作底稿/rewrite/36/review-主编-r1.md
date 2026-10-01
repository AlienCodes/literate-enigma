# 第 36 篇评审 · 英文总编辑 · 第 1 轮

## 总分：95.5 / 100（无硬伤）

| 项 | 满分 | 得分 |
|---|---|---|
| 1 史实准确 | 15 | 14 |
| 2 论证与结构 | 10 | 10 |
| 3 语言质量 | 15 | 12 |
| 4 适配读者 | 5 | 5 |
| 5 学习价值 | 12 | 12 |
| 6 用法典型 | 8 | 8 |
| 7 速查表释义 | 10 | 10 |
| 8 忠实 | 10 | 10 |
| 9 通顺地道 | 10 | 9.5 |
| 10 重点词对应 | 5 | 5 |

## 机检（英文单独抽出，逐行读，未过滤）
`en_check.py`：段落词数 [52, 45, 39, 64, 69]，合计 269 ✓；候选 54 个全部 ✓；**无“已被占用”行** ✓；各段加粗 12/11/11/10/10 ✓。
替补词实测：**未占用可用** ushered、heralded、imprints；**已占用** devoured、sequence、consecutive、reportedly、conceived、dazzled；**冷僻** hardbacks、perused、avidly；**基础** modest、teach、lessons、tutor、firms、printing、brought；△ initial。另：£ 符号会触发视频稿“特殊符号”提示，故不建议把 1,500 pounds 改成 £1,500。

## 史实核对（对照任务书 §3）
- 1990 年、晚点火车、曼彻斯特 → 国王十字 ✓（未写月份）
- 母亲 1990-12-30 去世、45 岁 ✓；移居波尔图教英语 ✓
- 1992 年 10 月结婚、1993 年 7 月女儿出生 ✓（无丈夫姓名）
- 1993 年底回爱丁堡、单亲、靠国家福利、常在咖啡馆写作 ✓；无取暖说、无餐巾纸、无店名 ✓；无贫困渲染 ✓
- 经纪人利特尔接稿 ✓（无年份）；reportedly rejected by twelve publishers ✓
- 牛顿把第一章给 8 岁的艾丽斯，她要看下一部分 ✓；预付 1,500 英镑与之并列，未说成因果 ✓
- 担心男孩不读女作家、用缩写、无中间名、K 取自祖母凯瑟琳 ✓
- 1997-06-26 出版、首印 500 册精装、300 册给图书馆 ✓
- 学乐 10.5 万美元、1998-09-01、Sorcerer's Stone ✓
- 系列及衍生书逾 5 亿册、80 种语言 ✓（spin-off volumes 交代了衍生书）
- 结尾 Alice's **appetite** was **evidently** shared by millions.（8 词）：无 book／twelve／publishers／turned／down 及同族 ✓；主语 Alice's appetite 符合建议 ✓；非任何已禁结构、非时间状语开头、无最高级、无冒号分号破折号 ✓；不新增事实、不鸡汤 ✓
- 推断性润色：an early endorsement（把接稿说成“认可”）、cautious（首印谨慎）、relished、in succession、relentless … little encouragement 属叙事推断；其中前两处写成了事实判断，合计 −1，其余按润色可接受，在第 3 项记语气问题。

## 逐条问题

**1.（该改）第 1 项 −0.5**
- 原文：A **literary** agent, Christopher Little, took on the manuscript, an early **endorsement**, and **pitched** it…
- 问题：“早期认可”是作者推断，来源只说接下书稿。
- 改法：A **literary** agent, Christopher Little, took on the manuscript and **pitched** it…（−3 词；P3 加粗 11→10，总数由问题 2 补回）；中文删“这是一份早期的**认可**(endorsement)”，速查表删 endorsement 行。

**2.（该改）第 3 项 −0.5**
- 原文：Rowling married in Porto in October 1992, and **motherhood** followed in July 1993 with the **arrival** of a daughter.
- 问题：followed … with the arrival of 绕。
- 改法：Rowling married in Porto in October 1992, and a daughter's **arrival** in July 1993 **ushered** in **motherhood**.（−1 词；ushered ✓ 未占用，P2 加粗 11→12）
- 速查表增：ushered | v. (usher in) 开创，引来（usher in a new era）；引领（usher sb into a room） | 2；中文：1992年10月，罗琳在波尔图结婚；1993年7月，女儿的**降生**(arrival)**开启**(ushered)了她为人**母**(motherhood)的生活。
- 已实测问题 1+2：264 词，段落 [52, 43, 36, 64, 69]，加粗 54 全部 ✓，无占用行，各段 12/12/10/10/10 ✓。（实测稿含 £ 时为 263，不采用 £。）

**3.（可改）第 1 项 −0.5**
- 原文：in a **cautious** first print run of 500 **hardcovers**
- 问题：cautious 为推断；hardcovers 为美式，英式作 hardbacks。但 hardbacks 冷僻、无合规替换，删任一词 P5 都会降到 9。保留。

**4.（可改）第 3 项 −2.5（五处，均因词库或加粗约束保留）**
- an orphaned young **wizard** 同位语插在主语与谓语之间 −0.5；
- **Grief** soon **overshadowed** that **spark** 隐喻略混（影子遮火花）、soon 有推断 −0.5；
- to give English **tuition**（teach English 更自然，teach 基础词）−0.5；
- a **relentless** run of **refusals** that offered the **newcomer** little **encouragement** 带情绪推断，近于煽情 −0.5；
- Bloomsbury paid an advance, a **sum** of 1,500 pounds 句式注水，且与 $105,000 写法不一 −0.5。
- prospective buyers 指出版社可接受；relished、eagerly 属允许的润色；appetite 地道；in succession 可接受。均不扣。

**5.（该改）第 9 项 −0.5**
- 原文：爱丽丝的这份**胃口**(appetite)，**显然**(evidently)有千百万人与她共享。
- 改法：**显然**(evidently)，千百万读者都有着和爱丽丝一样的**胃口**(appetite)。

## 改后词数
269 −3（1）−1（2）= 265（机检实测 264，以机检为准）✓

## 达标判断
95.5、零硬伤，按我这一票通过；落实 1、2、5 预计 97。词库已极挤，余下扣分多因无合规替换，不建议为此再大改。

会签：同意定稿

总分 = 各项之和 已核（14+10+12+5+12+8+10+10+9.5+5 = 95.5）
