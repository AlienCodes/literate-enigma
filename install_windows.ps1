# VoiceTwin 声音分身 - Windows 安装脚本
# 用法：双击 install_windows.bat，或在 PowerShell 中运行：
#   powershell -ExecutionPolicy Bypass -File install_windows.ps1 [-Mode gsv -GsvRoot D:\GPT-SoVITS] [-Mode venv]
param(
    [string]$Mode = "",
    [string]$GsvRoot = "",
    [string]$Mirror = "https://pypi.tuna.tsinghua.edu.cn/simple"
)
$ErrorActionPreference = "Stop"
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Here
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

function Step($msg) { Write-Host "`n==> $msg" -ForegroundColor Cyan }
function Fail($msg) { Write-Host "`n[错误] $msg" -ForegroundColor Red; Read-Host "按回车键退出"; exit 1 }
function Pip($py, [string[]]$pipArgs) {
    & $py -m pip install --disable-pip-version-check -i $Mirror @pipArgs
    if ($LASTEXITCODE -ne 0) {
        Write-Host "镜像安装失败，改用官方源重试……" -ForegroundColor Yellow
        & $py -m pip install --disable-pip-version-check @pipArgs
        if ($LASTEXITCODE -ne 0) { Fail "pip install $($pipArgs -join ' ') 失败" }
    }
}

Write-Host "=============================================" -ForegroundColor Green
Write-Host "   VoiceTwin 声音分身 安装程序" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green

if (-not $Mode) {
    Write-Host ""
    Write-Host "请选择安装方式："
    Write-Host "  1) 推荐：安装到 GPT-SoVITS 整合包里（最省事，语音识别和训练都用显卡，不用重复下载 PyTorch）"
    Write-Host "     还没有整合包？先按 README 的说明下载 GPT-SoVITS 官方 Windows 整合包并解压。"
    Write-Host "  2) 独立安装：创建单独的 Python 虚拟环境（需要本机已安装 Python 3.10 或 3.11）"
    $choice = Read-Host "请输入 1 或 2"
    if ($choice -eq "2") { $Mode = "venv" } else { $Mode = "gsv" }
}

$Py = ""
if ($Mode -eq "gsv") {
    if (-not $GsvRoot) { $GsvRoot = Read-Host "请输入 GPT-SoVITS 整合包所在文件夹（里面有 go-webui.bat 和 runtime 文件夹）" }
    $GsvRoot = $GsvRoot.Trim('"').Trim()
    $Py = Join-Path $GsvRoot "runtime\python.exe"
    if (-not (Test-Path $Py)) { Fail "没有找到 $Py ，请确认路径是 GPT-SoVITS 整合包的根目录。" }
    Step "安装 VoiceTwin 到整合包环境（--no-deps：不改动整合包已有的依赖版本）"
    Pip $Py @("--no-deps", "-e", $Here)
    Pip $Py @("pyloudnorm", "imageio-ffmpeg", "zhconv", "webrtcvad-wheels")
    Pip $Py @("--no-deps", "resemblyzer")
    Step "生成配置文件 config.yaml"
    & $Py -m voicetwin init-config --gptsovits-root "$GsvRoot" --backend gptsovits --force
} else {
    $sysPy = $null
    foreach ($cand in @("py -3.11", "py -3.10", "python")) {
        try {
            $ver = Invoke-Expression "$cand -c `"import sys;print('%d.%d'%sys.version_info[:2])`"" 2>$null
            if ($ver -match "^3\.(9|10|11|12)$") { $sysPy = $cand; break }
        } catch {}
    }
    if (-not $sysPy) { Fail "没有找到 Python 3.9~3.12。请从 https://www.python.org/downloads/ 安装 Python 3.11（勾选 Add to PATH）后重试。" }
    Step "创建虚拟环境 .venv（使用 $sysPy）"
    Invoke-Expression "$sysPy -m venv .venv"
    $Py = Join-Path $Here ".venv\Scripts\python.exe"
    & $Py -m pip install --disable-pip-version-check -U pip -i $Mirror | Out-Null
    Step "安装 VoiceTwin 及语音识别、网页界面等依赖（需要几分钟）"
    Pip $Py @("-e", "$Here[asr,webui,denoise,docx]")
    Step "安装声纹打分组件（PyTorch CPU 版 + resemblyzer）"
    Pip $Py @("torch", "--index-url", "https://download.pytorch.org/whl/cpu")
    Pip $Py @("webrtcvad-wheels")
    Pip $Py @("--no-deps", "resemblyzer")
    Step "生成配置文件 config.yaml"
    if (-not (Test-Path (Join-Path $Here "config.yaml"))) {
        if ($GsvRoot) { & $Py -m voicetwin init-config --gptsovits-root "$GsvRoot" }
        else { & $Py -m voicetwin init-config }
    }
}

Step "生成启动脚本 start_webui.bat / voicetwin.bat"
$pathLine = ""
if ($GsvRoot) { $pathLine = "set `"PATH=$GsvRoot;$GsvRoot\runtime;%PATH%`"`r`n" }
$header = "@echo off`r`nchcp 65001 >nul`r`ncd /d `"%~dp0`"`r`n$pathLine"
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText((Join-Path $Here "start_webui.bat"), $header + "`"$Py`" -m voicetwin webui`r`npause`r`n", $utf8NoBom)
[System.IO.File]::WriteAllText((Join-Path $Here "voicetwin.bat"), $header + "`"$Py`" -m voicetwin %*`r`n", $utf8NoBom)

Step "检查环境"
& $Py -m voicetwin doctor

Write-Host "`n安装完成！" -ForegroundColor Green
Write-Host "  - 双击 start_webui.bat 打开网页界面（浏览器访问 http://127.0.0.1:7860）"
Write-Host "  - 或在本目录打开命令行，使用 voicetwin.bat <命令>，例如： voicetwin.bat auto -v 我的声音 -i D:\讲课视频"
Read-Host "按回车键退出"
