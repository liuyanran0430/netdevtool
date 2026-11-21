@echo off
setlocal

REM === NetDev Tool: Start MySQL + Redis + Qdrant + Backend(FastAPI :8083) + Celery + Frontend(Vite :5175) ===

set "PATH=C:\Windows\System32;D:\nvm\nodejs;%PATH%"
set "ROOT=%~dp0.."
set "PY=%ROOT%\netdevtool-api\.venv\Scripts\python.exe"

REM ---------- 1. MySQL service ----------
echo [NetDev] Checking MySQL service ...
sc query MySQL >nul 2>&1
if errorlevel 1 (
    echo [NetDev] WARN: MySQL service "MySQL" not found, skip.
) else (
    sc query MySQL | findstr /I "RUNNING" >nul 2>&1
    if errorlevel 1 (
        echo [NetDev] Starting MySQL service ...
        net start MySQL
        if errorlevel 1 (
            echo [NetDev] WARN: failed to start MySQL, please run as Administrator.
        ) else (
            echo [NetDev] MySQL started.
        )
    ) else (
        echo [NetDev] MySQL already running.
    )
)

REM ---------- 2. Redis service (Celery broker) ----------
echo [NetDev] Checking Redis service ...
sc query Redis >nul 2>&1
if errorlevel 1 (
    echo [NetDev] WARN: Redis service "Redis" not found, translation tasks unavailable.
) else (
    sc query Redis | findstr /I "RUNNING" >nul 2>&1
    if errorlevel 1 (
        echo [NetDev] Starting Redis service ...
        net start Redis
        if errorlevel 1 (
            echo [NetDev] WARN: failed to start Redis, please run as Administrator.
        ) else (
            echo [NetDev] Redis started.
        )
    ) else (
        echo [NetDev] Redis already running.
    )
)

REM ---------- 3. Local Qdrant (:6333) ----------
set "QDRANT_DIR=%ROOT%\netdevtool-api\.qdrant-server"
echo [NetDev] Checking local Qdrant on port 6333 ...
netstat -ano | findstr :6333 | findstr LISTENING >nul 2>&1
if not errorlevel 1 (
    echo [NetDev] Qdrant already running.
) else (
    if not exist "%QDRANT_DIR%\qdrant.exe" (
        echo [NetDev] WARN: qdrant.exe not found at %QDRANT_DIR%, knowledge indexing unavailable.
    ) else (
        echo [NetDev] Starting local Qdrant ...
        start "NetDev-Tool-Qdrant" /d "%QDRANT_DIR%" "%QDRANT_DIR%\qdrant.exe"
        call :wait_port 6333
        if errorlevel 1 (
            echo [NetDev] WARN: Qdrant did not open port 6333 in time.
        ) else (
            echo [NetDev] Qdrant started.
        )
    )
)

REM ---------- 4. Backend (FastAPI :8083) ----------
echo [NetDev] Cleaning up any existing process on port 8083 ...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr :8083 ^| findstr LISTENING') do (
    taskkill /F /PID %%p >nul 2>&1
)

if not exist "%PY%" (
    echo [NetDev] ERROR: python venv not found at %PY%
    echo [NetDev] Create it with: python -m venv .venv
    endlocal
    exit /b 1
)

"%PY%" -c "import uvicorn, celery, redis" >nul 2>&1
if errorlevel 1 (
    echo [NetDev] Installing backend dependencies, please wait ...
    "%PY%" -m pip install -r "%ROOT%\netdevtool-api\requirements.txt"
    if errorlevel 1 (
        echo [NetDev] ERROR: dependency install failed.
        endlocal
        exit /b 1
    )
)

echo [NetDev] Starting backend on http://localhost:8083 ...
start "NetDev-Tool-Backend" /d "%ROOT%\netdevtool-api" cmd /k ".venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8083"

REM ---------- 5. Celery Worker ----------
echo [NetDev] Cleaning up existing Celery worker ...
taskkill /FI "WINDOWTITLE eq NetDev-Tool-Celery" /T /F >nul 2>&1
echo [NetDev] Starting Celery worker ...
start "NetDev-Tool-Celery" /d "%ROOT%\netdevtool-api" cmd /k ".venv\Scripts\python.exe -m celery -A app.tasks.celery_app worker --loglevel=info --pool=solo"

REM ---------- 5.1 Celery Beat (daily maintenance) ----------
echo [NetDev] Cleaning up existing Celery beat ...
taskkill /FI "WINDOWTITLE eq NetDev-Tool-CeleryBeat" /T /F >nul 2>&1
echo [NetDev] Starting Celery beat ...
start "NetDev-Tool-CeleryBeat" /d "%ROOT%\netdevtool-api" cmd /k ".venv\Scripts\python.exe -m celery -A app.tasks.celery_app beat --loglevel=info"

REM ---------- 6. Frontend (Vite :5175) ----------
echo [NetDev] Cleaning up any existing process on port 5175 ...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr :5175 ^| findstr LISTENING') do (
    taskkill /F /PID %%p >nul 2>&1
)

echo [NetDev] Starting frontend on http://localhost:5175 ...
start "NetDev-Tool-Frontend" /d "%ROOT%\netdevtool-web" cmd /k "npm run dev"

echo.
echo [NetDev] All services starting:
echo [NetDev]   MySQL    : Windows service "MySQL"
echo [NetDev]   Redis    : Windows service "Redis"
echo [NetDev]   Qdrant   : http://localhost:6333  (local, .qdrant-server)
echo [NetDev]   Backend  : http://localhost:8083  (docs: /docs)
echo [NetDev]   Celery   : standalone worker window (--pool=solo)
echo [NetDev]   Beat     : daily maintenance (ai_runs retention)
echo [NetDev]   Frontend : http://localhost:5175
echo.
endlocal
exit /b 0

REM ---------- helper: wait for a TCP port ----------
:wait_port
for /l %%i in (1,1,15) do (
    netstat -ano | findstr :%~1 | findstr LISTENING >nul 2>&1
    if not errorlevel 1 exit /b 0
    timeout /t 1 /nobreak >nul
)
exit /b 1
