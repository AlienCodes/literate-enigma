export const meta = {
  name: 'voicetwin-v015-build',
  description: 'Implement VoiceTwin v0.1.5: progress bars, GPU status, numbering, voice library, quality tuning, typo highlighting, UX fixes — research, parallel units in worktrees, integration with browser test',
  phases: [
    { title: 'Research', detail: 'GPT-SoVITS quality tuning; ASR cross-check + gradio 4.24 table rendering' },
    { title: 'Core', detail: 'U1 progress core, U5 errors, U9 GPU status, U6 installer/startup (parallel)' },
    { title: 'Features', detail: 'U2 web UI, U3 workflows/synth, U4 backends, U8 proofcheck (parallel)' },
    { title: 'Integrate', detail: 'merge all branches, full tests on both envs, real-browser smoke test under gradio 4.24' },
  ],
}

const SP = '<草稿目录>'
const REPO = '<仓库>'
const BASE = 'b518011'

const COMMON = `You are implementing part of VoiceTwin v0.1.5 (Windows voice-cloning tool for a non-technical Chinese teacher). Main repo: ${REPO} (base commit ${BASE} on master).
READ FIRST, fully: ${SP}/v015_requirements.md (user's explicit requirements R1-R7 and the rules) and the audit plan JSON ${SP}/ux_audit.json (plan.units[*] items with specs; plan.interfaces A-J are binding contracts). Where they conflict, v015_requirements.md wins. Version is 0.1.5.
You are running in an isolated git worktree. At the very start run: git checkout -b BRANCH (name given below). Commit your work on that branch (git add -A && git commit) with a clear message ending with the two lines:
Co-Authored-By: Claude <模型> <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01PwXvLynw8dAvAfJEJKMB77
Do NOT push. Do NOT edit files outside your ownership list. Implement all 'must' items of your unit and as many 'should' items as you can do well; skip 'later'. Write tests. Run tests as described in the rules section of v015_requirements.md (both the python3.11 env and the gradio-4.24/py3.9 venv with PYTHONPATH=$PWD). Before finishing, re-read your diff adversarially (python 3.9 compat, gradio 4.24 compat, thread safety, Chinese text clarity) and fix problems.
Your final answer must be JSON-like text: branch name, final commit sha (git rev-parse HEAD), files changed, what was implemented (must/should titles), what was skipped and why, test results (counts), and any interface deviations other units must know about.`

const RESULT = {
  type: 'object',
  properties: {
    branch: { type: 'string' }, sha: { type: 'string' },
    files: { type: 'array', items: { type: 'string' } },
    implemented: { type: 'array', items: { type: 'string' } },
    skipped: { type: 'array', items: { type: 'string' } },
    tests: { type: 'string' },
    deviations: { type: 'string', description: 'interface changes/notes other units or the integrator must know' },
  },
  required: ['branch', 'sha', 'files', 'implemented', 'skipped', 'tests', 'deviations'],
}

phase('Research')
const researchQuality = agent(`Research task (no code edits in the repo). Read ${SP}/v015_requirements.md section R5 and the current training/inference code: ${REPO}/voicetwin/backends/gptsovits.py (train params: batch_size, sovits_epochs, gpt_epochs, save_every, text_low_lr_rate, if_dpo, infer params), ${REPO}/voicetwin/backends/base.py (gpu_memory_gb), ${REPO}/voicetwin/synth/engine.py and select.py (candidates, ASR check, scoring), ${REPO}/voicetwin/default_config.yaml. Then research GPT-SoVITS (RVC-Boss/GPT-SoVITS) v2Pro/v2ProPlus best practices using web search/fetch (official GitHub README/docs/wiki/issues, the yuque docs, reputable community guides): recommended SoVITS/GPT epochs vs dataset size, batch size vs VRAM (e.g. 6/8/12/16/24 GB), whether DPO (if_dpo) helps and its VRAM/time cost, text_low_lr_rate, overfitting signs, inference top_k/top_p/temperature/repetition_penalty recommendations, aux reference audio (inp_refs) for v2Pro, speed_factor, sample_steps (v3/v4 only), parallel/batch inference. Write ${SP}/research_quality.md with: a table of concrete recommended settings per VRAM tier (low<8GB, mid 8-15.9, high>=16) for training AND inference, each with confidence (high/medium/low) and source URLs; a recommended 'max' synthesis tier (candidates, ASR thresholds, retries, aux_refs); and things NOT to do. Return a short summary.`, { label: 'research:quality', phase: 'Research' })

