export const meta = {
  name: 'voicetwin-ux-audit',
  description: 'Audit VoiceTwin end-to-end for user-friendliness (progress bars, guidance, errors, install, output) and produce a prioritized implementation plan',
  phases: [
    { title: 'Audit', detail: '5 parallel lenses over the codebase, each from a non-technical teacher perspective' },
    { title: 'Plan', detail: 'dedup, prioritize, group into conflict-free implementation units' },
  ],
}

const REPO = '<仓库>'
const GRADIO = '<草稿目录>/gsv39/lib/python3.9/site-packages/gradio'

const CONTEXT = `You are auditing "VoiceTwin 声音分身", a Windows voice-cloning tool for a NON-TECHNICAL Chinese teacher whose voice is hoarse. The repo is at ${REPO} (read-only for you: do NOT edit files). Python package: voicetwin/ (webui/app.py = Gradio UI, workflows.py, data/prepare.py, data/asr.py, backends/gptsovits.py, backends/base.py, synth/engine.py, synth/select.py, cli.py), installer install_windows.ps1, docs in 快速上手.md.
The user runs it inside the GPT-SoVITS Windows integration package, which ships gradio 4.24.0, Python 3.9, librosa 0.9.2. Anything you propose for the web UI MUST work on gradio 4.24 — verify component/parameter availability by reading the installed gradio 4.24 source at ${GRADIO} (e.g. components/*.py, blocks.py, helpers.py). Note: gr.Timer does NOT exist in 4.24; check before proposing any API.
Known facts: in gradio 4.24, Dropdown values can arrive as lists after choices updates (already fixed via _voice_name()). Long tasks run in a background thread via stream_task() in webui/app.py which polls logs every 0.6s; backend functions already accept a progress(frac, msg) callback but the web UI currently does NOT pass one, so no progress bar is shown — the user explicitly asked for a progress bar showing what step it is on.
The user said (translated): "While it is working, can there be a progress bar below so I know exactly what it is doing? Also look everywhere else to make it more user-friendly — think of everything you can, end to end."
Be concrete and grounded: cite file:line, quote the current behavior, and propose a specific change. Prefer high-value, low-risk changes. Do not propose things already implemented (read the code first). Write all user-facing text proposals in simple Chinese.`

const FINDINGS = {
  type: 'object',
  properties: {
    findings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          title: { type: 'string', description: 'short name of the improvement' },
          problem: { type: 'string', description: 'what the teacher experiences today, with file:line evidence' },
          proposal: { type: 'string', description: 'concrete change: functions to touch, UI text, behavior' },
          files: { type: 'array', items: { type: 'string' } },
          value: { type: 'string', enum: ['high', 'medium', 'low'] },
          effort: { type: 'string', enum: ['S', 'M', 'L'] },
          risk: { type: 'string', description: 'what could break; gradio 4.24 compatibility notes with evidence' },
        },
        required: ['title', 'problem', 'proposal', 'files', 'value', 'effort', 'risk'],
      },
    },
  },
  required: ['findings'],
}

