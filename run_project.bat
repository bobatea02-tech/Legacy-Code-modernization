@echo off
echo ========================================
echo  LEGACY CODE MODERNIZATION ENGINE
echo  Full-Stack Startup Script
echo ========================================
echo.

REM Step 1: Check Python installation
echo [1/8] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/
    pause
    exit /b 1
)
echo Python found!
echo.

REM Step 2: Check Node.js installation
echo [2/8] Checking Node.js installation...
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed or not in PATH
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)
echo Node.js found!
echo.

REM Step 3: Create Python virtual environment
echo [3/8] Creating Python virtual environment...
if not exist "venv" (
    python -m venv venv
    echo Virtual environment created!
) else (
    echo Virtual environment already exists!
)
echo.

REM Step 4: Activate virtual environment and install backend dependencies
echo [4/8] Installing backend dependencies...
call venv\Scripts\activate.bat
pip install -r backend\requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install backend dependencies
    pause
    exit /b 1
)
echo Backend dependencies installed!
echo.

REM Step 5: Install frontend dependencies
echo [5/8] Installing frontend dependencies...
cd frontend
call npm install
if errorlevel 1 (
    echo ERROR: Failed to install frontend dependencies
    cd ..
    pause
    exit /b 1
)
cd ..
echo Frontend dependencies installed!
echo.

REM Step 6: Start backend server
echo [6/8] Starting backend server on http://localhost:8000...
start "Backend Server" cmd /k "call venv\Scripts\activate.bat && cd backend && python main.py"
echo Backend server starting...
echo.

REM Step 7: Wait for backend to be ready with health check
echo [7/8] Waiting for backend to be ready...
set /a count=0
:WAIT_BACKEND
timeout /t 2 /nobreak >nul
powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://localhost:8000/health' -UseBasicParsing -TimeoutSec 1; if ($response.StatusCode -eq 200) { exit 0 } } catch { } exit 1" >nul 2>&1
if errorlevel 1 (
    set /a count+=1
    if %count% LSS 15 (
        echo Backend not ready yet, waiting... ^(attempt %count%/15^)
        goto WAIT_BACKEND
    ) else (
        echo WARNING: Backend may not be ready after 30 seconds
        echo Continuing anyway...
    )
) else (
    echo Backend is ready!
)
echo.

REM Step 8: Start frontend dev server
echo [8/8] Starting frontend server on http://localhost:5173...
start "Frontend Server" cmd /k "cd frontend && npm run dev"
echo Frontend server starting...
echo.

echo ========================================
echo  STARTUP COMPLETE!
echo ========================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5173
echo API Docs: http://localhost:8000/docs
echo.
echo Both servers are running in separate windows.
echo Close those windows to stop the servers.
echo.
echo Press any key to exit this window...
pause >nul
