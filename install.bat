@echo off
setlocal enabledelayedexpansion

:: Parse arguments
set DEPENDENCY_INSTALL_METHOD=
:parse_args
if "%~1"=="" goto done_parse
if "%~1"=="--deps" (
    shift
    set DEPENDENCY_INSTALL_METHOD=%~2
)
shift
goto parse_args
:done_parse

echo Dependency install method: %DEPENDENCY_INSTALL_METHOD%

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

:: Install required Python packages, if specified
if /i "%DEPENDENCY_INSTALL_METHOD%"=="conda" (
    echo Installing required Python packages using conda...
    conda install --file requirements.txt -y
) else if /i "%DEPENDENCY_INSTALL_METHOD%"=="pip" (
    echo Installing required Python packages using pip...
    pip install -r requirements.txt
) else (
    echo Python dependencies not installed. Install requirements.txt manually or rerun this script with the "--deps [pip/conda]" flag.
)
if %errorlevel% neq 0 (
    echo Error: Failed to install required packages.
    echo Ensure Python and pip or conda are installed and try again.
    exit /b 1
)

:: Add RMParse to the user PATH environment variable
echo Adding RMParse to the user PATH...

for /f "tokens=2* delims= " %%A in ('reg query "HKCU\Environment" /v Path 2^>nul') do set "USER_PATH=%%B"

set "RMPARSE_PATH=%~dp0"
if "%RMPARSE_PATH:~-1%"=="\" set "RMPARSE_PATH=%RMPARSE_PATH:~0,-1%"

echo %USER_PATH% | findstr /i /c:"%RMPARSE_PATH%" >nul
if %errorlevel% neq 0 (
    set "NEW_PATH=%USER_PATH%%RMPARSE_PATH%"
    powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ^
        "[Environment]::SetEnvironmentVariable('PATH', \"!NEW_PATH!\", 'User');"
) else (
    echo RMParse is already in PATH.
)

echo Installation successful. Start a new terminal to use RMParse.
pause
exit