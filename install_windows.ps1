# VoiceTwin 声音分身 - Windows 安装脚本
# 用法：双击 install_windows.bat，或在 PowerShell 中运行：
#   powershell -ExecutionPolicy Bypass -File install_windows.ps1 [-Mode gsv -GsvRoot D:\GPT-SoVITS] [-Mode venv]
# 加 -NoPause 时不停下来问问题（用默认答案），适合自动测试。
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
# 老式黑色窗口（例如右键「以管理员身份运行」，或者没有 Windows Terminal 的电脑）在「非 Unicode 程序的语言」不是中文的
# 电脑上，默认字体没有中文字，下面所有中文都会显示成「?」。换成有中文字的等宽字体「新宋体」（NSimSun）。
# Windows Terminal 里不需要（它自己会找字体）；换不了也不影响安装。
function Use-ChineseConsoleFont {
    if ($env:WT_SESSION) { return }
    if ($PSVersionTable.PSEdition -eq "Core" -and -not $IsWindows) { return }
    try {
        if (-not ("VtConsoleFont" -as [type])) {
            Add-Type -ErrorAction Stop -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public static class VtConsoleFont {
    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    public struct FontInfo {
        public uint cbSize; public uint nFont; public short X; public short Y; public uint FontFamily; public uint FontWeight;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)] public string FaceName;
    }
    [DllImport("kernel32.dll", SetLastError = true)] static extern IntPtr GetStdHandle(int n);
    [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)] static extern bool GetCurrentConsoleFontEx(IntPtr h, bool max, ref FontInfo f);
    [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)] static extern bool SetCurrentConsoleFontEx(IntPtr h, bool max, ref FontInfo f);
    public static string Face() {
        FontInfo f = new FontInfo(); f.cbSize = (uint)Marshal.SizeOf(typeof(FontInfo));
        if (!GetCurrentConsoleFontEx(GetStdHandle(-11), false, ref f)) { return null; }
        return f.FaceName;
    }
    public static bool Use(string face) {
        FontInfo f = new FontInfo(); f.cbSize = (uint)Marshal.SizeOf(typeof(FontInfo));
        IntPtr h = GetStdHandle(-11);
        if (!GetCurrentConsoleFontEx(h, false, ref f)) { return false; }
        f.FaceName = face; f.FontFamily = 54; f.FontWeight = 400; f.nFont = 0; f.X = 0;
        if (f.Y < 16) { f.Y = 16; }
        return SetCurrentConsoleFontEx(h, false, ref f);
    }
}
"@
        }
        $face = [VtConsoleFont]::Face()
        if ($null -eq $face) { return }   # 输出被重定向，不是黑色窗口
        if (Test-ChineseFace $face) { return }
        foreach ($name in @("NSimSun", "SimSun", "MS Gothic")) {
            if ([VtConsoleFont]::Use($name)) {
                $now = [VtConsoleFont]::Face()
                if ($now -eq $name -or (Test-ChineseFace $now)) { return }
            }
        }
    } catch {}
}
function Test-ChineseFace([string]$face) {
    return ($face -match "[^\x00-\x7F]" -or $face -match "(?i)simsun|simhei|yahei|gothic|mincho|ming|song|kai|hei|sarasa|cjk|source han")
}
Use-ChineseConsoleFont
$env:PYTHONIOENCODING = "utf-8"

$script:StepNo = 0
$YesPattern = '^\s*([yY]|是)'
$NoPattern = '^\s*([nN]|否|不)'
$script:Total = 6

