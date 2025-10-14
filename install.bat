@echo off
setlocal

REM Set environment name inside project folder
set ENV_NAME=myenv

REM Get the current directory (project folder)
set PROJECT_DIR=%~dp0

cd /d %PROJECT_DIR%

REM Step 1: Create virtual environment (inside project folder)
echo Creating virtual environment in %ENV_NAME%...
python -m venv %ENV_NAME%

REM Step 2: Activate virtual environment
echo Activating virtual environment...
call "%PROJECT_DIR%%ENV_NAME%\Scripts\activate.bat"

REM Step 3: Upgrade pip (optional)
echo Upgrading pip...
python -m pip install --upgrade pip

REM Step 4: Install dependencies
echo Installing dependencies from requirements.txt...
pip install -r requirements.txt

REM Step 5: Run main.py
echo Starting Flask server from main.py...
python main.py

endlocal
pause