const researchProof = agent(`Research task (no code edits in the repo). Read ${SP}/v015_requirements.md section R6, ${REPO}/voicetwin/data/asr.py (how faster-whisper and funasr are loaded/used), ${REPO}/voicetwin/data/prepare.py (where ASR results/avg_logprob are stored in the manifest) and ${REPO}/voicetwin/project.py. Determine and document precisely: (1) funasr 1.0.x AutoModel usage for paraformer-zh as installed in the GPT-SoVITS v2pro integration package (funasr 1.0.27): model ids, whether timestamps/char confidence are available, input formats (numpy 16k), batch usage, typical speed; use pip download/inspection of funasr==1.0.27 sources if network allows (pip download funasr==1.0.27 --no-deps -d /tmp/x and read the code), else web docs. (2) faster-whisper 1.1.1 word-level probabilities API (transcribe(..., word_timestamps=True) -> segment.words with .word/.probability/.start/.end) — read source via pip download faster-whisper==1.1.1 --no-deps. (3) gradio 4.24 Dataframe: read ${SP}/gsv39/lib/python3.9/site-packages/gradio/components/dataframe.py and the frontend templates to determine which datatype values exist ('markdown','html'?), how such a column renders and how editing behaves (does editing an html cell expose raw html? is sanitization applied? can individual cells be non-editable?), and whether pandas Styler cell colors are supported in 4.24. If feasible, actually test: write a tiny script under ${SP}/proofproto/ that builds a gr.Blocks with a Dataframe having a markdown/html column using ${SP}/gsv39/bin/python, launch it on port 7880, load it with playwright (python3, chromium at /opt/pw-browsers/chromium) and screenshot to ${SP}/proofproto/df.png; then kill the server (use a pid file, never pkill -f). (4) A robust character-level diff approach for Chinese+English mixed text (normalization: punctuation, full/half width, case, spaces; difflib SequenceMatcher on chars; mapping spans back to original text offsets). (5) Heuristic rules for typical Whisper mishearings in Chinese lecture transcripts (ALL-CAPS gibberish tokens, repeated phrases, homophone English-in-Chinese like 户字/whose) with a small allowlist of common acronyms. Write ${SP}/research_proofcheck.md with concrete API snippets and recommendations (which column rendering to use in 4.24). Return a short summary.`, { label: 'research:proofcheck', phase: 'Research' })

phase('Core')
const unitPrompt = (name, branch, files, extra) => `${COMMON}\n\nYOUR UNIT: ${name}. BRANCH: ${branch}. FILES YOU OWN (only edit these): ${files.join(', ')}.\n${extra}`

const u1 = agent(unitPrompt('U1 progress core (plan unit U1 + requirement R1)', 'v015/u1-progress',
  ['voicetwin/utils/progress.py', 'voicetwin/webui/tasks.py', 'tests/test_progress.py', 'tests/test_tasks.py'],
  `Implement plan unit U1 (interfaces B and C) plus R1: colors green running with moving stripes / amber stall (idle>=180s) / red error / solid green done / grey stopped; overall ETA (eta_total, eta_total_text, finish_clock) and snapshot 'level'. stream_task in webui/tasks.py must not import gradio. Guard the errors.explain import (U5) with fallback to str(exc). Include CSS for all states in PROGRESS_CSS and make the HTML self-explanatory for a non-technical user.`),
  { label: 'U1 progress', phase: 'Core', isolation: 'worktree', schema: RESULT })
const u5 = agent(unitPrompt('U5 error translation (plan unit U5)', 'v015/u5-errors',
  ['voicetwin/errors.py', 'tests/test_errors.py'],
  `Implement plan unit U5 (interface D). Cover at least: CUDA out of memory, NVIDIA driver/CUDA unavailable, no space left on device, network/SSL/proxy/timeout/HuggingFace/ModelScope download failures, ffmpeg errors, permission denied / file in use (WinError 32), path not found, port in use, GPT-SoVITS api start failure/timeout, missing python packages (ModuleNotFoundError -> which component), config.yaml YAML errors, TaskCancelled -> stopped. Each Friendly has a short Chinese title, concrete Chinese advice ("怎么办"), and the raw detail.`),
  { label: 'U5 errors', phase: 'Core', isolation: 'worktree', schema: RESULT })
const u9 = agent(unitPrompt('U9 GPU status (requirement R2)', 'v015/u9-gpu',
  ['voicetwin/utils/gpu.py', 'tests/test_gpu.py'],
  `Implement R2 exactly (gpu_status, render_gpu_badge_html, GPU_CSS, vram_tier). Must never raise; must be fast (cache 10s; nvidia-smi timeout 10s). Test with monkeypatched torch/nvidia-smi outputs (driver failure text, healthy RTX 5070 12GB, no GPU, low VRAM).`),
  { label: 'U9 gpu', phase: 'Core', isolation: 'worktree', schema: RESULT })