const LENSES = [
  { key: 'progress', prompt: `LENS: PROGRESS REPORTING. Trace every place progress is or could be reported for the three long tasks: material preparation (workflows.run_prepare -> data/prepare.py incl. per-file extraction, slicing, ASR per clip in data/asr.py, speaker filtering, references, profile), training (workflows.run_train -> backends/gptsovits.py train: 1A/1B/1C stages, s2/s1 training via backends/base.py run_logged which parses '进度 X%' from subprocess output, then synth/select.py model selection), and generation (workflows.run_narrate -> synth/engine.py per sentence and candidate). For each, list what progress(frac,msg) calls exist today, their fraction ranges, and gaps where the bar would freeze for minutes (e.g. first-time model download, ASR over hundreds of clips, a single long epoch). Propose ONE unified design: an overall percentage, current stage name in Chinese, step x/y, elapsed time and a rough remaining-time estimate, rendered in the web UI as a gr.HTML progress bar updated from stream_task (so it does not cover the log the way gr.Progress overlays do — verify how gr.Progress/show_progress behaves in 4.24 source and say which is better). Specify exactly how stream_task should receive and expose progress state thread-safely, and which backend functions need finer-grained calls. Also consider the CLI (cli.py) showing progress.` },
  { key: 'webui-flow', prompt: `LENS: WEB UI FLOW. Walk through voicetwin/webui/app.py as the teacher: first launch (no voice yet), preparing material, proofreading, training, generating, evaluating, and daily use afterwards. Identify confusion points and missing guidance: e.g. no status summary of the selected voice (material minutes, trained or not, best model), no "next step" hints after each step finishes, buttons that can be clicked twice while a task is running (could start two trainings at once — check), refreshing the browser mid-task loses the progress view although the task continues, tracebacks dumped into the log box, unclear labels/defaults, the advanced settings that a teacher should never touch being prominent, long text walls. Propose concrete UI changes that work on gradio 4.24 (verify each API in the installed source).` },
  { key: 'errors', prompt: `LENS: ERRORS, ROBUSTNESS AND SAFETY NETS. Find every path where an exception or failure reaches the teacher (web UI log, stream_task traceback, CLI). Identify raw English/technical errors that should be translated into actionable Chinese (CUDA out of memory, NVIDIA driver missing, disk full / no space, network or HuggingFace/ModelScope download failure, ffmpeg errors, file locked/in use, paths with spaces or Chinese, port already in use, GPT-SoVITS API not starting). Look for missing pre-flight checks before long tasks (free disk space, GPU available, enough material minutes, models present), missing cancellation (a 停止 button), concurrent task protection (a second task started while one runs — check workflows and backends for shared state like the GPT-SoVITS API port), and data-safety (overwriting outputs, losing proofreading edits). Propose a central error-translation helper and where to call it.` },
  { key: 'install-startup', prompt: `LENS: INSTALL, STARTUP AND ENVIRONMENT. Review install_windows.ps1, install_windows.bat, the generated start_webui.bat/voicetwin.bat (generated inside install_windows.ps1), voicetwin/cli.py webui launch, workflows.doctor, and config handling. As the teacher: what is confusing or fragile during install and every startup? Consider: clear success/failure summary at the end of install, pre-checks (disk space, path with Chinese/spaces, integration package version), desktop shortcut fallback, start_webui.bat behavior when the port 7860 is busy (auto-pick another port and print it), auto-opening the browser, a friendly startup banner, the 环境检查 tab readability (sorting ❌ first, explaining what to do), upgrade path (re-running installer keeps data), where logs are, and how to report problems. Propose concrete changes (PowerShell 5.1 compatible; the .ps1 must stay UTF-8 with BOM + CRLF).` },
  { key: 'output', prompt: `LENS: GENERATION AND OUTPUT EXPERIENCE. Review the ③ 生成讲课音频 and ④ 评估 tabs in webui/app.py, synth/engine.py, workflows.run_narrate, and how results are presented. As the teacher: after generating, how do I find, audition, fix and reuse results? Consider: auditioning individual sentences from the result table, one-click redo of a sentence by clicking it, an "open output folder" button (the server runs locally on Windows, os.startfile is possible), a history list of past generations, choosing mp3 vs wav in the UI, editing the pronunciation lexicon (lexicon.txt) inside the UI, picking a reference audio by listening instead of typing an id, script length/time estimate before generating, sensible output file names, and making the per-sentence table readable for a non-technical user. Propose concrete gradio 4.24-compatible changes (verify APIs in source).` },
]

phase('Audit')
const audits = await parallel(LENSES.map(l => () =>
  agent(`${CONTEXT}\n\n${l.prompt}\n\nReturn 5-15 findings, most valuable first.`, { label: `audit:${l.key}`, phase: 'Audit', schema: FINDINGS })
    .then(r => r ? { lens: l.key, findings: r.findings } : null)))
const ok = audits.filter(Boolean)
log(`audits returned: ${ok.map(a => `${a.lens}=${a.findings.length}`).join(', ')}`)

phase('Plan')
const PLAN = {
  type: 'object',
  properties: {
    summary_zh: { type: 'string', description: '3-6 sentence Chinese summary for the teacher of what will change' },
    units: {
      type: 'array',
      description: 'implementation units; each unit owns a disjoint set of files so units can be implemented in parallel without conflicts',
      items: {
        type: 'object',
        properties: {
          name: { type: 'string' },
          files: { type: 'array', items: { type: 'string' } },
          items: {
            type: 'array',
            items: {
              type: 'object',
              properties: {
                title: { type: 'string' },
                spec: { type: 'string', description: 'precise implementation spec incl. functions, UI text (Chinese), edge cases, gradio 4.24 notes' },
                priority: { type: 'string', enum: ['must', 'should', 'later'] },
                test: { type: 'string', description: 'how to verify (unit test and/or manual browser check)' },
              },
              required: ['title', 'spec', 'priority', 'test'],
            },
          },
        },
        required: ['name', 'files', 'items'],
      },
    },
    deferred: { type: 'array', items: { type: 'string' }, description: 'ideas intentionally left out and why' },
    interfaces: { type: 'string', description: 'cross-unit contracts (function signatures, state dict keys) that units must agree on' },
  },
  required: ['summary_zh', 'units', 'deferred', 'interfaces'],
}
const plan = await agent(`${CONTEXT}\n\nYou are the lead engineer. Below are audit findings from 5 independent reviewers (JSON). Deduplicate, drop anything already implemented or not grounded in the code (spot-check claims by reading the files), and produce a prioritized implementation plan for the next release (v0.1.4). The progress bar the user explicitly asked for is the top priority and must be 'must'. Keep the release shippable: 'must' items should be high-value and low-risk; mark ambitious ones 'should' or 'later'. Group items into implementation units with DISJOINT file ownership (webui/app.py will likely be one unit; backend progress granularity another; installer another; error translation helper may be a new module) and define the cross-unit interfaces precisely (e.g. the progress callback signature and the state keys stream_task exposes). Every web UI item must be compatible with gradio 4.24 — cite the source you checked in ${GRADIO}.\n\nFINDINGS:\n${JSON.stringify(ok)}`, { label: 'plan', phase: 'Plan', schema: PLAN })
return { audits: ok, plan }
