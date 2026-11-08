@echo off
rem Gene Detective - start backend server (uvicorn, port 8000)
chcp 65001 >nul
cd /d %~dp0
echo Starting backend on http://127.0.0.1:8000 ...
".venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000
pause
