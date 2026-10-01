export const meta = {
  name: 'manual-v016',
  description: 'Update the PDF manual HTML chapters for the v0.1.6 UI (4 disjoint file groups), then cross-check',
  phases: [
    { title: 'Update', detail: 'one agent per disjoint group of manual chapter files' },
    { title: 'Check', detail: 'independent accuracy review of each group against the real UI code' },
  ],
}

const FACTS = '<草稿目录>/v016_doc_facts.md'
const SRC = '<仓库>/docs/manual/src/'

const GROUPS = [
  { key: 'front', files: ['01_cover.html', '01_front.html', '02_ch01_02.html', '03_ch03.html'],
    focus: 'Cover + preface: version v0.1.6 everywhere; preface "关于截图" must say screenshots come from a demo computer (RTX 4070 12GB, demo voice) so similarity numbers shown are only examples. Ch1: feature description (what it does, how it becomes "like you", honest limits incl. calibrated similarity %, 85% elimination, absolute-silence pauses, 完美 tier two versions), 1.4 flow overview (mention progress bars, GPU badge, ⑤ 鉴别 optional). Ch2: GPU check can now also be read from the green/red badge at the top of the page once installed; driver advice. Ch3: install steps; installer now also installs noisereduce; 3.5/3.6 missing models can be downloaded from 🩺 环境检查 → "⬇️ 下载缺少的模型" (keep the command line as alternative); add a short "从旧版本升级" subsection (upgrade = extract over D:\\VoiceTwin replacing files → re-run install_windows.bat → 1 → path; workspace/voices/models are kept).' },
  { key: 'prep', files: ['04_ch04_05.html', '05_ch06_07.html'],
    focus: 'Ch4 material prep (mostly unchanged; keep). Ch5 start program + interface overview: new header with version, GPU badge (00_gpu_badge.png), voice library (00b_voice_library.png), six tabs, single-instance launcher behaviour, QuickEdit note, and a NEW section explaining the progress bar and its colours with figure 11_progress_states.png (and 02a_progress_running.png), stop button needs two clicks within 5 s, refresh/close page does not stop the task, red bar has 原因/怎么办 and the 详细过程 log accordion (09_error_red.png). Use 01_prepare_form.png as the overview figure. Ch6 prepare: progress bar instead of reading the log, done summary (02_prepare_done.png), clip count line with total. Ch7 proofreading: rewrite 7.2 for the automatic typo finder (03a_proofcheck_done.png, 03_proofread.png): 🔍 自动查找可能的错字, red marks + suggestions column, 只看可能有错的, click row → playback + comparison panel, ✅ 采用建议, double-click to edit 文字, 保留 是/否, 保存修改, 🔄 重新载入; remove the old "载入片段列表" button and ✔/✘ wording; Excel route: close Excel before reloading.' },
  { key: 'train-gen', files: ['06_ch08_09.html', '07_ch10_12.html'],
    focus: 'Ch8 training: automatic VRAM-aware plan shown before start (04a_train_plan.png), progress bar (04b_train_running.png), done (04_train_done.png) with "像你本人 xx%", OOM auto-retry, old runs archived, DPO explanation (auto = off, why; how to turn on in 高级设置 or `voicetwin train --dpo on`), 8.7 advanced settings labels exactly as app.py. Ch9 generation: 9.2 settings with 05_generate_form.png — the five quality tiers as a table (快速/均衡/最好/极致/完美, default chosen by VRAM), honest note, speed slider (05b_speed_slider.png; left faster, right slower, ±30, recommend −15…+15, ▶ 试听语速, only speed changes); 9.3 progress (05c_generate_running.png only if it exists) and result (06_generate_done.png); 9.4 result table "像你本人（%）" (06d_result_table.png) with calibration meaning and the 85% rule; NEW subsection for the 完美 two versions (06c_two_versions.png, ⭐ 推荐, 最终使用哪个版本, both saved); explicit statement that output has only the voice, no background/noise floor, pauses absolute digital silence; downloads (06b_download.png); 9.5 redo; 9.6 file locations incl. 📂 打开保存文件夹. Ch10 script writing: keep, but fix anything about pause audio content (pauses are absolute silence; lengths follow habits) and quality names. Ch11: 11.5 post-processing must NOT recommend adding room tone/background; say the output is already clean with silent pauses and loudness-matched. Ch12 checking: 12.1 now "④ 试试像不像（可选）" (07_evaluate.png); NEW ⑤ 鉴别 machine verification (08_verify.png) and the built-in audience blind test (08b_blind_test.png) incl. offline answer-card grading; keep honest caveats.' },
  { key: 'adv', files: ['08_ch13_15.html', '09_appendix.html'],
    focus: 'Ch13 tips: tier names (完美 instead of best), 13.3 config.yaml keys must match voicetwin/default_config.yaml (check save_every/if_dpo auto, quality tiers, similarity min_pct 85 etc. — only document keys that really exist), 13.5 multiple voices → 🎙️ 我的声音库. Ch14 CLI: commands/options exactly as voicetwin/cli.py (narrate -q fast|balanced|best|max|perfect, --speed/--faster/--slower, train --dpo, download-models, webui port auto-pick). Ch15 FAQ: add/adjust entries — red GPU badge, red progress bar (原因/怎么办, copy 详细过程), amber stalled bar, "现在正在「…」，同一时间只能做一件事", OOM auto retry then batch 2, two versions sound the same, similarity looks low (calibrated %, MFCC fallback note), "我要求完全没有背景音" answer (already guaranteed), clicking the black window freezes (QuickEdit now disabled; press Enter if 选择 appears), second double-click opens the existing page, port busy → another port. Remove entries about removed UI. Appendix: quality tier table (five tiers), any v0.1.3 mentions → v0.1.6, E.1 version table, changelog: add a v0.1.6 row at the top summarising the user-visible changes (progress bars with colours/ETA, always-visible GPU status, numbering + totals everywhere, voice library, automatic max-quality training plan, 完美 tier with two versions and recommendation, calibrated similarity % with 85% elimination, absolute silence, speed slider, red typo highlighting with suggestions, ⑤ 鉴别 + blind test, plain-Chinese errors, launcher improvements). Note versions 0.1.4/0.1.5 were never released, do not invent rows for them.' },
]

