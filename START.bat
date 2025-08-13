@echo off
setlocal
cd /d "%~dp0"

REM ── Find Python (python or py launcher) ─────────────────────────────────────
where python >nul 2>nul
if %errorlevel%==0 (
    set PY=python
) else (
    where py >nul 2>nul
    if %errorlevel%==0 (
        set PY=py -3
    ) else (
        echo Could not find Python. Please install Python 3.10+ and try again.
        pause
        exit /b 1
    )
)

REM ── Create venv if missing ──────────────────────────────────────────────────
if not exist ".venv\" (
    echo Creating virtual environment...
    %PY% -m venv .venv
    if %errorlevel% neq 0 (
        echo Failed to create virtual environment.
        pause
        exit /b 1
    )
)

REM ── Choose the venv python (Windows layout) ─────────────────────────────────
set VENV_PY=".venv\Scripts\python.exe"
if not exist %VENV_PY% (
    echo Could not find %VENV_PY%
    pause
    exit /b 1
)

REM ── Upgrade pip and install requirements on first run (or when changed) ─────
if exist requirements.txt (
    echo Ensuring dependencies are installed...
    %VENV_PY% -m pip install --upgrade pip
    %VENV_PY% -m pip install -r requirements.txt
)

REM ── Run the app ─────────────────────────────────────────────────────────────
%VENV_PY% main.py
pause