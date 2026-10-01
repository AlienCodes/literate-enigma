# Research: R6 proofcheck (finding likely transcription errors)

Scope: verify the APIs that U8 (`voicetwin/data/proofcheck.py`) and U2/U3 need. Every claim below was checked
against installed or downloaded source code, or by a live test. Estimates are labelled as such.

Evidence on disk (scratchpad = `<草稿目录>`):
- `pkgsrc/funasr/` is the funasr **1.0.27** wheel, unpacked (`pip download funasr==1.0.27 --no-deps`).
- `pkgsrc/fw/` is the faster-whisper **1.1.1** wheel, unpacked.
- `pkgsrc/ms/` is modelscope **1.10.0** (hub code only).
- `gsv39/lib/python3.9/site-packages/gradio` is gradio **4.24.0** (`_frontend_code/` holds the Svelte sources).
- `proofproto/app.py` is a live gradio 4.24 Dataframe prototype. Its screenshots are `proofproto/df.png` (all variants), `df_md.png`, `df_md_editing.png`, `df_html_editing.png`, `df_sty_i.png`, `df_sty_n.png`, `df_mdraw.png` and `df_raw.png`.
- `proofproto/diffproto.py` is a working, Python 3.9-compatible prototype of the tokenizer, diff, heuristics, word-probability mapping, evidence scoring and rendering recommended below. Run it with `python3 diffproto.py`.

---------------------------------------------------------------------------------------------------------------
## 0. Recommendations (TL;DR)

1. **Second engine.** The GPT-SoVITS v2pro integration package ships **funasr==1.0.27 + modelscope==1.10.0** and **faster-whisper** (unpinned in `extra-req.txt`; 1.1.1 at package build time). I verified this from the tags `20250606v2pro` and `20250422v4` on GitHub. In the recommended "install into the integration package" mode, **both engines are importable**.
   - Use `importlib.util.find_spec("funasr")` and `find_spec("modelscope")` / `find_spec("faster_whisper")` to detect them. Do not import funasr just to probe: its `__init__` walks and imports every submodule, which takes seconds.
2. **funasr for checking.** Load paraformer with **no VAD and no punctuation model** (clips are 2–12 s, and punctuation is stripped before diffing anyway):
   `AutoModel(model=<local dir or "paraformer-zh">, disable_update=True, disable_pbar=True, check_latest=False, device=...)`.
   - Prefer the integration package's local copy `<gsv_root>/tools/asr/models/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch` when it exists. Then try the ModelScope cache dir. Fall back to the id (network).
   - Output is `[{"key", "text", ("timestamp")}]`. There is **no per-token confidence** in funasr 1.0.27, so low-probability words come only from faster-whisper.
3. **faster-whisper words.** `model.transcribe(wav16k, language=lang, word_timestamps=True, ...)` gives `seg.words[i].word/.start/.end/.probability`. Each probability is the mean of that word's token probabilities from a forced-alignment pass.
   - In `zh` mode, "words" are unicode-safe token pieces. An English word can be split, e.g. `" V","FIX","ED"`, so merge the pieces and keep the minimum probability.
4. **Dataframe rendering in 4.24: use `datatype="markdown"` for the read-only display column "可能有错（红色）".**
   - Verified live: `<span style="color:#dc2626;font-weight:700;background:#fee2e2">…</span>` renders red/bold/pink inside a markdown cell. The cell is sanitized by DOMPurify, so `onerror=` is stripped.
   - `datatype="html"` also renders, but it is **NOT sanitized**. The live XSS probe executed `onerror`, so do not use it.
   - All text must be HTML-escaped **and** markdown-escaped (`*`, `_`, `1.`, `#`, `$`… as numeric entities; see §4.5). Pass `latex_delimiters=[]`.
   - Per-cell or per-column read-only does **not exist** in 4.24. Double-clicking the display cell shows the raw `<span …>` markup in an input box, and edits there are sent to the backend. So `do_save` must ignore that column, and a hint should say "这一列只用来看".
   - pandas `Styler` cell colours work **only when `interactive=False`** (verified), so they are no option for the editable proofreading table.
   - The 【】 plain-text fallback also works (verified) and needs nothing special.
5. **Diff.** Tokenize both texts into normalized tokens that keep offsets into the original string:
   - one token per CJK char (NFKC, lower case, traditional to simplified);
   - one token per Latin word;
   - one `#` token per number run (Arabic digits or Chinese numerals, including 百分之X);
   - punctuation and whitespace dropped.

   Run `difflib.SequenceMatcher(None, a_keys, b_keys, autojunk=False)`. Drop or soften these differences:
   - spacing-only differences;
   - filler-only insertions and deletions (嗯/呃/那个…);
   - homophones with the same pinyin and tone (他/她, 的/地/得, 在/再), which do not change the TTS phonemes;
   - English in A vs a Chinese transliteration in B (paraformer cannot spell English; e.g. Python vs 派森).
6. **`alt` must be a merged sentence, not the raw paraformer text.** Raw paraformer text has no punctuation, space-separated characters (seaco variant), lower-case English and Chinese numerals. So start from `record["text"]`, splice in B's text only for the kept diff regions, then run `clean_transcript`. If nothing remains, `alt = ""` and the UI disables "✅ 采用建议". When the sentences diverge completely (`SequenceMatcher.ratio() < 0.5`), mark the whole text and offer the full cleaned B text.
7. **Score.** Combine the evidence weights with a noisy-OR, `score = 1 - Π(1 - w_i)`, and flag a clip when `score ≥ 0.45`. The weights are in §6.4. With these weights, one engine disagreement, one ALL-CAPS gibberish token, or one word with probability < 0.3 is enough to flag a clip. One word with probability in 0.3–0.45 is not.

