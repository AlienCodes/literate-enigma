# VoiceTwin 声音分身 - Windows 安装脚本
# 用法：双击 install_windows.bat，或在 PowerShell 中运行：
#   powershell -ExecutionPolicy Bypass -File install_windows.ps1 [-Mode gsv -GsvRoot D:\GPT-SoVITS] [-Mode venv]
param(
    [string]$Mode = "",
    [string]$GsvRoot = "",
    [string]$Mirror = "https://pypi.tuna.tsinghua.edu.cn/simple",
    [switch]$NoPause,
    [switch]$NoShortcut
)
# 注意：不用 "Stop"——Windows PowerShell 5.1 会把 pip/python 输出到 stderr 的普通提示当成致命错误，
# 这里改为逐条检查退出码。
$ErrorActionPreference = "Continue"
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Here
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}

function Pause-End { if (-not $NoPause) { Read-Host "按回车键关闭窗口" | Out-Null } }
function Step($msg) { Write-Host "`n==> $msg" -ForegroundColor Cyan }
function Fail($msg) { Write-Host "`n[错误] $msg" -ForegroundColor Red; Pause-End; exit 1 }
function Pip($py, [string[]]$pipArgs) {
    & $py -m pip install --disable-pip-version-check -i $Mirror @pipArgs
    if ($LASTEXITCODE -ne 0) {
        Write-Host "镜像源安装失败，改用官方源重试……" -ForegroundColor Yellow
        & $py -m pip install --disable-pip-version-check @pipArgs
        if ($LASTEXITCODE -ne 0) { Fail "安装失败：pip install $($pipArgs -join ' ')。请检查网络后重新运行安装程序。" }
    }
}

Write-Host "=============================================" -ForegroundColor Green
Write-Host "   VoiceTwin 声音分身 安装程序" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
Write-Host "安装位置：$Here"
if ($Here -match "[^\x00-\x7F]" -or $Here -match " ") {
    Write-Host "提示：安装路径里有中文或空格，个别组件可能出问题。建议放到类似 D:\VoiceTwin 的路径。" -ForegroundColor Yellow
}

if (-not $Mode) {
    Write-Host ""
    Write-Host "请选择安装方式："
    Write-Host "  1) 推荐：安装到 GPT-SoVITS 整合包里（最省事，语音识别和训练都用显卡，不用重复下载 PyTorch）"
    Write-Host "  2) 独立安装：创建单独的 Python 虚拟环境（需要本机已安装 Python 3.10 或 3.11，适合有经验的用户）"
    $choice = Read-Host "请输入 1 或 2，然后按回车"
    if ($choice.Trim() -eq "2") { $Mode = "venv" } else { $Mode = "gsv" }
}

