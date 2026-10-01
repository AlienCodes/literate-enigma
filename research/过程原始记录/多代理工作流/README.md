# 多代理工作流（一次派出很多个子代理并行检查 / 开发 / 审查）

每个文件夹是一次工作流：`script.js` 是编排脚本原文，`result.json` 是最终结果（所有发现、核实结论、修复情况），
`各子代理的任务和结论.md` 是每个子代理拿到的任务原文和它交回的结论。
`子代理大段输出/` 是子代理执行命令时输出太长而单独保存的原始输出。

| 开始（北京时间） | 工作流 | 做什么 | 子代理数 | 工具调用 | 用时（分钟） | 状态 |
|---|---|---|---:|---:|---:|---|
| 2026-10-01 10:29:16 | [voicetwin-ux-audit](voicetwin-ux-audit/) | Audit VoiceTwin end-to-end for user-friendliness (progress bars, guidance, errors, install, output) and produce a prioritized implementation plan | 6 | 284 | 59 | completed |
| 2026-10-01 11:33:08 | [voicetwin-v015-build](voicetwin-v015-build/) | Implement VoiceTwin v0.1.5: progress bars, GPU status, numbering, voice library, quality tuning, typo highlighting, UX fixes — research, parallel units in worktrees, integration with browser test | 11 | 1428 | 326 | completed |
| 2026-10-01 17:04:05 | [voicetwin-v016-review](voicetwin-v016-review/) | Adversarial review of VoiceTwin v0.1.6 (requirements checklist, correctness, gradio 4.24, Windows, audio pipeline), verify each finding with 3 skeptics, then fix confirmed issues | 132 | 2639 | 268 | completed |
| 2026-10-01 22:56:20 | [manual-v016](manual-v016/) | Update the PDF manual HTML chapters for the v0.1.6 UI (4 disjoint file groups), then cross-check | 12 | 285 | 15 | completed |
