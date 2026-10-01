# R5 research: GPT-SoVITS v2Pro / v2ProPlus quality settings by VRAM tier

For VoiceTwin v0.1.5 (U4 backends, U3 synth, U9 `vram_tier`). Written 2026-10-01.

Confidence labels:
- **H (high)**: verified in the GPT-SoVITS source code, or an official default.
- **M (medium)**: an official guide or changelog statement, or several independent community sources, or a direct consequence of the code.
- **L (low)**: a single community source, or my own engineering judgement without measurements.

R5 says implement **only H and M** findings.

---

## 0. TL;DR (what to implement)

1. **Fix the tier thresholds first (H).** `torch.cuda.get_device_properties(0).total_memory` reports less than the size printed on the box. Examples: 6 GB card ≈ 5.8 GiB, RTX 3060 12 GB ≈ 11.76 GiB, 8 GB cards ≈ 7.6–8.0 GiB.
   - The official `config.py` adds **+0.4 GiB** before using the value.
   - If `vram_tier` cuts at exactly 8.0 / 16.0, it puts most 8 GB cards in "low" and many 16 GB cards in "mid".
   - Use `G = total_GiB + 0.4` with cutoffs **low < 7.5 ≤ mid < 15.5 ≤ high**.
2. **Training batch size = official formula `floor(G/2)`, with these limits (H/M):**
   - capped at 12;
   - capped at `n_clips//4` (VoiceTwin already does this, and so does the official GPT dataloader);
   - halved when `is_half` is false (already done);
   - low tier: at most 2 (4 GB-class cards: 1).
   - Add an OOM fallback: if the log contains `CUDA out of memory` / `OutOfMemoryError`, halve the batch and retry once.
3. **Epochs depend on the amount and quality of material, not on VRAM (M).** Keep the current rules:
   - SoVITS: 8 epochs under 30 min, 12 at 30 min or more (save every 4);
   - GPT: 15 epochs (save every 5);
   - new: cap SoVITS at 8 when the material is noisy;
   - new: always force `epochs % save_every == 0`.
4. **DPO (`if_dpo`) stays OFF by default on every tier in v0.1.5 (M).** Offer it only as an opt-in in 高级设置, and warn when VRAM < 20 GB. The example log in R5, "显存 12 GB … 开启 DPO", contradicts the evidence; see §4.
5. **`text_low_lr_rate` = 0.4 on all tiers (H, official default).** There is no evidence that changing it helps.
6. **Inference sampling stays at the official defaults on all tiers (H):** `top_k=15, top_p=1.0, temperature=1.0, repetition_penalty=1.35`.
   - Only retry rounds use more conservative sampling (M for the direction, L for the exact numbers).
7. **aux_refs:**
   - Supported on v2Pro: the global timbre embedding, including the SV embedding, is averaged over the main and aux refs (H).
   - The cost is negligible and does **not** depend on VRAM (H).
   - Use 2 by default and 3 in `max` (L–M).
   - Be honest in the UI: "VRAM-aware aux_refs" is not a real lever.
8. **`max` tier:**
   - 8 candidates (6 on the low tier, with a warning);
   - ASR check always on, using a **stronger checker**: paraformer-zh for Chinese when funasr is importable, otherwise a larger faster-whisper on mid/high;
   - stricter CER threshold, plus a "≥ 2 wrong characters" floor for short sentences;
   - 3 retry rounds × 3 candidates with conservative sampling;
   - hard gating: a candidate that passes the CER check always beats one that fails;
   - early stop after the first 4 candidates when one is clearly good. Details in §6.
9. `sample_steps` and `super_sampling` are **v3/v4 only** (H). Ignore them for v2Pro. `lora_rank` and `grad_ckpt` are v3/v4 SoVITS only (H).

---

## 1. Sources and how they were checked

- **Primary source: the GPT-SoVITS source code**, read locally at commit `48b1a01` (2026-08-18, "Fix Fun-ASR-Nano Transformers requirement (#2824)"). It is in `scratchpad/ref/GPT-SoVITS`. GitHub code search reports the same `ref=48b1a01…` for `RVC-Boss/GPT-SoVITS` `webui.py`, so it matches upstream `main`. GitHub links below point to `main`.
- **Network limits in this sandbox:**
  - Blocked by the egress proxy: yuque.com (the official 用户指南), zhihu, csdn, cnblogs, onethingai, compshare, huggingface, arxiv, deepwiki.
  - So the community-guide numbers below come from **search-engine snippets** of pages that copy the official yuque guide. They are marked M or L accordingly.
  - github.com pages could be read with WebFetch.
- **Version note:** the wiki page "GPT‐SoVITS‐features (Latest‐Including‐v5)" (edited 2026-09-27) describes a **v5** (330M+77M, "about 4× faster than v2"). v5 is **not** in the code on `main` as of 2026-08-18, and not in the README. VoiceTwin should stay on v2ProPlus and re-check later.
- **What users actually run:** VoiceTwin tells users to install the "latest v2pro 整合包". That package dates from 2025-06-04, and several later fixes are **not** in it (see §4 DPO and §5).

---

## 2. Facts from the source code (all H)

