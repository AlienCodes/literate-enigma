#!/bin/bash
# Run the temp-folder regex check script with pwsh.
SP=<草稿目录>
"$SP/pwsh/pwsh" -NoProfile -File "$SP/u6_regex.ps1"
grep -n "Temp" "$SP/u6_install_windows.ps1.txt"
