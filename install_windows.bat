@echo off
chcp 65001 >nul
REM VoiceTwin installer launcher (logic lives in install_windows.ps1)
REM This file is UTF-8 (no BOM); chcp 65001 above makes the Chinese text below display correctly.
cd /d "%~dp0"
if not exist "%~dp0install_windows.ps1" goto noscript
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install_windows.ps1" %*
exit /b %errorlevel%
:noscript
echo 看起来你是在压缩包里直接双击的。请先右键压缩包 → 全部解压缩，再双击解压出来的 install_windows.bat
pause
exit /b 1