---------------------------------------------------------------------------------------------------------------
## 1. What VoiceTwin already does (relevant facts)

`voicetwin/data/asr.py`
- `Transcriber(cfg)` takes the dict `prepare.asr`. `engine` is `faster-whisper` (default) or `funasr`. The model is loaded lazily in `_load()` and stored in `self._model`.
- faster-whisper: `WhisperModel(model_name, device, compute_type)`. `compute_type="auto"` means `float16` on CUDA and `int8` on CPU, with default model `large-v3`.
  - `_whisper()` calls `transcribe(wav16k, language=lang, beam_size=cfg.beam_size(5), initial_prompt=cfg.initial_prompt_zh if zh, condition_on_previous_text=False, vad_filter=False, temperature=0.0)`. It does **not** request words.
  - The text is joined (`""` for zh, `" "` for en), then passed through `to_simplified` (zh only) and `clean_transcript`.
  - `avg_logprob` is the duration-weighted mean of `seg.avg_logprob`. `no_speech_prob` is the max over segments.
  - `_detect_lang()` uses `model.detect_language(wav)` and chooses only zh or en.
- funasr: `AutoModel(model=name or "paraformer-zh", device="cuda:0"|"cpu", disable_update=True)` plus, for paraformer, `vad_model="fsmn-vad", punc_model="ct-punc"`.
  - `_funasr()` calls `generate(input=wav16k, language="auto", use_itn=True, batch_size_s=60)` and takes `res[0]["text"]`.
  - It then calls `rich_transcription_postprocess`. That function does not exist in 1.0.27, but the existing `try/except Exception` already covers it.
  - Finally it calls `clean_transcript(to_simplified(text))`, which also removes the spaces paraformer puts between CJK characters.
  - In 1.0.27, `ct-punc` maps to `iic/punc_ct-transformer_cn-en-common-vocab471067-large`. That is a different and larger model than the integration package's `punc_ct-transformer_zh-cn-common-vocab272727-pytorch` (`ct-punc-c`).
- `looks_hallucinated()` already drops clips where one character repeats 6+ times or a 2–5 character phrase repeats 4+ times, and clips with known subtitle hallucinations. Proofcheck should cover the *milder* cases.

`voicetwin/data/prepare.py`
- The manifest record (`manifest.jsonl`, one JSON per line) has these fields: `id`, `path` (relative clip wav, **44.1 kHz**), `source`, `source_file`, `start`, `end`, `duration`, `text`, `lang` (`zh`/`en`), `keep`, `split`, `drop_reason`, `seg_mode` (`srt`/`energy`), `asr_done`, `asr = {"engine", "avg_logprob", "no_speech_prob"}`, `manual_keep`, `voiced`, `rate`, `snr`, `clip_ratio`, `_stats_text` and more.
- `asr.avg_logprob` is only set for faster-whisper (funasr leaves it `None`). Clips with `avg_logprob < -1.0` are already dropped as "识别置信度低", so kept clips have `avg_logprob ≥ -1.0`. It is a weak clip-level signal and cannot produce spans.
- Audio is loaded as `load_audio(project.abspath(r["path"]), sr=16000)`. `voicetwin.utils.audio.load_audio` returns contiguous **float32** mono, which is exactly what funasr's numpy path and faster-whisper expect.
- Records with `seg_mode == "srt"` have text from sidecar subtitles. That text may be human-made, so a disagreement there is more likely an ASR error. Still check these records, but you may lower the weight.

`voicetwin/project.py`
- `load_manifest()`, `save_manifest(records)` (atomic tmp+replace), `export_csv()` (columns `MANIFEST_FIELDS_CSV`; `suspect` is not exported) and `import_csv()`.
  - Per R6, `import_csv` must `rec.pop("suspect", None)` when the text changes.
- `project.cache_dir` (`<voice>/cache`) is a good place for an optional per-engine result cache, e.g. `cache/proofcheck_funasr.json` = `{clip_id: {"for_text": text, "alt_raw": ..., "words": [[w, p], ...]}}`. Re-running then only re-diffs clips whose text is unchanged, without decoding again.
- `project.load_lexicon()` returns `(src, dst)` pairs. Feed the `src` terms into the heuristics allowlist (`known_terms`).

`voicetwin/webui/app.py` (today)
- `CLIP_HEADERS = ["#", "id", "保留", "语言", "秒", "文字", "丢弃原因"]`, `gr.Dataframe(headers=..., datatype=["number"]+["str"]*6, interactive=True, wrap=True)`.
- **Existing bug, relevant to R6:** `on_select` maps `evt.index[0]` to `project.load_manifest()[row]`. That breaks as soon as the table is filtered ("只看可能有错的") or sorted. See §4.4 for the fix.
- `do_save` reads positional columns `row[1:]` → `id, 保留, 语言, 秒, 文字, 丢弃原因`. With a new display column, index by **header name** (`table["id"]`, `table["文字"]`) and never read the display column.

---------------------------------------------------------------------------------------------------------------
## 2. funasr 1.0.27 (as in the GPT-SoVITS v2pro integration package)

### 2.1 Version facts (verified)
- `requirements.txt` at GSV tags `20250606v2pro` and `20250422v4` contains `funasr==1.0.27` and `modelscope==1.10.0`. v4 also has `gradio>=4.0,<=4.24.0`, and v2pro has `gradio<5`. Both have `ctranslate2>=4.0,<5`, and `extra-req.txt` has `faster-whisper`. The integration package also contains `pypinyin`, `cn2an`, `jieba` and `opencc` (all in GSV requirements).
- The clone in `scratchpad/ref/GPT-SoVITS` is the *current main branch* (`funasr>=1.3.7`, Fun-ASR-Nano). It does **not** represent the integration package.
- GSV v2pro `tools/asr/funasr_asr.py` uses local model dirs under `tools/asr/models/` when they exist, and otherwise ModelScope ids:
  - ASR: `iic/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch`, `model_revision="v2.0.4"` (plain Paraformer);
  - VAD: `iic/speech_fsmn_vad_zh-cn-16k-common-pytorch` (v2.0.4);
  - punctuation: `iic/punc_ct-transformer_zh-cn-common-vocab272727-pytorch` (v2.0.4).

  They are called as `model.generate(input=file_path)[0]["text"]`.

