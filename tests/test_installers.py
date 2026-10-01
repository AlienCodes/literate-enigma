"""安装脚本：装进 GPT-SoVITS 整合包（推荐的安装方式）时，「完美」档要用的组件也要装上。"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_windows_installer_gsv_mode_installs_noisereduce():
    raw = (ROOT / "install_windows.ps1").read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf")  # PowerShell 5 要 UTF-8 BOM 才认中文
    text = raw[3:].decode("utf-8")
    assert "\n" not in text.replace("\r\n", "")  # 全部是 CRLF
    gsv = text.split('if ($Mode -eq "gsv") {', 1)[1].split("\r\n} else {", 1)[0]
    # 整合包里没有 noisereduce：不装的话「完美」档永远只有「未去杂音」一个版本，提示的「重新安装」也没用
    assert 'Pip $Py @("--no-deps", "noisereduce")' in gsv


def test_linux_installer_gsv_mode_installs_noisereduce():
    text = (ROOT / "install.sh").read_text(encoding="utf-8")
    gsv = text.split('if [[ -n "$GSV" ]]; then', 1)[1].split("\nelse\n", 1)[0]
    assert "pipi --no-deps noisereduce" in gsv and "python-docx" in gsv


# ---- 桌面快捷方式：老师的电脑上「非 Unicode 程序的语言」不是中文，WScript.Shell 把中文文件名变成 ????，保存失败 ----
_FAKE_WSCRIPT = r'''
class FakeLnk {
    [string]$Path; [string]$TargetPath; [string]$WorkingDirectory
    FakeLnk([string]$p) {
        $this.Path = $p
        if (Test-Path -LiteralPath $p) { $this.TargetPath = (Get-Content -LiteralPath $p -Raw).Trim() }
    }
    [void] Save() {
        # 和老师电脑上一样：中文变成 ? 之后，文件名不合法，保存失败；记下的目标位置里的中文也变成 ?
        if ($this.Path -match "[^\x00-\x7F]") { throw ("Unable to save shortcut `"" + ($this.Path -replace "[^\x00-\x7F]", "?") + "`".") }
        Set-Content -LiteralPath $this.Path -Value ($this.TargetPath -replace "[^\x00-\x7F]", "?") -Encoding utf8
    }
}
class FakeShell { [object] CreateShortcut([string]$p) { return [FakeLnk]::new($p) } }
function New-Object { param([string]$ComObject) if ($ComObject -eq "WScript.Shell") { return [FakeShell]::new() }; throw "unexpected New-Object" }
'''


def _shortcut_block(text: str) -> str:
    block = text.split("$shortcutOk = $false\r\nif (-not $NoShortcut) {", 1)[1].split("\r\n}\r\n\r\nStep ", 1)[0]
    return block.replace('[Environment]::GetFolderPath("Desktop")', "$TestDesktop")


def _run_shortcut(tmp_path, here_name: str):
    import shutil
    import subprocess

    import pytest

    pwsh = shutil.which("pwsh")
    if not pwsh:
        pytest.skip("没有 PowerShell 7（pwsh）")
    text = (ROOT / "install_windows.ps1").read_bytes()[3:].decode("utf-8")
    fn = [ln for ln in text.split("\r\n") if ln.startswith("function Test-NonAscii(")]
    here = tmp_path / here_name
    desk = tmp_path / "OneDrive" / "Desktop"
    here.mkdir()
    desk.mkdir(parents=True)
    (here / "start_webui.bat").write_text("@echo off\r\n", encoding="utf-8")
    script = "\r\n".join([_FAKE_WSCRIPT, *fn, f"$Here = '{here}'", f"$TestDesktop = '{desk}'", "$NoShortcut = $false",
                          "$shortcutOk = $false", "if (-not $NoShortcut) {" + _shortcut_block(text) + "\r\n}",
                          'Write-Host "OK=$shortcutOk"'])
    ps1 = tmp_path / "t.ps1"
    ps1.write_bytes(b"\xef\xbb\xbf" + script.encode("utf-8"))
    out = subprocess.run([pwsh, "-NoProfile", "-File", str(ps1)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         timeout=120).stdout.decode("utf-8", "replace")
    return out, here, desk


def test_windows_shortcut_survives_non_chinese_ansi_codepage(tmp_path):
    out, here, desk = _run_shortcut(tmp_path, "VoiceTwin")
    lnk = desk / "声音分身 VoiceTwin.lnk"
    assert "OK=True" in out, out
    assert lnk.exists() and lnk.read_text(encoding="utf-8-sig").strip() == str(here / "start_webui.bat")
    assert not list(here.glob("*.lnk"))  # 临时的英文名快捷方式已经移走


def test_windows_shortcut_chinese_install_folder_falls_back_to_hint(tmp_path):
    out, here, desk = _run_shortcut(tmp_path, "声音分身")
    assert "OK=False" in out and "没能在桌面创建快捷方式" in out and "发送到" in out, out
    assert not list(desk.glob("*.lnk"))  # 不放一个指向错误位置的快捷方式


def test_requirements_accept_gsv_package_versions():
    """GPT-SoVITS 官方整合包（v2pro-20250604）自带的版本必须满足声音分身的依赖，
    否则安装时 pip 会打出红色的 ERROR（老师安装时就看到了 librosa 0.9.2 的这条）。"""
    import re

    import pytest

    packaging = pytest.importorskip("packaging.requirements")
    from packaging.version import Version

    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    deps = re.search(r"dependencies = \[(.*?)\]", text, re.S).group(1)
    reqs = {r.name.lower(): r for r in (packaging.Requirement(s) for s in re.findall(r'"([^"]+)"', deps))}
    gsv = {"numpy": "1.23.4", "scipy": "1.9.3", "soundfile": "0.12.1", "librosa": "0.9.2", "pyloudnorm": "0.2.0",
           "imageio-ffmpeg": "0.6.0"}
    for name, ver in gsv.items():
        assert Version(ver) in reqs[name].specifier, f"{name} {ver} 不满足 {reqs[name]}"


# ---- 老式黑色窗口里中文全部变成「?」（老师右键「以管理员身份运行」安装 v0.1.8 时遇到）----
def test_windows_launcher_reopens_in_windows_terminal():
    text = (ROOT / "install_windows.bat").read_bytes().decode("utf-8")
    assert "\n" not in text.replace("\r\n", "")  # 全部是 CRLF
    lines = text.split("\r\n")
    ps_line = next(i for i, ln in enumerate(lines) if ln.startswith("powershell "))
    start = next(i for i, ln in enumerate(lines) if ln.startswith('start "" wt.exe'))
    assert start < ps_line
    guards = lines[:start]
    # 带参数运行（自动测试、高级用法）、已经在 Windows Terminal 里、已经换过一次：都不再换窗口，避免来回打开
    assert 'if not "%~1"=="" goto run' in guards and "if defined WT_SESSION goto run" in guards
    assert "if defined VOICETWIN_NO_WT goto run" in guards and "where wt.exe >nul 2>nul || goto run" in guards
    assert '-d "%~dp0."' in lines[start] and "VOICETWIN_NO_WT=1&& install_windows.bat" in lines[start]
    assert lines[start + 1] == "if errorlevel 1 goto run" and lines[start + 2] == "exit /b 0"
    # 换不了窗口时给一句看得见的英文提示（中文这时候显示不出来）
    assert any("Run as administrator" in ln and ln.isascii() for ln in lines[start:ps_line])


def test_windows_installer_switches_old_console_to_chinese_font():
    text = (ROOT / "install_windows.ps1").read_bytes()[3:].decode("utf-8")
    call = text.index("\r\nUse-ChineseConsoleFont\r\n")
    first_output = min(text.index("Write-Host"), text.index("\r\nStep "))
    assert text.index("function Use-ChineseConsoleFont") < call
    assert text.index("function Test-ChineseFace") < call
    assert call < text.index("function Step(")  # 在打印任何中文之前
    assert "if ($env:WT_SESSION) { return }" in text and '"NSimSun", "SimSun", "MS Gothic"' in text
    assert first_output > 0


def test_windows_installer_font_code_compiles():
    """C# 部分用 PowerShell 实际编译一次（有 pwsh 时）；在 Windows 上再调用一次，没有黑色窗口时不能报错。"""
    import re
    import shutil
    import subprocess

    import pytest

    pwsh = shutil.which("pwsh")
    if not pwsh:
        pytest.skip("没有 PowerShell 7（pwsh）")
    text = (ROOT / "install_windows.ps1").read_bytes()[3:].decode("utf-8")
    csharp = re.search(r'-TypeDefinition @"\r\n(.*?)\r\n"@', text, re.S).group(1)
    script = ("Add-Type -ErrorAction Stop -TypeDefinition @'\n" + csharp.replace("\r\n", "\n") + "\n'@\n"
              "if ($IsWindows) { [void][VtConsoleFont]::Face() }\n'COMPILED'\n")
    out = subprocess.run([pwsh, "-NoProfile", "-Command", script], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         timeout=180).stdout.decode("utf-8", "replace")
    assert "COMPILED" in out, out


