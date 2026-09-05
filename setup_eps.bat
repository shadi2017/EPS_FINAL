@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" python -m venv .venv
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed
echo EPS Studio is ready. Open run_eps.bat to start.
pause
exit /b 0
:failed
echo Setup failed. Check Python and your internet connection.
pause
exit /b 1