### 2.2 Model ids (`funasr/download/name_maps_from_hub.py`, 1.0.27)
| alias | ModelScope id | notes |
|---|---|---|
| `paraformer` | `iic/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch` | same model as GSV's local copy; class `Paraformer`; **no timestamps** |
| `paraformer-zh` | `iic/speech_seaco_paraformer_large_asr_nat-zh-cn-16k-common-vocab8404-pytorch` | SeACo-Paraformer: hotword support, **char timestamps** (CifPredictorV3) |
| `paraformer-en` | `iic/speech_paraformer-large-vad-punc_asr_nat-en-16k-common-vocab10020` | English |
| `fsmn-vad` | `iic/speech_fsmn_vad_zh-cn-16k-common-pytorch` | |
| `ct-punc` | `iic/punc_ct-transformer_cn-en-common-vocab471067-large` | big cn-en punctuation model |
| `ct-punc-c` | `iic/punc_ct-transformer_zh-cn-common-vocab272727-pytorch` | GSV's punctuation model |

- `SenseVoiceSmall` has model classes in 1.0.27 (`models/sense_voice`, registered as `SenseVoice`) but no alias. `iic/SenseVoiceSmall` was not tested here.
- A model id is passed to modelscope `snapshot_download` on every load, which needs network access. A local dir that contains `configuration.json` (or `config.yaml` + `model.pt`) is used directly.
  - With `check_latest=True` (the default) a local dir still triggers `check_local_model_is_latest` over the network, wrapped in try/except. Pass `check_latest=False`.
  - The modelscope 1.10 cache is `$MODELSCOPE_CACHE` or `~/.cache/modelscope/hub/<org>/<name>`.
  - **Offline with an id and no local path fails.** funasr prints "Download: … failed!" and the build then breaks. Therefore resolve a local path yourself first.

### 2.3 `AutoModel` behaviour (`funasr/auto/auto_model.py`)
- `AutoModel(**kwargs)` accepts arbitrary kwargs, which are merged into the model config. Model classes take `**kwargs`, so `disable_update=True` is harmless in 1.0.27 (it is needed in ≥1.1 to skip the version check).
- Useful kwargs:
  - `device` (`"cuda:0"`/`"cpu"`; falls back to cpu automatically when CUDA is unavailable, and then forces `batch_size=1`);
  - `disable_pbar=True` (suppresses tqdm);
  - `disable_log=True` (the default);
  - `ncpu` (default 4);
  - `check_latest=False`;
  - `model_revision`, `vad_model`, `punc_model`, `hotword` (at generate time, seaco only);
  - `fp16` — do NOT use it: the model goes to fp16 while the features stay fp32.
- **Process-wide side effects at construction:**
  - `logging.basicConfig(level=INFO)` (a no-op if the root logger already has handlers);
  - `set_all_random_seed(0)` (python, numpy and torch seeds);
  - `torch.set_num_threads(ncpu or 4)`.

  Construct the model lazily, once, and only inside the proofcheck run.
- `generate(input, **cfg)`: when no `vad_model` was given it calls `inference()`, otherwise `inference_with_vad()`. `cfg` is `deep_update`d into `self.kwargs` **persistently**, so the kwargs leak into later calls.
- Input formats (`prepare_data_iterator` / `load_audio_text_image_video`):
  - `np.ndarray`: `torch.from_numpy(x).squeeze()`, assumed to be at `fs` (kwarg, default 16000). Pass **float32, mono, 16 kHz**.
  - `str` path: `torchaudio.load` (resampled to 16 kHz automatically); the key is the file stem.
  - a `list`/`tuple` of arrays or paths is a batch. Keys for numpy items are random (`rand_key_…`).
  - Also accepted: bytes (int16 PCM), URLs, and `.scp`/`.jsonl` lists.
- Output, per input: `{"key": str, "text": str}`. The seaco `paraformer-zh` also returns `"timestamp": [[start_ms, end_ms], …]` (one per output token: a CJK char or an English word).
  - With timestamps, `sentence_postprocess` returns **space-separated tokens** (`"我 们 今 天 讲 python"`). The plain `paraformer` joins CJK without spaces.
  - Consecutive single letters are upper-cased into an abbreviation (`AI`). Other English words are **lower case**.
  - No ITN: numbers come out in Chinese ("二零二四", "百分之五十").
  - No punctuation without `punc_model`.
- **Confidence:** `seaco_paraformer.inference` computes `score = sum(max logit)` per hypothesis but does **not** return it, and there is no per-token probability. Do not monkeypatch it. Treat funasr as a text-only second opinion.
- **Batch edge case:** if every item in a batch decodes to 0 tokens (`torch.max(pre_token_length) < 1`), the model returns `([],)`. The batch then contributes **no results**, so `len(out) != len(inputs)`. Either check lengths and retry one clip at a time, or just call one clip at a time.

