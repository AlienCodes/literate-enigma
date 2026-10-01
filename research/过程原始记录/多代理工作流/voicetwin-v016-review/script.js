export const meta = {
  name: 'voicetwin-v016-review',
  description: 'Adversarial review of VoiceTwin v0.1.6 (requirements checklist, correctness, gradio 4.24, Windows, audio pipeline), verify each finding with 3 skeptics, then fix confirmed issues',
  phases: [
    { title: 'Find', detail: '5 reviewers, one lens each' },
    { title: 'Verify', detail: '3 skeptics per finding try to refute it' },
    { title: 'Fix', detail: 'one fixer applies confirmed fixes on a branch, runs both test envs' },
  ],
}
const SP = '<草稿目录>'
const REPO = '<仓库>'
const CTX = `Project: VoiceTwin 声音分身 v0.1.6 — Windows voice-cloning tool for a non-technical Chinese teacher, running inside the GPT-SoVITS integration package (gradio 4.24.0, Python 3.9, librosa 0.9.2). Code under review: ${REPO} at HEAD (branch claude/happy-heisenberg-u52a72, commit 83bff05; diff vs previous release: git diff b518011 HEAD). The user's requirements are in ${SP}/v015_requirements.md (R1-R9 incl. R5b-R5f; version is 0.1.6) and the audit plan ${SP}/ux_audit.json. Research notes: ${SP}/research_quality.md, ${SP}/research_proofcheck.md. Real GPT-SoVITS source for reference: ${SP}/ref/GPT-SoVITS. gradio 4.24 source: ${SP}/gsv39/lib/python3.9/site-packages/gradio. A py3.9/gradio-4.24 venv: ${SP}/gsv39/bin/python (use PYTHONPATH=<repo or worktree>, because an old voicetwin is installed there). Do NOT edit files in ${REPO}. You may write scratch scripts under ${SP}/review/.`

const FIND = {
  type: 'object',
  properties: { findings: { type: 'array', items: { type: 'object', properties: {
    id: { type: 'string', description: 'short unique slug' },
    severity: { type: 'string', enum: ['blocker', 'major', 'minor'] },
    file: { type: 'string' }, line: { type: 'integer' },
    claim: { type: 'string', description: 'what is wrong, concretely, with evidence (quote code)' },
    scenario: { type: 'string', description: 'concrete inputs/steps -> wrong behaviour the teacher would see' },
    fix: { type: 'string', description: 'proposed minimal fix' },
  }, required: ['id', 'severity', 'file', 'claim', 'scenario', 'fix'] } } },
  required: ['findings'],
}
const VERDICT = { type: 'object', properties: {
  real: { type: 'boolean', description: 'true only if you could NOT refute it and believe it is a genuine defect worth fixing for this release' },
  evidence: { type: 'string' },
}, required: ['real', 'evidence'] }

