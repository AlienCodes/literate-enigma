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