const UPDATE_SCHEMA = {
  type: 'object',
  properties: {
    files_changed: { type: 'array', items: { type: 'string' } },
    images_referenced: { type: 'array', items: { type: 'string' } },
    summary: { type: 'string' },
    open_questions: { type: 'array', items: { type: 'string' } },
  },
  required: ['files_changed', 'images_referenced', 'summary', 'open_questions'],
}

const CHECK_SCHEMA = {
  type: 'object',
  properties: {
    problems_fixed: { type: 'array', items: { type: 'string' } },
    remaining_concerns: { type: 'array', items: { type: 'string' } },
  },
  required: ['problems_fixed', 'remaining_concerns'],
}

const results = await pipeline(
  GROUPS,
  g => agent(
    `You are updating part of a Chinese PDF user manual (HTML source) for the VoiceTwin (声音分身) Windows app from v0.1.3 to v0.1.6.\n\n` +
    `FIRST read the facts/rules file ${FACTS} completely — it is the source of truth and lists the available screenshots.\n` +
    `Then read the files you own and edit them in place with the Edit tool. You own ONLY these files (in ${SRC}): ${g.files.join(', ')}. ` +
    `Do not modify any other file. Also read docs/manual/src/00_head.html (CSS, read-only) to know which classes exist.\n\n` +
    `Focus for your files:\n${g.focus}\n\n` +
    `Verify every UI label/button text you write against <仓库>/voicetwin/webui/app.py (grep for it) and CLI/config facts against voicetwin/cli.py and voicetwin/default_config.yaml. ` +
    `Check image files exist with ls <仓库>/docs/manual/images before referencing them (05c_generate_running.png, 00b_voice_library.png, 08b_blind_test.png, 09_error_red.png, 10_doctor.png are being captured right now; you may reference them — they will exist before the PDF is built). You can view screenshots with the Read tool to write accurate captions. ` +
    `Keep the existing HTML conventions, heading ids, chapter numbering and figure numbering style. Keep growth modest. Write natural, simple Simplified Chinese for a non-technical teacher. ` +
    `Do not run git commands and do not build the PDF. When done, return the structured summary.`,
    { label: `update:${g.key}`, phase: 'Update', schema: UPDATE_SCHEMA }),
  (upd, g) => agent(
    `Independent accuracy check of a just-edited part of a Chinese user manual (HTML) for VoiceTwin v0.1.6. Files: ${g.files.map(f => SRC + f).join(', ')}.\n` +
    `Read the facts file ${FACTS} first. Then read the files and verify, claim by claim: (1) every button/label/tab/table header text matches <仓库>/voicetwin/webui/app.py exactly; ` +
    `(2) CLI options and config keys match voicetwin/cli.py and voicetwin/default_config.yaml; (3) quality tier behaviour matches voicetwin/synth/engine.py QUALITY_LABELS/QUALITY_PRESETS; ` +
    `(4) no text promises 100% identical voice, and nothing suggests adding background noise/room tone (absolute silence between sentences is a fixed requirement); ` +
    `(5) no leftover v0.1.3-only UI (e.g. "载入片段列表" button, ✔/✘ keep marks, "④ 评估相似度" tab name, balanced/best English tier names presented as the UI labels, version v0.1.3 as current); ` +
    `(6) every <img src="../images/X.png"> exists in <仓库>/docs/manual/images (05c_generate_running.png, 00b_voice_library.png, 08b_blind_test.png, 09_error_red.png, 10_doctor.png may still be being captured; treat them as existing) and figure numbers are sequential within each chapter; (7) HTML is well-formed (balanced tags). ` +
    `Fix every real problem directly in these files with the Edit tool (do not touch other files, no git). The updater reported: ${JSON.stringify(upd)}. Return what you fixed and any remaining concerns.`,
    { label: `check:${g.key}`, phase: 'Check', schema: CHECK_SCHEMA }).then(chk => ({ group: g.key, update: upd, check: chk })),
)
return results.filter(Boolean)
