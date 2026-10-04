# 只用 IndexTTS 2.5（v18.7）

## 老师的决定（10-04 晚，北京时间 10-05 早上）

老师用 v18.6 生成了音频：「还是没有我自己说的那种味儿，听着有点机械感」，问 IndexTTS 会不会更好。
我如实说了没在她的声音上试过、零样本一般说话自然但音色没有训练的像。老师随后决定：
「IndexTTS25……就单独只用这个大模型，那另外两个不用了……你帮我做出来，我要用这个大模型来生成我的声音。」

→ v18.7：程序只用 IndexTTS 2.5（不训练）；v2ProPlus、V4（GPT-SoVITS）和 Qwen3-TTS 不再提供。
按永久规定 14 的精神（冗杂的以后去掉、没必要动的不动）：界面、安装、文档里去掉；GPT-SoVITS 的代码这一版先不删。

## IndexTTS 2.5 是什么（调查结果，来源见下）

调查方法：开发机上直接打不开 huggingface / modelscope / arxiv / bilibili，代码事实来自官方仓库的克隆（commit d9e41aa，2026-09-30），
GitHub issue 直接读；标「（搜索摘要）」的是搜索引擎摘要，没打开原页面，可信度低一些。B = https://github.com/index-tts/index-tts/blob/d9e41aac89fd00b3d71497fddb287b7f24613712

- 官方发布：README「2026/08/10 We release IndexTTS-2.5」，GitHub release v2.5.0（2026-08-13）。0.8B 参数。
  官方渠道只有 GitHub 仓库；模型 `IndexTeam/IndexTTS-2.5`（Hugging Face 和 ModelScope 都有）。
- 和 IndexTTS2 比：语义编码 25 Hz、S2M 换成 Zipformer、五种语言、GRPO 强化学习、`duration_factor` 语速控制（0.5~2.0）、
  拼音 / 英文音标标注更好、需要 `lang` 参数、用 bf16。论文说 RTF 提升 2.28 倍、WER 和相似度和 IndexTTS2 差不多；
  README 里 4090 实测 RTF：2.0 fp16 0.3257，2.5 bf16 0.2065。
- 模型文件：gpt.pth 3.26 GB、codec.pth 607 MB、s2mel.pth 415 MB 等，一共约 5.49 GB（搜索摘要）；第一次运行还会下载
  w2v-bert-2.0（约 2.32 GB）、campplus、BigVGAN、MaskGCT 语义编码（177 MB）。**合计估计约 8.5 GB**（估算，不是官方数字）。
- 安装：Python 3.11（>=3.10,<3.12），官方说必须用 uv（`uv sync`），torch 2.8 + cu128（RTX 50 / Blackwell 需要 CUDA 12.8，
  torch 2.7 以后支持）。Windows：CI 只跑 CPU 测试，README 有 Windows 说明，没有明确写「Windows 显卡完全支持」。
- 显存（官方在 4090 上测的峰值）：bf16 不开情绪模型 5.48 GB，bf16 + 情绪模型 6.54 GB，fp32 + 情绪模型 8.15 GB。
  显卡小于 10 GB 时官方网页自动用半精度、不加载情绪模型，文字超过 40 个字自动切开。**8 GB 的 RTX 50 没有人实测过**。
- 没有官方的 Windows 整合包（README：其他网站都不是官方的）；网上有个人做的整合包，都没法核实。→ 安装程序从官方仓库 + ModelScope 自己装。
- 参考录音：不需要文字；只用前 15 秒；没有官方的长度建议。中英混合用 `lang="ZH"`。
- 许可：bilibili 模型使用协议（月活过 1 亿 / 年收入过 10 亿要另外授权；禁止未经授权克隆别人的声音）。老师克隆自己的声音符合条款（不是法律意见）。
- 质量：**没有找到 IndexTTS2 / 2.5 和微调过的 GPT-SoVITS 的公开对比**；论文数字用的声纹模型不同，不能直接比。
  有用户反映 2.5 比 2.0 有退步（issue #781），一位听众盲听 6 组里 5 组觉得 2.0 更好（#801），语速在长句后面变慢（#800）。

## 开发机的限制

- 没有显卡；ModelScope、Hugging Face、download.pytorch.org 都连不上（10-04 22:10 实测，curl 返回 000）。
  → **没法在开发机上真跑 IndexTTS**，只能按官方代码的真实接口写测试替身；第一次真跑在老师电脑上。
- 老师可以在环境设置里放开 modelscope.cn（Custom → Allowed domains），放开以后可以用 CPU 真跑一两句验证接法。

## 现在的代码（调查结论，详细的 file:line 见本目录 代码地图.md）

- 已经能用 IndexTTS 生成（不需要训练、不需要训练好的模型），「一模一样」也能跑，但：网页一直叫你去训练、
  安装程序完全不装 IndexTTS、「下载缺少的模型」没有整合包就报错、网页里从来不给 IndexTTS 校准语速。
- 接口问题：2.5 没传 `use_cuda_kernel=False`（启动时会去编译，Windows 上要 nvcc/MSVC）；`emo_alpha` 用同一段录音时没作用；
  句子里有中文但识别成英文时会传 EN（应该有汉字就传 ZH）；采样参数是给 GPT-SoVITS 调的（temperature 1.0、top_k 15/5），
  会盖掉 IndexTTS 自己的默认（0.8 / 0.8 / 30）；8 GB 显卡上超过 40 个字会被自动切开、中间插 200 ms 静音（我们控制不了）；
  `duration_factor` 没限制在 0.5~2.0；check() 只看 config.yaml；没设 ModelScope 下载；worker 不检查输出文件是不是真的写出来了。

## 计划

1. 安装：不要整合包。安装程序自己装 IndexTTS 2.5（官方代码、uv、torch cu128、官方模型从 ModelScope 下载），VoiceTwin 也装进去。
2. 网页：只剩 ① 准备素材 → ③ 生成；去掉 ② 训练、确认训练素材、引擎选择；顶上显示 IndexTTS25。校对表留着但不是必须的。
3. 生成：「一模一样」改成适合 IndexTTS（一次生成一个版本）：每句换几段老师的录音当参考各生成几遍，按声纹挑最像的、检查读错；
   参数用 IndexTTS 自己的默认；每次请求不超过 40 个字（不让它自己插静音）；句子之间仍是精确的数字静音。
4. 修好上面的接口问题，每一处都有测试（用按官方接口写的测试替身）。
5. 一页纸《快速上手》、发布说明、教学手册、时间线、开发记录。
