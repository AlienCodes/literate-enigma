> **朋克英语隐藏署名版（最新PDF）**：全部相关PDF统一加入默认关闭的“来源署名｜朋克英语”图层；已认可书封的新顺序合订本共475页。下载[全本PDF](https://github.com/alienalgorithm/postgraduate-vocabulary/releases/download/punk-english-pdfs-2026.11.13-v2/PUNK-ENGLISH-70-STORIES.pdf)、[70份分篇PDF包](https://github.com/alienalgorithm/postgraduate-vocabulary/releases/download/punk-english-pdfs-2026.11.13-v2/70-PDF-BOOKLETS-PUNK-ENGLISH.zip)或[全部相关PDF署名版](https://github.com/alienalgorithm/postgraduate-vocabulary/releases/tag/punk-english-pdfs-2026.11.13-v2)。[查看隐藏署名的方法](朋克英语署名版/2026-11-13-v1/查看隐藏署名.md)。旧版保留供追溯。

> **70篇新顺序版**：已按用户指定顺序重新编号为01—70，PDF目录、篇内编号与视频文件名一一对应。只下载PDF小册子和4K视频，请使用[新顺序版Release](https://github.com/alienalgorithm/postgraduate-vocabulary/releases/tag/reading-reordered-2026.11.13-v1)；附件仅含合订PDF、70份分篇PDF包、70部4K视频包。详见[新顺序版说明](顺序重排版/README.md)。
>
> **2026-11-13 原顺序完整成果归档**：70部最终4K视频、70篇插图小册子、7册合订PDF及配套素材、源码和审校记录，见[完整下载Release](https://github.com/alienalgorithm/postgraduate-vocabulary/releases/tag/reading-complete-2026.11.13-v2)与[归档说明](成果归档/README.md)。保存规则见[AGENTS.md](AGENTS.md)。

# 记词 · 考研词汇双语读本

《经济学人》风格的双语科普短文，面向考研词汇学习。每篇自题材中挑出 50 个重点词，跨篇不重复（含同根）。英文重点词加粗，中文自然译法同步加粗并保留英文原样括注；网站提供中英连线、单语阅读、挖空自测、字号切换、打印和1500词索引。

**网站** → https://alienrocketbus.github.io/postgraduate-vocabulary/

## 怎么用这 3,500 个词

- **看片**：[`watch.html?a=01`](watch.html?a=01) —— 16:9 黑板视频（1920×1080，重点词金色，配英音朗读），可直接下载 mp4。
- **听读**：[`listen.html?a=01`](listen.html?a=01) —— 黑板跟读，英文逐词高亮、中英重点词同色，配离线合成的英音朗读（第 01 篇已做）。

- **学习大纲**：[`exports/学习大纲.md`](exports/学习大纲.md) —— 词分四档（核心 412／常用 1,080／进阶 1,344／冷僻 664）、七十篇难度梯队与主题索引、十二周路径。
- **Anki 卡**：[`exports/anki-3500.tsv`](exports/anki-3500.tsv) —— 3,500 张，每张带原句；**已按学习顺序排好**（牌组选项 → 新卡顺序 → 按添加顺序）。只背核心词：搜索 `tag:核心`。
- 机器读：[`exports/syllabus.json`](exports/syllabus.json)

## 黑板视频（听读 / 看片）

把一篇文章变成 **1920×1080 的黑板朗读视频**：标题页（中英标题，念出来）→ 一段英文＋紧跟它的中文，
重点词金色 → 结尾静音缓冲。配音是**离线合成**的（kokoro，不联网、无 API key）。

### 成品

| 篇 | 标题 | 视频 |
|---|---|---|
| 01 | Snow and the Broad Street Pump / 斯诺与宽街水泵 | [`reader/a01.mp4`](reader/a01.mp4) |
| 02 | A Garden Without Sunlight / 不见阳光的花园 | [`reader/a02.mp4`](reader/a02.mp4) |
| 03 | The Graph That Changed the Sky / 改变天空的那张图 | [`reader/a03.mp4`](reader/a03.mp4) |
| 04 | Fifteen Degrees an Hour / 一小时，十五度 | [`reader/a04.mp4`](reader/a04.mp4) |
| 05 | The Price Was Elsewhere / 价格在别处 | [`reader/a05.mp4`](reader/a05.mp4) |
| 06 | The Reaction That Had to Be Invented Twice / 一种不得不发明两次的反应 | [`reader/a06.mp4`](reader/a06.mp4) |
| 07 | The Meaning He Left Out / 他暂时略去的意义 | [`reader/a07.mp4`](reader/a07.mp4) |
| 08 | A Ruler Without a Zero / 一把没有零点的尺子 | [`reader/a08.mp4`](reader/a08.mp4) |
| 09 | Zero Was Not Enough / 归零还不够 | [`reader/a09.mp4`](reader/a09.mp4) |

> **a01-a05** 由 **Git LFS** 管（见 `.gitattributes`）；克隆后要拿到真文件：`git lfs install && git lfs pull`。
> **a06 起是普通 git blob**，直接 clone 就有，不必跑 LFS 命令——这个沙箱的网络白名单到不了
> LFS 实际传输用的 `github-cloud.s3.amazonaws.com`，改用 `git lfs migrate export` 把 a06 起的视频
> 转成普通 blob 才推上去的（2026-09-13）。往后的新视频（a10 起）也按普通 blob 直接 `git add`，
> 不必再跑 migrate——`.gitattributes` 已经把 `reader/*.mp4` 的通配 LFS 规则改成只列 a01-a05 五行，
> 新文件默认就不会被 LFS 接管。详情见 `notes/对话交接文档.md`。

网页两个入口：[`watch.html?a=01`](watch.html?a=01)（播视频，点句跳转）、
[`listen.html?a=01`](listen.html?a=01)（跟读页，逐词高亮）。

### 怎么做一篇

```bash
git lfs install && git lfs pull        # 只有 a01-05.mp4 和 say-en 模型走 LFS；a06 起是普通 blob，clone 就有
pip install kokoro-onnx soundfile numpy --break-system-packages

python3 scripts/build_reader.py 10     # 合成音频 + 切意群 → reader/a10.json
python3 scripts/make_video.py  10      # 渲视频 → reader/a10.mp4（渲完自动过检察官）
```

**离线 TTS 连同 338 MB 模型都在仓库里**（`tools/say-en/`，走 Git LFS），
`build_reader.py` 默认就用它，不必另外下载。

`build_reader.py` 支持断点续跑（`--n 8` 限流，反复跑同一条命令推进）——批量合成会被 OOM killer
无声杀掉，这是 say-en 文档第五条的教训。

### 这套程序都有什么

| 脚本 | 干什么 |
|---|---|
| `scripts/build_reader.py` | 合成逐句音频（含标题）、切中英意群、写逐词时间轴，产出 `reader/aNN.json` |
| `scripts/make_video.py` | 渲 1920×1080 黑板视频；渲完自动调检察官，**不过就把 mp4 删掉** |
| `scripts/video_inspector.py` | **视频检察官**：三层二十四条，见下 |
| `scripts/check_chunks.py` | 意群对齐检查员，每次 build 完自动跑，有 A 级就红；自带坏例子自测 |
| `scripts/gate_drill.py` | **闸门演习**：把每条标准故意做坏一次，看检察官响不响。挂在 preflight 里 |
| `listen.html` / `watch.html` | 跟读页 / 看片页 |

### 视频检察官（三层二十四条）

任何一条不过，视频不算成品——`make_video.py` 渲完自动跑，不过就删。

**一层 · 分句与对齐（8）**　拼回等于原句／中英不为空／重点词与括注同段／数字两边对上／
否定词两边对上／断在标点或开头词前／中英长度占比相称／没有本可拆而未拆的超长段

**二层 · 画面（7）**　标题页不写「第几篇」／标题不折行／标题字号 ≥0.85 档／
**没有任何文字溢出黄框**／每帧都有文字／正文字号 ≥0.45／段距标准（段间 ≥5×段内）

> 溢出这一条是**按像素查**的：把每一句真渲一帧，安全区外到黑板内沿之间那一圈里
> 不许有任何白或金像素——文字要碰到木框，必先穿过这一圈。

**三层 · 音画（9）**　1920×1080 H.264 ／ AAC ／ 时长＝标题页＋各句解码时长＋停顿＋结尾缓冲 ／
标题有配音 ／ 标题页真的在念 ／ 句间停顿 ≥0.4 秒 ／ 结尾缓冲是静音 ／
每句音频解码质检过 ／ 逐词时间轴毫秒、递增、不越界

### 为什么还要「闸门演习」

检察官报「全过」只说明**这一篇**没问题，不说明闸本身是活的——判据写反、阈值填错、变量拼错，
一样报全过。`gate_drill.py` 把每条标准**故意做坏一次**，看它响不响。**不响的闸不算闸。**
第一次跑就有三条没响（两条是演习自己没做够坏，一条是真漏洞）。

### 版面标准

| | 值 |
|---|---|
| 画幅 | 16:9，1920×1080，25 fps |
| 重点词 | 金 `#f5c542`，英文中文同色 |
| 段内距（英文→它的中文） | 1.0% 画面高 |
| 段间距（一组→下一组） | **6.2%**，≈ 段内的 6 倍 |
| 句间停顿 | 0.55 秒 |
| 结尾缓冲 | 1.5 秒静音 |
| 字号 | 由大往小搜，取放得下的最大档；安全区左右 4.5%、上下 5.5%，**文字不碰木框** |

## 体式

每一篇都写在同一副镣铐里，这是**声明在先的固定体式**，不是巧合：

| | |
|---|---|
| 段落 | 恰好 5 段：布景与触发 · 异常本身 · 当时的解释为何不够 · 判别性证据 · 意义与升华 |
| 重点词 | 恰好 50 个，每段 10 个 |
| 篇幅 | 249—271 词 |
| 跨篇 | 重点词不重复，含同根 |

**篇幅不硬凑。** 在 249—271 之间，论证说完、赘词削净，落在哪个数就是哪个数——
不看它是否整齐，也不为了「不整齐」而多删一个词。

曾把「不许整十」定成规则，随即为脱离整十而逐篇削一个词
（如 The inquest of 1628 → The 1628 inquest，不是因为原句冗余，而是要减掉一个词）。
**那仍是凑数，只不过从「凑到 270」换成了「凑到不是 270」。** 该规则已撤。

真正要防的是**贴着上限停手**，那由减法轮解决：
写完之后逐词问「删掉它，读者会不会觉得少了东西」，削到自己该落的地方为止。

---
## Anki 卡片

全库 3,500 个词元已导出为 Anki 可直接导入的卡片：[`exports/anki-3500.tsv`](exports/anki-3500.tsv)。正面是英文词，背面是中文释义、它所在的那一句（该词加粗）与篇名链接；标签为篇号与段号。导入时选 Tab 分隔、允许 HTML。重新生成：`python3 scripts/export_anki.py`。

## 当前最终定稿

截至2026-08-24，共有 **70篇文章、3500个重点词**。每篇恰好50个重点词，密度均低于20%。

| 编号 | 文章 | 题材 | 指标 | 阅读 |
|---|---|---|---|---|
| **01** | ***Snow and the Broad Street Pump*** | **1854年伦敦霍乱** | **267词 · 50词 · 18.7%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=snow-cholera) · [Markdown](articles/01-snow-cholera.md) |
| **02** | *A Garden Without Sunlight* | 1977年加拉帕戈斯热液喷口 | **271词 · 50词 · 18.5%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=a-garden-without-sunlight) · [Markdown](articles/02-a-garden-without-sunlight.md) |
| **03** | ***The Graph That Changed the Sky*** | **1985年南极臭氧洞** | **267词 · 50词 · 18.7%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=the-graph-that-changed-the-sky) · [Markdown](articles/03-the-graph-that-changed-the-sky.md) |
| **04** | ***Fifteen Degrees an Hour*** | **约翰·哈里森与海上经度** | **270词 · 50词 · 18.5%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=fifteen-degrees-an-hour) · [Markdown](articles/04-fifteen-degrees-an-hour.md) |
| **05** | ***The Price Was Elsewhere*** | **UPC条形码与零售信息基础设施** | **271词 · 50词 · 18.5%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=the-price-was-elsewhere) · [Markdown](articles/05-the-price-was-elsewhere.md) |
| **06** | ***The Reaction That Had to Be Invented Twice*** | **Haber–Bosch合成氨与工业放大**  | **268词 · 50词 · 18.7%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=the-reaction-invented-twice) · [Markdown](articles/06-the-reaction-invented-twice.md) |
| **07** | ***The Meaning He Left Out*** | **1948年香农与信息论** | **266词 · 50词 · 18.8%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=the-meaning-he-left-out) · [Markdown](articles/07-the-meaning-he-left-out.md) |
| **08** | ***A Ruler Without a Zero*** | **1908—1912年莱维特与造父变星周光关系** | **268词 · 50词 · 18.7%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=a-ruler-without-a-zero) · [Markdown](articles/08-a-ruler-without-a-zero.md) |
| **09** | ***Zero Was Not Enough*** | **1967—1980年全球天花根除、监测与环形接种**  | **271词 · 50词 · 18.5%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=zero-was-not-enough) · [Markdown](articles/09-zero-was-not-enough.md) |
| **10** | *A Name Inside an Oval* | 1799—1824年罗塞塔石碑与埃及圣书体破译 | **271词 · 50词 · 18.5%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=a-name-inside-an-oval) · [Markdown](articles/10-a-name-inside-an-oval.md) |
| **11** | ***The Needle Moved Twice*** | **1831年法拉第与电磁感应** | **271词 · 50词 · 18.5%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=the-needle-moved-twice) · [Markdown](articles/11-the-needle-moved-twice.md) |
| **12** | ***The Blank Was Not Blank*** | **1956—1996年克莱尔·帕特森、地球年龄与工业铅污染**  | **268词 · 50词 · 18.7%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=the-blank-was-not-blank) · [Markdown](articles/12-the-blank-was-not-blank.md) |
| **13** | ***The Colour Returned in Patches*** | **1944—1983年麦克林托克、玉米斑驳与转座元件**  | **270词 · 50词 · 18.5%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=the-colour-returned-in-patches) · [Markdown](articles/13-the-colour-returned-in-patches.md) |
| **14** | ***The Ship Built to Be Trapped*** | **1881—1896年“前进号”、跨北冰洋漂流与深海盆地**  | **271词 · 50词 · 18.5%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=the-ship-built-to-be-trapped) · [Markdown](articles/14-the-ship-built-to-be-trapped.md) |
| **15** | ***When a Broken Pipe Applied the Brakes*** | **1869—1893年威斯汀豪斯、自动空气制动与失效安全逻辑**  | **270词 · 50词 · 18.5%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=when-a-broken-pipe-applied-the-brakes) · [Markdown](articles/15-when-a-broken-pipe-applied-the-brakes.md) |
| **16** | *The Wave That Should Not Have Arrived* | 1929—1952年英格·莱曼、P波阴影区与地球内核 | **270词 · 50词 · 18.5%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=the-wave-that-should-not-have-arrived) · [Markdown](articles/16-the-wave-that-should-not-have-arrived.md) |
| 17 | *The Few That Came Back* | 1909—1913年盖革—马斯登散射实验与卢瑟福核式原子 | **270词 · 50词 · 18.5%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=the-few-that-came-back) · [Markdown](articles/17-the-few-that-came-back.md) |
| **18** | *The Sky Would Not Go Quiet* | 1964—1992年彭齐亚斯、威尔逊、普林斯顿团队与宇宙微波背景 | **269词 · 50词 · 18.6%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=the-sky-would-not-go-quiet) · [Markdown](articles/18-the-sky-would-not-go-quiet.md) |
| **19** | ***Five Alarms, Still Descending*** | **1969年阿波罗11号1201/1202程序警报、优先级软件与地面‘继续’判断** | **270词 · 50词 · 18.5%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=five-alarms-still-descending) · [Markdown](articles/19-five-alarms-still-descending.md) |
| **20** | ***The Market Came After the Limit*** | **1990—2010年美国酸雨计划、二氧化硫总量控制与排放权交易** | **268词 · 50词 · 18.7%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=the-market-came-after-the-limit) · [Markdown](articles/20-the-market-came-after-the-limit.md) |
| **21** | ***They Never Held the Same Foot*** | **1628年瓦萨号沉没与测量标准** | **269词 · 50词 · 18.6%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=they-never-held-the-same-foot) · [Markdown](articles/21-they-never-held-the-same-foot.md) |
| **22** | ***Only That Question Had a Number*** | **1912—1953年皮尔当人骗局与氟测年** | **271词 · 50词 · 18.5%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=only-that-question-had-a-number) · [Markdown](articles/22-only-that-question-had-a-number.md) |
| **23** | ***Its First Two Verdicts Were Denials*** | **1984—1987年杰弗里斯、DNA指纹与司法证据** | **268词 · 50词 · 18.7%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=its-first-two-verdicts-were-denials) · [Markdown](articles/23-its-first-two-verdicts-were-denials.md) |
| **24** | ***The Change That Doubled the Load*** | **1981年堪萨斯城凯悦酒店天桥垮塌与一处未经复核的设计变更** | **262词 · 50词 · 19.1%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=the-change-that-doubled-the-load) · [Markdown](articles/24-the-change-that-doubled-the-load.md) |
| **25** | ***The Patient Came Before the Envelope*** | **1947—1948年英国MRC链霉素肺结核试验、随机序列与分配隐藏** | **267词 · 50词 · 18.7%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=the-patient-came-before-the-envelope) · [Markdown](articles/25-the-patient-came-before-the-envelope.md) |
| **26** | ***The Image Arrived Two Days Later*** | **1957—1979年Cormack、Hounsfield与计算机断层成像** | **266词 · 50词 · 18.8%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=the-image-arrived-two-days-later) · [Markdown](articles/26-the-image-arrived-two-days-later.md) |
| **27** | ***The Cable Stretched Every Pulse*** | **1858年第一条跨大西洋电报电缆、Thomson、Whitehouse与长距离信号迟滞** | **271词 · 50词 · 18.5%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=the-cable-stretched-every-pulse) · [Markdown](articles/27-the-cable-stretched-every-pulse.md) |
| **28** | ***The Route Became the Engine*** | **20世纪60年代—1989年多行星引力助推、Grand Tour轨道设计与Voyager 2外行星飞掠** | **271词 · 50词 · 18.5%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=the-route-became-the-engine) · [Markdown](articles/28-the-route-became-the-engine.md) |
| **29** | ***The Ships Climbed on Rainwater*** | **1879—1914年巴拿马运河船闸方案、加通湖与重力供水机制** | **271词 · 50词 · 18.5%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=the-ships-climbed-on-rainwater) · [Markdown](articles/29-the-ships-climbed-on-rainwater.md) |
| **30** | ***The Window Floated on Tin*** | **1952—1959年皮尔金顿浮法玻璃、熔锡浴与液体自整平机制** | **271词 · 50词 · 18.5%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=the-window-floated-on-tin) · [Markdown](articles/30-the-window-floated-on-tin.md) |
| **31** | ***What Bayer Patented Was the Wrapper*** | **1935年百浪多息、磺胺的发现与一项没能守住的专利** | **266词 · 50词 · 18.8%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=what-bayer-patented-was-the-wrapper) · [Markdown](articles/31-what-bayer-patented-was-the-wrapper.md) |
| **32** | ***The Metre Kept Its Mistake*** | **1792—1799年子午线测量、被隐瞒的3.24角秒与米原器的误差** | **271词 · 50词 · 18.5%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=the-metre-kept-its-mistake) · [Markdown](articles/32-the-metre-kept-its-mistake.md) |
| **33** | ***Thirteen Pence for a Thirty-Sixth*** | **1837年罗兰·希尔的邮政改革与「成本不在运送而在记账」这一发现** | **264词 · 50词 · 18.9%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=thirteen-pence-for-a-thirty-sixth) · [Markdown](articles/33-thirteen-pence-for-a-thirty-sixth.md) |
| **34** | ***Seven Times, Whatever the Age*** | **1693年哈雷的布雷斯劳生命表、为何用一座西里西亚小城的数，以及一张没人用的表** | **268词 · 50词 · 18.7%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=seven-times-whatever-the-age) · [Markdown](articles/34-seven-times-whatever-the-age.md) |
| **35** | ***Thirteen Months and Thirteen Years*** | **1859年皇家宪章号风灾、菲茨罗伊的风暴预警制度，以及它被停掉之后的那次天然实验** | **270词 · 50词 · 18.5%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=thirteen-months-and-thirteen-years) · [Markdown](articles/35-thirteen-months-and-thirteen-years.md) |
| **36** | ***Two Plants, Two Patterns*** | **1850年代《柳叶刀》分析卫生委员会与英国食品掺假的查验** | **268词 · 50词 · 18.7%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=two-plants-two-patterns) · [Markdown](articles/36-two-plants-two-patterns.md) |
| **37** | ***The Blotter Recorded Who Paid*** | **1876年贝尔与格雷的电话优先权之争，以及一份从未为此设计的记录** | **271词 · 50词 · 18.5%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=the-blotter-recorded-who-paid) · [Markdown](articles/37-the-blotter-recorded-who-paid.md) |
| **38** | ***He Made It Wear Their Words*** | **法国米制推行中的1812年敕令：还名不还量** | **269词 · 50词 · 18.6%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=he-made-it-wear-their-words) · [Markdown](articles/38-he-made-it-wear-their-words.md) |
| **39** | ***The Footsteps Dictate*** | **美国公共土地测量制度：原始界标为何压过图上的数字** | **268词 · 50词 · 18.7%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=the-footsteps-dictate) · [Markdown](articles/39-the-footsteps-dictate.md) |
| **40** | ***The Book of Winchester Left Out Winchester*** | **末日审判书：一份记录的权威来自终局性而非完备性** | **270词 · 50词 · 18.5%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=the-book-of-winchester-left-out-winchester) · [Markdown](articles/40-the-book-of-winchester-left-out-winchester.md) |
| **41** | ***The Planet Ran a Surplus With Itself*** | **全球经常账户统计差额：一个必须为零却从不为零的数** | **270词 · 50词 · 18.5%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=the-planet-ran-a-surplus-with-itself) · [Markdown](articles/41-the-planet-ran-a-surplus-with-itself.md) |
| **42** | ***It Lasted at the Marketplace*** | **希伯来语复兴：一个人的决心、一门市集语言与六十所学校** | **271词 · 50词 · 18.5%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=it-lasted-at-the-marketplace) · [Markdown](articles/42-it-lasted-at-the-marketplace.md) |
| **43** | ***The Obstacle Was What Went In*** | **杂交玉米：一项无人反驳的发现，为何等了二十五年才落地** | **269词 · 50词 · 18.6%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=the-obstacle-was-what-went-in) · [Markdown](articles/43-the-obstacle-was-what-went-in.md) |
| **44** | ***The Day the Remedy Was Blunted*** | **坏血病与柑橘配给：一味没有机理的解药，能被照抄却守不住** | **270词 · 50词 · 18.5%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=the-day-the-remedy-was-blunted) · [Markdown](articles/44-the-day-the-remedy-was-blunted.md) |
| **45** | ***Defined Against the Structure*** | **1903年易洛魁剧院火灾：一个标准被定义在可查验之物上，而非致命之物** | **268词 · 50词 · 18.7%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=defined-against-the-structure) · [Markdown](articles/45-defined-against-the-structure.md) |
| **46** | ***Three Who Err Alike*** | **手动计时的系统性偏差：中位数管得住离群值，管不住三人同向的错** | **270词 · 50词 · 18.5%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=three-who-err-alike) · [Markdown](articles/46-three-who-err-alike.md) |
| **47** | ***It Becomes the Subject*** | **剑桥数学Tripos排名制：一份排序如何取代它本要衡量的那门学科** | **270词 · 50词 · 18.5%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=it-becomes-the-subject) · [Markdown](articles/47-it-becomes-the-subject.md) |
| **48** | ***The Maxim Made Visible*** | **1829年伦敦警察的制服：一支队伍的每一处设计都在回答政治恐惧** | **270词 · 50词 · 18.5%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=the-maxim-made-visible) · [Markdown](articles/48-the-maxim-made-visible.md) |
| **49** | ***Two Percentages Side by Side*** | **1721年波士顿人痘接种之争：在没有机理可援引时，计数如何独自赢下一场辩论** | **268词 · 50词 · 18.7%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=two-percentages-side-by-side) · [Markdown](articles/49-two-percentages-side-by-side.md) |
| **50** | ***The Unattainable Ideal*** | **赛马让分制：一个若真达成便会摧毁自身目的的目标** | **267词 · 50词 · 18.7%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=the-unattainable-ideal) · [Markdown](articles/50-the-unattainable-ideal.md) |
| **51** | ***Named for a Plant That Does Not Smell*** | **1882年 Fougère Royale：合成香料抬掉的不是成本，是「香味须来自植物」这道限制** | **264词 · 50词 · 18.9%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=named-for-a-plant-that-does-not-smell) · [Markdown](articles/51-named-for-a-plant-that-does-not-smell.md) |
| **52** | ***A Third Ingredient Added to Both*** | **骨瓷：一个在障碍消失之后仍然留下来的「权宜之计」** | **267词 · 50词 · 18.7%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=a-third-ingredient-added-to-both) · [Markdown](articles/52-a-third-ingredient-added-to-both.md) |
| **53** | ***Wild Was Not a Description*** | **英国猎场法：一部保护「野生」的法律，保护的是一种离开看守就活不下去的养殖鸟** | **270词 · 50词 · 18.5%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=wild-was-not-a-description) · [Markdown](articles/53-wild-was-not-a-description.md) |
| **54** | ***Steadiness and Command Are Contrary*** | **莱特兄弟的三轴操纵：稳定与操纵不是可以折中的两样好处，而是相反的两件事** | **270词 · 50词 · 18.5%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=steadiness-and-command-are-contrary) · [Markdown](articles/54-steadiness-and-command-are-contrary.md) |
| **55** | ***Upkeep Without End*** | **荷兰围垦：治理消耗了被治理之物，于是维护再无尽头** | **269词 · 50词 · 18.6%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=upkeep-without-end) · [Markdown](articles/55-upkeep-without-end.md) |
| **56** | ***The Shape of the Metalwork*** | **英国换鸣：看着像民族性情的东西，往往只是器械的形状** | **270词 · 50词 · 18.5%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=the-shape-of-the-metalwork) · [Markdown](articles/56-the-shape-of-the-metalwork.md) |
| **57** | ***An Experiment That Builds Its Own Opponent*** | **马项圈之谜：自己动手复原对手的实验，事先就定下了对手能有多好** | **266词 · 50词 · 18.8%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=it-built-its-own-opponent) · [Markdown](articles/57-it-built-its-own-opponent.md) |
| **58** | ***Willingness Was the Evidence*** | **中世纪神判：筛选发生在试炼之前——在人们决定要不要上的那一刻** | **271词 · 50词 · 18.5%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=each-works-by-never-being-used) · [Markdown](articles/58-each-works-by-never-being-used.md) |
| **59** | ***A Story That Gives a Luxury Some Use*** | **香料与腐肉：一个给奢侈品安上实用理由的故事，总能胜过真相** | **268词 · 50词 · 18.7%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=a-story-that-gives-a-luxury-some-use) · [Markdown](articles/59-a-story-that-gives-a-luxury-some-use.md) |
| **60** | ***It Keeps What a Child Can Hold*** | **苹果籽约翰：传说只留下孩子拿得住的那部分，丢掉一个申领人所需要的** | **270词 · 50词 · 18.5%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=keeps-what-a-child-can-hold) · [Markdown](articles/60-keeps-what-a-child-can-hold.md) |
| **61** | ***The Men Who Felt It Were Filed as Anecdote*** | **纽芬兰鳕鱼崩溃：测量存量的仪器感觉不到鱼在变少，感觉得到的人不被当作仪器** | **270词 · 50词 · 18.5%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=filed-as-anecdote) · [Markdown](articles/61-filed-as-anecdote.md) |
| **62** | ***A Mill's Terms of Sale*** | **维多利亚服丧礼俗：看起来是虔敬的规矩，其实是一家丝厂的销售条款** | **271词 · 50词 · 18.5%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=a-mills-terms-of-sale) · [Markdown](articles/62-a-mills-terms-of-sale.md) |
| **63** | ***The Bear That Lived Was the One on Paper*** | **泰迪熊：玩具纪念的是漫画家画出来的那个下午，不是真发生的那个** | **271词 · 50词 · 18.5%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=the-bear-that-lived-was-on-paper) · [Markdown](articles/63-the-bear-that-lived-was-on-paper.md) |
| **64** | ***The Secret Was the Box*** | **钱伯伦产钳：守了一百五十年的不是器械，是让两片铁看起来像一台机器的那场戏** | **271词 · 50词 · 18.5%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=the-secret-was-the-box) · [Markdown](articles/64-the-secret-was-the-box.md) |
| **65** | ***The Rank Was in the Dye*** | **红衣军：红色不是为伤口或敌人选的，是军需官按染料价格选的，染工按军衔分的等** | **267词 · 50词 · 18.7%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=the-rank-was-in-the-dye) · [Markdown](articles/65-the-rank-was-in-the-dye.md) |
| **66** | ***A Roof That Was Not There*** | **伦敦大火与茅草：一条管用了四百五十年的规矩，从它本来要防的那场火的故事里消失了** | **271词 · 50词 · 18.5%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=a-roof-that-was-not-there) · [Markdown](articles/66-a-roof-that-was-not-there.md) |
| **67** | ***The Tool With Its Lesson Cut Out*** | **拼图：头一百五十年是教室里的地理教具，刀离开国界之后才成了玩具** | **270词 · 50词 · 18.5%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=the-tool-with-its-lesson-cut-out) · [Markdown](articles/67-the-tool-with-its-lesson-cut-out.md) |
| **68** | ***Grandeur That Looks Like Defence*** | **护城河：英格兰六千道护城河几乎没有一道属于城堡，它们是乡绅用土方说出的身份** | **271词 · 50词 · 18.5%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=grandeur-that-looks-like-defence) · [Markdown](articles/68-grandeur-that-looks-like-defence.md) |
| **69** | ***Cheaper, Better, and Eleven*** | **稻草人：它顶替的不是农具，是一个十一岁的赶鸟童** | **271词 · 50词 · 18.5%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=cheaper-better-and-eleven) · [Markdown](articles/69-cheaper-better-and-eleven.md) |
| **70** | ***The Fire's Waste, Collected*** | **灯塔：变亮不靠火，靠把散掉的光收回来的那座玻璃蜂巢** | **271词 · 50词 · 18.5%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=the-fires-waste-collected) · [Markdown](articles/70-the-fires-waste-collected.md) |
| **46** | ***Three Who Err Alike*** | **手动计时的系统性偏差：中位数管得住离群值，管不住三人同向的错** | **270词 · 50词 · 18.5%** | [网页](https://alienrocketbus.github.io/postgraduate-vocabulary/article.html?a=three-who-err-alike) · [Markdown](articles/46-three-who-err-alike.md) |

第30篇以271词第13轮独立盲审最终精进锁定稿为准。正文从垂直牵引薄片的光学畸变和磨光板玻璃的高成本出发，说明浮法如何把“固体设备先留下损伤、后续设备再修复”改写成“熔融玻璃先在锡液上自整平、玻璃带变硬后才接触轧辊”。本轮把锡的低反应性明确限定为相对于玻璃，把约6.8毫米写成进一步变薄受限的平衡点，并把浮渣改为可能留下瑕疵；史实边界继续保留早期专利、Kenneth Bickerstaff的共同发明人身份和七年开发期。1100°C入锡浴、氮氢保护气氛、约600°C离浴与退火机制均有原始专利、Royal Society资料或Pilkington官方技术说明支持。

第29篇以270词第14轮最终精进锁定稿为准。正文没有把巴拿马运河写成一条单纯“挖穿”的水沟，而是依次说明海平面方案为何失败、加通湖怎样把26米高差变成资源、重力如何经直径18英尺的涵洞和100个底孔抬船、水位齐平后为何才可开闸，以及传统通航约消耗5200万加仑淡水的水文代价。功劳边界分别保留Godin de Lépinay、John Stevens与Hodges、Schildhauer、Goldmark的有据贡献，不把发明或设计强归于一人。

第28篇以270词最终精进锁定稿为准。第13轮独立盲审把推进剂与飞行时间拆成并列约束，将行星参考系的速度矢量偏转与日心参考系的动能变化写成更严格的机制链，并把“限制变成资产”收紧为“限制仍在，路线补充火箭推进”。功劳边界仍不把“发明引力助推”强归于一人，而只界定Michael Minovitch的多行星弹道计算与Gary Flandro对外行星机会窗口的工作。

第20篇以267词最终精进锁定稿为准。终审彻底区分了 `allowance` 与一般意义上的 `permit`，把额度缺口明确写成自动处罚并用未来额度弥补，将铁路承运商竞争限定为运输成本来源，并以 `statutory / marginal / reallocate` 三个更准确的词收紧制度结论：法律先设法定总量，交易只重新配置许可并暴露相对边际成本。

第19篇以267词最终精进锁定稿为准。最终上限审查进一步修复了警报显示语序与五次警报计数，明确雷达开关配置和交流相位失配共同产生虚假计数请求，并把执行程序写成按优先级调度、在无空闲工作区时重启并从记录检查点恢复。遥测判断和警报边界也被收紧：警报提供可供行动的信息，却不会自动命令中止。结尾以“系统可以过载而不崩溃”重新定义稳健性。

第18篇以270词最终精进锁定稿为准。新版把3.5 K明确写成额外天线温度，用 accounted for 代替过度绝对的 ruled out，消除第三段代词归属歧义，修正 corroborate 的搭配，并以“the sky would not go quiet”直接回扣标题。最终微调还把 `every seam` 收紧为 `the seams`，把 `black-body profile` 完整为 `black-body spectral profile`，并以 `every plausible local culprit` 避免过度绝对化。最终语言收口又把生硬的 `made a roost` 改为 `roosted`，恢复 `Nearby` 的空间衔接，并用 `that interpretation` 消除代词歧义；中文同步删去英文已不存在的“炽热”。文章仍严格区分1965年单波段结果、普林斯顿解释与COBE后续证据。

---

## 最终版本铁律

- 一旦某篇文章形成新的最终稿、最终精校稿或最终锁定稿，必须在同一次变更中同步权威数据、Markdown、网站、README、交接文档、入库记录和最终版本清单。
- 新最终稿一经进入主分支，旧稿立即失去权威性；旧内容只能留在Git历史中，不得继续留在活动数据文件、正式Markdown、网站入口或未合并分支中制造歧义。
- 只有从 `main` 回读确认新正文，并且全量校验成功后，才可以声称“已经存到云端”。
- `data/final-version-manifest.json` 保存每篇文章的完整内容指纹；`node scripts/final-version-guard.js` 会阻止旧稿、错误指标或未同步文件重新进入主分支。

完整规则见 [notes/最终版本铁律.md](notes/最终版本铁律.md)。

---

## 网站已完成的同步

网站当前实际加载第01—30篇，并自动计算30篇、1500个重点词和平均篇幅。

### 首页

- 自动统计文章数、重点词数与平均篇幅
- 第30篇作为最新定稿专题展示
- 三十篇文章卡片全部由数据层自动生成
- 深浅主题、响应式排版和无障碍焦点状态

### 文章阅读器

- 双语、仅英文、仅中文三种视图
- 英文重点词与中文自然译法悬停／点击连线
- 词源显示开关
- 挖空自测、逐词揭晓与一键重置
- 三档字号、阅读进度、段落导航和打印版式
- 50词速查表点击回到正文
- 史实核对与来源分层展示
- 上一篇／下一篇导航

### 1500词词库

- 中英文实时搜索
- 按文章筛选
- A—Z首字母筛选
- 每个词都能回跳到原文段落

---

## 数据层与生成方式

当前权威数据层按以下顺序加载：

```text
data/articles.js      # 第01—07篇
data/article-08.js—data/article-30.js    # 第08—30篇
```

它们共同构成 `window.SITE.ARTICLES`。网站三个页面与Markdown生成脚本都加载同一数据层，因此不会出现“网页一版、Markdown另一版”。

生成与校验：

```bash
python3 scripts/build_markdown.py
```

脚本会：

- 生成／刷新 `articles/*.md`
- 校验英文加粗、中文对应括注和速查表数量
- 校验词数、密度和20%红线
- 检查文章编号、slug及跨篇精确重复

仓库还包含 `.github/workflows/validate-content.yml`，会在PR和主分支提交时执行同一套30篇全量校验，并检查数据脚本、最终版本身份与网站入口。

---

## 目录

```text
├── index.html                 首页
├── article.html               双语阅读器
├── words.html                 1500词索引
├── 404.html
├── manifest.webmanifest
├── robots.txt
├── sitemap.xml
├── assets/
│   ├── site.css
│   ├── site.js
│   ├── favicon.svg
│   └── share-card.svg
├── data/
│   ├── articles.js            第01—07篇
│   └── article-08.js—article-30.js
├── articles/
│   └── 01—30 Markdown定稿
├── scripts/
│   └── build_markdown.py
├── tools/
│   ├── 单词检察官v3.html
│   └── 单词检察官v2.html
├── vocabulary/
└── notes/
    ├── 对话交接文档.md
    ├── 写作规范.md
    ├── 缺陷库.md
    ├── 最终定稿校正记录_2026-08-10.md
    ├── 第八篇入库与网站重构记录_2026-08-10.md
    ├── 第九至第十一篇入库记录_2026-08-11.md
    ├── 第十二至第十五篇入库记录_2026-08-11.md
    ├── 第十六篇入库记录_2026-08-12.md
    ├── 第十七篇入库记录_2026-08-12.md
    ├── 第十八篇入库记录_2026-08-13.md
    ├── 第十九篇入库记录_2026-08-13.md
    ├── 第二十八篇入库记录_2026-08-24.md
    ├── 第二十九篇入库记录_2026-08-24.md
    └── 第三十篇入库记录_2026-08-24.md
```

---

## 硬性标准

| 项目 | 要求 |
|---|---|
| 英文词数 | **249—271词；不贴上限凑数，也不为制造不整齐而机械删词** |
| 重点词 | 恰好50个 |
| 密度 | ≤20% |
| 文体 | 《经济学人》风格科普社论 |
| 内容 | 人物、日期、数字或具体案例 |
| 中文 | 先自然表达，再建立加粗对应 |
| 结尾 | 提供新的理解框架，不只复述正文 |
| 事实 | 关键数据与叙事边界可追溯 |

铁律：

> 英文加粗的重点词，在中文译文中必须有对应的自然译法；中文译法同样加粗，并在后面附英文原样括注。
