#!/bin/bash
# More installer smoke runs (after u6_smoke_install.sh): auto-find and pasted go-webui.bat path.
SP=<草稿目录>
PWSH=$SP/pwsh/pwsh
D=$SP/u6inst
touch "$D/GSV/GPT_SoVITS/prepare_datasets/2-get-sv.py"
mkdir -p "$D/home/Downloads"
rm -rf "$D/home/Downloads/GPT-SoVITS-v2pro"
cp -a "$D/GSV" "$D/home/Downloads/GPT-SoVITS-v2pro"
rm -f "$D/VoiceTwin/config.yaml"

echo "=================== RUN 5: no config, auto-find in Downloads"
printf '1\n\nY\nN\nN\n' | USERPROFILE="$D/home" $PWSH -NoProfile -File "$D/VoiceTwin/install_windows.ps1" -NoShortcut 2>&1 | grep -v "^ *[0-9]*\. [✅⚠️❌]" | sed -n 1,25p
grep -n "^    root:" "$D/VoiceTwin/config.yaml" | head -1

echo "=================== RUN 6: pasted go-webui.bat path"
rm -f "$D/VoiceTwin/config.yaml"
printf '1\n%s\nY\nN\nN\n' "$D/GSV/go-webui.bat" | USERPROFILE="$D/nohome" $PWSH -NoProfile -File "$D/VoiceTwin/install_windows.ps1" -NoShortcut 2>&1 | sed -n '/第 1\/6 步/,/检查通过/p'
grep -n "^    root:" "$D/VoiceTwin/config.yaml" | head -1
