@echo off
setlocal

set PYTHON_VERSION=3.9.10
set PYTHON_INSTALLER=python-%PYTHON_VERSION%-amd64.exe
set PYTHON_PATH=C:\Python%PYTHON_VERSION%

if not exist "%PYTHON_INSTALLER%" (
    echo Downloading Python %PYTHON_VERSION% installer...
    powershell -Command "Invoke-WebRequest -Uri https://www.python.org/ftp/python/%PYTHON_VERSION%/%PYTHON_INSTALLER% -OutFile %PYTHON_INSTALLER%"
)

if not exist "%PYTHON_PATH%" (
    echo Installing Python %PYTHON_VERSION%...
    start /wait %PYTHON_INSTALLER% /quiet InstallAllUsers=1 PrependPath=1
)

echo Updating pip...
"%PYTHON_PATH%\Scripts\pip.exe" install --upgrade pip

if exist "requirements.txt" (
    echo Installing dependencies from requirements.txt...
    "%PYTHON_PATH%\Scripts\pip.exe" install -r requirements.txt
) else (
    echo requirements.txt not found.
)

echo.
echo Installation complete.
echo You can now run your Python script or execute the CMD file again to run it.
echo.
echo To run the script, type: python hamster_keys.py
echo To execute this CMD file again, simply run it again.
echo.

pause