function Pause-End { if (-not $NoPause) { Read-Host "按回车键关闭窗口" | Out-Null } }
function Step($msg) {
    $script:StepNo++
    Write-Host "`n【第 $($script:StepNo)/$($script:Total) 步】$msg" -ForegroundColor Cyan
}
function Fail($msg) { Write-Host "`n[错误] $msg" -ForegroundColor Red; Pause-End; exit 1 }
function Ask([string]$prompt, [string]$default) {
    # -NoPause 时不等输入，直接用默认答案
    if ($NoPause) { Write-Host "$prompt（自动选择：$default）"; return $default }
    $answer = Read-Host $prompt
    return "$answer".Trim()
}
function Pip($py, [string[]]$pipArgs) {
    # --no-warn-script-location：不显示"voicetwin.exe 不在 PATH 里"的英文警告（程序不靠 PATH 启动，这个警告没有影响）
    & $py -m pip install --disable-pip-version-check --no-warn-script-location -i $Mirror @pipArgs
    if ($LASTEXITCODE -ne 0) {
        Write-Host "镜像源安装失败，改用官方源重试……" -ForegroundColor Yellow
        & $py -m pip install --disable-pip-version-check --no-warn-script-location @pipArgs
        if ($LASTEXITCODE -ne 0) { Fail "安装失败：pip install $($pipArgs -join ' ')。请检查网络后重新运行安装程序。" }
    }
}
function Test-NonAsciiOrSpace([string]$path) { return ($path -match "[^\x00-\x7F]" -or $path -match " ") }
function Test-NonAscii([string]$path) { return ($path -match "[^\x00-\x7F]") }

