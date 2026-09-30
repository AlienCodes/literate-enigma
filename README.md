# 🎙️ VoiceTwin 声音分身

**用你自己的讲课视频和录音，复刻你的音色、语气和说话节奏。支持中文、英文，也支持中英混说。**

嗓子哑了录不了课的时候，把讲稿交给它，就能用"你的声音"读出来，并同时生成字幕。

> **👉 Windows 用户从这里开始：**
> 1. 下载程序：[**Releases 页面 → VoiceTwin-Windows-v….zip**](https://github.com/AlienCodes/literate-enigma/releases/latest)
> 2. 照着做：[**Windows 详细使用教程（一步一步，从下载到生成音频）**](docs/Windows详细使用教程.md)

> 你已经录好的课程视频/音频就是训练素材。程序会自动从里面提取你的声音、识别文字、训练一个专属模型，
> 然后按你本人的语速、停顿和语气来朗读新讲稿。

---

## 目录

- [它是怎么做到"像你"的](#它是怎么做到像你的)
- [需要什么电脑](#需要什么电脑)
- [安装（Windows，推荐路线）](#安装windows推荐路线)
- [三步用起来](#三步用起来)
- [素材怎么准备效果最好](#素材怎么准备效果最好)
- [讲稿怎么写](#讲稿怎么写)
- [让它更像你的技巧](#让它更像你的技巧)
- [命令行用法](#命令行用法)
- [可选引擎：Qwen3-TTS、IndexTTS](#可选引擎qwen3-ttsindextts)
- [常见问题](#常见问题)
- [使用须知](#使用须知)
- [项目结构（开发者）](#项目结构开发者)

---

## 它是怎么做到"像你"的

"像不像"主要取决于三件事：**音色**（声音本身）、**语气**（抑扬顿挫、疑问/感叹的语调）、**节奏**（语速和停顿）。
VoiceTwin 把目前最好的开源技术组合起来，逐项处理：

| 环节 | 做了什么 | 对应"像"的哪一部分 |
|---|---|---|
| 素材清理 | 从视频提取音轨；去低频嗡嗡声；只在底噪明显时轻度降噪（降噪过猛会伤音色）；可选去背景音乐 | 音色干净不失真 |
| 智能切片 | 在你自然停顿的地方切成 3~10 秒的句子；有字幕就按字幕切 | 训练数据完整、准确 |
| 语音识别 | faster-whisper large-v3 / 阿里 FunASR，中英文逐段自动判断，输出简体+标点 | 文字和声音严格对齐 |
| 质量过滤 | 剔除识别置信度低、语速异常（文字对不上）、爆音、**不是你本人**（声纹比对）的片段 | 模型只学你的声音 |
| 风格档案 | 统计你的语速（中/英分开）、逗号/句号/段落的停顿时长、音高和起伏、原始录音响度 | 节奏、语气 |
| 微调训练 | GPT-SoVITS v2ProPlus 用你全部素材微调（官方说明：v2Pro 系列更贴近**整个训练集的风格**，而不只是模仿参考音频） | 音色 + 语气 + 口音 |
| 自动挑模型 | 训练会保存多个版本；用**没参与训练**的你的真实录音做考试：让每个模型读同样的句子，比声纹相似度、错字率、时长比，选总分最高的 | 选出最像的 |
| 语速校准 | 同一句话，模型读的时长 ÷ 你本人读的时长 → 自动算出语速系数 | 快慢和你一致 |
| 多候选择优 | 每句话生成 3~5 个版本，按"声纹相似度 + 语速/音高偏差 +（可选）识别错字率"打分，只保留最好的；漏字/读错会自动重试 | 每一句都尽量最像 |
| 语气匹配 | 疑问句用你的疑问语气参考音频，感叹句用感叹参考，陈述句用陈述参考 | 语气 |
| 自然拼接 | 句间、段间停顿按你本人的习惯（带自然波动），最终响度对齐你原来的录音 | 节奏、可无缝剪进旧课程 |

> **实话实说**：目前没有任何技术能做到 100% 分辨不出。用 1~3 小时干净素材训练后，大多数听众很难分辨；
> 素材越多、越干净、文字越准，效果越好。程序每次都会输出一份报告，告诉你每句话的声纹相似度，
> 不满意的句子可以单独重新生成。

---

## 需要什么电脑

| | 最低 | 推荐 |
|---|---|---|
| 系统 | Windows 10/11、Linux、macOS | Windows 10/11 或 Linux |
| 显卡 | NVIDIA 6GB 显存（训练 GPT-SoVITS） | NVIDIA 8GB+（RTX 3060 及以上） |
| 内存 | 16GB | 32GB |
| 硬盘 | 20GB 可用空间 | 50GB（SSD） |

- 没有 NVIDIA 显卡也能运行，但训练会非常慢（CPU 可能要几天），建议用有显卡的电脑，或者租一台云 GPU。
- 训练时间参考：1 小时素材，RTX 3060 大约 40~90 分钟；RTX 4090 大约 15~30 分钟。

---

## 安装（Windows，推荐路线）

推荐把 VoiceTwin 装进 **GPT-SoVITS 官方整合包**里：整合包已经带好了 PyTorch、显卡加速和语音识别，省去最麻烦的环境配置。

### 第 1 步：下载 GPT-SoVITS 整合包

- 国内：打开 [GPT-SoVITS 官方文档的整合包下载页](https://www.yuque.com/baicaigongchang1145haoyuangong/ib3g1e/dkxgpiy9zb96hob4#KTvnO)，下载**最新版**（文件名里带 `v2pro` 或更新日期的）。
- 海外：[Hugging Face 整合包仓库](https://huggingface.co/lj1995/GPT-SoVITS-windows-package/tree/main)。
- 用 7-Zip 解压到**不含中文和空格**的路径，例如 `D:\GPT-SoVITS`。解压后里面应该有 `go-webui.bat` 和 `runtime` 文件夹。

### 第 2 步：下载 VoiceTwin

打开 [Releases 页面](https://github.com/AlienCodes/literate-enigma/releases/latest)，在 Assets 里下载 `VoiceTwin-Windows-v….zip`，
右键"全部解压缩"到 `D:\`，得到 `D:\VoiceTwin`。（也可以点本页面绿色的 **Code → Download ZIP**，或者 `git clone`。）

### 第 3 步：运行安装脚本

双击 `install_windows.bat`，选择 **1**，粘贴第 1 步的整合包路径（如 `D:\GPT-SoVITS`），等它装完。
安装脚本会：把 VoiceTwin 装进整合包环境（不改动整合包原有依赖的版本）→ 生成 `config.yaml` → 生成启动脚本和桌面图标「声音分身 VoiceTwin」→ 自动检查环境。

> 每一步的截图级说明见 [Windows 详细使用教程](docs/Windows详细使用教程.md)。

### 第 4 步：补齐预训练模型（如有提示）

如果环境检查提示"缺少预训练模型：…v2Pro…"（旧整合包没有 v2Pro 模型），在 VoiceTwin 目录打开命令行运行：

```bat
voicetwin.bat download-models --source hf-mirror
```

> 也可以在 `config.yaml` 里把 `backends.gptsovits.version` 改成 `v2`，直接用整合包自带的 v2 模型（效果略逊）。

### Linux / macOS

```bash
# 先按 GPT-SoVITS 官方说明装好它的 conda 环境并激活，然后：
bash install.sh --gsv /path/to/GPT-SoVITS --mirror
# 或者独立安装（再在 config.yaml 里指定 GPT-SoVITS 的 root 和 python）：
bash install.sh --mirror
```

---

## 三步用起来

双击桌面上的 **「声音分身 VoiceTwin」**（或 `start_webui.bat`），浏览器会打开 `http://127.0.0.1:7860`：

### ① 准备素材

1. 在最上面填一个声音名称，例如"我的声音"。
2. 上传讲课视频/录音（可以一次选很多个），或者直接填视频所在的文件夹路径。
   如果视频有同名字幕（`第1课.mp4` + `第1课.srt`），一起放进去，会直接用字幕文字，更准确。
3. 点"开始准备素材"。结束后会显示：保留了多少分钟、你的语速、你的停顿习惯、自动挑选的参考音频。
4. （强烈建议）点"载入片段列表"，快速扫一遍识别出来的文字，改掉错字，不是你说的片段标成 ✘，点"保存修改"。点击任意一行可以试听。

### ② 训练模型

选 GPT-SoVITS，其它保持默认（全部自动），点"开始训练"。训练完会自动用验证集挑选最像你的模型并校准语速。

### ③ 生成讲课音频

粘贴讲稿（或上传 txt/md/srt/docx），质量选 `balanced`（重要的课可以选 `best`），点"生成"。
得到：**音频（wav/mp3）+ 字幕（srt）+ 报告（每句的相似度和提示）**。
某几句不满意，在"只重新生成第几句"里填编号（如 `3,5,8-10`）再点生成，其它句子直接用缓存，几秒钟就好。

> 懒人模式：命令行一条命令全自动完成 ①②③：
> ```bat
> voicetwin.bat auto -v 我的声音 -i D:\讲课视频
> ```

---

## 素材怎么准备效果最好

- **时长**：至少 10 分钟能用；**30 分钟以上明显更好；1~3 小时最佳**。超过 3 小时收益变小。
- **只要你本人**：学生提问、插播的视频片段、背景音乐多的段落，程序会用声纹自动剔除大部分，但素材越纯越好。
- **尽量用原始录音**：如果当初录课有单独的麦克风音轨（未压缩的 wav），比从压缩过的视频里提取效果更好。
- **中英文都要像**：如果以后要录英文课，请放入你讲英文的录音（至少 5~10 分钟），否则英文会带"中文腔"。
- **风格一致**：用和你想要的效果一致的素材（正常讲课状态）。嗓子哑之后的录音不要放进去。
- **有字幕最好**：字幕文字比语音识别准，训练效果更好。
- 以后有新视频，重新运行素材准备即可，**只会处理新增的文件**，之前的校对不会丢。

---

## 讲稿怎么写

支持 `.txt` `.md` `.srt` `.docx`，或者直接粘贴文字。

```markdown
# 第三课：列表推导式            ← 标题会被读出来，后面自动停顿

大家好，今天我们来学习 Python 里面的列表推导式。它可以让代码更简洁。

那么大家想一想，这段代码输出什么？[停顿=2]   ← 指定停顿 2 秒（也可写 [停顿]、[pause=1.5s]）

Next, let's look at a slightly more complex example.   ← 英文句子自动用英文参考音频

```python
squares = [x**2 for x in range(10)]   ← 代码块默认不朗读
```
```

- **空一行 = 段落停顿**（按你本人的段落停顿习惯）。
- 太长的句子会在逗号处自动拆开合成；一两个字的短句会和下一句合并，避免不自然。
- **读音纠正**：编辑 `workspace/我的声音/lexicon.txt`，每行 `原文 => 读法`，例如：
  ```
  SQL => sequel
  GPT => G P T
  行长 => 航长
  ```
  字幕里仍显示原文。
- **按字幕时间轴配音**：讲稿用 `.srt`，每句会放在字幕的开始时间上，适合给已有视频重新配音。
  生成后可以用 `voicetwin mux --video 原视频.mp4 --audio 新音频.wav -o 新视频.mp4` 替换视频的音轨。

---

## 让它更像你的技巧

1. **校对文字**：训练素材里的错字会直接变成模型的"口误"。花 10 分钟校对，效果提升很明显。
2. **素材再多一点**：30 分钟 → 2 小时，像度会有一个台阶式的提升。
3. **用 `best` 质量**：每句 5 个候选 + 识别校验，最慢但最稳。
4. **指定参考音频**：在 `workspace/我的声音/references.json` 里找一条你最满意的，把它的 id 填到"指定参考音频"。
   参考音频决定语气基调：想要更有激情就选一条激情的，想要平稳就选平稳的。
5. **看报告**：`xxx.report.json` 里每句都有 `speaker_sim`（声纹相似度，越高越像）和提示，低的句子用 `--redo` 重做。
6. **重新挑模型**：素材校对/增加后，重新训练；也可以单独运行"重新挑选最佳模型"。
7. **语速微调**：默认已按你的真实语速校准；如果某节课想整体快一点，把语速倍数调到 1.05。

---

## 命令行用法

Windows 下用 `voicetwin.bat`，Linux/macOS 下用 `./voicetwin.sh`（或激活环境后直接 `voicetwin`）。

```bash
voicetwin doctor                                    # 检查环境（显卡、模型、依赖）
voicetwin prepare -v 我的声音 -i D:/讲课视频 E:/录音   # 准备素材（可多个文件/文件夹）
voicetwin prepare -v 我的声音 -i D:/讲课视频 --asr funasr   # 纯中文课用阿里 FunASR 识别
voicetwin review  -v 我的声音                        # 用 Excel 改完 transcripts.csv 后同步
voicetwin train   -v 我的声音                        # 训练 + 自动挑最佳模型 + 语速校准
voicetwin select  -v 我的声音 --asr                  # 单独重新挑模型（带识别校验）
voicetwin narrate -v 我的声音 第3课.md -q best        # 讲稿 → 音频 + 字幕 + 报告
voicetwin narrate -v 我的声音 第3课.md --redo 3,7-9   # 只重做第 3、7、8、9 句
voicetwin say     -v 我的声音 "这是一句测试。" -o test.mp3
voicetwin evaluate -v 我的声音 某段音频.wav --text "对应文字"   # 测一测有多像
voicetwin mux --video 原视频.mp4 --audio 讲解.wav -o 新视频.mp4
voicetwin auto    -v 我的声音 -i D:/讲课视频           # 全自动
voicetwin webui                                      # 网页界面
```

所有设置都在 `config.yaml` 里（带中文注释），例如识别模型、降噪、训练轮数、候选数量、输出格式等。

每个声音的数据都在 `workspace/声音名/` 下：

```
workspace/我的声音/
├── clips/              切好的训练片段
├── references/         自动挑选的参考音频（references.json 有文字和 id）
├── transcripts.csv     校对表（Excel 可直接打开）
├── profile.json        你的说话风格档案（语速、停顿、音高、响度）
├── models.json         训练好的模型、自动挑选结果、语速校准系数
├── lexicon.txt         读音纠正词典
├── outputs/            生成的音频、字幕、报告
└── logs/               各步骤日志（出问题时看这里）
```

---

## 可选引擎：Qwen3-TTS、IndexTTS

默认的 GPT-SoVITS 在"用自己的素材微调"这件事上最成熟、显存要求最低，推荐作为主力。另外两个引擎可以作为补充：

| 引擎 | 特点 | 是否需要训练 | 显存 |
|---|---|---|---|
| **GPT-SoVITS v2ProPlus**（默认） | 微调后最像，中英混读好，速度快 | 需要（全自动） | 6GB+ |
| **Qwen3-TTS**（阿里 2026 开源） | 零样本 3 秒克隆，也支持微调；自然度高 | 可选 | 零样本 8GB+；微调 0.6B 约 12GB+，1.7B 建议 32GB+ |
| **IndexTTS 2.5**（B 站开源） | 零样本克隆，情绪和时长控制强 | 不需要 | 8GB+ |

它们各自需要独立的 Python 环境（依赖版本互相冲突），VoiceTwin 通过子进程调用它们：

**Qwen3-TTS**
```bash
conda create -n qwen3-tts python=3.12 -y && conda activate qwen3-tts
pip install -U qwen-tts
git clone https://github.com/QwenLM/Qwen3-TTS.git third_party/Qwen3-TTS   # 微调需要
```
然后在 `config.yaml` 设置 `backends.qwen3tts.python` 为该环境的 python 路径（如 `C:/Users/你/miniconda3/envs/qwen3-tts/python.exe`），
国内把 `download_source` 设为 `modelscope`。使用：`voicetwin narrate -v 我的声音 讲稿.md -b qwen3tts`，微调：`voicetwin train -v 我的声音 -b qwen3tts`。

**IndexTTS 2.5**
```bash
git clone https://github.com/index-tts/index-tts.git third_party/index-tts
cd third_party/index-tts && uv sync --all-extras
modelscope download --model IndexTeam/IndexTTS-2.5 --local_dir checkpoints
```
VoiceTwin 会自动使用 `third_party/index-tts/.venv` 里的 Python。使用：`voicetwin narrate -v 我的声音 讲稿.md -b indextts`。

> 想比较哪个引擎更像你？分别生成同一段讲稿，用"④ 评估相似度"或 `voicetwin evaluate` 打分对比。

---

## 常见问题

**Q：下载模型很慢/失败？**
国内网络建议：语音识别模型设置环境变量 `HF_ENDPOINT=https://hf-mirror.com` 后再运行；
GPT-SoVITS 预训练模型用 `voicetwin download-models --source hf-mirror`；
纯中文课程也可以换成 `--asr funasr`（模型从 ModelScope 下载，国内快）。

**Q：训练报显存不足（CUDA out of memory）？**
在 `config.yaml` 把 `backends.gptsovits.train.batch_size` 改小（如 2 或 1）；10 系及更早的显卡把 `is_half` 改成 `false`。

**Q：英文听起来有中文口音？**
加入你讲英文的录音重新训练（`prepare` 会增量处理新文件，然后 `train`）。

**Q：某个字总是读错（多音字/术语）？**
写进 `lexicon.txt`，例如 `重庆 => 虫庆`、`Kubernetes => 酷伯内提斯`。

**Q：有的句子声音发飘/有杂音/漏字？**
用 `--redo 句子编号` 重新生成；或者用 `-q best`（识别校验会自动重试漏字的句子）。
如果普遍如此，检查素材是否干净、文字是否校对过，再考虑增加素材后重新训练。

**Q：我已经在用 GPT-SoVITS 官方界面训练过模型了，能直接用吗？**
可以。把训练好的权重路径写到 `workspace/声音名/models.json` 的 `gptsovits.selected`（`sovits`、`gpt` 两个路径），
或者先启动官方 `api_v2.py`，在 `config.yaml` 里填 `backends.gptsovits.api_url: http://127.0.0.1:9880`。
VoiceTwin 训练出的模型也会出现在官方界面的模型列表里（名字以 `vt_` 开头）。

**Q：出错了怎么办？**
先运行 `voicetwin doctor` 看环境；再看 `workspace/声音名/logs/` 下对应步骤的日志；命令行加 `--verbose` 可以看到完整报错。

---

## 使用须知

- **只克隆你自己的声音**，或者已经取得本人明确授权的声音。未经同意模仿他人声音可能侵犯他人权益。
- 根据《互联网信息服务深度合成管理规定》《人工智能生成合成内容标识办法》等规定，公开发布的 AI 合成音频
  可能需要按平台要求进行标识（例如在课程简介中注明"部分音频由 AI 根据讲师本人声音合成"）。请遵守你所在平台和地区的规定。
- 你的录音、模型和生成结果都只保存在你自己的电脑上（`workspace/` 目录），默认不会上传到任何地方，也不会被提交到 Git。

本项目整合/调用了以下开源项目，感谢它们的作者：
[GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS)（MIT）、
[Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS)（Apache-2.0）、
[IndexTTS](https://github.com/index-tts/index-tts)、
[faster-whisper](https://github.com/SYSTRAN/faster-whisper)、
[FunASR](https://github.com/modelscope/FunASR)、
[Resemblyzer](https://github.com/resemble-ai/Resemblyzer)、
[Demucs](https://github.com/facebookresearch/demucs)、
[Gradio](https://github.com/gradio-app/gradio)。各引擎模型的使用请同时遵守其各自的许可协议。

---

## 项目结构（开发者）

```
voicetwin/
├── cli.py / workflows.py     命令行与高层工作流（网页界面共用）
├── config.py / default_config.yaml
├── project.py                声音项目的目录与数据（manifest、校对表、模型记录）
├── data/                     素材流水线：提取、清理、切片、字幕、识别、过滤、参考音频、导出
├── style/                    风格档案：语速、停顿、音高、响度
├── eval/                     声纹相似度、识别错字率、综合打分
├── synth/                    讲稿解析、多候选合成与拼接、模型挑选与语速校准
├── backends/                 引擎适配：GPT-SoVITS（训练编排 + api_v2）、Qwen3-TTS、IndexTTS、测试引擎
│   └── workers/              在各引擎自己的 Python 环境里运行的子进程（JSON Lines 协议）
└── webui/                    Gradio 中文界面
tests/                        单元测试、端到端测试、仿真 GPT-SoVITS 集成测试
```

运行测试：`pip install -e ".[dev]" && pytest`（不需要显卡：用测试引擎和仿真的 GPT-SoVITS 目录验证整条流程）。
