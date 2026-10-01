from pathlib import Path

SP = Path("<草稿目录>")
p = SP / "u6_install_windows.ps1.txt"
s = p.read_text(encoding="utf-8")
old = """# 在压缩包里直接双击时，解压软件会把文件放进临时文件夹（Temp1_xxx.zip、Rar$EXa…、7zO…）
if ($Here -match '\\\\AppData\\\\Local\\\\Temp\\\\' -or $Here -match '\\\\(Temp\\d*_[^\\\\]*\\.zip|Rar\\$[^\\\\]*|7z[^\\\\]*)(\\\\|$)') {
"""
new = """# 在压缩包里直接双击时，解压软件会把文件放进临时文件夹（%TEMP%\\Temp1_xxx.zip、Rar$EXa…、7zO…）
if ($Here -match '\\\\AppData\\\\Local\\\\Temp\\\\' -or $Here -match '\\\\Temp\\d+_[^\\\\]*\\.zip(\\\\|$)') {
"""
assert s.count(old) == 1
s = s.replace(old, new)
p.write_text(s, encoding="utf-8")
out = Path("<仓库>/.claude/worktrees/wf_08725f86-d54-6/install_windows.ps1")
out.write_bytes(b"\xef\xbb\xbf" + s.replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8"))
(SP / "u6_regex.ps1").write_text(r"""foreach ($h in @('C:\Users\x\AppData\Local\Temp\Temp1_VoiceTwin.zip\VoiceTwin', 'C:\Users\x\AppData\Local\Temp\Rar$EXa123\VoiceTwin', 'D:\Temp\VoiceTwin', 'D:\VoiceTwin', 'E:\x\Temp2_VoiceTwin-v0.1.6.zip', 'D:\7zip\VoiceTwin')) {
  $hit = ($h -match '\\AppData\\Local\\Temp\\' -or $h -match '\\Temp\d+_[^\\]*\.zip(\\|$)')
  Write-Host "$hit  $h"
}
""", encoding="utf-8")
print("ok")
