@echo off
setlocal
cd /d "%~dp0"
py -3 --version >nul 2>&1
if errorlevel 1 (
 echo Install Python 3.11 or newer from python.org with the Python launcher, then run Setup.cmd again.
 pause
 exit /b 1
)
py -3 -m venv .venv
if errorlevel 1 goto failed
.venv\Scripts\python.exe -m pip install --require-hashes -r requirements.txt
if errorlevel 1 goto failed
.venv\Scripts\python.exe -m immigration_monitor init
if errorlevel 1 goto failed
echo Setup complete. Open Launch.cmd to use Immigration Source Monitor.
pause
exit /b 0
:failed
echo Setup failed. Read the error above; no success is implied.
pause
exit /b 1
