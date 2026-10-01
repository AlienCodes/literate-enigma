#!/bin/bash
# Smoke test of install_windows.ps1 (U6 worktree) with pwsh on Linux against a fake GPT-SoVITS root.
WT=<仓库>/.claude/worktrees/wf_08725f86-d54-6
SP=<草稿目录>
PWSH=$SP/pwsh/pwsh
D=$SP/u6inst
rm -rf "$D"; mkdir -p "$D/GSV/runtime" "$D/GSV/GPT_SoVITS/prepare_datasets" "$D/VoiceTwin"
touch "$D/GSV/api_v2.py" "$D/GSV/GPT_SoVITS/prepare_datasets/2-get-sv.py"
cat > "$D/GSV/runtime/python.exe" <<EOF
#!/bin/bash
# fake integrated-package python: pip is a no-op, voicetwin runs from the worktree
echo "[fake python] \$*" >> "$D/calls.log"
if [ "\$1" = "-m" ] && [ "\$2" = "pip" ]; then echo "(pip skipped)"; exit 0; fi
if [ "\$1" = "-c" ]; then exit 0; fi
export PYTHONPATH="$WT"
exec python3 "\$@"
EOF
chmod +x "$D/GSV/runtime/python.exe"
cp "$WT/install_windows.ps1" "$D/VoiceTwin/"

echo "=================== RUN 1: -Mode gsv -GsvRoot -NoPause -NoShortcut"
$PWSH -NoProfile -File "$D/VoiceTwin/install_windows.ps1" -Mode gsv -GsvRoot "$D/GSV" -NoPause -NoShortcut
echo "exit=$?"
echo "=================== start_webui.bat"
cat "$D/VoiceTwin/start_webui.bat"
echo "=================== voicetwin.bat"
cat "$D/VoiceTwin/voicetwin.bat"
echo "=================== calls"
cat "$D/calls.log"
grep -n "root:" "$D/VoiceTwin/config.yaml" | head -3

echo "=================== RUN 2: interactive, remembered root + typo first"
mkdir -p "$D/VoiceTwin/workspace/老师的声音" && touch "$D/VoiceTwin/workspace/老师的声音/manifest.jsonl"
printf '1\n/no/such/place\n\nY\nN\nN\n' | $PWSH -NoProfile -File "$D/VoiceTwin/install_windows.ps1" -NoShortcut
echo "exit=$?"

echo "=================== RUN 3: wrong -GsvRoot with -NoPause must fail in Chinese"
$PWSH -NoProfile -File "$D/VoiceTwin/install_windows.ps1" -Mode gsv -GsvRoot "/no/such/dir" -NoPause -NoShortcut
echo "exit=$?"

echo "=================== RUN 4: old package without 2-get-sv.py"
rm "$D/GSV/GPT_SoVITS/prepare_datasets/2-get-sv.py"
$PWSH -NoProfile -File "$D/VoiceTwin/install_windows.ps1" -Mode gsv -GsvRoot "$D/GSV" -NoPause -NoShortcut
echo "exit=$?"