# ---------------------------------------------------------------- 找 GPT-SoVITS 整合包
function Test-GsvRoot([string]$p) {
    if (-not $p) { return $false }
    return (Test-Path -LiteralPath (Join-Path (Join-Path $p "runtime") "python.exe"))
}
function Test-GsvFull([string]$p) {
    return ((Test-GsvRoot $p) -and (Test-Path -LiteralPath (Join-Path $p "api_v2.py")))
}
function Normalize-GsvPath([string]$p) {
    if (-not $p) { return "" }
    $p = $p.Trim().Trim('"').Trim("'").Trim().TrimEnd('\', '/')
    if (-not $p) { return "" }
    # 粘贴了 go-webui.bat、runtime 文件夹或 python.exe 的路径：退回到整合包的根目录
    $leaf = Split-Path -Leaf $p
    if ($leaf -match '^(go-webui\.bat|go-webui\.ps1|api_v2\.py|webui\.py|python\.exe)$') {
        $p = Split-Path -Parent $p
        $leaf = Split-Path -Leaf $p
    }
    if ($leaf -eq "runtime") { $p = Split-Path -Parent $p }
    return $p
}
function Resolve-GsvRoot([string]$p) {
    $p = Normalize-GsvPath $p
    if (-not $p) { return "" }
    if (Test-GsvRoot $p) { return $p }
    # 常见错误：多套了一层文件夹，自动往下找一层
    if (Test-Path -LiteralPath $p) {
        $inner = Get-ChildItem -LiteralPath $p -Directory -ErrorAction SilentlyContinue |
            Where-Object { Test-GsvRoot $_.FullName } | Select-Object -First 1
        if ($inner) {
            Write-Host "已自动找到整合包目录：$($inner.FullName)" -ForegroundColor Yellow
            return $inner.FullName
        }
    }
    return ""
}
function Get-ConfigText {
    $cfgPath = Join-Path $Here "config.yaml"
    if (-not (Test-Path -LiteralPath $cfgPath)) { return "" }
    try { return [IO.File]::ReadAllText($cfgPath, [Text.Encoding]::UTF8) } catch { return "" }
}
function Get-RememberedGsv {
    $text = Get-ConfigText
    if (-not $text) { return "" }
    foreach ($m in [regex]::Matches($text, '(?m)^\s{4}root:\s*"?([^"\r\n#]+?)"?\s*(#|$)')) {
        $r = $m.Groups[1].Value.Trim()
        if ($r -and (Test-GsvRoot $r)) {
            try { return (Resolve-Path -LiteralPath $r).Path } catch { return $r }
        }
    }
    return ""
}
function Find-GsvCandidates {
    $found = New-Object System.Collections.Generic.List[string]
    $skip = '^(Windows|Program Files|Program Files \(x86\)|ProgramData|\$Recycle\.Bin|System Volume Information|Recovery|PerfLogs|\$WinREAgent|MSOCache)$'
    $places = New-Object System.Collections.Generic.List[string]
    try {
        foreach ($d in [System.IO.DriveInfo]::GetDrives()) {
            try { if ($d.DriveType -eq "Fixed" -and $d.IsReady) { $places.Add($d.RootDirectory.FullName) } } catch {}
        }
    } catch {}
    foreach ($name in @("Desktop", "MyDocuments")) {
        try { $f = [Environment]::GetFolderPath($name); if ($f) { $places.Add($f) } } catch {}
    }
    if ($env:USERPROFILE) { $places.Add((Join-Path $env:USERPROFILE "Downloads")) }
    foreach ($top in $places) {
        if (-not (Test-Path -LiteralPath $top)) { continue }
        $level1 = Get-ChildItem -LiteralPath $top -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -notmatch $skip }
        foreach ($dir in $level1) {
            if (Test-GsvFull $dir.FullName) { if (-not $found.Contains($dir.FullName)) { $found.Add($dir.FullName) }; continue }
            foreach ($sub in (Get-ChildItem -LiteralPath $dir.FullName -Directory -ErrorAction SilentlyContinue)) {
                if ((Test-GsvFull $sub.FullName) -and -not $found.Contains($sub.FullName)) { $found.Add($sub.FullName) }
            }
        }
    }
    return $found.ToArray()
}
function Find-GsvRoot([string]$given) {
    if ($given) {
        $r = Resolve-GsvRoot $given
        if ($r) { return $r }
        Write-Host "在 $given 里没有找到 GPT-SoVITS 整合包（打开正确的文件夹，应该能看到 runtime 文件夹和 go-webui.bat）。" -ForegroundColor Yellow
        if ($NoPause) { Fail "没有找到 GPT-SoVITS 整合包：$given" }
    }
    $default = Get-RememberedGsv
    $cands = @()
    Write-Host ""
    if ($default) {
        Write-Host "上次用的整合包：$default（直接按回车继续用它；要换就输入新的路径）" -ForegroundColor Green
    } else {
        Write-Host "正在自动查找 GPT-SoVITS 整合包（大约几秒钟）……"
        $cands = @(Find-GsvCandidates)
        if ($cands.Count -eq 1) {
            $default = $cands[0]
            Write-Host "找到了整合包：$default（直接按回车用它；不对的话输入正确的路径）" -ForegroundColor Green
        } elseif ($cands.Count -gt 1) {
            Write-Host "找到了 $($cands.Count) 个整合包："
            for ($i = 0; $i -lt $cands.Count; $i++) { Write-Host "  $($i + 1)) $($cands[$i])" }
            Write-Host "输入序号选择（直接按回车 = 第 1 个），或者输入别的路径。"
            $default = $cands[0]
        } else {
            Write-Host "请输入 GPT-SoVITS 整合包所在的文件夹路径（打开那个文件夹，里面能看到 go-webui.bat 和 runtime 文件夹）。"
            Write-Host "小技巧：在文件夹窗口顶部的地址栏点一下，复制路径，再回到这里右键粘贴。"
        }
    }
    $prompt = "GPT-SoVITS 整合包路径（例如 D:\GPT-SoVITS）"
    for ($try = 1; $try -le 5; $try++) {
        $answer = "$(Read-Host $prompt)".Trim()
        if (-not $answer -and $default) { $answer = $default }
        elseif ($answer -match '^\d+$' -and $cands.Count -gt 0) {
            $n = [int]$answer
            if ($n -ge 1 -and $n -le $cands.Count) { $answer = $cands[$n - 1] }
        }
        $r = Resolve-GsvRoot $answer
        if ($r) { return $r }
        $shown = if ($answer) { $answer } else { "（什么都没输入）" }
        Write-Host "在 $shown 里没有找到 GPT-SoVITS 整合包（打开正确的文件夹，应该能看到 runtime 文件夹和 go-webui.bat）。请再输入一次：" -ForegroundColor Yellow
    }
    Fail "试了 5 次都没有找到 GPT-SoVITS 整合包。请先确认整合包已经解压好，再重新双击 install_windows.bat。"
}

