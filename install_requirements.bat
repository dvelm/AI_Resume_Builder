@echo off
echo ===================================================
echo AI Resume Builder - Installation Script
echo ===================================================
echo.

:: Check for Python installation
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH.
    echo Please install Python 3.10 or higher from https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

:: Check for updates
echo Checking for updates...

:: First check if git is available
where git >nul 2>&1
if %errorlevel% neq 0 (
    echo Git not found. Skipping update check.
    goto :skip_git_check
)

:: Check if this is a git repository
git rev-parse --is-inside-work-tree >nul 2>&1
if %errorlevel% neq 0 (
    echo Not a Git repository. Skipping update check.
    goto :skip_git_check
)

:: Check for updates
git fetch >nul 2>&1
git status -uno | findstr "behind" >nul 2>&1
if %errorlevel% neq 0 (
    echo No updates available.
    goto :skip_git_check
)

:: Prompt for update
echo Updates are available. Would you like to update? (Y/N)
set /p update_choice="Your choice: "
if /i "%update_choice%"=="Y" (
    git pull
    echo Repository updated successfully.
) else (
    echo Update skipped.
)

:skip_git_check

:: Create virtual environment if it doesn't exist
if not exist "virtual" (
    echo Creating virtual environment...
    python -m venv virtual
) else (
    echo Virtual environment already exists.
)

:: Activate virtual environment and install requirements
echo Activating virtual environment and installing requirements...
call virtual\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt

echo.
echo ===================================================
echo Installation completed successfully!
echo.
echo To run the application, use the run_app.bat script.
echo ===================================================
echo.
pause