### 2.4 Recommended loader and call (works on 1.0.27 and ≥1.1)
```python
import os
from pathlib import Path

PARAFORMER_LOCAL = "tools/asr/models/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch"
SEACO_ID = "iic/speech_seaco_paraformer_large_asr_nat-zh-cn-16k-common-vocab8404-pytorch"   # == "paraformer-zh"

def _paraformer_path(cfg) -> str:
    root = cfg.get_path("backends.gptsovits.root", "") if hasattr(cfg, "get_path") else ""
    cands = []
    if root:
        cands.append(Path(resolve_path(cfg, root)) / PARAFORMER_LOCAL)      # integration package copy (plain paraformer)
    ms_cache = os.environ.get("MODELSCOPE_CACHE") or str(Path.home() / ".cache" / "modelscope" / "hub")
    cands += [Path(ms_cache) / SEACO_ID, Path(ms_cache) / "iic" / Path(PARAFORMER_LOCAL).name]
    for c in cands:
        if (c / "configuration.json").exists() or ((c / "config.yaml").exists() and (c / "model.pt").exists()):
            return str(c)
    return "paraformer-zh"   # needs network (ModelScope); first download is about 1 GB (estimate)

def load_paraformer(cfg, device: str):
    from funasr import AutoModel   # slow import (walks all submodules) -> only here
    path = _paraformer_path(cfg)
    kw = dict(model=path, device="cuda:0" if device == "cuda" else "cpu", disable_update=True,
              disable_pbar=True, disable_log=True, check_latest=False, log_level="ERROR")
    if path in ("paraformer-zh",) or "paraformer-large_asr_nat" in path:
        kw["model_revision"] = "v2.0.4"     # GSV pins this revision; harmless for local dirs
    return AutoModel(**kw)

def paraformer_text(model, wav16k_f32) -> str:
    res = model.generate(input=wav16k_f32)            # one clip; returns [] for silence
    txt = res[0].get("text", "") if res else ""
    return clean_transcript(to_simplified(txt))       # removes spaces between CJK, NFKC, CJK punctuation
```
- Optional batching: `model.generate(input=[w1, w2, …], batch_size=8)`. Accept the result only if `len(res) == len(batch)`, otherwise retry one clip at a time.
- Optional hotwords (seaco `paraformer-zh` only): `model.generate(input=w, hotword="术语1 术语2")`. Lexicon `src` terms could be fed in. Note the setting then sticks in `self.kwargs`.
- Only run paraformer-zh on clips with `lang == "zh"` (or `count_cjk(text) > 0`). For `en` clips use faster-whisper words and heuristics only.
- **Speed (estimates, not measured here: ModelScope and HF are blocked by the sandbox proxy).**
  - Paraformer-large has about 220 M parameters.
  - GPU: RTF about 0.005–0.02, so one hour of clips takes about 1–2 min, plus about 10 s to load the model.
  - CPU, PyTorch, 4 threads: RTF about 0.1–0.3.
  - Both are far faster than faster-whisper large-v3 on CPU (int8 RTF about 0.5–1.5).
  - VRAM is about 1–1.5 GB. Free the Whisper model before loading paraformer in the same process.

---------------------------------------------------------------------------------------------------------------
## 3. faster-whisper 1.1.1 word probabilities (verified in `pkgsrc/fw/faster_whisper/transcribe.py`)

- `Word` dataclass: `start: float, end: float, word: str, probability: float`.
- `Segment` dataclass: `id, seek, start, end, text, tokens, avg_logprob, compression_ratio, no_speech_prob, words: Optional[List[Word]], temperature`.
- `WhisperModel.transcribe(audio, language=None, …, word_timestamps=False, prepend_punctuations="\"'“¿([{-", append_punctuations="\"'.。,，!！?？:：”)]}、", vad_filter=False, hotwords=None, …)` returns `(generator[Segment], TranscriptionInfo)`. The segments are lazy, so iterate them to actually decode.
- `word_timestamps=True` runs `find_alignment()` (ctranslate2 `model.align`, an extra cross-attention/DTW pass). For each word, `probability = np.mean(text_token_probs[word_tokens])`, the mean probability of that word's tokens in the forced alignment.
  - Leading spaces and punctuation are merged into neighbouring words (`merge_punctuations`), so `"".join(w.word for w in words)` equals the segment text.
- Word splitting is `Tokenizer.split_to_word_tokens`. For `zh/ja/th/lo/my/yue` it splits wherever the decoded bytes form valid unicode (`split_tokens_on_unicode`).
  - A Chinese "word" is therefore 1–3 characters, whatever one BPE token covers.
  - **An English word inside zh text may be split into several words** (`" V"`, `"FIX"`, `"ED"`). Otherwise words are split on spaces.
- The words carry the raw Whisper text, which may contain traditional characters, half-width punctuation and spaces. Map them onto `record["text"]` with the same token alignment as the diff (§5.4), not with naive offsets.
- Cost: about 10–20 % on top of a normal transcribe (estimate).
- Thresholds (starting points; tune on real data): p < 0.30 is strong (weight 0.5), 0.30 ≤ p < 0.45 is weak (weight 0.3), and p ≥ 0.45 is ignored. Large-v3 gives typical clear Mandarin characters p > 0.8. Skip pure-punctuation words.

```python
def whisper_words(transcriber, wav16k, lang, cfg):
    transcriber._load()                         # reuse VoiceTwin's loader (device/compute_type/model name logic)
    segs, _info = transcriber._model.transcribe(
        wav16k, language=lang, beam_size=int(cfg.get("beam_size", 5)),
        initial_prompt=cfg.get("initial_prompt_zh") if lang == "zh" else None,
        condition_on_previous_text=False, vad_filter=False, temperature=0.0,
        word_timestamps=True)
    words, texts = [], []
    for seg in segs:                            # generator: decoding happens here
        texts.append(seg.text)
        for w in (seg.words or []):
            words.append((w.word, float(w.probability)))
    return ("".join(texts) if lang == "zh" else " ".join(t.strip() for t in texts)), words
```
- If the primary engine was funasr, `cfg["model"]` is a paraformer name. Use `large-v3` instead, as asr.py does for the reverse switch, and print `hf_mirror_hint()`.
- Also mirror asr.py's language choice: use `record["lang"]` when it is zh or en.

