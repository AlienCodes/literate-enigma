# VoiceTwin v0.1.6: extra requirements (on top of the audit plan)

> **VERSION UPDATE (user's latest decision): the release is v0.1.6, not 0.1.5.** Wherever this file, the plan, or your prompt says 0.1.5/0.1.4, use **0.1.6** (pyproject.toml, voicetwin/__init__.py, page header "声音分身 VoiceTwin v0.1.6"). The user asked for every feature below to be done to the highest possible standard; the top priority is the closest possible reproduction of the user's voice (R5b–R5f), with ABSOLUTE SILENCE between sentences and NO background noise/room tone anywhere (R5d).


The audit plan is in `scratchpad/ux_audit.json`, under `plan`:
- `plan.units` holds U1–U7, each with items (title / spec / priority / test).
- `plan.interfaces` holds the cross-unit contracts A–J.
- `plan.deferred` lists what is left out on purpose.

That plan was written for "v0.1.4". **The release is now v0.1.5.** Treat every "0.1.4" in the plan as "0.1.5".

The user (a non-technical Chinese teacher) then asked for more. Their requests are below and override the plan wherever the two conflict. Write all user-facing text in simple Chinese.

Paths:
- Repo: `<仓库>`
- Scratchpad: `<草稿目录>`

## R1. Every long task has a progress bar that changes colour

This applies to preparing material, finding typos, training, choosing the model, generating, and downloading models. The bar shows:
- the overall percentage, in large text;
- the step it is on ("第 3 步（共 7 步）：识别每段话的文字");
- a step counter when one is known ("已完成 120 / 800 段");
- the elapsed time;
- an approximate time for the whole task to finish ("全部大约还要 12 分钟，预计 21:40 左右完成").

If no honest estimate is possible yet, the bar shows "正在估算……" and never a fake number.

Colours (this is the user's explicit requirement):
- **Running normally**: GREEN bar (#16a34a), with moving diagonal stripes so the teacher can see it is alive.
- **No progress for a long time** (idle ≥ 180 s): AMBER/YELLOW bar (#d97706), with the text "已经 N 分钟没有新进度：这一步可能比较慢，也可能卡住了。请先等一等，不要关闭黑色窗口。"
- **Error, or the task stopped working**: RED bar (#dc2626). It names the step where it stopped and gives the friendly error from errors.explain(), with "怎么办".
- **Finished**: solid GREEN bar with "✅ 全部完成！用时 …".
- **Stopped by the user**: GREY bar (#6b7280), "⏹ 已停止".

Owners:
- U1 owns `ProgressTracker`, `render_progress_html` and `PROGRESS_CSS`. The overall time estimate uses the overall fraction and the elapsed time, smoothed (EMA). It is shown only once frac ≥ 0.03 and elapsed ≥ 30 s; per-stage estimates stay as the plan describes.
- The snapshot gains these keys: `eta_total` (Optional[float] seconds), `eta_total_text` (str), `finish_clock` (str such as "21:40", or ""), and `level` ('ok' | 'stall' | 'error' | 'done' | 'stopped').

## R2. The web page always shows whether the GPU works

At the top of the page, under the title, a GPU status line is always visible. Every time the page is opened (app.load) and on the 🔄 button, it is refreshed. It is also refreshed when each long task finishes.

**New unit U9 owns the new file `voicetwin/utils/gpu.py`** (no gradio import, never raises):
- `gpu_status(refresh: bool = False) -> Dict[str, Any]`, cached for 10 s. Keys:
  - `ok` (bool), `level` ('ok' | 'warn' | 'error')
  - `name`, `total_gb`, `free_gb`, `used_gb` (float or None)
  - `driver` (str), `torch_cuda` (bool or None), `torch_version` (str)
  - `message` (one Chinese line), `advice` (Chinese, '' when ok)
- How it works: use torch when importable (`torch.cuda.is_available()`, `get_device_name`, `mem_get_info`). Otherwise use `nvidia-smi --query-gpu=name,memory.total,memory.used,driver_version --format=csv,noheader,nounits`. Driver failure is detected the same way as `workflows.nvidia_smi_status`; copy the logic, do not import it, to avoid a cycle.
- The results mean:
  - torch sees no CUDA, or nvidia-smi fails → `level='error'`, message "❌ 显卡没有正常工作", with advice to install the latest driver from https://www.nvidia.cn/drivers/lookup/ and reboot (RTX 50 series needs the nvidia50 package).
  - No NVIDIA GPU at all → error.
  - Free VRAM < 2 GB, or total < 6 GB → `warn`.
- `render_gpu_badge_html(status) -> str` returns a single line inside `<div class="vt-gpu vt-gpu-ok|warn|error">`, e.g. "✅ 显卡正常：NVIDIA GeForce RTX 5070（显存 12.0 GB，可用 10.3 GB）". On error the line is red and includes the advice.
- `GPU_CSS: str`
- `vram_tier(status) -> str` returns 'none' | 'low' (<8 GB) | 'mid' (8–15.9 GB) | 'high' (≥16 GB). It is used by the quality tuning in R5.
- U2 shows the badge. U3's `doctor()` may reuse `gpu_status` behind a guarded import.

## R3. Every list or table shown anywhere has row numbers and a total

Every list or table has a 1-based "#" column (or a numbered list), and a visible total line ("共 N 条" / "共 N 个声音" / "共 N 项"). This covers:
- the proofreading table (already done in v0.1.3; keep it);
- the generated-sentence result table, which must start at 1, not 0;
- the environment-check table;
- the voice library;
- the reference-audio list in the prepare summary;
- the skipped-files list;
- the drop-reasons list;
- any history list.

Owners: U2 for UI tables. U3 makes `NarrationResult` / `seg_report` indexes 1-based for display, keeping internal 0-based indexes, and makes `--redo` numbers 1-based consistently with what is displayed. Check what `--redo` uses today and keep the CLI and the UI consistent, including a test.

## R4. Voice library

Near the top of the page there is a "🎙️ 我的声音库（共 N 个）" section, open by default when at least one voice exists. It lists every saved, named voice with these columns:
- #
- 名称
- 素材（分钟 / 条）
- 状态 ("✅ 已训练，可以生成" / "⚠️ 素材已准备，还没训练" / "⏳ 还没准备素材")
- 最佳模型
- 最后修改时间 (local time "2026-10-01 21:30")

Clicking a row selects that voice in the global 声音名称 dropdown, and everything else follows. A "▶ 试听这个声音" audio element plays that voice's main reference clip.

Owners: U3 extends `wf.list_voices(cfg)` (or adds `wf.voice_library(cfg) -> List[Dict]`) with `minutes`, `clips_kept`, `trained` (bool), `best_model` (str), `main_reference` (absolute path or ''), `modified` (float mtime) and `status` (Chinese). U2 builds the UI.

## R5. Get the most out of the GPU and the model, honestly

**First, a research agent writes `scratchpad/research_quality.md`.** It covers concrete, evidence-backed GPT-SoVITS v2Pro/v2ProPlus training and inference settings that improve quality, scaled by VRAM: batch size, SoVITS/GPT epochs relative to the amount of material, DPO (`if_dpo`) for GPT, `text_low_lr_rate`, inference `top_k`/`top_p`/`temperature`/`repetition_penalty`, aux refs, candidate counts, and ASR re-check thresholds.

Then implementation:
- **U4 (backends)**: VRAM-aware automatic training parameters, using `vram_tier` via a guarded import or the existing `gpu_memory_gb`. Use only the research findings marked high or medium confidence. Every automatic choice is logged in Chinese ("显存 12 GB：batch 8，SoVITS 12 轮，GPT 20 轮，开启 DPO……"). The user can still override them in 高级设置.
- **U3 (synth)**: a new quality tier `max` (UI label "极致（最慢，最稳最像，建议显存 ≥ 8GB）"):
  - more candidates per sentence (e.g. 8);
  - ASR check always on;
  - a stricter CER retry threshold and more retries;
  - VRAM-aware `aux_refs`.

  Keep `fast` / `balanced` / `best`, with UI labels in Chinese. `default_config.yaml` is owned by U3. Document every tier in the config.
- Never claim magic. The UI help text explains, in one line each, that a higher tier is slower but more consistent.

## R6. Highlight likely transcription errors in the proofreading table

**New unit U8 owns the new file `voicetwin/data/proofcheck.py`** (+ `tests/test_proofcheck.py`). **A research agent first writes `scratchpad/research_proofcheck.md`.** It verifies:
- the funasr 1.0.x AutoModel paraformer-zh API, as shipped in the GPT-SoVITS integration package;
- how VoiceTwin's `data/asr.py` already loads funasr and faster-whisper;
- faster-whisper word-level probabilities (`word_timestamps=True` → `segment.words[i].probability`);
- the gradio 4.24 Dataframe `datatype` values ("markdown" / "html"?) and how a markdown/html column renders and edits. Verify in the installed source `scratchpad/gsv39/lib/python3.9/site-packages/gradio`.

`proofcheck.py` API:
- `available_checker(cfg) -> Tuple[str, str]`: (engine name, or '' when none, plus a Chinese reason). It prefers a SECOND engine different from the primary ASR in `cfg prepare.asr.engine`:
  - primary faster-whisper → funasr paraformer-zh for Chinese clips;
  - primary funasr → faster-whisper.
  - If no second engine is installed, re-run faster-whisper with word probabilities, or use heuristics only.
- `find_suspects(project, cfg, progress=None, only_kept=True, limit=None) -> Dict` returns `{checked, flagged, engine, note}`. For each clip it:
  - runs the second recognizer and diffs the normalized texts at character level;
  - adds low-probability words where available;
  - adds heuristics: ALL-CAPS Latin tokens of length ≥ 3 inside Chinese text that are not common acronyms (e.g. "VFIXED", "WHOOZ"), immediately repeated words or phrases, mixed garbage, and English words inside Chinese text that look like phonetic mishearings.

  It writes `record["suspect"] = {"spans": [[start, end], ...], "alt": str, "reasons": [str], "score": float}` (spans are character offsets into `record["text"]`), or removes the key when the clip is clean. It saves the manifest and reports progress per clip. `check_cancel()` comes from U1 behind a guarded import. It never crashes the whole run on a single clip error.
- `render_marked(text, spans) -> str`: escaped text with suspicious characters wrapped in `<span style="color:#dc2626;font-weight:700;background:#fee2e2">`.
- `render_diff_html(text, alt) -> str`: two lines, "识别 A" and "识别 B", with the differing characters highlighted, for the detail panel.

Integration:
- U3: `project.import_csv` and `do_save` must drop `suspect` when the user edits a clip's text. Add `wf.run_proofcheck(cfg, voice, progress=None)` and `wf.apply_suggestion(cfg, voice, clip_id) -> Dict`; the latter sets the text to `alt`, clears `suspect` and re-exports the CSV. Optionally run proofcheck at the end of `run_prepare` as a stage "查找可能的错字" when `cfg prepare.proofcheck` is `auto` (default `auto`) and a second engine is available. Adjust `STAGES_PREPARE` and the sub-ranges, and keep the progress monotonic.
- U2 UI:
  - The proofreading table gains a read-only display column "可能有错（红色）". Use the markdown/html datatype only if verified to work in 4.24; otherwise use plain text with 【】 around the suspicious characters.
  - The count line adds "其中 M 条可能有错（已标红）".
  - A checkbox "只看可能有错的" filters the table. Row → clip mapping must use the id column, not the row index.
  - A button "🔍 自动查找可能的错字" runs `run_proofcheck` with a progress bar.
  - Selecting a row shows `render_diff_html` plus the audio, and a button "✅ 采用建议" that calls `apply_suggestion` and refreshes the table.
  - Honest note under the table: "标红只是提醒「可能有错」，不一定真错；也可能有个别错字没被发现。"

## R7. Version and docs

- The version is **0.1.5** (`pyproject.toml`, `voicetwin/__init__.py`). Show "声音分身 VoiceTwin v0.1.5" in the page header.
- Documentation (U7) is done AFTER the code is merged, by the lead. Implementation units must NOT edit docs, the manual or the PDFs.

## Rules for every implementation unit

- Edit ONLY the files your unit owns (listed in your prompt). Use guarded imports (`try/except ImportError`) for cross-unit enhancements, as plan interface I says. Follow the interfaces exactly.
- Python 3.9 compatible: no `X | Y` types at runtime and no `match`. The gradio code must work on gradio **4.24.0**, so verify every API you use in `scratchpad/gsv39/lib/python3.9/site-packages/gradio`.
- Test with `python3 -m pytest -q` in your worktree (Python 3.11 env, newer libs). For gradio-4.24 / py3.9 checks, run `PYTHONPATH=$PWD <草稿目录>/gsv39/bin/python -m pytest -q -p no:cacheprovider tests --deselect tests/test_gptsovits_fake.py::test_train_select_and_narrate`. That one deselected test is a known env artifact. PYTHONPATH must point at your worktree, because an old voicetwin copy is installed in that venv.
- Do not break existing tests. Add tests for new behaviour.
- `install_windows.ps1` must stay UTF-8 with BOM + CRLF.

## R5b. (NEW, user's latest explicit request — overrides R5 where stricter) "Perfect" quality, fully automatic, pushing the GPU to the limit
The user wants the training and generation settings chosen AUTOMATICALLY for the highest achievable quality on their GPU ("不仅要极致，我要完美，要超过极致"), no manual tuning. Implement honestly: the goal is the closest achievable match, chosen by measurement, not just "bigger numbers" (too many epochs overfit and get WORSE — selection on the held-out validation set decides).
- U4 training (automatic, default — there is no "fast training" default anymore):
  * Pick batch size as large as VRAM safely allows (from research_quality.md), epochs scaled to the amount of material (high/medium-confidence research only), enable GPT DPO (if_dpo) when VRAM tier and research support it, and SAVE MORE CHECKPOINTS (smaller save_every for both SoVITS and GPT) so the automatic selection can choose the best epoch among more candidates. Log one Chinese summary line of every automatic choice and why ("显存 12 GB → batch 8；素材 85 分钟 → SoVITS 16 轮、GPT 25 轮；开启 DPO；每 2 轮保存一次，训练后自动挑最像的"). Keep explicit overrides in 高级设置/config/CLI.
  * If a CUDA out-of-memory happens during training, automatically retry once with half the batch size (log in Chinese) instead of failing — only if this can be done safely within backends (the plan deferred this; do it now if feasible with the fake GPT-SoVITS test emulating an OOM line).
- U3 selection & synthesis:
  * Model selection: evaluate MORE checkpoints and more validation sentences when time allows (e.g. up to 20 items, ASR/CER check on when available), so the chosen model is measurably the most similar.
  * New top synthesis tier `perfect`, label "完美（超过极致：每句试 12 次、严格检查，最慢）": more candidates (e.g. 12), ASR check always on, strict CER retry threshold (e.g. 0.08) with more retries (e.g. 4), VRAM-aware aux_refs, per-sentence choice of the reference clip that best matches the sentence type/length, and pick the candidate with the best combined score (speaker similarity + CER + rate/pitch match to the user's profile). Keep `max` ("极致") as the next tier below.
  * Default quality in the UI = the highest tier recommended for the detected VRAM tier (high/mid → perfect; low → max; none/CPU → balanced with a note), with a one-line note that higher tiers are slower but more consistent.
- U2 UI: show the tiers as Chinese labels with value tuples; show the automatically chosen training plan before/while training (from the backend log/summary).
- Honesty in UI/docs: never promise "100% identical"; say "尽可能接近你本人" and that material quality/quantity and proofreading matter most.

## R5c. (NEW, user insists — strengthen the `perfect` tier further; U3 synth owns, U2 shows it)
The user wants the 完美 tier to do "everything possible" to sound identical to them. In addition to R5b:
- **Adaptive best-of-N instead of a fixed 12**: generate candidates in batches (e.g. 4 at a time) and stop early only when a candidate meets strict targets; otherwise keep going up to a hard cap (e.g. 20 per sentence, VRAM/time aware). Targets: CER ≤ 0.05 (when ASR available) and speaker similarity ≥ a target derived from the user's OWN real clips (e.g. the 25th percentile of similarity between the user's real validation clips and their voice centroid), plus rate/pitch within the user's normal range. If no candidate meets targets, keep the best-scoring one and flag the sentence in the result table ("这一句可能不够像，建议重新生成或改写").
- ~~Match the recording sound~~ — REMOVED by the user. Do NOT implement EQ matching or room tone. See R5d: pauses are absolute digital silence, no background noise at all.
- Log a Chinese summary per narration: how many candidates were tried on average, how many sentences met the targets, which were flagged.
- UI text for the tier: see R5d.

## R5d. (NEW — the user's latest explicit decision; it REPLACES the "Match the recording sound" part of R5c entirely)
The user does NOT want any recording-environment matching. FIXED requirement ("一定要固定住"):
- NO room-tone / background noise / noise floor anywhere in the output. Pauses between sentences (and the lead-in/lead-out) must be ABSOLUTE DIGITAL SILENCE (exact zeros). Do NOT implement the EQ matching or room-tone fill from R5c; remove them if already written. No `synth.match_recording` option.
- Output must contain only the user's voice: trim each generated sentence's leading/trailing non-speech (energy-based, with a few ms fade-in/out to avoid clicks) so no residual hiss sits at sentence edges; between sentences only zeros.
- In the `perfect` tier (optionally also `max`), apply a light, safe noise reduction to each generated sentence to remove residual hiss (e.g. noisereduce stationary mode if installed, moderate strength), but KEEP the denoised version only if it does not reduce speaker similarity / quality score (measure before/after; otherwise keep the original). Never fail the narration if denoise is unavailable.
- Tests: assembled output pauses are exactly 0.0; no non-zero samples in the gaps; sentence edge trimming works; denoise fallback works without noisereduce.
- UI/docs text for 完美: "完美：每句最多试 20 次、严格检查漏字错字，去掉杂音，句子之间完全静音，尽最大可能接近你本人（最慢）".

## R5e. (NEW — user's latest decision; REPLACES the "keep the denoised version only if not worse" bullet of R5d)
In the `perfect` tier, produce and SAVE TWO complete versions of every narration and let the user choose:
- Version A "未去杂音": the selected best candidates, assembled as-is (edges trimmed, pauses exact zeros).
- Version B "去杂音": the same selected candidates, each lightly denoised (noisereduce stationary, moderate strength, if installed; otherwise Version B is skipped with a Chinese note), assembled identically (same timing, pauses exact zeros, same SRT).
- Automatically compare which is closer to the user's real voice: score each FULL version with the same metric (mean per-sentence speaker similarity to the user's voice centroid, plus pitch/rate deviation as in the scorer; report the numbers). Mark the higher-scoring one as recommended ("⭐ 推荐：更像你的原声").
- Files in outputs/: `<stem>_未去杂音.wav`, `<stem>_去杂音.wav`, and `<stem>.wav` = the final version (initially a copy of the recommended one), plus the shared `<stem>.srt` and the report. The report JSON lists both variants with path, score, recommended flag, and which one is final.
- NarrationResult gains `variants: List[Dict]` with keys name ('未去杂音'|'去杂音'), path, score (float), recommended (bool). CLI prints both versions with scores and the recommendation. Add `wf.choose_variant(cfg, voice, report_path, name) -> Dict` that copies the chosen variant to `<stem>.wav` and updates the report's `final` field.
- UI (U2) in ③ after a perfect-tier generation: show two audio players, "版本 A：未去杂音（相似度 0.912）" and "版本 B：去杂音（相似度 0.905）", a clear line "⭐ 推荐：版本 A，更像你的原声（相似度高 0.007）", and a radio "最终使用哪个版本" (default = recommended). Changing it calls choose_variant and updates the main result player + download list. Both variant files are always in the download list. Other tiers keep a single version (no denoise), so nothing changes for them.
- Tests: two files written, pauses exactly zero in both, recommendation equals the higher score, choose_variant copies the right file, graceful skip of B without noisereduce.

## R5f. (NEW) Similarity percentage for EVERY candidate / sentence / version, ranking, 85% elimination — as accurate as possible
The user wants every generated audio to carry a similarity percentage to their real voice, ranked; anything below 85% is discarded; aim for 99%+. Implement HONESTLY and as ACCURATELY as possible:
- **Calibrated percentage "像你本人"** (per voice, per encoder): 100% means "as similar to your voice as your OWN real recordings typically are". Compute and cache, per voice, the similarity of the user's held-out real clips (validation split; fall back to a sample of training clips not used for the centroid) to the voice centroid → median `p50_real` (and p10/p90). For a generated clip with raw cosine `s`: pct = 100 × min(1, s / p50_real), rounded to 0.1. Show raw cosine too in details/report for transparency. Document the definition in the UI help ("100% = 和你自己的真实录音一样像").
- **Accuracy**: use an ENSEMBLE of speaker-verification models when available and average their calibrated percentages: (1) GPT-SoVITS's own ERes2NetV2 speaker-verification model shipped with v2Pro (`GPT_SoVITS/pretrained_models/sv/pretrained_eres2netv2w24s4ep4.ckpt` in the integration package; study RVC-Boss/GPT-SoVITS `GPT_SoVITS/sv.py` and its eres2net code via web/GitHub to load it from `cfg backends.gptsovits.root` in-process, GPU if available), (2) resemblyzer, (3) MFCC fallback only if nothing else. Guarded imports; never crash; record which models were used. U3 additionally OWNS `voicetwin/eval/speaker.py` and `tests/test_speaker_filter.py` for this requirement. Per-clip scoring can use the GPU fully (batch embeddings).
- **Elimination & ranking**: in best-of-N synthesis (all tiers; strict in `max`/`perfect`), candidates below 85% are eliminated; rank the remaining by a combined score where similarity dominates (CER/rate/pitch as tie-breakers/penalties). If no candidate reaches 85% after the tier's maximum attempts, keep the best one but flag the sentence red "低于 85%，建议重新生成或改写这一句". In `perfect`, keep trying (adaptive batches, up to the cap) aiming for ≥ 99% before stopping early.
- **Reporting**: the report JSON stores, per sentence, every candidate's percentage (sorted, with the chosen one marked) and the chosen percentage; per version (A 未去杂音 / B 去杂音) the overall percentage (duration-weighted mean of sentence percentages) and the ranking. Results table columns: #, 句子, 像你本人（%）, 状态 (✅ ≥95 / 🟢 85–95 / 🔴 <85 flagged), 提示. Version cards show the overall % and "⭐ 推荐". Evaluate tab (④) shows the calibrated % plus raw scores per model.
- Honest wording everywhere: "相似度是声纹模型自动打分，越高越像，但不是绝对精确，最终以耳朵为准".

## R8. (NEW) "⑤ 鉴别" tab — machine verification + audience blind test
- **机器鉴别**: pick (or upload) one or more of the user's ORIGINAL recordings and one or more GENERATED files (default: the latest narration's versions/variants and sentence clips); compute the calibrated "像你本人" percentage for each generated file with every available model (ensemble) and show a ranked, numbered table (#, 文件, 各模型 %, 综合 %, 排名, 是否 ≥85%) with the total count. GPU may be used fully.
- **观众盲听测试**: `wf.build_blind_test(cfg, voice, n=10, quality=...) -> Dict` picks n held-out real clips (validation split preferred), synthesizes the same texts with the current best model (respecting the chosen quality tier), loudness-matches all clips, shuffles real+generated into `outputs/盲听测试_<time>/01.wav…`, writes `答案.json` (hidden from the page until submitted) and `听众答题卡.txt` (numbered list for sharing with an audience offline). The UI plays each numbered item with a 真人/生成 choice; on submit it shows per-item correctness and the overall accuracy with the interpretation (≈50–60% → 听众基本分辨不出; 60–80% → 有时能分辨; >80% → 容易分辨, with improvement tips). Progress bar while building (uses the GPU/engine). Owners: U3 (workflows + eval), U2 (UI tab).

## R9. (NEW) Speaking-speed slider: free, continuous, left = faster, right = slower, voice must not change
- UI (U2, ③ tab): replace the current 语速倍数 slider with a continuous slider (not tiers) labelled "语速（← 往左更快　·　中间 0 = 和你原声一样　·　往右更慢 →）", value range −30…+30 (step 1), default 0. Mapping: speed_factor = 1 − value/100 (left/negative → faster, e.g. −20 → 1.20; right/positive → slower, e.g. +15 → 0.85). Under it show a live line "当前：和你原声一样" / "比你原声快 20%" / "比你原声慢 15%". The automatic speed calibration (so 0 == the user's own natural rate) stays on top of this.
- "▶ 试听语速" button: synthesizes one short sample sentence (from the script's first sentence, or a default sentence) at the chosen speed with the fast tier, so the user can try the speed before generating everything.
- Quality guarantee (U3 engine / U4 backends): speed must be applied INSIDE the synthesis model (GPT-SoVITS `speed_factor` — duration control that keeps pitch and timbre), NEVER by resampling or naive time-stretching the waveform. If any post-hoc adjustment is ever needed, it must be pitch-preserving — but prefer none. Pauses between sentences scale with the speed (slower → proportionally longer, still absolute digital silence). Verify in the GPT-SoVITS api_v2 code/docs (research) that speed_factor preserves pitch; document the finding in the report/code comment.
- Tests: the engine passes the mapped speed_factor to the backend for every candidate; no resampling of the waveform happens for speed; pause lengths scale; F0 median of the output at speed 0.85/1.0/1.2 differs by < 0.5 semitone using the fake backend (make the fake generate pitch-stable audio at different speeds, like a real duration-controlled model). Also extend `synth.speed` config docs. The CLI `--speed` keeps working (factor), plus a new `--slower PERCENT` / `--faster PERCENT` convenience if simple.
- Honest UI note: "语速调得越极端（超过 ±20%），越可能不自然；建议在 −15～+15 之间。"
