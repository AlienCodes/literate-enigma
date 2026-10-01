@echo off
chcp 65001 >nul
REM VoiceTwin installer launcher (logic lives in install_windows.ps1)
REM This file is UTF-8 (no BOM); chcp 65001 above makes the Chinese text below display correctly.
cd /d "%~dp0"
if not exist "%~dp0install_windows.ps1" goto noscript
REM Old-style console windows (for example "Run as administrator") on PCs whose language for non-Unicode programs
REM is not Chinese have no Chinese font, so every Chinese character shows as "?". Windows Terminal shows Chinese
REM correctly, so when it is installed, re-open this installer there (WT_SESSION is set inside Windows Terminal).
REM install_windows.ps1 also switches an old-style window to a Chinese font when Windows Terminal is not available.
if not "%~1"=="" goto run
if defined WT_SESSION goto run
if defined VOICETWIN_NO_WT goto run
where wt.exe >nul 2>nul || goto run
start "" wt.exe -d "%~dp0." cmd.exe /c "set VOICETWIN_NO_WT=1&& install_windows.bat"
if errorlevel 1 goto run
exit /b 0
:run
if not defined WT_SESSION echo If the Chinese text below shows as ??? : close this window, then double-click install_windows.bat (do not use "Run as administrator").
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install_windows.ps1" %*
exit /b %errorlevel%
:noscript
echo 看起来你是在压缩包里直接双击的。请先右键压缩包 → 全部解压缩，再双击解压出来的 install_windows.bat
pause
exit /b 1