def test_windows_launcher_runs_installer_without_windows_terminal(tmp_path):
    """只在 Windows 上跑：没有 Windows Terminal、或者已经在里面时，install_windows.bat 直接运行 install_windows.ps1。"""
    import os
    import shutil
    import subprocess
    import sys

    import pytest

    if sys.platform != "win32":
        pytest.skip("只在 Windows 上测试")
    shutil.copy(ROOT / "install_windows.bat", tmp_path / "install_windows.bat")
    (tmp_path / "install_windows.ps1").write_bytes(b"\xef\xbb\xbfWrite-Output 'DUMMY-INSTALLER-RAN'\r\n")
    sysroot = os.environ.get("SystemRoot", r"C:\Windows")
    base = {k: v for k, v in os.environ.items() if k.upper() not in ("WT_SESSION", "VOICETWIN_NO_WT", "PATH")}
    base["PATH"] = os.pathsep.join([os.path.join(sysroot, "System32"), sysroot,
                                    os.path.join(sysroot, "System32", "WindowsPowerShell", "v1.0")])
    for extra in ({}, {"WT_SESSION": "test"}):
        out = subprocess.run(["cmd", "/c", "install_windows.bat"], cwd=str(tmp_path), env=dict(base, **extra),
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=120).stdout.decode("utf-8", "replace")
        assert "DUMMY-INSTALLER-RAN" in out, out