---------------------------------------------------------------------------------------------------------------
## 4. gradio 4.24 Dataframe (source + live test)

### 4.1 Backend (`gradio/components/dataframe.py`)
- `datatype: str | list[str] = "str"`. The docstring lists "str", "number", "bool", "date" and "markdown", but the code's default-value table also contains **"html"** (`values = {"str","number","bool","date","markdown","html"}`). Any other string raises `KeyError` when `row_count > 0`.
- Other relevant parameters: `latex_delimiters` (markdown columns only; default `$$…$$`), `wrap`, `line_breaks` (markdown only), `column_widths`, `height`, and `interactive`. There is **no per-column or per-cell `editable`**.
- `Styler` values: `postprocess` extracts `metadata = {"display_value": [[...]], "styling": [["css"]]}`. With `interactive=True` it warns "Cannot display Styler object in interactive mode…".
- `SelectData` in 4.24 has only `.index` (`[row, col]`), `.value` (the raw cell value, i.e. the HTML/markdown *source* for such cells) and `.selected`. **There is no `row_value`** (that arrived later).
- `.change` fires once when the component mounts (observed live) and after every edit or sort.

### 4.2 Frontend (`_frontend_code/dataframe/shared/EditableCell.svelte`, `Table.svelte`)
```svelte
{#if edit}<input bind:value={_value} … />{/if}          <!-- _value = raw cell value -->
<span …>
  {#if datatype === "html"}      {@html value}            <!-- NO sanitizing -->
  {:else if datatype === "markdown"} <MarkdownCode message={value.toLocaleString()} {latex_delimiters} {line_breaks} chatbot={false}/>
  {:else} {editable ? value : display_value || value} {/if}
</span>
```
- `MarkdownCode` (`_frontend_code/markdown/shared/MarkdownCode.svelte`) runs `marked.parse()` and then `DOMPurify.sanitize()`, with `sanitize_html=true` by default. DOMPurify keeps `<span style="…">`.
- `Table.svelte`: `editable` comes from `interactive` and covers the whole table (`start_edit` returns early only when `!editable`). The `<td style={styling?.[i]?.[j]}>` binding exists, but live, Styler colours did **not** show in interactive mode (see 4.3).
- Sorting by clicking a header reorders `data` and then fires `change`. The backend value is therefore in display order, and `evt.index[0]` refers to the same order, so reading the id from the table value is consistent.

### 4.3 Live test results (`proofproto/app.py`, gsv39 python, port 7880, chromium via playwright)
| variant | result |
|---|---|
| A: `datatype=[…,"markdown"]`, interactive, escaped text + red span | **renders correctly** (`df_md.png`). Text like `1. 首先打开 *设置* 页面_然后` stays literal because the markdown chars are entity-escaped. Rows are the same height as plain rows. |
| B: `datatype=[…,"html"]`, interactive | renders the same (`df_html.png`) |
| C: `"html"` with **unescaped** `<img src=x onerror=…>` | **script executed** (`window.__xss == 2`: once in the hidden measuring row, once in the visible row) → html is unsanitized |
| G: `"markdown"` with unescaped text | `<img>` kept but `onerror` stripped (no execution); `<b>` rendered bold; `*设置*` became italic → escaping is mandatory |
| editing a markdown or html cell (double-click) | the `<input>` shows the **raw markup** `我们今天讲 <span style="color:#dc2626;…">VFIXED</span> …` (`df_md_editing.png`); typing "ZZ" + Enter sent the raw string + "ZZ" to the backend `change` |
| D: pandas Styler, `interactive=True` | **no colours** (td style is only the width) + warning |
| E: pandas Styler, `interactive=False` | whole-cell colours work (`background-color: rgb(254,226,226)`); there is no way to colour individual characters |
| F: plain text with 【】 | works (`df_plain.png`) |
| select on the markdown cell | `evt.index=[1,3]`, `evt.value` = raw markup; `table.iloc[row]["id"]` → `c_0002` ✔ |

The server was started with a pid file (`proofproto/server.pid`) and stopped with `kill $(cat server.pid)`. Port 7880 is free again.

### 4.4 Recommended UI wiring (U2)
```python
CLIP_HEADERS = ["#", "id", "保留", "语言", "秒", "文字", "可能有错（红色）", "丢弃原因"]
clips = gr.Dataframe(headers=CLIP_HEADERS,
                     datatype=["number", "str", "str", "str", "str", "str", "markdown", "str"],
                     interactive=True, wrap=True, latex_delimiters=[])

def on_select(voice_name, table, evt: gr.SelectData):
    row = evt.index[0] if isinstance(evt.index, (list, tuple)) else evt.index
    cid = str(table.iloc[int(row)]["id"])                      # never index the manifest by row number
    rec = {r["id"]: r for r in wf.Project(cfg, voice_name).load_manifest()}.get(cid)
    ...  # audio path, render_diff_html(rec["text"], rec["suspect"]["alt"]), enable "✅ 采用建议" iff alt
clips.select(on_select, [voice, clips], [clip_audio, diff_html, adopt_btn, selected_id_state])
```
- `do_save`: `for _, r in table.iterrows(): rid = str(r["id"]); text = r["文字"]; keep = r["保留"]; …`. **Never read "可能有错（红色）"**: it is display-only and may contain user-mangled markup. Rebuild the table from the manifest after saving.
- Put the note "这一列只用来看，改字请改「文字」列（双击会看到格式代码，不用管）" next to the honest note from R6.
- Show the detail panel (`render_diff_html`) in a `gr.HTML` (raw, so the function must escape) or a `gr.Markdown` (sanitized). Both work in 4.24.
- Keep the selected clip id in a `gr.State` for "✅ 采用建议", so the action does not depend on the row index.
- The filter checkbox rebuilds the table from the manifest (`[r for r in recs if r.get("suspect")]`). The `#` column stays the running row number of the displayed rows, and `id` is the key.

