@echo off
setlocal
cd /d "%~dp0"

echo ============================================
echo   Gene Detective - local demo launcher
echo ============================================
echo.

netstat -ano | findstr ":8000" | findstr "LISTENING" >nul
if errorlevel 1 (
    echo [start] backend on port 8000 ...
    start "GD backend :8000" /D "%~dp0backend" cmd /k ".venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
    timeout /t 4 /nobreak >nul
) else (
    echo [skip]  port 8000 already listening
)

netstat -ano | findstr ":8123" | findstr "LISTENING" >nul
if errorlevel 1 (
    echo [start] frontend on port 8123 ...
    start "GD frontend :8123" /D "%~dp0" cmd /k "node tools\devserver.js"
    timeout /t 3 /nobreak >nul
) else (
    echo [skip]  port 8123 already listening
)

echo.
echo [open]  http://127.0.0.1:8123/home.html
echo [login] demo / demo1234   (all 6 cases cleared)
echo.
echo Close the two console windows to stop the servers.
start "" http://127.0.0.1:8123/home.html

endlocal
