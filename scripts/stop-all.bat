@echo off
setlocal

REM === NetDev Tool: Stop Backend(:8083), Celery Worker/Beat, Frontend(:5175) and local Qdrant(:6333) ===

set "PATH=C:\Windows\System32;%PATH%"

set "FOUND=0"

echo [NetDev] Looking for backend process on port 8083 ...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr :8083 ^| findstr LISTENING') do (
    echo [NetDev] Killing backend PID %%p
    taskkill /F /PID %%p >nul 2>&1
    set "FOUND=1"
)

echo [NetDev] Looking for frontend process on port 5175 ...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr :5175 ^| findstr LISTENING') do (
    echo [NetDev] Killing frontend PID %%p
    taskkill /F /PID %%p >nul 2>&1
    set "FOUND=1"
)

echo [NetDev] Looking for Celery worker window ...
taskkill /FI "WINDOWTITLE eq NetDev-Tool-Celery" /T /F >nul 2>&1
if not errorlevel 1 (
    echo [NetDev] Celery worker stopped
    set "FOUND=1"
)

echo [NetDev] Looking for Celery beat window ...
taskkill /FI "WINDOWTITLE eq NetDev-Tool-CeleryBeat" /T /F >nul 2>&1
if not errorlevel 1 (
    echo [NetDev] Celery beat stopped
    set "FOUND=1"
)

echo [NetDev] Looking for local Qdrant on port 6333 ...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr :6333 ^| findstr LISTENING') do (
    echo [NetDev] Killing Qdrant PID %%p
    taskkill /F /PID %%p >nul 2>&1
    set "FOUND=1"
)
taskkill /FI "WINDOWTITLE eq NetDev-Tool-Qdrant" /T /F >nul 2>&1

if "%FOUND%"=="0" (
    echo [NetDev] no backend, Celery worker, frontend or Qdrant is running
) else (
    echo [NetDev] done
)

endlocal
exit /b 0