# ---------------------------------------------------------------- 预检查
function Check-Disk([string[]]$paths) {
    $seen = @{}
    foreach ($path in $paths) {
        if (-not $path) { continue }
        try {
            $root = [System.IO.Path]::GetPathRoot($path)
            if (-not $root -or $seen.ContainsKey($root)) { continue }
            $seen[$root] = $true
            $di = New-Object System.IO.DriveInfo($root)
            $gb = [math]::Round($di.AvailableFreeSpace / 1GB, 1)
            if ($gb -lt 20) {
                $drive = $root.TrimEnd('\', '/').TrimEnd(':')
                if (-not $drive) { $drive = $root }
                $ans = Ask "⚠️ $drive 盘只剩 $gb GB，训练大约需要 20~30GB。建议先清理空间。输入 Y 继续安装，直接按回车退出" "Y"
                if ($ans -notmatch $YesPattern) { Write-Host "已退出安装。清理出空间后再双击 install_windows.bat 即可。"; Pause-End; exit 1 }
            }
        } catch {}
    }
}
function Show-ExistingVoices {
    $ws = Join-Path $Here "workspace"
    $text = Get-ConfigText
    if ($text) {
        $m = [regex]::Match($text, '(?m)^workspace:\s*"?([^"\r\n#]+?)"?\s*(#|$)')
        if ($m.Success) {
            $w = $m.Groups[1].Value.Trim()
            if ($w) { if ([IO.Path]::IsPathRooted($w)) { $ws = $w } else { $ws = Join-Path $Here $w } }
        }
    }
    if (-not (Test-Path -LiteralPath $ws)) { return }
    $voices = @(Get-ChildItem -LiteralPath $ws -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -notlike "__*" -and (Test-Path -LiteralPath (Join-Path $_.FullName "manifest.jsonl")) } |
        ForEach-Object { $_.Name })
    if ($voices.Count -gt 0) {
        Write-Host "检测到你已经有的声音（共 $($voices.Count) 个）：$($voices -join '、')（重新安装不会删除它们）" -ForegroundColor Green
    }
}

