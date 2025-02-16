@echo off
setlocal

:: Get the directory of this script (assumed to be the top level of RMParse)
set "RMPARSE_PATH=%~dp0"
:: Remove trailing backslash if present
if "%RMPARSE_PATH:~-1%"=="\" set "RMPARSE_PATH=%RMPARSE_PATH:~0,-1%"

:: Check if Python 3.12 or greater is installed
for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PYTHON_VERSION=%%v
echo Detected Python version: %PYTHON_VERSION%

:: Extract major and minor version
for /f "tokens=1,2 delims=." %%a in ("%PYTHON_VERSION%") do (
    set MAJOR=%%a
    set MINOR=%%b
)

:: Check version requirement
if %MAJOR% LSS 3 (
    echo Python 3.12 or greater is required.
    exit /b 1
)
if %MAJOR% EQU 3 if %MINOR% LSS 12 (
    echo Python 3.12 or greater is required.
    exit /b 1
)

echo Python 3.12 or greater is installed.

:: Install required Python packages
echo Installing required packages...
pip install tabulate PyYAML

:: Add RMParse to the Path environment variable
echo Adding RMParse to the system PATH...

:: Check if the path is already in the user's PATH
echo %PATH% | findstr /i /c:"%RMPARSE_PATH%" >nul
if %errorlevel% neq 0 (
    :: Add the path to user environment variable
    setx PATH "%PATH%;%RMPARSE_PATH%"
    echo RMParse path added to PATH.
) else (
    echo RMParse is already in PATH.
)

echo Setup completed successfully.
pause