### 4.5 Markdown-safe escaping (verified to render literally in both "markdown" and "html" cells)
```python
import html
MD_ESC = {c: "&#%d;" % ord(c) for c in "\\`*_{}[]()#+-.!|~>$"}
def _esc(s: str) -> str:
    return "".join(MD_ESC.get(c, c) for c in html.escape(s, quote=True))
RED = '<span style="color:#dc2626;font-weight:700;background:#fee2e2">'
def render_marked(text, spans):
    out, pos = [], 0
    for s, e in merge_spans([[max(0, s), min(len(text), e)] for s, e in spans]):
        out += [_esc(text[pos:s]), RED, _esc(text[s:e]), "</span>"]; pos = e
    out.append(_esc(text[pos:]))
    return "".join(out)
```
- Escaping `$` as `&#36;` keeps MarkdownCode's KaTeX check (`value.includes("$$")`) from firing. Passing `latex_delimiters=[]` is belt and braces.

---------------------------------------------------------------------------------------------------------------
## 5. Character-level diff for mixed Chinese and English (prototype: `proofproto/diffproto.py`)

### 5.1 Normalization and tokenization (keeps offsets into the ORIGINAL text)
Rules, applied per character of the original string with `unicodedata.normalize("NFKC", ch).lower()`:
- **Latin run** `[a-z0-9']` that starts with a letter becomes one token, the lower-cased word. This handles case and full-width letters (NFKC), and `GPT4`/`MP3` stay single tokens.
- **Number run**: digits, Chinese numerals `零〇一二两三四五六七八九十百千万亿`, `.`/`%`, `点` between numerals, and `百分之X`. It becomes the single token `#`, so 2024 = 二零二四, 50% = 百分之五十 and 3.5 = 三点五.
  - Both sides are tokenized the same way, so a CJK numeral inside a word ("统一", "一下") is harmless.
  - Limitation: a difference *inside* a number run (三十 vs 四十) is not seen.
- **CJK char** becomes one token, converted to simplified per character (zhconv `convert(ch, "zh-cn")`; identity if zhconv is missing).
- **Punctuation, whitespace and symbols** are dropped (full and half width alike, since NFKC is applied first).
- Clean B (the second engine) with `clean_transcript(to_simplified(b))` before diffing. That removes paraformer's spaces between CJK characters and makes splicing clean.

Token = `(key, start, end)`. Running `SequenceMatcher(None, [k for k,_,_ in A], [k for k,_,_ in B], autojunk=False)` and then `get_opcodes()` gives token ranges, and `A[i1][1]..A[i2-1][2]` is the character span in the original text.
- Set **autojunk=False**: the default junk heuristic misbehaves on sequences longer than 200 tokens with frequent tokens.

### 5.2 Opcode handling
- `equal`: nothing.
- `replace`/`delete`: span = `[A[i1].start, A[i2-1].end]`. The suggestion splices in B's *original* substring `B_text[B[j1].start : B[j2-1].end]`, or nothing for a delete.
- `insert` (A lacks something): highlight the neighbouring A token (the previous one, else the next) so the user sees where. The splice inserts at `A[i1-1].end`.
- Filters (verified in the prototype):
  1. `"".join(a_keys) == "".join(b_keys)`: only spacing or word-boundary differs (`VFIXED` vs `v fixed`) → ignore. The heuristics still catch `VFIXED`.
  2. An insert or delete made only of fillers or particles (`嗯呃额啊哦噢唉诶欸哎呀吧呢嘛啦哈`, `那个/这个/就是/然后`, `的地得了着过`), at most 2 characters → ignore. Whisper drops disfluencies, and paraformer keeps them.
  3. **Same pinyin with the same tone** (`pypinyin.lazy_pinyin(x, style=Style.TONE3, neutral_tone_with_five=True)`, available in the integration package) on an equal-length CJK replace → `homophone`, not flagged. TTS training is phoneme-based, so 他/她, 的/得 and 在/再 do not matter. Without pypinyin, fall back to a tiny table (`他她它祂 的地得 在再 做作 象像 须需 账帐 分份 即既 副付`).
  4. A side all Latin and B side all CJK (Python vs 派森, the vs 的) → `en_vs_cjk`: weak evidence, weight 0.25 or none, and **not spliced into `alt`** unless a heuristic also flagged that English word. That rule turns `whose`→`户字` and `the`→`的` into real suggestions.
  5. `ratio() < 0.5` → treat as total mismatch: span = whole text, reason "两次识别结果差别很大，整句可能不对", `alt` = the full cleaned B text. Skip this when B is empty, which usually means the second engine heard nothing.
- `alt` = A with the kept edits spliced in from the end to the start (so earlier offsets stay valid), then `clean_transcript()`. This keeps the user's punctuation, English case and Arabic numerals. If `alt == text`, set `alt = ""`.

Prototype outputs (`python3 proofproto/diffproto.py`):
```
这个户字的意思是whose，大家记一下。 vs 这个户字的意思是户字大家记一下
  → spans [[8,13]] 'whose', alt '这个户字的意思是户字，大家记一下。', score 0.6
大家好，今天天气不错 the 我们开始上课。 vs ...不错的我们...
  → spans 'the', alt '大家好，今天天气不错的我们开始上课。'
2024年我们讲了50%的内容。 vs 二零二四年...百分之五十...   → no diff
那个，我们打开Python的设置页面。 vs 嗯那个...派森...       → clean (filler + en_vs_cjk ignored)
他说的在理，我们再看一下。 vs 她说得在理我们在看一下       → clean with pypinyin (homophones)
我们今天讲十个函数。 vs 我们今天讲是个函数              → '十' flagged, alt '…是个…'
```