const u6 = agent(unitPrompt('U6 install & startup (plan unit U6)', 'v015/u6-install',
  ['install_windows.ps1', 'install_windows.bat', 'voicetwin/cli.py', 'voicetwin/config.py', 'voicetwin/utils/log.py', 'voicetwin/utils/winsys.py', 'voicetwin/webui/launcher.py', 'tests/test_cli.py', 'tests/test_launcher.py', 'tests/test_winsys.py'],
  `Implement plan unit U6 (interface G and cli _parse_redo). launcher.launch must call voicetwin.webui.app.build_app(cfg, local=...) with TypeError fallback to build_app(cfg), set GRADIO_ANALYTICS_ENABLED=False, auto-pick a free port if 7860 busy (print the URL in Chinese), and reuse an already-running instance (open browser to it). cli 'webui' command must use launcher.launch. Keep install_windows.ps1 UTF-8 BOM + CRLF and verify it parses with PowerShell: ${SP}/pwsh/pwsh -NoProfile -Command "$e=$null; [System.Management.Automation.Language.Parser]::ParseFile('<abs path>',[ref]$null,[ref]$e) | Out-Null; $e.Count". Installer must keep working for the existing flow (option 1 + path) and keep generating start_webui.bat/voicetwin.bat. Redo numbers: CLI --redo and UI must use the SAME numbering as displayed result tables (1-based); coordinate via the deviations field.`),
  { label: 'U6 install', phase: 'Core', isolation: 'worktree', schema: RESULT })

const [rq, rp] = await Promise.all([researchQuality, researchProof])
log('research done; core units still running are awaited by the features phase')
const core = await Promise.all([u1, u5, u9, u6])
const coreOk = core.filter(Boolean)
log(`core units: ${coreOk.map(c => `${c.branch}@${(c.sha || '').slice(0, 7)}`).join(', ')}`)
const coreNotes = JSON.stringify(coreOk.map(c => ({ branch: c.branch, sha: c.sha, deviations: c.deviations, implemented: c.implemented })))

phase('Features')
const featNote = `Core units are finished and committed on these branches (merge any you need into your branch first with: git merge --no-edit <branch>): ${coreNotes}\nResearch notes: ${SP}/research_quality.md and ${SP}/research_proofcheck.md (read them).`
const features = await parallel([
  () => agent(unitPrompt('U2 web UI (plan unit U2 + R1 display, R2 badge, R3 numbering, R4 voice library UI, R5 quality labels, R6 proofreading UI, R7 header version)', 'v015/u2-webui',
    ['voicetwin/webui/app.py', 'tests/test_webui_helpers.py', 'tests/test_webui_build.py'],
    `${featNote}\nFIRST merge v015/u1-progress, v015/u5-errors, v015/u9-gpu and v015/u6-install into your branch (they own other files, so no conflicts expected), so you can build against real code. U3 (workflows: task_stages, voice_library/list_voices, run_proofcheck, apply_suggestion, 1-based result indexes) and U8 (data/proofcheck.py: render_marked, render_diff_html) are being implemented in parallel right now: code against the interfaces in v015_requirements.md/plan with guarded imports and graceful fallbacks (e.g. hide the proofcheck button if wf.run_proofcheck is missing). Every handler yield must match its outputs list exactly. Build the app under gradio 4.24 in a test (tests/test_webui_build.py: build_app(cfg) with the venv) and also do a real-browser smoke check: start the app with ${SP}/gsv39/bin/python (PYTHONPATH=worktree, a temp workspace, port 7875, pid file) and load it with playwright (python3; chromium /opt/pw-browsers/chromium), screenshot the top area (GPU badge, voice library, progress bar after clicking 开始准备素材 with a tiny generated wav folder) to ${SP}/u2_shots/, then kill via pid. Make the page friendly and uncluttered: advanced options inside an Accordion '高级设置'.`),
    { label: 'U2 webui', phase: 'Features', isolation: 'worktree', schema: RESULT }),
  () => agent(unitPrompt('U3 workflows / prepare / synth (plan unit U3 + R3 indexes, R4 voice_library, R5 max tier, R6 integration)', 'v015/u3-workflows',
    ['voicetwin/workflows.py', 'voicetwin/data/prepare.py', 'voicetwin/data/asr.py', 'voicetwin/synth/engine.py', 'voicetwin/synth/select.py', 'voicetwin/synth/script.py', 'voicetwin/project.py', 'voicetwin/eval/metrics.py', 'voicetwin/default_config.yaml', 'tests/test_progress_flow.py', 'tests/test_pipeline.py', 'tests/test_script.py'],
    `${featNote}\nMerge v015/u1-progress, v015/u5-errors, v015/u9-gpu first if you need them (guarded imports anyway). U8 (data/proofcheck.py) is being written in parallel: call proofcheck.find_suspects / available_checker via guarded import in run_proofcheck and run_prepare. Implement the 'max' synthesis tier per research_quality.md (high/medium confidence only). Make sure the progress fractions are monotonic end-to-end and add tests recording every frac.`),
    { label: 'U3 workflows', phase: 'Features', isolation: 'worktree', schema: RESULT }),
  () => agent(unitPrompt('U4 backends (plan unit U4 + R5 VRAM-aware training)', 'v015/u4-backends',
    ['voicetwin/backends/base.py', 'voicetwin/backends/gptsovits.py', 'voicetwin/backends/qwen3tts.py', 'voicetwin/backends/indextts.py', 'voicetwin/backends/worker_backend.py', 'tests/fake_gptsovits.py', 'tests/test_gptsovits_fake.py'],
    `${featNote}\nMerge v015/u1-progress (check_cancel, TaskCancelled) and v015/u9-gpu (vram_tier) if useful, with guarded imports. Implement VRAM-aware automatic training parameters from research_quality.md (high/medium confidence only), logged in Chinese, overridable by explicit options/config. Keep tests/fake_gptsovits.py faithful (it emulates GPT-SoVITS scripts/log lines) and extend it if you rely on new log formats.`),
    { label: 'U4 backends', phase: 'Features', isolation: 'worktree', schema: RESULT }),
  () => agent(unitPrompt('U8 proofcheck (requirement R6 core)', 'v015/u8-proofcheck',
    ['voicetwin/data/proofcheck.py', 'tests/test_proofcheck.py'],
    `${featNote}\nImplement R6 proofcheck.py API exactly, following research_proofcheck.md. The second-engine path must load models lazily and degrade gracefully (heuristics only) when funasr/faster-whisper are not installed — tests must not need any ASR model (monkeypatch recognizers). Use check_cancel from voicetwin.utils.progress via guarded import. Unit-test span mapping on mixed Chinese/English text including the examples 'VFIXED WHOOZ WINDOW', '户字', repeated phrases, punctuation/width differences that must NOT be flagged.`),
    { label: 'U8 proofcheck', phase: 'Features', isolation: 'worktree', schema: RESULT }),
])
const featOk = features.filter(Boolean)
log(`feature units: ${featOk.map(c => `${c.branch}@${(c.sha || '').slice(0, 7)}`).join(', ')}`)