| # | Fact | Where |
|---|------|-------|
| F1 | WebUI default batch for v1/v2/v2Pro/v2ProPlus: `default_batch_size = default_batch_size_s1 = int(minmem // 2)`. The slider maximum is 3× that. CPU fallback: RAM/4. | `webui.py` L104–136 ([link](https://github.com/RVC-Boss/GPT-SoVITS/blob/main/webui.py)) |
| F2 | `mem_gb = total_memory/1024**3 + 0.4`. fp32 is used when `mem_gb < 4` or `sm < 5.3`; otherwise fp16. | `config.py` L149–167 ([link](https://github.com/RVC-Boss/GPT-SoVITS/blob/main/config.py)) |
| F3 | Defaults for the v2 family:<br>SoVITS: `total_epoch=8`, `save_every_epoch=4`, max epoch slider **25**, label "总训练轮数total_epoch，不建议太高".<br>GPT: `total_epoch=15` (slider 2–50), `save_every=5`.<br>`text_low_lr_rate`: 0.4 (slider 0.2–0.6, hidden for v3/v4).<br>DPO: checkbox "是否开启DPO训练选项(实验性)", default **False**. | `webui.py` L123–127, L1709–1820 |
| F4 | `is_half == False` → batch halved for both SoVITS and GPT. | `webui.py` L519–522, L613–615 |
| F5 | GPT dataloader:<br>`batch = batch_size // 2 if if_dpo else batch_size`, so **DPO halves the batch internally**.<br>Then `batch = max(min(batch, len(dataset)//4), 1)`. | `GPT_SoVITS/AR/data/data_module.py` L46–51 |
| F6 | The DPO forward pass runs the transformer **twice per step**: once on the chosen sequences and once on rule-made "rejected" sequences.<br>Rejected = randomly repeat a span (`repeat_P`) or drop a span (`lost_P`).<br>Loss = CE + reference-free DPO loss (β=0.2). | `AR/models/t2s_model.py` L408–448, `AR/models/utils.py` `make_reject_y` |
| F7 | GPT learning rate is effectively **constant 1e-4**. `WarmupCosineLRSchedule.set_lr` writes `end_lr` into every param group ("锁定用线性"), and `lr_end: 0.0001`. So the number of optimizer updates is `epochs × N/batch`: a bigger batch means fewer updates per epoch. | `AR/modules/lr_schedulers.py` L38–42, `configs/s1longer-v2.yaml` |
| F8 | SoVITS: AdamW, lr 1e-4, `lr_decay 0.999875` per epoch (practically constant). The text embedding, text encoder and MRTE get `lr × text_low_lr_rate`. | `s2_train.py` L172–190, `configs/s2v2ProPlus.json` |
| F9 | Both the SoVITS and GPT datasets are **repeated up to ≥100 items** when there are fewer than 100 clips. Tiny datasets therefore see each clip many times per "epoch". | `module/data_utils.py` L54–58, `AR/data/dataset.py` L179–188 |
| F10 | SoVITS keeps clips of 0.6–54 s, and GPT drops clips longer than 54 s. Long clips raise VRAM sharply: issue #1630 hit OOM on a 24 GB card with 38 s unsliced clips "no matter the batch size". | `module/data_utils.py` L96, `AR/data/dataset.py`, [#1630](https://github.com/RVC-Boss/GPT-SoVITS/issues/1630) |
| F11 | Weights are saved **only when `epoch % save_every == 0`** (SoVITS) or `(epoch+1) % every_n == 0` (GPT). If epochs is not a multiple of save_every, **the final epoch is never exported** to `*_weights_*`. | `s2_train.py` L514, `s1_train.py` L50 |
| F12 | api_v2 defaults: `top_k 15, top_p 1, temperature 1, repetition_penalty 1.35, batch_size 1, parallel_infer True, split_bucket True, speed_factor 1.0, fragment_interval 0.3, sample_steps 32 ("for VITS model V3"), super_sampling False`. The inference WebUIs use the same sliders (top_k 1–100, top_p 0–1, **temperature 0–1**, repetition penalty 0–2, speed 0.6–1.65). | `api_v2.py` L27–44, `inference_webui_fast.py` L374–420, `inference_webui.py` L1329–1349 |
| F13 | `sample_steps` is used only on the vocoder (v3/v4 CFM) path, and `super_sampling` only for v3. Neither has any effect on v2Pro/v2ProPlus. | `TTS_infer_pack/TTS.py` L1336–1349, L1600–1750 |
| F14 | **aux refs on v2Pro:**<br>Each aux ref gets its own spectrogram and a 16 kHz SV embedding.<br>The decoder computes `ge = ref_enc(spec) + sv_emb(...)` per ref and then **averages** `ge` over all refs.<br>The GPT (prosody) prompt uses **only the main ref**.<br>Aux specs are cached in `prompt_cache` and recomputed only when the aux path list changes.<br>Official label: "平均融合他们的音色…如是微调模型，建议参考音频全部在微调训练集音色内". | `TTS.py` L1139–1150, L1258–1263; `module/models.py` L995–1017; `inference_webui.py` L1257–1272 |
| F15 | The main ref must be 3–10 s (16 kHz length check), otherwise "参考音频在3~10秒范围外". There is no such check for aux refs. | `TTS.py` L815–816 |
| F16 | api_v2 runs `uvicorn ... workers=1` with `async def tts_handle` doing blocking GPU work. Concurrent client requests are therefore **serialized**, and parallel requests give no speed-up. | `api_v2.py` L345, L572 |
| F17 | `batch_size` / `parallel_infer` batch the **text fragments of one request**. VoiceTwin sends one sentence with `cut0`, so `batch_size=1` is correct and `parallel_infer` brings no speed-up. | `TTS.py` L1064–1110, `TextPreprocessor.pre_seg_text` |
| F18 | `set_seed(seed)` seeds python, numpy and torch (CUDA too) per request, so the same seed and inputs give a reproducible candidate. | `TTS.py` L194–206 |
| F19 | v2Pro training needs the SV feature step (`2-get-sv.py`). The v2Pro "SV input at wrong sample rate" bug claimed in [#2784](https://github.com/RVC-Boss/GPT-SoVITS/issues/2784) is **not** present on current `main`: the audio is resampled to 16 kHz in `_get_ref_spec`, L800–803. | `TTS.py` |
| F20 | `s2_train.py` (used for v2/v2Pro) ignores `grad_ckpt` and `lora_rank`. Those only matter for `s2_train_v3_lora.py` (v3/v4). | `webui.py` L540–545, `s2_train.py` |

Official README on v2Pro ([link](https://github.com/RVC-Boss/GPT-SoVITS#v2pro-release-notes)):
- "Slightly higher VRAM usage than v2, surpassing v4's performance, with v2's hardware cost and speed."
- "For training sets with average audio quality, v1/v2/v2Pro can deliver decent results, but v3/v4 cannot… the synthesized tone and timbre of v3/v4 lean more toward the reference audio rather than the overall training set."

The wiki adds that v2ProPlus is "slightly more computationally demanding" than v2Pro ([wiki](https://github.com/RVC-Boss/GPT-SoVITS/wiki/GPT%E2%80%90SoVITS%E2%80%90features(Latest%E2%80%90Including%E2%80%90v5))).

Speed: the README gives RTF 0.028 on a 4060 Ti and 0.014 on a 4090 for v2ProPlus. That is long text with batching; a single sentence at batch 1 is slower because of fixed per-request overhead.

---

## 3. VRAM detection (input to U9 `vram_tier` and U4)

| Topic | Recommendation | Conf. | Source |
|---|---|---|---|
| Reported vs marketed VRAM | torch/nvidia report less than the marketed size: a 6 GB card ≈ 5.8 GiB, a 3060 12 GB ≈ 11.76–11.77 GiB. The official code adds +0.4 GiB. | H (official code), M (examples) | `config.py` L157–158; examples from PyTorch-forum OOM reports, e.g. https://discuss.pytorch.org/t/cuda-out-of-memory-issue/35265 |
| Tier formula | `G = total_GiB + 0.4`. Then 'none' (no CUDA), 'low' G < 7.5, 'mid' 7.5 ≤ G < 15.5, 'high' G ≥ 15.5. So 6 GB → low, 8 GB → mid, 12 GB → mid, 16 GB → high, 24 GB → high. | H | as above |
| `gpu_memory_gb()` in `backends/base.py` | Today it returns raw GiB, so an 8 GB card gets batch 3 where the official WebUI gives 4. Apply the same +0.4 (or reuse `utils.gpu.gpu_status()['total_gb']` plus the fudge). | H | F1, F2 |
| Windows shared-memory fallback | Since driver 536.40, Windows **spills to shared system RAM instead of raising OOM**, which is 5–10× slower. On Windows, "too-large batch" therefore often shows up as a silent slowdown. Keep a safety margin, and mention "NVIDIA 控制面板 → CUDA - 系统内存回退策略 → 首选无系统内存回退" in troubleshooting text (not automatic). | M | https://nvidia.custhelp.com/app/answers/detail/a_id/5490 ; https://discuss.pytorch.org/t/documented-fix-slow-execution-pytorch-using-gpu-shared-memory/218909 ; community guide: "显卡 3D 占用达到 100% … 会使用到共享显存，速度会慢好几倍" (search snippet of https://docs.onethingai.com/05560/5e88b) |

---

## 4. TRAINING: recommended settings per VRAM tier

Tier = `vram_tier` with the corrected thresholds from §3. `G = total_GiB + 0.4`. `N` = number of training clips.

| Setting | low (< 8 GB class, e.g. 4/6 GB) | mid (8–15.9 GB class, e.g. 8/10/12 GB) | high (≥ 16 GB class, e.g. 16/24 GB) | Conf. | Sources |
|---|---|---|---|---|---|
| **SoVITS batch_size** | `min(2, floor(G/2))`. 6 GB → 2, 4 GB → 1. The official formula would give 3 on 6 GB, but community tables give 1 for 10 s clips and v2ProPlus is heavier than v2. | `floor(G/2)`: 8 GB → 4, 10 GB → 5, 12 GB → 6 | `min(12, floor(G/2))`: 16 GB → 8, 24 GB → 12 | M (H that it is the official default) | F1; community table (10 s clips): 6G:1, 8G:2, 12G:5, 16G:8 — snippet of https://docs.onethingai.com/05560/5e88b and https://www.compshare.cn/images/compshareImage-1alx595r4v44 |
| **GPT batch_size** (no DPO) | same as SoVITS | same as SoVITS | same as SoVITS (cap 12) | M | F1 (official uses the same `minmem//2` for GPT); community table: 6G:1, 8G:2, 12G:4, 16G:7, 22G:10, 24G:11 (same snippet sources) |
| Always apply | `bs ≤ max(1, N//4)`; halve if `is_half` false; on Windows keep ≥ 1 GB headroom | same | same | H | F4, F5; VoiceTwin already clamps N//4 |
| **Why cap at 12** | — | — | A bigger batch means fewer optimizer updates per epoch at a constant LR (F7, F8). It is mainly a speed knob. SoVITS training is often data-loader-bound, with low GPU load reported on v2Pro ([#2582](https://github.com/RVC-Boss/GPT-SoVITS/issues/2582), [#2598](https://github.com/RVC-Boss/GPT-SoVITS/issues/2598)), so beyond ~12 there is little speed gain and less training per epoch. | M | F7, F8, issues |
| **OOM fallback** | If the training log contains `CUDA out of memory` / `OutOfMemoryError`: halve the batch, log it in Chinese and retry once. | same | same | H (detection) / M (policy) | [#1630](https://github.com/RVC-Boss/GPT-SoVITS/issues/1630) |
| **DPO `if_dpo`** | **OFF** (cannot train) | **OFF**. 12 GB allows only batch 1, and the GPT stage is ~4× slower. | **OFF by default.** Opt-in in 高级设置 only, with the warning "实验功能，GPT 训练会慢 2～4 倍，需要素材干净、文字已校对". Auto-enable is **not** supported by H/M evidence. | M | See the DPO evidence below |
| GPT batch when the user turns DPO on | — | 12 GB: 1 | nominal 16 GB: 1–2, 22 GB: 4, 24 GB: 6, ≥32 GB: 6–8 (the code halves it internally, F5) | L–M | community DPO table (search snippet): "6G/8G 无法训练, 12G:1, 16G:1, 22G:4, 24G:6, 32G:6, 40G:8" |
| **text_low_lr_rate** | 0.4 | 0.4 | 0.4 | H (default) | F3, F8 |
| fp16 (`is_half`) | true unless the card is pre-Volta / `sm < 5.3` / < 4 GB | true | true | H | F2 |
| `grad_ckpt`, `lora_rank` | not used for v2Pro | — | — | H | F20 |
| Epochs | **independent of VRAM**: see the table below | | | M | — |
| save_every | SoVITS 4, GPT 5. **Force `epochs % save_every == 0`**, also for user overrides: round epochs up to the next multiple, or set `save_every = epochs // k`. | same | same | H | F11 |

**DPO evidence (why it stays off by default):**
- Official changelog 2024-02-12: "添加 DPO 损失实验性训练选项, 通过构造负样本训练缓解 GPT 重复漏字问题"; 2024-02-15: "DPO 训练修改为可选项…若勾选则 Batch Size 自动减半" ([Changelog_CN](https://github.com/RVC-Boss/GPT-SoVITS/blob/main/docs/cn/Changelog_CN.md)). The checkbox is still labelled 实验性 on `main`, and the code still halves the batch (F5).
- PR #457 (the DPO author): "DPO会将训练显存翻倍", and recommends halving the batch ([PR #457](https://github.com/RVC-Boss/GPT-SoVITS/pull/457)).
- A community copy of the official guide (search snippets of https://docs.onethingai.com/05560/5e88b and https://www.compshare.cn/images/compshareImage-1alx595r4v44) says:
  - DPO "能显著优化模型效果，减少吞字和复读"; however VRAM rises "2 倍以上", training "速度降低 4 倍", and "12G 以下显卡无法训练";
  - enable it only if VRAM > 12 GB, the data is high quality and you accept the long training;
  - noisy, reverberant or uncorrected data has "负面效果".
- **Bug in the package users install:** until **2026-04-18** ([PR #2733](https://github.com/RVC-Boss/GPT-SoVITS/pull/2733)), `torch.randint(0,1)` made the `lost_P` (omission) branch unreachable, so DPO only trained against *repetition*, never against *omission*. The 2025-06-04 v2pro integration package predates this fix.
- From the code (F5, F6, F7): with DPO, an epoch has 2× as many optimizer updates (half batch), each running two forward passes. GPT time is ≥ 2× (the guide says ~4×), and per-epoch adaptation also doubles.
- **No source quantifies the quality gain.** VoiceTwin already catches repetition and omission at inference with ASR-checked best-of-N.
- **Verdict:** keep it opt-in.
- **Note on R5's example log "显存 12 GB … 开启 DPO":** do NOT enable it at 12 GB automatically.

### Epochs by amount of material (all VRAM tiers)

`minutes` = kept training material, excluding the validation clips.

| Material | SoVITS epochs / save_every | GPT epochs / save_every | Checkpoints VoiceTwin evaluates (last 3 × last 3) | Conf. | Sources |
|---|---|---|---|---|---|
| < 30 min | 8 / 4 | 15 / 5 | s4, s8 × g5, g10, g15 | M (official defaults) | F3 |
| 30–120 min | 12 / 4 | 15 / 5 | s4, s8, s12 × g5, g10, g15 | M | official guide via community copies: "SoVITS 模型轮数可以设置的高一点" for clean data; "GPT 模型轮数一般情况下不高于 20，建议设置 10" (search snippets); webui SoVITS max 25 |
| > 120 min | 12 / 4 | 15 / 5. Do **not** raise GPT: longer GPT fine-tuning of v2Pro/v2ProPlus makes hallucination (omission/repetition, loss of English) "grow rapidly". | same | M | [#2508](https://github.com/RVC-Boss/GPT-SoVITS/issues/2508) |
| Noisy material (denoise was triggered on many clips, low SNR, reverb, inconsistent loudness) | **cap at 8 / 4** | 15 / 5 | | M | guide copies: "如果你的素材中有底噪、混响…请不要调高SoVITS模型轮数，否则会有负面效果" (search snippet) |
| User turns DPO on | unchanged | 15 / 5. Optionally 10 / 5, because updates per epoch double. | | L | F5, F7 |
| Hard caps for any automatic choice | ≤ 25 (official slider max) | ≤ 20 | | M | F3; guide copies |

Suggested Chinese log line (U4), example:

> 显存 12 GB（中档）：batch 6；素材 45 分钟 → SoVITS 12 轮（每 4 轮存一次）、GPT 15 轮（每 5 轮存一次）；DPO 未开启（实验功能，GPT 训练会慢 2～4 倍，建议显存 ≥ 20GB 且素材已校对才手动开启）。

---

## 5. INFERENCE: recommended settings per VRAM tier

For VoiceTwin → api_v2, with one sentence per request.

| Setting | low | mid | high | Conf. | Sources |
|---|---|---|---|---|---|
| top_k / top_p / temperature (first-round candidates) | 15 / 1.0 / 1.0 | same | same | H (official default) | F12 |
| repetition_penalty | 1.35 | 1.35 | 1.35 | H (default) | F12 |
| Retry-round sampling | more conservative: temperature 0.7, then 0.6; top_k 10–20; top_p 0.8 (or 0.6) | same | same | M (direction: lower temperature/top_p means less random) / L (exact values) | PR #457 author's tested defaults: top_k=20, top_p=0.6, temperature=0.6 "for improved output consistency" ([PR #457](https://github.com/RVC-Boss/GPT-SoVITS/pull/457)); these are still the `get_tts_wav()` signature defaults in `inference_webui.py` L789–798. VoiceTwin today uses temperature 0.7, top_k 10. |
| temperature ceiling | ≤ 1.0 | ≤ 1.0 | ≤ 1.0 | H (UI max is 1) | F12 |
| aux_refs | 2 | 2 (3 in `max`) | 2 (3 in `max`) | H that it works on v2Pro and costs little; L–M for the count | F14 |
| Choosing aux refs | same speaker, clean, same language, 3–10 s, taken from the training set (VoiceTwin refs already are) | same | same | H | F14 official label |
| speed_factor | 1.0 × calibration; keep VoiceTwin's clamp of 0.8–1.25 (the official slider is 0.6–1.65) | same | same | H (range) / L (quality vs. distance from 1.0) | F12 |
| sample_steps, super_sampling | ignored for v2Pro: leave the defaults, do not expose | — | — | H | F13 |
| batch_size / parallel_infer | 1 / True (no effect with one fragment) | same | same | H | F17 |
| Concurrent requests | do not: they are serialized server-side | — | — | H | F16 |
| Seeds | a distinct seed per candidate (already done) | — | — | H | F18 |
| **ASR checker model** (VoiceTwin side) | faster-whisper **small**, `int8_float16` on GPU (<1 GB) | **paraformer-zh** (funasr, in the 整合包) for zh sentences if importable; else faster-whisper small, or `large-v3-turbo` with `int8_float16` | paraformer-zh for zh; faster-whisper `large-v3-turbo` fp16 for en | M | Chinese CER, AISHELL-1 test (FunAudioLLM paper, numbers via search snippet): Whisper-small 10.04, Whisper-large-v3 5.14, Paraformer-zh 1.95, SenseVoice-S 2.96 (https://arxiv.org/abs/2407.04051, charts at https://github.com/FunAudioLLM/SenseVoice). VRAM: faster-whisper large-v2 fp16 ≈ 4.5 GB, int8 ≈ 2.9 GB (https://github.com/SYSTRAN/faster-whisper benchmark, RTX 3070 Ti) |
| Running ASR next to the TTS server | OK with small / int8 | OK | OK | M | the GPT-SoVITS server is resident too; large-v3 fp16 (~4.5 GB) on 6–8 GB cards risks spill-over (§3) |

Why the checker matters for CER thresholds (M):
- With whisper-small, ~5–10 % CER is ASR noise. Homophones (同音字) count as errors because `textutil.cer` compares characters.
- A strict 0.08 threshold with whisper-small would trigger many false retries.
- With paraformer-zh, the noise floor is ~2 %.
- Optional, M: when `pypinyin` is importable (it is in the 整合包), compute the zh CER on **toneless pinyin**, so that ASR homophone errors do not count as TTS errors.

---

## 6. Synthesis tiers, including the new `max`

| Tier (UI label) | candidates | ASR check | checker | CER retry threshold | short-sentence floor | retries (rounds × candidates) | retry sampling | aux_refs | early stop |
|---|---|---|---|---|---|---|---|---|---|
| `fast` 快速 | 1 | off | — | — | — | 0 | — | 2 | — |
| `balanced` 均衡 | 3 | off (auto) | — | 0.15 | — | 2 × 2 (only if the ASR check is forced on) | t=0.7, k=10 | 2 | — |
| `best` 最好 | 5 | on | per §5 table | 0.15 with whisper-small / 0.10 with paraformer | retry only if ≥ 2 wrong chars | 2 × 2 | t=0.7, k=10 | 2 | — |
| **`max` 极致** | **8** (low tier: 6, with the warning "显存较小，已减少候选数") | **always on** | per §5 table, preferring paraformer-zh for zh | **0.12 with whisper-small / 0.08 with paraformer or larger whisper** | retry only if ≥ 2 wrong chars (avoids "1 error in 6 chars = 17 %") | **3 × 3** | round 1: t=0.7, k=10, p=1.0; rounds 2–3: t=0.6, k=15, p=0.8 | **3** (2 on low) | generate 4; if the best has CER = 0 (or ≤ half the threshold) and speaker_sim ≥ that voice's median, stop; else generate 4 more |

Confidence:
- M for the structure: best-of-N with ASR gating, a stronger checker, gating before ranking, a length-aware error floor.
- L for the exact numbers (8, 3×3, 0.12/0.08). These are engineering choices, not published measurements. They are safe because the ASR gate decides, not the numbers themselves.

Selection rule for `max` (M):
1. Prefer candidates with `cer ≤ threshold` (hard gate).
2. Among those, rank by the existing `Score.total` (speaker sim, rate, pitch, pauses).
3. If none pass after all retries, keep the lowest-CER candidate and flag the sentence in the result table, e.g. "第 N 句可能有错字，可点“重做”"; `--redo` exists.
4. Keep the existing "几乎没有声音" penalty. The 2025-06-04 package predates two v2Pro fixes for silent output: "修复ge.sum数值可能爆炸导致推理无声的问题" (2025-06-09) and "v2pro对ge提取时会出现数值溢出的问题修复" (2025-06-11) in [Changelog_CN](https://github.com/RVC-Boss/GPT-SoVITS/blob/main/docs/cn/Changelog_CN.md). Silent candidates can therefore occur, and the voiced-ratio check catches them (H).

Cost (L, estimate):
- Each candidate is one TTS call plus ASR plus a speaker embedding.
- Worst case for `max` is 8 + 9 = 17 synth calls per sentence; the typical case with early stop is 4–8.
- Expect roughly **3–5× the time of `balanced`**. Show it honestly in the UI.

Chinese one-line help texts (honest, no magic):
- 快速：每句只生成 1 次，最快；偶尔会有读错或不太像的句子。
- 均衡：每句生成 3 次，自动挑最像的；速度和效果兼顾。
- 最好：每句生成 5 次，并用语音识别检查漏字、错字；更慢，但更稳。
- 极致（最慢，最稳最像，建议显存 ≥ 8GB）：每句最多生成十几次并严格检查，时间大约是"均衡"的 3～5 倍。它只是让出错更少、挑得更准，不会超过模型训练出来的水平。

Config documentation (U3, `default_config.yaml`), suggested keys:
- `synth.quality: fast|balanced|best|max`
- `synth.asr_check_model: auto`, where auto = small on low tier, and paraformer-zh (zh) or large-v3-turbo on mid/high
- per-tier `cer_retry_threshold`, `max_retries`, `retry_candidates`
- `backends.gptsovits.infer.aux_refs: auto` (2; 3 in max)
- `train.if_dpo: false`

---

## 7. Overfitting and undertraining signs (for help text; VoiceTwin detects them automatically)

| Model | Signs | Conf. | Sources |
|---|---|---|---|
| GPT, too many epochs | 吞字/漏字、复读、拖长音; rhythm breaks on text unlike the training set; loses English ability; output copies the reference audio | M | official guide copies (search snippet): "GPT模型训练轮数过大…吞字、复读、拖长音…遇到训练集外文本时韵律崩坏"; [#2508](https://github.com/RVC-Boss/GPT-SoVITS/issues/2508); [#53](https://github.com/RVC-Boss/GPT-SoVITS/issues/53) (GPT 15 epochs on English copied the reference; 5 epochs dropped words) |
| GPT, too few epochs | drops words; accent or rhythm not the teacher's | M | #53 |
| SoVITS, too many epochs | 电音/金属音, high-frequency artifacts, background noise and room tone get learned; word drops reported above 20 epochs (cured at 12) | M | guide copies (search snippet); [#1093](https://github.com/RVC-Boss/GPT-SoVITS/issues/1093) |
| Detection in VoiceTwin | `select_and_calibrate` evaluates the last 3 SoVITS × last 3 GPT checkpoints on held-out validation clips (speaker sim, sim to the real clip, CER, rhythm), so an overfitted last checkpoint is usually not chosen. Keep `validation_count ≥ 12`, and make sure the saved epochs (F11) actually span early → late. | H (code) | `voicetwin/synth/select.py`, `backends/gptsovits.py checkpoints()` |

---

## 8. Things NOT to do

1. **Do not tie epochs to VRAM.** More VRAM means a bigger batch, which means *fewer* updates per epoch at constant LR (F7, F8). VRAM decides batch size and whether DPO is feasible; material decides epochs. (M)
2. **Do not treat a bigger batch as higher quality.** Past ~12 it mostly reduces updates per epoch. On Windows, over-filling VRAM silently spills to system RAM and is 5–10× slower instead of raising an error. (M)
3. **Do not use raw `total_memory` with 8/16 cutoffs** for tiers or batch size. Add +0.4 like the official code. (H)
4. **Do not pick epochs that are not multiples of save_every** (e.g. SoVITS 10 with save 4): the final weights are never exported, and VoiceTwin would evaluate older checkpoints only. Enforce this for user overrides too. (H)
5. **Do not auto-enable DPO.** It is experimental in the official UI; VRAM rises ≥ 2× and the GPT stage is 2–4× slower; it is harmful with noisy or unproofread text; omission negatives were broken in packages before 2026-04-18; and there is no published quality measurement. It is especially wrong at 12 GB (batch 1). (M)
6. **Do not raise SoVITS epochs on noisy or reverberant material**, and never automatically exceed SoVITS 25 or GPT 20. **Do not raise GPT epochs for large datasets** (#2508). (M)
7. **Do not change `text_low_lr_rate` automatically.** It is 0.4 officially, it only scales the LR of the SoVITS text encoder, embedding and MRTE, and there is no evidence that other values help. (H/M)
8. **Do not expose or tune `sample_steps`, `super_sampling`, `lora_rank` or `grad_ckpt` for v2Pro.** They do nothing there. (H)
9. **Do not send concurrent TTS requests** to one api_v2 server hoping for speed: they are serialized (F16). Do not set `batch_size > 1` for single-sentence requests: no effect (F17). (H)
10. **Do not use temperature > 1** or large `top_k` to "add variety". The official UI caps temperature at 1. Do not move `repetition_penalty` away from 1.35 without measurements. (H/M)
11. **Do not use aux refs from other speakers, noisy clips or clips outside the training set.** Do not expect aux refs to fix prosody (the GPT prompt uses only the main ref, F14). Do not sell aux_refs as "VRAM-aware": their cost is negligible on any GPU. Avoid large counts: averaging many embeddings may flatten expressiveness (L). (H for the mechanism)
12. **Do not set strict CER thresholds with a weak ASR.** With whisper-small, ~5–10 % CER is recognizer noise on Chinese, so a threshold below ~0.12 means endless retries. Use paraformer-zh or pinyin CER first, and require ≥ 2 wrong characters on short sentences. (M)
13. **Do not run faster-whisper large-v3 fp16 (~4.5 GB) next to the TTS server on 6–8 GB cards.** (M)
14. **Do not train on very long clips.** VRAM explodes (#1630 hit OOM at 38 s on a 24 GB card). Keep VoiceTwin's `max_duration: 12`. (H/M)
15. **Do not claim that `max` makes the voice "more like you" than the trained model can.** It reduces reading errors and picks the best of several samples. (R5 requirement)
16. **Do not start GPT-SoVITS training while the TTS api server (or ASR on GPU) is still loaded.** They compete for the same VRAM. (M)

---

## 9. Low-confidence ideas (not for v0.1.5 unless measured)

- **Batch the candidates in one request:** send the sentence N times separated by newlines with `batch_size=N`. GPU utilization at batch 1 is low; compare the README's RTF 0.014–0.028 for batched long text. But the API returns one concatenated wav (fragments joined with `fragment_interval` silence), and `pre_seg_text` may merge or prefix fragments, so splitting is fragile. (L)
- **Auto-tune `aux_refs` (0/2/3) inside `select_and_calibrate`** on the validation set, scoring speaker sim, and keep the best. The method is sound, but the gain is unmeasured. (M for the method, L for the gain)
- **Two different main references per sentence in `max`** (e.g. 2 refs × 4 seeds), to diversify prosody before selection. This needs a cache-key change. (L)
- **Re-check v5** once it lands in code: the wiki claims higher similarity and ~4× speed, but it is not on `main` yet. (L)

---

## 10. Current VoiceTwin gaps found while reading the code (for U3/U4)

- `backends/base.py: gpu_memory_gb()` has no +0.4: an 8 GB card gets batch 3 instead of the official 4, and would be tier 'low' if `vram_tier` used raw GiB.
- `backends/gptsovits.py: _auto_params()`:
  - batch = `mem//2` uncapped (a 48 GB card would get 24);
  - no low-tier cap;
  - epochs are not forced to multiples of `save_every`;
  - no noisy-material cap;
  - no OOM retry.
  - `if_dpo` is hard-coded `False`. That is the right default; only expose it as an opt-in.
- `synth/engine.py`:
  - retry rounds are hard-coded `(2, 0.7)` with top_k 10;
  - the CER gate only stops retrying; it is not a hard filter in the final pick (`max(candidates, key=total)` can choose a higher-CER candidate with better speaker sim);
  - the checker is always `asr_check_model: small`.
- `default_config.yaml`: the `aux_refs` comment says "v2/v2Pro 支持". That is correct, but it is not VRAM-related; describe it honestly.

---

## 11. Source list

- GPT-SoVITS source, `main` @ 48b1a01 (2026-08-18):
  - https://github.com/RVC-Boss/GPT-SoVITS/blob/main/webui.py
  - https://github.com/RVC-Boss/GPT-SoVITS/blob/main/config.py
  - https://github.com/RVC-Boss/GPT-SoVITS/blob/main/api_v2.py
  - https://github.com/RVC-Boss/GPT-SoVITS/blob/main/GPT_SoVITS/TTS_infer_pack/TTS.py
  - https://github.com/RVC-Boss/GPT-SoVITS/blob/main/GPT_SoVITS/AR/data/data_module.py
  - https://github.com/RVC-Boss/GPT-SoVITS/blob/main/GPT_SoVITS/AR/models/t2s_model.py
  - https://github.com/RVC-Boss/GPT-SoVITS/blob/main/GPT_SoVITS/AR/modules/lr_schedulers.py
  - https://github.com/RVC-Boss/GPT-SoVITS/blob/main/GPT_SoVITS/s2_train.py
  - https://github.com/RVC-Boss/GPT-SoVITS/blob/main/GPT_SoVITS/module/models.py
  - https://github.com/RVC-Boss/GPT-SoVITS/blob/main/GPT_SoVITS/inference_webui.py
  - https://github.com/RVC-Boss/GPT-SoVITS/blob/main/GPT_SoVITS/inference_webui_fast.py
  - https://github.com/RVC-Boss/GPT-SoVITS/blob/main/GPT_SoVITS/configs/s1longer-v2.yaml
  - https://github.com/RVC-Boss/GPT-SoVITS/blob/main/GPT_SoVITS/configs/s2v2ProPlus.json
- README (v2Pro notes, RTF): https://github.com/RVC-Boss/GPT-SoVITS
- Changelog (DPO, v2Pro fixes, PR #2733): https://github.com/RVC-Boss/GPT-SoVITS/blob/main/docs/cn/Changelog_CN.md
- Wiki, version features: https://github.com/RVC-Boss/GPT-SoVITS/wiki/GPT%E2%80%90SoVITS%E2%80%90features-(%E5%90%84%E7%89%88%E6%9C%AC%E7%89%B9%E6%80%A7) and https://github.com/RVC-Boss/GPT-SoVITS/wiki/GPT%E2%80%90SoVITS%E2%80%90features(Latest%E2%80%90Including%E2%80%90v5)
- PR #457 (DPO, sampling defaults): https://github.com/RVC-Boss/GPT-SoVITS/pull/457
- PR #2733 (DPO lost_P fix, merged 2026-04-18): https://github.com/RVC-Boss/GPT-SoVITS/pull/2733
- PR #2450 (v2Pro api cache fix, 2025-06-11): https://github.com/RVC-Boss/GPT-SoVITS/pull/2450
- Issues:
  - #2508 (v2Pro GPT longer fine-tune → hallucination): https://github.com/RVC-Boss/GPT-SoVITS/issues/2508
  - #1093 (SoVITS > 20 epochs word drop): https://github.com/RVC-Boss/GPT-SoVITS/issues/1093
  - #53 (GPT epochs over/under): https://github.com/RVC-Boss/GPT-SoVITS/issues/53
  - #1630 (OOM with long clips): https://github.com/RVC-Boss/GPT-SoVITS/issues/1630
  - #2582 and #2598 (low GPU load in SoVITS training): https://github.com/RVC-Boss/GPT-SoVITS/issues/2582 , https://github.com/RVC-Boss/GPT-SoVITS/issues/2598
  - #2784 (claimed v2Pro bugs; not present on main): https://github.com/RVC-Boss/GPT-SoVITS/issues/2784
  - #631 (DPO necessity, unanswered): https://github.com/RVC-Boss/GPT-SoVITS/issues/631
- Official user guide (blocked here; content seen via community copies): https://www.yuque.com/baicaigongchang1145haoyuangong/ib3g1e
- Community copies of the guide (batch/VRAM and DPO tables, epoch advice; read via search snippets only): https://docs.onethingai.com/05560/5e88b , https://www.compshare.cn/images/compshareImage-1alx595r4v44 , https://zhuanlan.zhihu.com/p/681754094
- NVIDIA sysmem fallback: https://nvidia.custhelp.com/app/answers/detail/a_id/5490 ; https://discuss.pytorch.org/t/documented-fix-slow-execution-pytorch-using-gpu-shared-memory/218909
- faster-whisper VRAM benchmark: https://github.com/SYSTRAN/faster-whisper
- ASR CER comparison (FunAudioLLM / SenseVoice): https://arxiv.org/abs/2407.04051 ; https://github.com/FunAudioLLM/SenseVoice
- Reported VRAM examples (5.80 GiB on 6 GB, 11.76 GiB on 12 GB): https://discuss.pytorch.org/t/cuda-out-of-memory-issue/35265 (and similar PyTorch-forum OOM threads)