### 5.3 Rendering both sides (`render_diff_html(text, alt)`)
Use the same opcodes. Line 1 is "识别 A：" with A's spans in red (`#dc2626` on `#fee2e2`). Line 2 is "识别 B：" with B's spans `B[j1].start..B[j2-1].end` in green (`#15803d` on `#dcfce7`). Escape every piece with `_esc`, wrap the lines in `<div>`, and show a muted "（没有建议）" when `alt == ""`.

### 5.4 Mapping Whisper low-probability words onto `record["text"]`
```python
W = "".join(w for w, _p in words)                  # equals Whisper's raw text
ranges = cumulative (start, end, p) of each word in W
wt, tt = tokenize(W), tokenize(record["text"])
sm = SequenceMatcher(None, keys(wt), keys(tt), autojunk=False)
w2t = {blk.a + k: blk.b + k for blk in sm.get_matching_blocks() for k in range(blk.size)}
for (s, e, p) in ranges with p < 0.45:
    idx = [i for i, t in enumerate(wt) if t.start < e and t.end > s and i in w2t]
    if idx: span = (tt[w2t[idx[0]]].start, tt[w2t[idx[-1]]].end)
merge overlapping spans, keep min p      # fixes " V"/"FIX"/"ED" pieces
```
- Verified: `VFIXED` came out as one span with p = 0.20.
- Words that fall into non-matching regions are dropped, because the text there differs anyway.

---------------------------------------------------------------------------------------------------------------
## 6. Heuristics for typical Whisper mishearings in Chinese lecture transcripts

Apply these only when the text is Chinese (`count_cjk(text) >= 4`). The prototype's `heuristics()` returns `(start, end, reason, weight)`.

### 6.1 Latin tokens inside Chinese text (`[A-Za-z][A-Za-z']*`)
1. **ALL-CAPS, length ≥ 3**, not in `ACRONYMS ∪ lexicon terms ∪ Roman numerals` → "「VFIXED」像是听错的英文", weight 0.7.
   - Tokens that contain digits (`GPT4`, `MP3`, `H264`) are never matched, because the regex only takes letters.
   - Optional: if the same ALL-CAPS token appears in at least 3 different clips, lower the weight to 0.4. It is probably a real term the teacher uses, but keep it so a second-engine disagreement can still flag it.
2. **Phonetic-confusable English word**, isolated between CJK characters or CJK punctuation (looking past spaces): `whose who how she so say the one way why hey yeah me my bye buy no know now show sure shoe see sea tea door low law lay lie pie pay tie die hi yo ya ma na la ha he her here high hum oh ah wow` → "中文里夹着「whose」，可能是把中文听成了英文", weight 0.6.
   - Examples: 户字 → whose, 的 → the, 是/谁 → she, 说/所 → so, 万 → one, 好 → how.
3. **Garbage-looking Latin**: mixed case twice inside a word (`[a-z][A-Z].*[a-z][A-Z]`, e.g. `wHoOz`; ordinary camelCase like `iPhone`, `YouTube` and `PowerPoint` does not match), no vowels and length ≥ 4, or length > 15 → "像是乱码", weight 0.6.
4. Non-Chinese scripts in a zh clip: kana `぀-ヿ`, Hangul, Cyrillic, `�`, private-use → "出现了不该有的外文字符", weight 0.8.

### 6.2 Repetitions (on the punctuation-free token stream; spans cover the *repeated copies*, not the first)
- One character repeated ≥ 3 times (not 哈呵嘻啦嗯, not `#`) → weight 0.5.
- A 2–3 token unit repeated ≥ 3 times → weight 0.5.
- A unit of ≥ 4 tokens repeated ≥ 2 times ("我们来看一下我们来看一下") → weight 0.6.
- Do **not** flag plain AA/ABAB reduplication: 看看, 试试, 慢慢, 谢谢, 常常, 研究研究… (allowlist `REDUP_OK`), and a single "这个这个" stutter. These are usually what was actually said.
- `looks_hallucinated()` already drops the extreme cases (6+ characters, 4+ phrase repeats).

### 6.3 Acronym allowlist (upper-case compare; extend it with `project.load_lexicon()` sources)
```
AI API APP CPU GPU NPU TPU RAM ROM SSD HDD USB HDMI WIFI PDF PPT PPTX DOC DOCX XLS XLSX CSV TXT JPG JPEG PNG GIF SVG
MP3 MP4 AVI MOV HTML CSS JSON XML SQL URL HTTP HTTPS FTP SSH IP TCP UDP DNS VPN LAN WAN NAS IT IOS OS PC CEO CFO CTO COO
HR KPI OKR ROI GDP CPI PPI PMI IPO ETF VIP DIY FAQ CAD BIM UI UX ID OK QQ VR AR MR XR IOT LLM GPT AIGC NLP CNN RNN LSTM
GAN TTS ASR OCR SDK IDE ATM NBA CBA CCTV BBC USA UK EU UN WHO WTO NASA MBA PHD GRE GMAT IELTS TOEFL SAT DNA RNA PCR
MRI ECG BMI LED LCD OLED PCB CNC PLC ERP CRM SAAS SEO SEM GPS SIM SMS APK EXE DLL BUG CMD PPP GNU AWS GCP RGB CMYK
DPI FPS HDR PS PR AE AM PM ABC TV DVD CD NFC PIN QR OA OTA SOP PDCA SWOT PEST MECE STEM STEAM AP IB
SUM IF IFS AND OR NOT AVERAGE COUNT COUNTA COUNTIF COUNTIFS SUMIF SUMIFS VLOOKUP HLOOKUP XLOOKUP INDEX MATCH LEFT RIGHT
MID LEN TRIM ROUND MAX MIN IFERROR TEXT DATE TODAY NOW RANK
```
Roman numerals are matched with a regex, e.g. `^(?=[IVXLCDM]+$)M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$`. The Excel function names are included because lecture recordings about spreadsheets are common.

