@echo off
setlocal

:: Check if any version of Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH.
    echo Please install Python and ensure it is added to the system PATH.
    exit /b 1
)

:: Check if Python version is 3.12 or greater
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

:: Check for errors
if %errorlevel% neq 0 (
    echo Error: Failed to install required packages.
    echo Ensure Python and pip are installed and try again.
    exit /b 1
)

:: Add RMParse to the user PATH environment variable
echo Adding RMParse to the user PATH...

:: Get the current user PATH
for /f "tokens=2* delims= " %%A in ('reg query "HKCU\Environment" /v Path 2^>nul') do set "USER_PATH=%%B"

:: Get the directory of this script (assumed to be the top level of RMParse)
set "RMPARSE_PATH=%~dp0"
:: Remove trailing backslash if present
if "%RMPARSE_PATH:~-1%"=="\" set "RMPARSE_PATH=%RMPARSE_PATH:~0,-1%"

:: Add the path to user environment variable if not present
echo %USER_PATH% | findstr /i /c:"%RMPARSE_PATH%" >nul
if %errorlevel% neq 0 (
    setx PATH "%USER_PATH%;%RMPARSE_PATH%"
    echo RMParse added to PATH.
) else (
    echo RMParse is already in PATH.
)

echo Installation successful.
pause