$Py = ""
if ($Mode -eq "gsv") {
    if (-not $GsvRoot) {
        Write-Host ""
        Write-Host "请输入 GPT-SoVITS 整合包所在的文件夹路径（打开那个文件夹，里面能看到 go-webui.bat 和 runtime 文件夹）。"
        Write-Host "小技巧：在文件夹窗口顶部的地址栏点一下，复制路径，再回到这里右键粘贴。"
        $GsvRoot = Read-Host "GPT-SoVITS 整合包路径（例如 D:\GPT-SoVITS）"
    }
    $GsvRoot = $GsvRoot.Trim().Trim('"').TrimEnd('\', '/')
    # 常见错误：多套了一层文件夹，自动往下找一层
    if (-not (Test-Path (Join-Path $GsvRoot "runtime")) -and (Test-Path $GsvRoot)) {
        $inner = Get-ChildItem -Path $GsvRoot -Directory -ErrorAction SilentlyContinue |
            Where-Object { Test-Path (Join-Path $_.FullName "runtime") } | Select-Object -First 1
        if ($inner) { $GsvRoot = $inner.FullName; Write-Host "已自动找到整合包目录：$GsvRoot" -ForegroundColor Yellow }
    }
    $Py = Join-Path (Join-Path $GsvRoot "runtime") "python.exe"
    if (-not (Test-Path $Py)) { Fail "没有找到 $Py 。请确认输入的是 GPT-SoVITS 整合包解压后的根目录（里面有 runtime 文件夹）。" }
    if (-not (Test-Path (Join-Path $GsvRoot "api_v2.py"))) {
        Fail "这个 GPT-SoVITS 整合包版本太旧（缺少 api_v2.py），请下载最新版整合包后重试。"
    }
    Step "安装 VoiceTwin 到整合包环境（--no-deps：不改动整合包原有依赖的版本）"
    Pip $Py @("--no-deps", "--upgrade", "--force-reinstall", $Here)
    Pip $Py @("pyloudnorm", "imageio-ffmpeg", "zhconv", "webrtcvad-wheels")
    Pip $Py @("--no-deps", "resemblyzer")
    # 语音识别：整合包一般自带 faster-whisper；没有的话按 GPT-SoVITS 官方方式 --no-deps 安装
    & $Py -c "import faster_whisper" *> $null
    if ($LASTEXITCODE -ne 0) {
        Step "安装语音识别组件 faster-whisper"
        Pip $Py @("--no-deps", "faster-whisper")
    }
} else {
    $sysPy = $null
    foreach ($cand in @("py -3.11", "py -3.10", "python")) {
        try {
            $ver = Invoke-Expression "$cand -c `"import sys;print('%d.%d'%sys.version_info[:2])`"" 2>$null
            if ($ver -match "^3\.(9|10|11|12)$") { $sysPy = $cand; break }
        } catch {}
    }
    if (-not $sysPy) { Fail "没有找到 Python 3.9~3.12。请从 https://www.python.org/downloads/ 安装 Python 3.11（安装时勾选 Add python.exe to PATH）后重试。" }
    Step "创建虚拟环境 .venv（使用 $sysPy）"
    Invoke-Expression "$sysPy -m venv .venv"
    $Py = Join-Path (Join-Path (Join-Path $Here ".venv") "Scripts") "python.exe"
    if (-not (Test-Path $Py)) { $Py = Join-Path (Join-Path (Join-Path $Here ".venv") "bin") "python" }
    & $Py -m pip install --disable-pip-version-check -U pip -i $Mirror | Out-Null
    Step "安装 VoiceTwin 及语音识别、网页界面等依赖（需要几分钟）"
    Pip $Py @("-e", "$Here[asr,webui,denoise,docx]")
    Step "安装声纹打分组件（PyTorch CPU 版 + resemblyzer）"
    Pip $Py @("torch", "--index-url", "https://download.pytorch.org/whl/cpu")
    Pip $Py @("webrtcvad-wheels")
    Pip $Py @("--no-deps", "resemblyzer")
}

Step "生成配置文件 config.yaml"
$cfgArgs = @("-m", "voicetwin", "init-config")
if ($GsvRoot) { $cfgArgs += @("--gptsovits-root", $GsvRoot) }
if ($Mode -eq "gsv") { $cfgArgs += @("--backend", "gptsovits") }
& $Py @cfgArgs
if ($LASTEXITCODE -ne 0) { Fail "生成配置文件失败" }

Step "生成启动脚本 start_webui.bat / voicetwin.bat"
$lines = @("@echo off", "chcp 65001 >nul", "cd /d `"%~dp0`"",
           "if not defined HF_ENDPOINT set `"HF_ENDPOINT=https://hf-mirror.com`"")
if ($GsvRoot) { $lines += "set `"PATH=$GsvRoot;$GsvRoot\runtime;%PATH%`"" }
$header = ($lines -join "`r`n") + "`r`n"
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText((Join-Path $Here "start_webui.bat"),
    $header + "echo 正在启动声音分身，浏览器会自动打开 http://127.0.0.1:7860 ，使用期间请不要关闭本窗口……`r`n`"$Py`" -m voicetwin webui`r`npause`r`n", $utf8NoBom)
[System.IO.File]::WriteAllText((Join-Path $Here "voicetwin.bat"), $header + "`"$Py`" -m voicetwin %*`r`n", $utf8NoBom)

if (-not $NoShortcut) {
    try {
        $desktop = [Environment]::GetFolderPath("Desktop")
        $shell = New-Object -ComObject WScript.Shell
        $lnk = $shell.CreateShortcut((Join-Path $desktop "声音分身 VoiceTwin.lnk"))
        $lnk.TargetPath = Join-Path $Here "start_webui.bat"
        $lnk.WorkingDirectory = $Here
        $lnk.Save()
        Write-Host "已在桌面创建快捷方式「声音分身 VoiceTwin」" -ForegroundColor Green
    } catch {
        Write-Host "（没能创建桌面快捷方式，可以直接双击 start_webui.bat）" -ForegroundColor Yellow
    }
}

Step "检查环境"
& $Py -m voicetwin doctor

Write-Host "`n安装完成！" -ForegroundColor Green
Write-Host "  - 双击桌面上的「声音分身 VoiceTwin」或本文件夹里的 start_webui.bat 打开网页界面"
Write-Host "  - 上面的检查如果有 ❌，请按提示处理（详见《Windows详细使用教程》的常见问题部分）"
Pause-End