phase('Integrate')
const allUnits = coreOk.concat(featOk)
const integration = await agent(`${COMMON}\n\nYOUR ROLE: INTEGRATOR. BRANCH: v015/integration. You MAY edit any code/test file now (not docs/manual/PDFs — the lead does docs). Unit results (branches, deviations): ${JSON.stringify(allUnits.map(u => ({ branch: u.branch, sha: u.sha, deviations: u.deviations, skipped: u.skipped, tests: u.tests })))}\nSteps: (1) git checkout -b v015/integration; merge every unit branch (git merge --no-edit), resolve conflicts carefully. (2) Fix interface mismatches between units (e.g. stream_task signature, task_stages, voice_library, proofcheck functions, 1-based indexes and --redo consistency, GPU badge wiring), remove dead guarded fallbacks only if the real code is present and simpler. Set version 0.1.5 in pyproject.toml and voicetwin/__init__.py. (3) Run the full test suite in both envs (see rules) until green. (4) Real-browser smoke test under gradio 4.24: copy ${SP}/m24 to ${SP}/m24i (it has a fake GPT-SoVITS root GSV/, demo material folder literally named 'D:\\讲课素材', config.yaml, run_webui.py); edit run_webui.py/config to use port 7876 and the m24i paths; start the server with PYTHONPATH=<your worktree> ${SP}/gsv39/bin/python run_webui.py (pid file; never pkill -f). With playwright (python3, chromium /opt/pw-browsers/chromium, viewport 1280x1000, device_scale_factor 2) verify and screenshot to ${SP}/integ_shots/: (a) header with version + GPU badge (no GPU in sandbox, so an error/red badge is expected) + voice library; (b) prepare: type voice 我的声音, folder D:\\讲课素材, click 开始准备素材, capture the progress bar mid-run (green) and at completion (✅), the count line and numbered table with the 可能有错 column; (c) click 自动查找可能的错字 (heuristics-only in this env) and capture; (d) training tab with progress bar during and after training (fake GSV is fast); (e) generation with progress and the numbered 1-based result table; (f) environment check table numbered; (g) force an error (e.g. generate with an empty script or a nonexistent voice) and capture the red bar/friendly message. Use ${SP}/m24/flow_check.py and count_check.py as reference for selectors. Fix any bug you find and re-test. Kill the server via pid at the end. (5) Commit on v015/integration. Return the RESULT schema plus in 'tests' list both env results and which browser checks passed, and list screenshot paths in 'deviations'.`,
  { label: 'integrate', phase: 'Integrate', isolation: 'worktree', schema: RESULT })
return { research: { quality: rq, proofcheck: rp }, units: allUnits, integration }
