# 第 65 篇 The Fungus That Turns Ants into Zombies（僵尸蚂蚁真菌）评审 · 英文总编辑 · 第 1 轮

## 总分：98.5 / 100（无硬伤）

| 项 | 满分 | 得分 |
|---|---|---|
| 1 史实准确 | 15 | 15 |
| 2 论证与结构 | 10 | 10 |
| 3 语言质量 | 15 | 14.5 |
| 4 适配读者 | 5 | 5 |
| 5 学习价值 | 12 | 12 |
| 6 用法典型 | 8 | 8 |
| 7 速查表释义 | 10 | 10 |
| 8 忠实 | 10 | 10 |
| 9 通顺地道 | 10 | 9.5 |
| 10 重点词对应 | 5 | 4.5 |

## 机检（英文单独抽出，逐行读，未过滤）
- `en_check.py`：段落词数 [49, 47, 53, 45, 39, 22]，合计 **255** ✓；候选 **55** 个全部 ✓；**无“已被占用”行** ✓。
- **人工复核屈折碰撞**（对 used_words.json 前四字母近形逐个比对）：fungal／fungi・fungus、loosen／loose、lofty／loft、wanders／wanderer、rigidly／rigid、humid／humidity、invader／invade、location／locate、microscope／microscopic、narration／narrative、envisioned／envisage、hypothetical／hypothesis、infectious／infection、disappeared／disappearance、lifeless／lifetime、unsteady／unstable——均为派生词或不同词，**无同一词的屈折形式**（envisioned 的原形 envision 与台账 envisage 是两个不同的词）✓。

## 逐项核查（协调人点名）
| 词／句 | 判断 |
|---|---|
| **Swaying** / as if **intoxicated** | S1“走路失常（醉步）”——摇晃、像喝醉了，忠实 ✓ |
| the bite holds **rigidly** | S2 下颚肌肉被毁、死后仍咬住——“牢牢咬住”✓ |
| **infectious** spores | 孢子正是感染途径（S3 被觅食蚂蚁带上），准确 ✓ |
| where foraging ants **tread** | S3“觅食的蚂蚁能把它们带上”——tread 写“踩过”，蚂蚁经过即接触孢子，忠实 ✓ |
| **fussy** about **location** | S1 叶背、主叶脉、离地约 25 厘米、西北侧——“挑剔位置”是对这一串精确条件的概括 ✓ |
| **mostly** on the north-west side | 约稿单 T2 写“多在西北侧”；S1 原文为 on the north-west side，作者加 mostly 是更稳妥的对冲，不夸大 ✓ |
| puppet 比喻 | 写作 a picture that **evokes** the strings of a **puppet**，明确是“让人想到”，并紧接 Yet the fungus had not **infiltrated** the brain，点出控制在肌肉而非大脑——比喻贴着 S4，克制 ✓ |
| fictional horror for **gamers** | 游戏中的设定，准确 ✓；但与上句 hypothetical **scenario** 语义略叠（可改 1）|
| far deeper **geological** roots | 4800 万年化石出自梅塞尔（地层），与 2013 年游戏形成对照，成立 ✓ |
| pushes from its head | S3 菌柄从死蚁头部长出 ✓ |

## 其余史实（T1–T7）
泰国雨林木蚁、离开树冠路径 ✓；正午前后咬叶背主叶脉、离地约 25 厘米 ✓；黄昏死亡、下颚肌肉被毁、死后仍咬着 ✓；两三天后菌柄从头部长出、孢子落向地面 ✓；移高则真菌生长异常、移到地面则尸体消失（被吃或冲走）✓；2017 年三维显微成像、肌肉纤维周围的网络、未进入大脑 ✓；《地球脉动》阿滕伯勒解说片段启发 2013 年《最后生还者》、创作者设想跳到人类身上（间接转述，无引语）✓；4800 万年前德国叶片化石上有同样咬痕 ✓。

## 结尾
A 48-million-year-old **fossil** leaf from Messel, in Germany, bears the same **characteristic** bite **scars**.（14 词）
- 字面属实（S5）✓；无 fungus／turns／ants／zombies ✓。
- 开头：以冠词 A 开头，不是阿拉伯数字开头；不在禁用开头列表（A haven 被禁，A 48-million-year-old 不同）✓。
- 结构：简单主谓宾（X bears Y），不是“主句, + 名词短语”、极短判词、The year … saw、倒装、In effect、partly … has yet to、At that pace、so each of us carries、Its builders were not、A haven built against … had a weakness、The X that … was the one、The man whose … helped、would, decades later ✓。
- 禁用词与标点：无 ✓。

## 其他
- 代词跨段：各段以名词开头；P5 It helped inspire 的 It 指同段 A Planet Earth episode ✓。
- 对冲：每句至多一处 ✓。

## 中文
1. **bites** 译“咬痕”不妥（第 10 项 −0.5）：P3 讲的是蚂蚁“咬在哪里”（位置），不是留下的痕迹；而且“咬痕”与结尾 scars 的“疤痕”意思重叠，容易让读者以为两个英文词是一回事。
   - 改法：这些**咬合点**(bites)大多在植物的**西北**(north-west)侧……（或：蚂蚁大多**咬**在……——但须整词加粗，故推荐“咬合点”）
   - 结尾“留着同样**典型**(characteristic)的咬合**疤痕**(scars)”保留即可（scars＝疤痕，准确）。
2. **lifeless** 译“没了生气”欠准（第 9 项 −0.5）：“没了生气”多指萎靡无活力；lifeless 此处是“已死”。
   - 改法：到**黄昏**(dusk)时，这只昆虫已经**毫无生命**(lifeless)——或“已经**死去**(lifeless)”。

## 可改
**1. 第 3 项 −0.5**：That **hypothetical** **scenario** became **fictional** horror for **gamers**.——hypothetical 与 fictional 叠义（假想 → 虚构）。可作 That **scenario** became horror for **gamers**（失 hypothetical、fictional 两个加粗，55 → 53，仍 ≥50；−2 词），或保留。

## 必改
无（中文两条为该改）。

## 达标判断
98.5 ≥ 95、零硬伤，按我这一票通过。

会签：同意定稿

总分 = 各项之和 已核（15+10+14.5+5+12+8+10+10+9.5+4.5 = 98.5）