function Get-ShortcutFolder {
    # 桌面上「声音分身 VoiceTwin」图标原来打开的文件夹（没有 / 读不出来返回 ""）
    try {
        $desktop = [Environment]::GetFolderPath("Desktop")
        $lnkPath = Join-Path $desktop "声音分身 VoiceTwin.lnk"
        if (-not (Test-Path -LiteralPath $lnkPath)) { return "" }
        # 中文文件名直接交给 WScript.Shell，在非中文系统上可能读不了：先复制成英文名再读
        $tmp = Join-Path ([System.IO.Path]::GetTempPath()) "VoiceTwin-old-shortcut.lnk"
        Copy-Item -LiteralPath $lnkPath -Destination $tmp -Force
        $shell = New-Object -ComObject WScript.Shell
        $dir = "$($shell.CreateShortcut($tmp).WorkingDirectory)"
        Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue
        return $dir.Trim()
    } catch { return "" }
}
function Get-VoiceNames([string]$root) {
    $ws = Join-Path $root "workspace"
    if (-not (Test-Path -LiteralPath $ws)) { return @() }
    return @(Get-ChildItem -LiteralPath $ws -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -notlike "__*" -and (Test-Path -LiteralPath (Join-Path $_.FullName "manifest.jsonl")) } |
        ForEach-Object { $_.Name })
}
function Check-OtherInstall {
    # 升级时解压到了新的文件夹（不是原来装的地方）：装好以后打开的是空的声音分身，老师会以为以前的声音都没了
    $old = Get-ShortcutFolder
    if (-not $old) { return }
    try {
        $same = ([IO.Path]::GetFullPath($old).TrimEnd('\') -ieq [IO.Path]::GetFullPath($Here).TrimEnd('\'))
    } catch { return }
    if ($same) { return }
    $oldVoices = @(Get-VoiceNames $old)
    if ($oldVoices.Count -eq 0) { return }
    if (@(Get-VoiceNames $Here).Count -gt 0) { return }
    $parent = Split-Path -Parent $old
    Write-Host ""
    Write-Host "⚠️ 你以前装的声音分身在 $old ，你的声音（$($oldVoices.Count) 个：$($oldVoices -join '、')）都在那里。" -ForegroundColor Yellow
    Write-Host "   这次的压缩包解压到了 $Here （是一个新的文件夹），在这里装好以后会看不到你以前的声音。" -ForegroundColor Yellow
    Write-Host "   请这样做：关掉这个窗口 → 把下载的压缩包重新解压，位置填 $parent ，提示有同名文件时选「替换」→ 双击 $old\install_windows.bat" -ForegroundColor Yellow
    $ans = Ask "一定要装到这个新文件夹的话，输入 Y 再按回车继续；直接按回车 = 退出" ""
    if ($ans -notmatch $YesPattern) { Write-Host "已退出安装（什么都没有改）。"; Pause-End; exit 1 }
}
function Test-VoiceTwinRunning {
    # 声音分身是不是正开着（网页在 7860~7869 端口）：升级时旧的黑色窗口要先关掉
    foreach ($port in 7860..7869) {
        try {
            $req = [System.Net.WebRequest]::Create("http://127.0.0.1:$port/config")
            $req.Proxy = $null
            $req.Timeout = 1500
            $resp = $req.GetResponse()
            $reader = New-Object System.IO.StreamReader($resp.GetResponseStream(), [Text.Encoding]::UTF8)
            $body = $reader.ReadToEnd()
            $reader.Close(); $resp.Close()
            if ($body -match "声音分身") { return $true }
        } catch {}
    }
    return $false
}
function Wait-OldClosed {
    if (-not (Test-VoiceTwinRunning)) { return }
    Write-Host ""
    Write-Host "⚠️ 声音分身现在还开着（另一个黑色窗口）。升级前请先把它关掉（点那个黑色窗口右上角的 ×），不然装好以后打开的还是旧版本。" -ForegroundColor Yellow
    for ($i = 0; $i -lt 5; $i++) {
        $ans = Ask "关好以后按回车继续（输入 Y 再按回车 = 不管它，直接继续）" "Y"
        if ($ans -match $YesPattern) { return }
        if (-not (Test-VoiceTwinRunning)) { Write-Host "好的，已经关掉了。" -ForegroundColor Green; return }
        Write-Host "还开着：请找到那个黑色窗口，点右上角的 ×。" -ForegroundColor Yellow
    }
}

Write-Host "=============================================" -ForegroundColor Green
Write-Host "   VoiceTwin 声音分身 安装程序" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
Write-Host "安装位置：$Here"
# 在压缩包里直接双击时，解压软件会把文件放进临时文件夹（%TEMP%\Temp1_xxx.zip、Rar$EXa…、7zO…）
if ($Here -match '\\AppData\\Local\\Temp\\' -or $Here -match '\\Temp\d+_[^\\]*\.zip(\\|$)') {
    Fail "看起来你是在压缩包里直接双击的。请先右键压缩包 → 全部解压缩，再双击解压出来的 install_windows.bat"
}
if (Test-NonAsciiOrSpace $Here) {
    Write-Host "提示：安装路径里有中文或空格，个别组件可能出问题。建议放到类似 D:\VoiceTwin 的路径。" -ForegroundColor Yellow
}
Show-ExistingVoices
Check-OtherInstall
Wait-OldClosed

if (-not $Mode) {
    Write-Host ""
    Write-Host "请选择安装方式："
    Write-Host "  1) 推荐：安装到 GPT-SoVITS 整合包里（最省事，语音识别和训练都用显卡，不用重复下载 PyTorch）"
    Write-Host "  2) 独立安装：创建单独的 Python 虚拟环境（需要本机已安装 Python 3.10 或 3.11，适合有经验的用户）"
    $choice = "$(Read-Host "请输入 1 或 2，然后按回车")".Trim()
    if ($choice -eq "2") { $Mode = "venv" } else { $Mode = "gsv" }
}

$Py = ""
if ($Mode -eq "gsv") {
    $script:Total = 7
    Step "检查电脑和整合包"
    $GsvRoot = Find-GsvRoot $GsvRoot
    Write-Host "整合包位置：$GsvRoot"
    $Py = Join-Path (Join-Path $GsvRoot "runtime") "python.exe"
    if (-not (Test-Path -LiteralPath $Py)) { Fail "没有找到 $Py 。请确认输入的是 GPT-SoVITS 整合包解压后的根目录（里面有 runtime 文件夹）。" }
    if (-not (Test-Path -LiteralPath (Join-Path $GsvRoot "api_v2.py"))) {
        Fail "这个 GPT-SoVITS 整合包版本太旧（缺少 api_v2.py），请下载最新版整合包后重试。"
    }
    if (-not (Test-Path -LiteralPath (Join-Path $GsvRoot "GPT_SoVITS\prepare_datasets\2-get-sv.py"))) {
        Fail "这个整合包版本较旧，不支持 v2Pro。请下载最新的 v2pro 整合包后重试。"
    }
    if (Test-NonAsciiOrSpace $GsvRoot) {
        $ans = Ask "⚠️ 整合包的路径里有中文或空格（$GsvRoot），训练时可能出错。建议把整合包移到类似 D:\GPT-SoVITS 的位置。输入 Y 继续安装，直接按回车退出" "Y"
        if ($ans -notmatch $YesPattern) { Write-Host "已退出安装。移动整合包后再双击 install_windows.bat 即可。"; Pause-End; exit 1 }
    }
    Check-Disk @($Here, $GsvRoot)
    Write-Host "检查通过。" -ForegroundColor Green

    Step "把声音分身装进整合包（约 1~3 分钟，下面滚动的英文是正常的，请不要关窗口）"
    # --no-deps：不改动整合包原有依赖的版本
    Pip $Py @("--no-deps", "--upgrade", "--force-reinstall", $Here)

    Step "安装辅助组件"
    Pip $Py @("pyloudnorm", "imageio-ffmpeg", "zhconv", "webrtcvad-wheels", "python-docx")
    Pip $Py @("--no-deps", "resemblyzer")
    # 「完美」档的「去杂音」版本要用 noisereduce（整合包里没有）。--no-deps：它要的 numpy、scipy、joblib、tqdm、
    # matplotlib 整合包里都有，不改动整合包原有依赖的版本
    Pip $Py @("--no-deps", "noisereduce")
    # 精准声纹打分（"像你本人"百分比）用 onnxruntime 运行模型：整合包一般自带 onnxruntime-gpu，没有才装 CPU 版
    & $Py -c "import onnxruntime" *> $null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "安装声纹打分组件 onnxruntime……"
        Pip $Py @("onnxruntime")
    }
    # 语音识别：整合包一般自带 faster-whisper；没有的话按 GPT-SoVITS 官方方式 --no-deps 安装
    & $Py -c "import faster_whisper" *> $null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "安装语音识别组件 faster-whisper……"
        Pip $Py @("--no-deps", "faster-whisper")
    }
} else {
    $script:Total = 8
    Step "检查电脑和 Python"
    Check-Disk @($Here)
    $sysPy = $null
    foreach ($cand in @("py -3.11", "py -3.10", "python")) {
        try {
            $ver = Invoke-Expression "$cand -c `"import sys;print('%d.%d'%sys.version_info[:2])`"" 2>$null
            if ($ver -match "^3\.(9|10|11|12)$") { $sysPy = $cand; break }
        } catch {}
    }
    if (-not $sysPy) { Fail "没有找到 Python 3.9~3.12。请从 https://www.python.org/downloads/ 安装 Python 3.11（安装时勾选 Add python.exe to PATH）后重试。" }
    Write-Host "找到 Python：$sysPy" -ForegroundColor Green

    Step "创建独立的 Python 环境 .venv（使用 $sysPy）"
    Invoke-Expression "$sysPy -m venv .venv"
    $Py = Join-Path (Join-Path (Join-Path $Here ".venv") "Scripts") "python.exe"
    if (-not (Test-Path -LiteralPath $Py)) { $Py = Join-Path (Join-Path (Join-Path $Here ".venv") "bin") "python" }
    & $Py -m pip install --disable-pip-version-check -U pip -i $Mirror | Out-Null

    Step "安装声音分身及语音识别、网页界面等组件（需要几分钟，下面滚动的英文是正常的，请不要关窗口）"
    Pip $Py @("-e", "$Here[asr,webui,denoise,docx,sv]")

    Step "安装声纹打分组件（PyTorch CPU 版 + resemblyzer）"
    Pip $Py @("torch", "--index-url", "https://download.pytorch.org/whl/cpu")
    Pip $Py @("webrtcvad-wheels")
    Pip $Py @("--no-deps", "resemblyzer")
}

Step "生成设置文件"
$cfgArgs = @("-m", "voicetwin", "init-config")
if ($GsvRoot) { $cfgArgs += @("--gptsovits-root", $GsvRoot) }
if ($Mode -eq "gsv") { $cfgArgs += @("--backend", "gptsovits") }
& $Py @cfgArgs
if ($LASTEXITCODE -ne 0) { Fail "生成设置文件 config.yaml 失败（上面有原因）。" }
if ($GsvRoot) {
    & $Py -m voicetwin download-models --check
    $modelCode = $LASTEXITCODE
    if ($modelCode -eq 3) {
        $ans = Ask "检测到缺少 GPT-SoVITS 预训练模型（大约 1~2GB）。现在自动下载吗？直接按回车 = 下载，输入 N = 以后再说" "N"
        if ($ans -notmatch $NoPattern) {
            & $Py -m voicetwin download-models --source hf-mirror
            if ($LASTEXITCODE -ne 0) {
                Write-Host "⚠️ 模型没有下载成功（多半是网络问题）。安装会继续；以后重新双击 install_windows.bat 会再问一次要不要下载。" -ForegroundColor Yellow
            }
        } else {
            Write-Host "好的，先不下载。以后重新双击 install_windows.bat 会再问一次。" -ForegroundColor Yellow
        }
    } elseif ($modelCode -ne 0) {
        Write-Host "⚠️ 没能检查预训练模型是否齐全（下面的环境检查会再看一次）。" -ForegroundColor Yellow
    }
}

Step "下载精准声纹打分的模型（约 170 MB，用来算「像你本人」的百分比）"
& $Py -m voicetwin download-models --sv
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️ 声纹模型没有下载成功（多半是网络问题）。不影响使用：先用旧的打分方式；以后在网页上点「⬇️ 下载缺少的模型」再试。" -ForegroundColor Yellow
}

Step "生成桌面图标"
$pre = @("@echo off", "chcp 65001 >nul")
$lines = @("cd /d `"%~dp0`"", "if not defined HF_ENDPOINT set `"HF_ENDPOINT=https://hf-mirror.com`"")
if ($GsvRoot) { $lines += "set `"PATH=$GsvRoot;$GsvRoot\runtime;%PATH%`"" }
$lines += "if not exist `"$Py`" goto nogsv"
# 窗口标题只给网页启动脚本加（goto 跳转：提示文字里有全角括号，不放进 ( ) 代码块）
$startHeader = (($pre + @("title 声音分身 VoiceTwin（使用期间请不要关闭）") + $lines) -join "`r`n") + "`r`n"
$header = (($pre + $lines) -join "`r`n") + "`r`n"
if ($GsvRoot) {
    $missing = "echo 找不到 GPT-SoVITS 整合包：$GsvRoot`r`n" +
               "echo 如果你移动或改名了整合包文件夹，请重新双击 install_windows.bat，输入新的位置。`r`n"
} else {
    $missing = "echo 找不到声音分身的 Python 环境：$Py`r`n" +
               "echo 如果你移动或改名了文件夹，请重新双击 install_windows.bat。`r`n"
}
$footer = "pause`r`nexit /b 0`r`n:nogsv`r`n" + $missing + "pause`r`nexit /b 1`r`n"
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText((Join-Path $Here "start_webui.bat"),
    $startHeader + "echo 正在启动声音分身，第一次大约需要 10~30 秒，请稍候……（浏览器会自动打开）`r`n`"$Py`" -m voicetwin webui`r`n" + $footer,
    $utf8NoBom)
[System.IO.File]::WriteAllText((Join-Path $Here "voicetwin.bat"),
    $header + "`"$Py`" -m voicetwin %*`r`nexit /b %errorlevel%`r`n:nogsv`r`n" + $missing + "exit /b 1`r`n", $utf8NoBom)
Write-Host "已生成启动脚本 start_webui.bat 和 voicetwin.bat" -ForegroundColor Green

$shortcutOk = $false
if (-not $NoShortcut) {
    try {
        $desktop = [Environment]::GetFolderPath("Desktop")
        $target = Join-Path $Here "start_webui.bat"
        # Windows 的快捷方式组件（WScript.Shell）在「非 Unicode 程序的语言」不是中文的电脑上，会把中文文件名变成 ????，
        # 然后保存失败（Unable to save shortcut "...\???? VoiceTwin.lnk"）。所以先用英文文件名建好，
        # 再用 PowerShell（支持中文）改成中文名、移到桌面（桌面在 OneDrive 里也可以）。
        $tmpDir = $Here
        if (Test-NonAscii $tmpDir) { $tmpDir = [System.IO.Path]::GetTempPath() }
        $tmpLnk = Join-Path $tmpDir "VoiceTwin-shortcut.lnk"
        $shell = New-Object -ComObject WScript.Shell
        $lnk = $shell.CreateShortcut($tmpLnk)
        $lnk.TargetPath = $target
        $lnk.WorkingDirectory = $Here
        $lnk.Save()
        # 安装文件夹的路径里有中文时，快捷方式里记下的位置也可能变成 ????：读回来核对，不对就不放到桌面
        if (-not (Test-Path -LiteralPath $shell.CreateShortcut($tmpLnk).TargetPath)) {
            Remove-Item -LiteralPath $tmpLnk -Force -ErrorAction SilentlyContinue
            throw "安装文件夹的路径里有中文（$Here）"
        }
        Move-Item -LiteralPath $tmpLnk -Destination (Join-Path $desktop "声音分身 VoiceTwin.lnk") -Force
        $shortcutOk = $true
        Write-Host "已在桌面创建快捷方式「声音分身 VoiceTwin」" -ForegroundColor Green
    } catch {
        if ($tmpLnk) { Remove-Item -LiteralPath $tmpLnk -Force -ErrorAction SilentlyContinue }
        Write-Host "没能在桌面创建快捷方式（$($_.Exception.Message)）。" -ForegroundColor Yellow
        Write-Host "  自己创建：在 $Here 里右键 start_webui.bat → 发送到 → 桌面快捷方式（Windows 11 先点「显示更多选项」）" -ForegroundColor Yellow
        Write-Host "  不创建也可以：以后直接双击 $Here\start_webui.bat" -ForegroundColor Yellow
    }
}

Step "检查环境（约 10~30 秒）"
& $Py -m voicetwin doctor
$doctorCode = $LASTEXITCODE

if ($shortcutOk) { $howToOpen = "双击桌面上的「声音分身 VoiceTwin」" } else { $howToOpen = "双击 $Here 里的 start_webui.bat" }
Write-Host ""
if ($doctorCode -eq 0) {
    Write-Host "✅ 安装成功！$($howToOpen)就能开始使用。" -ForegroundColor Green
} elseif ($doctorCode -eq 2) {
    Write-Host "⚠️ 程序已经装好，但还有问题要先处理：请看上面标着 ❌ 的行。处理完后再双击 install_windows.bat 检查一次（你的数据不会丢）。" -ForegroundColor Yellow
    Write-Host "  - 「NVIDIA 显卡」或「PyTorch 显卡加速」是 ❌ 时，先安装最新显卡驱动并重启电脑，否则训练会非常慢" -ForegroundColor Yellow
    Write-Host "  - 其它问题请看《快速上手》最后的「遇到问题」" -ForegroundColor Yellow
} else {
    Write-Host "❌ 环境检查没能运行。请把这个窗口拍照或截图，发给帮你安装的人。" -ForegroundColor Red
}

if ($NoPause) { exit $doctorCode }
if ($doctorCode -eq 0 -or $doctorCode -eq 2) {
    $open = "$(Read-Host "现在就打开声音分身吗？直接按回车 = 打开，输入 N 再按回车 = 不打开")".Trim()
    if ($open -notmatch $NoPattern) {
        Start-Process -FilePath (Join-Path $Here "start_webui.bat") -WorkingDirectory $Here
    }
} else {
    Pause-End
}
