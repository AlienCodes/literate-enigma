# v0.1.6 manual update — facts and rules (source of truth)

Repo: <仓库> (branch claude/happy-heisenberg-u52a72). The PDF manual is built from
docs/manual/src/*.html (00_head.html holds the CSS — do NOT edit it). Images live in docs/manual/images/ and are
referenced from the HTML as `../images/NAME.png`.

The manual currently describes v0.1.3. Bring the files you own up to date with v0.1.6. The authoritative,
already-updated descriptions of the v0.1.6 UI are:
- 快速上手.md (repo root) — short user guide, already rewritten for v0.1.6
- docs/Windows详细使用教程.md — steps 6–10, "怎么检验像不像：鉴别和盲测" and FAQ, already rewritten for v0.1.6
- README.md — feature table and "三步用起来", already rewritten for v0.1.6
- voicetwin/webui/app.py — the real UI (labels, button texts, headers). Quote button/label texts EXACTLY as in app.py.
- voicetwin/synth/engine.py — QUALITY_LABELS / QUALITY_HELP / QUALITY_PRESETS (quality tiers)
- voicetwin/cli.py — CLI options (narrate -q fast|balanced|best|max|perfect, --speed/--faster/--slower, train --dpo auto|on|off)
- voicetwin/default_config.yaml — config keys

## What changed in v0.1.6 (user-visible)
1. Progress bar for EVERY long task (prepare, typo check, training, model re-selection, generation, speed preview,
   verification, blind test, model download). Shows %, "第 i 步（共 n 步）：name", "已用 …", "这一步大约还要 …",
   "⏱ 全部大约还要 N 分钟，预计 HH:MM 左右完成", "现在：…". Colours: green striped moving = normal;
   amber/yellow = no new progress for ≥ 3 minutes (stall warning, ETA hidden); red = stopped with an error, box
   "原因 / 怎么办", plus "详细过程（出问题时可以复制给帮你的人）" accordion with the log; grey = stopped by user
   ("⏹ 停止" must be clicked twice within 5 s; finished parts are kept); solid green 100% "✅ 全部完成！用时 …" with
   "完成时间". Closing/refreshing the page does not interrupt the task; reopening re-attaches to the running bar.
   Only one heavy task runs at a time.
2. GPU status badge always shown at the very top: green "✅ 显卡正常：NVIDIA GeForce RTX 4070（显存 12.0 GB，可用 10.5 GB）",
   yellow warn (small VRAM / little free VRAM), red "❌ 显卡没有正常工作：…" with "怎么办" (install the latest NVIDIA
   driver from https://www.nvidia.cn/drivers/lookup/ and reboot; RTX 50 series needs the nvidia50 package);
   button "🔄 重新检查显卡".
3. Every table has a "#" row-number column starting at 1, and a total count ("📊 一共 228 条片段：保留 228 条（16.4 分钟），
   不保留 0 条", "我的声音库（共 N 个）", doctor "共 N 项").
4. "🎙️ 我的声音库（共 N 个）" accordion under the voice-name box: table # / 名称 / 素材（分钟 / 条）/ 状态 / 最佳模型 /
   最后修改时间; click a row to select that voice (and preview it).
5. Training is fully automatic and VRAM-aware: the ② tab shows "🧠 这次自动选择的训练方案：显存 12 GB → 每批 6 条；
   素材 15 分钟（208 条）→ 音色 SoVITS 8 轮、语气 GPT 15 轮；音色每 2 轮、语气每 3 轮存一次模型，训练完自动挑最像你的那个；
   不开 DPO（…）". On out-of-memory it automatically retries with a smaller batch. Old training runs are archived.
   DPO: radio "DPO（GPT-SoVITS 的实验功能）" 自动（推荐）/开/关 in 高级设置 — auto = OFF (no reliable evidence it helps,
   makes GPT training 2–4× slower). CLI: `voicetwin train --dpo on`.
   Training done shows "✅ 训练完成（用时 …）", "已经自动挑出最像你的版本（像你本人 xx%），并把语速调得和你本人一样。"
6. Quality tiers (Radio "质量"): 快速 (1 try) / 均衡 (3, pick best) / 最好 (5 + ASR check for missing/wrong words) /
   极致 (8 + strict check, ≥8GB) / 完美 (up to 20 tries per sentence, strict check, produces TWO versions, pauses are
   absolute silence; slowest). Default is chosen from the GPU: ≥ 8 GB → 完美; < 8 GB → 极致; no usable GPU → 均衡.
   The note under it is honest: higher tiers are slower and more stable, but nothing makes it 100% identical; material
   quality/quantity and proofreading matter most.
7. "像你本人（%）" similarity: calibrated against the user's own real recordings — 100% = as similar as another real
   recording of the user. Shown for every candidate, every sentence, every version and in ⑤. Candidates below 85% are
   eliminated (only when a reliable speaker-verification model is available; with only MFCC fallback the % is rough
   and nothing is eliminated — a ⚠️ note says so). If even the best candidate of a sentence is below 85%, the sentence is
   flagged "低于 85%，建议重新生成或改写这一句". Honest caveat everywhere: automatic score, not absolute; ears decide.
8. 完美 tier two versions: card "🎧 这次做了两个版本，听一听，选你更喜欢的": "版本 A：未去杂音（像你本人 xx%）",
   "版本 B：去杂音（像你本人 xx%）", "⭐ 推荐：版本 A，更像你的原声" (the one more similar to the original voice is
   recommended), two players, radio "最终使用哪个版本". Both versions are saved; picking one switches the result
   player and the download files. The two versions have identical text, pauses and subtitles; B only removes faint noise.
9. ABSOLUTE SILENCE (fixed requirement from the user): generated audio contains ONLY the user's voice — no background
   sound, no room tone, no noise floor; pauses between sentences are exact digital silence. Pause LENGTHS follow the
   user's own habits (comma/period/paragraph). There is NO "recording-environment matching" — never describe adding
   room tone/EQ/background. Remove/rewrite any old text that says pauses have "natural fluctuation of background" or
   suggests adding room tone.
10. Speed slider "语速（← 往左更快 · 中间 0 = 和你原声一样 · 往右更慢 →）", range −30…+30, step 1; text under it
    "当前：和你原声一样" / "当前：比你原声快 10%"; note: beyond ±20% may sound unnatural, recommend −15…+15. Changes only speed,
    not timbre/pitch. Button "▶ 试听语速" generates a one-sentence preview. CLI: --faster 10 / --slower 15 / --speed 1.1.
11. Typo finder in ①: button "🔍 自动查找可能的错字" re-listens every clip with a second ASR engine (FunASR vs
    faster-whisper; without a second engine it uses word confidence; without any, rules only — fewer finds) plus rules
    (ALL-CAPS nonsense English, repeated words…). Result: "✅ 检查完了：一共查了 228 条，其中 2 条可能有错（已在表格里标红）".
    Column "可能有错（红色）" shows suspicious characters in RED with the suggestion. Checkbox "只看可能有错的",
    button "🔄 重新载入". Clicking a row plays the clip and shows a red-bordered panel comparing 识别 A（现在的文字）/
    识别 B with the reason; button "✅ 采用建议" applies the suggestion; edit "文字" by double-clicking; "保存修改".
    Clip table columns: # / id / 保留（是/否）/ 语言 / 秒 / 文字 / 可能有错（红色）/ 丢弃原因. (Old v0.1.3 had a
    "载入片段列表" button and ✔/✘ in 保留 — both gone; the table loads automatically after prepare.)
12. Tabs now: ① 准备素材 / ② 训练模型 / ③ 生成讲课音频 / ④ 试试像不像（可选）/ ⑤ 鉴别 / 🩺 环境检查.
    ④ = single-file evaluation (upload audio + optional text, "评估", "📥 评估刚才生成的音频").
    ⑤ 鉴别 = "🤖 机器鉴别": optional uploads "你的原始录音（可选，可多选）" and "要鉴别的生成音频（可选，可多选）"
    (defaults: held-out real recordings + latest generation), button "开始鉴别", table # / 文件 / 各模型 % / 综合 % /
    排名 / 是否 ≥85%; and "👂 观众盲听测试": slider "用几句话（真人和生成的各这么多段）", button "生成盲听测试",
    shuffled numbered clips with radio 真人/生成 each, "提交答案" grades it; accordion
    "📝 批改收上来的答题卡（离线测试、网页刷新过也能用）" to grade answers pasted later.
13. 🩺 环境检查: table # / 状态 / 项目 / 说明 with "共 N 项"; button "⬇️ 下载缺少的模型" (with progress bar) replaces the
    command-line download for most users; "🔄 重新检查（约 10~30 秒）". Optional components accordion.
14. Launcher: double-clicking the icon again does not start a second copy, it opens the running page; if port 7860 is
    busy it picks another port automatically; Windows: keeps the PC awake during long tasks; disables the console's
    QuickEdit so clicking inside the black window no longer freezes the program (if the title shows "选择", press Enter).
15. Errors are explained in plain Chinese ("原因 / 怎么办") instead of raw tracebacks.
16. Installer (gsv mode) now also installs noisereduce (needed for version B); re-running install_windows.bat keeps
    config and voices. Upgrade = extract new zip over D:\VoiceTwin (replace) → run install_windows.bat → 1 → D:\GPT-SoVITS.
17. Header shows "声音分身 VoiceTwin v0.1.6".

## Screenshots available in docs/manual/images/ (real UI, demo machine with RTX 4070 12GB; demo voice, so the
## similarity numbers in screenshots are low/meaningless — captions must say numbers are only examples)
- 00_gpu_badge.png — green GPU badge + 🔄 重新检查显卡
- 00b_voice_library.png — 我的声音库（共 1 个） accordion opened with the numbered table
- 01_prepare_form.png — whole top of page: title v0.1.6, GPU badge, voice name, library, tabs, ① form filled (D:\讲课素材)
- 02a_progress_running.png — green striped progress bar at 30% during prepare with ETA
- 02_prepare_done.png — 100% done bar + "✅ 素材准备好了" summary (speech rate, pause habits, references)
- 03a_proofcheck_done.png — clip count line, typo buttons, done bar, "✅ 检查完了… 2 条可能有错"
- 03_proofread.png — filtered table with red marks + playing clip + red-bordered comparison panel
- 04a_train_plan.png — "🧠 这次自动选择的训练方案" + 开始训练 / 重新挑选最佳模型 buttons
- 04b_train_running.png — training progress bar
- 04_train_done.png — done bar + "✅ 训练完成"
- 05_generate_form.png — ③ form: script, quality radio (完美 selected), note, speed slider, ▶ 试听语速, redo box, 生成
- 05b_speed_slider.png — speed slider close-up
- 05c_generate_running.png — generation progress bar (may be missing; only reference it if the file exists)
- 06_generate_done.png — done bar + "✅ 生成好了" + result player
- 06b_download.png — result player + 下载（音频 / 字幕） files
- 06c_two_versions.png — two-version card with ⭐ 推荐 and 最终使用哪个版本
- 06d_result_table.png — per-sentence table # / 句子 / 像你本人（%）/ 状态 / 提示
- 07_evaluate.png — ④ 试试像不像 result
- 08_verify.png — ⑤ machine verification table
- 08b_blind_test.png — ⑤ blind test with numbered clips and 真人/生成 radios
- 09_error_red.png — red error bar with 原因/怎么办 (empty script example)
- 10_doctor.png — 🩺 环境检查 numbered table
- 11_progress_states.png — legend of the 5 progress-bar states (green/amber/red/grey/done)
Before referencing an image, check it exists (ls docs/manual/images). Old images 03_proofread.png etc. were
replaced in place, so existing <img> references stay valid, but captions must match the new content.

## Writing rules
- Simplified Chinese, plain words for a non-technical teacher; keep the existing HTML structure, classes
  (tip/warn/bad/note boxes, <figure><img><figcaption><b>图 x-y</b>…, tables, .path, .btn etc. — copy what the file
  already uses), heading ids and chapter numbering. Renumber figures inside a chapter consistently.
- Keep page-count growth modest: update and add where needed, cut text that describes removed UI.
- Honesty: never promise 100% identical; similarity is an automatic score.
- Never add model identifiers or AI-tool attribution to the docs.
- Do not touch files you were not assigned. Do not commit. Do not run the PDF build.
