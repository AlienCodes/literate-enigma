# 46／49／55机器复听只读诊断

本轮三处报告没有对应新增成片音频变化：已重新取得原失败artifact中的公开1080p MP4和GitHub既有获批4K MP4，六份整文件SHA分别匹配原记录；三对AAC ADTS、包载荷／绝对PTS-DTS／包时长／音频codec参数均完全相等。用同一ffmpeg解码的48kHz单声道float32整轨也逐字节相等，最大样本差均为0。因此这三处不能归因于本轮新增增益、剪切或换声。

| 原篇／句 | 脚本与实际机器差异 | 现有确认 | 判断边界 |
|---|---|---|---|
| 46 S6 | 句末light被parakeet写成lights | 只有S2、S8，没有S6 | 单路复数识别差异；/t/与/ts/并非同音，不能只凭拼写近似确认读音正确。 |
| 49 S8 | omission被parakeet写成old mission | 没有逐句机器复听旧确认 | 分词／词汇识别误差候选，但old mission比omission多出辅音成分，并非严格同音。 |
| 55 S11 | The clasts, it suggested…被parakeet多写as | 机器复听旧确认只有S7；S11仅有停顿位置旧证据 | 现有0.736125秒插入边界和2026-11-05历史记录确实涉及同一种as插入现象，但这不是本轮新实音证明，不能改写成已核实ASR豁免。 |

三篇当前PAY的目标英文、所查音频控制字段及机器复听确认，与失败artifact工作JSON一致。既有机器确认涉及其他句子，不能以“全轨指纹续期”顺带豁免这三个新失败句。

机器复听原工具已从本run真实head `1ec776c9c214ef668cab4c27b43780bc12c38c19`取回，SHA-256为`40caf651184d50efeb8d3b4477cd7a2b85911a495360554db1b3cd09ab596229`。它将每句从原工作a.wav裁出后重采样到16k，small.en与parakeet分别转写，按同一注音程序归一比较；任一路有未豁免差异就失败。现日志仅打印差异，没有保存这三句两路完整转写。small.en未在目标处报差异，不能进一步虚构它的完整原始识别文本。

实际公开整句素材已经导出，无须为取得这三句成片局部再开workflow：

- 46 S6：48.2968125–53.6320833秒，`public-media/46/46-S6-actual-failed-public-sentence.wav`。
- 49 S8：72.8510625–79.3738958秒，`public-media/49/49-S8-actual-failed-public-sentence.wav`。
- 55 S11：84.0945833–92.2384792秒，`public-media/55/55-S11-actual-failed-public-sentence.wav`。

句界沿用公开信号的原音频体检静音分句方法，三篇均得到标题加17句共18段；片段是公开MP4的样本裁切，没有取出私人GT、缓存、模型或原工作PCM。完整标量及文件SHA在`actual-public-audio-comparison.json`和各篇`public-media-retrieval.json`、`audio-comparison.json`。

这份比较证明成片与既有获批声轨相同，不能单独证明既有发音绝对正确，也不能证明ASR实际使用的未编码a.wav与旧工作PCM逐样本一致。没有进行人工复听，没有写确认，没有改任何源稿、音控、核查器或阈值。

若仍需区分ASR输入／后端变动，可在下一次既有同轮native job的失败诊断分支额外记录这些最小字段，无须另建串行workflow：实际run、源／工具／模型／运行库哈希；目标句官方分段起止秒及原工作a.wav裁切后16k ASR输入的字节哈希、样本数、RMS；使用未改原识别函数得到的small.en和parakeet完整转写及差异；对同一公开MP4样本范围重采样所得输入的相同标量和两路转写。只导标量、公开文字和公开MP4派生片段，不导出私人原PCM／GT／cache／model。该诊断只说明证据，不改变原门结果。
