@echo off
REM VoiceTwin installer launcher (logic lives in install_windows.ps1)
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install_windows.ps1" %*