### 6.4 Evidence weights and decision (noisy-OR; flag if score ≥ 0.45)
| evidence | weight |
|---|---|
| second-engine diff region (CJK substitution with different pinyin, or insertion/deletion of non-fillers) | 0.6 each |
| total mismatch (`ratio < 0.5`, B non-empty) | 0.7 (whole text) |
| ALL-CAPS non-acronym | 0.7 (0.4 if frequent across clips) |
| non-Chinese script / `�` | 0.8 |
| confusable English word | 0.6 |
| garbage Latin | 0.6 |
| repetition | 0.5–0.6 |
| Whisper word p < 0.30 / 0.30–0.45 | 0.5 / 0.3 |
| `en_vs_cjk` diff alone | 0.25 (not flagged by itself) |
| optional clip-level `asr.avg_logprob < -0.6` | +0.15, only when other spans exist (no spans of its own) |

`record["suspect"] = {"spans": merged [[s,e],...], "alt": str, "reasons": unique list in order, "score": round(score, 3)}`. Remove the key when the score is below the threshold or there are no spans.

---------------------------------------------------------------------------------------------------------------
## 7. Engine selection and the run loop (for U8)

```python
import importlib.util
def _has(mod): return importlib.util.find_spec(mod) is not None

def available_checker(cfg) -> Tuple[str, str]:
    primary = str(cfg.get_path("prepare.asr.engine", "faster-whisper"))
    fun = _has("funasr") and _has("modelscope") and _has("torch")
    fw = _has("faster_whisper")
    if primary != "funasr" and fun:
        return "funasr", "用阿里 FunASR（paraformer-zh）把中文片段再听一遍，对比两次结果"
    if primary == "funasr" and fw:
        return "faster-whisper", "用 faster-whisper 再听一遍，对比两次结果，并标出没把握的字"
    if fw:
        return "faster-whisper-words", "没有第二个识别引擎：用 faster-whisper 重新识别，标出没把握的字"
    return "", "没有可用的识别引擎，只用规则检查（准确度较低）"
```
- The engine names are suggestions. Keep them stable, because the UI and the notes show them.
- Loop: `recs = project.load_manifest()`, then `todo = [r for r in recs if r.get("text") and (r.get("keep", True) or not only_kept)][:limit]`. For each clip:
  - call `check_cancel()` (guarded import from U1);
  - `wav16, _ = load_audio(project.abspath(r["path"]), sr=16000)`;
  - get B (and the words) from the engine;
  - run `build_suspect(r["text"], B, words, known_terms)`;
  - set or pop `r["suspect"]`;
  - call `progress(i / n, f"检查 {i}/{n}")` every clip;
  - catch `Exception` per clip (log it, count it in the note, continue);
  - `save_manifest` every 20 clips and at the end.
- When no engine is available, the loop runs heuristics only. That is fast (no audio decoding), and the engine is reported as `""`.
- Apply funasr to `lang == "zh"` clips only. For `en` clips with funasr as the only second engine, use heuristics only, and say so in `note`.
- Load only one model at a time. After finishing, `del model`, then `gc.collect()`, then `torch.cuda.empty_cache()` inside a try.
- `apply_suggestion` sets `text = alt`, `lang = detect_lang(alt)`, recomputes `rate` the way `import_csv` does, pops `suspect`, and re-exports the CSV.

### Tests (`tests/test_proofcheck.py`; no models needed, and must pass without zhconv or pypinyin in the 3.11 env)
- tokenize: offsets round-trip (`text[s:e]` gives the token source); full-width `ＡＢＣ`→`abc`; `2024`/`二零二四`/`百分之五十`→`#`; punctuation is dropped.
- diff: the prototype's cases above (VFIXED spacing ignored, whose/户字, the/的, Python/派森 ignored, filler ignored, 十/是 flagged), `alt` keeps the user's punctuation, and `ratio < 0.5` marks the whole text.
- heuristics: `VFIXED`/`WHOOZ` flagged; `VLOOKUP`/`GPU`/`III`/`GPT4` not; kana flagged; 看看 not flagged; "我们来看一下我们来看一下" flagged.
- `render_marked`: escapes `<b>`, `*`, `1.`, `$$`, wraps the spans, and merges overlapping spans. Output for empty spans equals `_esc(text)`.
- `low_prob_spans` with fake word objects (traditional characters + split Latin pieces).
- `find_suspects` with a monkeypatched recognizer: it writes or removes `suspect`, saves the manifest, survives one clip raising, and reports progress per clip. `available_checker` with `find_spec` monkeypatched.

---------------------------------------------------------------------------------------------------------------
## 8. Pitfalls checklist
- Do not use `datatype="html"` with any text that came from a transcript or CSV. It is unsanitized; the XSS probe proved it.
- The markdown display column is editable in 4.24 and shows raw markup on double-click. Ignore it on save.
- Map rows to clips by the `id` column, never by row index. Filtering and header sorting change the order.
- funasr 1.0.27 has no confidence output, and the seaco `paraformer-zh` output is space-separated and lower case without punctuation. Always clean it, and never offer it raw as `alt`.
- Offline: always pass a local model dir to funasr when one exists, and pass `check_latest=False`.
- funasr `AutoModel` changes global logging, random seeds and torch threads. Build it lazily, once per run.
- Whisper zh word pieces can split English words. Merge them before mapping.
- Do not report homophones (same pinyin and tone) as errors: they do not affect training. This explains why the note says "不一定真错".