const LENSES = [
  { key: 'requirements', prompt: `LENS: REQUIREMENTS CHECKLIST. Enumerate EVERY user requirement in v015_requirements.md (R1 progress bar colours green/amber/red/grey + overall ETA + finish clock; R2 GPU badge always visible + refresh on load/button/after tasks; R3 numbering + totals on EVERY list/table incl. result table 1-based, env check, voice library, references list, skipped files, drop reasons, verify table, blind test list; R4 voice library columns + click selects + audition; R5/R5b auto training params by VRAM + save more checkpoints + OOM retry; R5c adaptive best-of-N up to 20 with targets; R5d absolute digital silence between sentences, NO room tone/EQ, edge trimming; R5e perfect tier two variants saved + auto recommendation + choose_variant + UI radio; R5f calibrated percentage, ensemble encoders incl. ERes2NetV2, 85% elimination, per-candidate % in report, honest wording; R6 proofcheck incl. markdown column, filter, diff panel, 采用建议, count line; R7 version 0.1.6 header; R8 ⑤ 鉴别 machine verification + blind test with answer sheet; R9 speed slider −30…+30 left=faster right=slower mapping speed_factor=1−v/100, live text, 试听语速, no resampling, pauses scale). For each, find the implementing code and verify it actually works as specified (read code; run small scripts or tests where possible). Report every requirement that is missing, partially implemented, or implemented wrongly.` },
  { key: 'correctness', prompt: `LENS: CORRECTNESS & DATA SAFETY. Review the diff for real bugs: task registry/concurrency in voicetwin/webui/tasks.py (single-task lock, attach after refresh, stop/cancel, thread exceptions), ProgressTracker thread safety and monotonicity, progress ranges across workflows/backends, cancellation leaving files half-written, manifest/CSV writes (atomicity, proofreading edits lost, suspect cleared on edit), synthesis cache keys (must include tier/speed/variant/settings so changed settings don't return stale audio), report JSON consistency, choose_variant file copying, blind test answer leakage, CLI regressions (all commands in voicetwin/cli.py still work: run them against the dummy backend), error translation never masking the real error in logs. Run the test suite and targeted scripts to confirm suspicions.` },
  { key: 'gradio424', prompt: `LENS: GRADIO 4.24 UI. In voicetwin/webui/app.py verify against the installed gradio 4.24 source: every event handler's outputs vs every yield/return arity (count them programmatically if helpful), components/params that do not exist in 4.24, Dataframe markdown column handling on save (edited display column must be ignored), filter + select mapping by id, .input/.change events firing spuriously (e.g. the variants radio), JS injected via Blocks(js=)/head working in 4.24, concurrency settings, show_progress hidden, Accordion/Tabs ids, app.load handlers. Build the app under the gsv39 venv and, if useful, run a quick headless-browser check (port 7890, pid file; never pkill -f; python3 playwright with chromium /opt/pw-browsers/chromium; the demo env ${SP}/m24i can be copied). Report concrete breakages.` },
  { key: 'windows', prompt: `LENS: WINDOWS RUNTIME. Review Windows-specific code paths that cannot run in this Linux sandbox: install_windows.ps1 (PowerShell 5.1 syntax, UTF-8 BOM + CRLF kept, logic of new pre-checks/prompts, no regression in the option-1 + path flow, generated start_webui.bat/voicetwin.bat), voicetwin/utils/winsys.py (SetThreadExecutionState flags, quick-edit disable via kernel32 GetConsoleMode/SetConsoleMode correctness), voicetwin/webui/launcher.py (port probing, detecting an existing instance, opening the browser), subprocess tree kill (taskkill /T /F usage), path handling with Chinese characters/spaces, encodings (cp936 consoles, chcp 65001), GPU OOM detection/retry in backends/gptsovits.py against real GPT-SoVITS log messages (see ${SP}/ref/GPT-SoVITS), and the ERes2NetV2 in-process loader in voicetwin/eval/speaker.py versus the REAL GPT-SoVITS sv.py/eres2net code in ${SP}/ref/GPT-SoVITS (module paths, class names, checkpoint loading, feature extraction, sample rate). Parse the ps1 with ${SP}/pwsh/pwsh. Report concrete defects.` },
  { key: 'audio', prompt: `LENS: AUDIO PIPELINE & QUALITY LOGIC. Review voicetwin/synth/engine.py, synth/select.py, eval/metrics.py, eval/speaker.py, backends/gptsovits.py training plan: (a) assembled output: pauses between sentences and lead-in/out are EXACT zeros in every tier and every variant; no room tone/EQ code remains; edge trimming + short fades don't clip speech; loudness normalisation does not re-introduce non-zero samples into gaps (check carefully: gain applied to zeros is fine, but dithering/filters/resampling after assembly would not be); (b) speed: speed_factor mapping, passed to backend, no waveform resampling for speed, pauses scale; (c) best-of-N: adaptive batches, cap, 85% elimination only with reliable encoders, targets, retries, combined score ordering; (d) calibrated percentage math (p50_real, cap at 100, ensemble averaging, MFCC-only fallback honesty); (e) perfect tier two variants: identical timing/SRT, denoise only on B, recommendation = higher score, ties; (f) training auto-params consistent with research_quality.md (DPO off by default, save_every divides epochs, batch formula, OOM halving retry). Write small numpy scripts using the dummy/fake backends to empirically verify (e.g. assert gaps are exactly 0.0). Report concrete defects.` },
]

phase('Find')
const results = await pipeline(LENSES,
  l => agent(`${CTX}\n\n${l.prompt}\n\nReturn only genuine, concrete defects (not style nits). Up to 15 findings, most severe first.`, { label: `find:${l.key}`, phase: 'Find', schema: FIND })
        .then(r => (r ? r.findings : []).map(f => ({ ...f, lens: l.key }))),
  findings => parallel(findings.map(f => () =>
    parallel([0, 1, 2].map(k => () => agent(`${CTX}\n\nYou are skeptic #${k + 1}. Try hard to REFUTE this reported defect by reading the code and, where possible, running a quick experiment. Default to real=false if it is not clearly a genuine defect that matters for this release (e.g. already handled elsewhere, misread code, only theoretical).\n\nFINDING (${f.lens}): ${JSON.stringify(f)}`, { label: `verify:${f.id}#${k + 1}`, phase: 'Verify', schema: VERDICT })))
      .then(vs => { const ok = vs.filter(Boolean); const yes = ok.filter(v => v.real).length; return { ...f, votes: `${yes}/${ok.length}`, confirmed: yes >= 2, evidence: ok.map(v => v.evidence).join('\n---\n') } })
  )))
const all = results.filter(Boolean).flat().filter(Boolean)
const confirmed = all.filter(f => f.confirmed)
log(`findings: ${all.length}, confirmed: ${confirmed.length} (${confirmed.map(f => f.severity[0] + ':' + f.id).join(', ')})`)
if (!confirmed.length) return { all, confirmed, fix: null }

phase('Fix')
const fix = await agent(`${CTX}\n\nYOU ARE THE FIXER. You may edit code and tests (not docs/manual/PDFs). Work in your isolated worktree: first run git checkout -b v016/review-fixes. Fix ALL of the following CONFIRMED defects (each was verified by independent skeptics; their evidence is included). Keep fixes minimal and correct, add a regression test for each where feasible, keep Python 3.9 + gradio 4.24 compatibility, keep install_windows.ps1 UTF-8 BOM + CRLF (parse-check with ${SP}/pwsh/pwsh). Then run the full suite in both envs (python3 -m pytest -q; and PYTHONPATH=$PWD ${SP}/gsv39/bin/python -m pytest -q -p no:cacheprovider tests --deselect tests/test_gptsovits_fake.py::test_train_select_and_narrate) until green. Commit on v016/review-fixes with a message ending with:\nCo-Authored-By: Claude <模型> <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01PwXvLynw8dAvAfJEJKMB77\nDo not push. Return: branch, sha, per-finding status (fixed / not fixed + why), test results.\n\nCONFIRMED DEFECTS:\n${JSON.stringify(confirmed)}`,
  { label: 'fixer', phase: 'Fix', isolation: 'worktree' })
return { all, confirmed, fix }
