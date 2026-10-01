#!/bin/bash
# Parse-check install_windows.ps1 of the U6 worktree with PowerShell.
F=<仓库>/.claude/worktrees/wf_08725f86-d54-6/install_windows.ps1
<草稿目录>/pwsh/pwsh -NoProfile -Command "\$e=\$null; [System.Management.Automation.Language.Parser]::ParseFile('$F',[ref]\$null,[ref]\$e) | Out-Null; \$e.Count; \$e | ForEach-Object { \$_.ToString() }"
