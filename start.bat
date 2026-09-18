@echo off
echo ========================================================
echo               ArgusCX System Startup 
echo ========================================================
echo.

REM Kill any running instances first to avoid port conflicts
echo Stopping any running servers...
taskkill /F /IM python.exe 2>nul
taskkill /F /IM node.exe 2>nul
timeout /t 2 /nobreak >nul

echo.
echo Starting the Backend Server (Port 8000)...
start "ArgusCX Backend" cmd /k "cd /d %~dp0backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"

echo.
echo Starting the Frontend Server (Port 3000)...
start "ArgusCX Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ========================================================
echo  Both services are launching in separate windows.
echo  Wait ~30 seconds for the backend to fully start.
echo  Then open: http://localhost:3000
echo ========================================================
echo.
pause
