@echo off
REM Build script for Windows - DataMatrix Quality Checker
REM Requires Python 3.8+ and pip

setlocal enabledelayedexpansion

echo.
echo ===== DataMatrix Quality Checker - Windows Build =====
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check if pip is available
pip --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: pip is not installed
    pause
    exit /b 1
)

echo [1/4] Installing/upgrading required packages...
pip install --upgrade pip setuptools wheel pyinstaller pyside6 opencv-python pillow pylibdmtx numpy
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo [2/4] Cleaning previous build...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
if exist *.spec del *.spec

echo.
echo [3/4] Building executable with PyInstaller...
pyinstaller build.spec --distpath dist --buildpath build --specpath .
if errorlevel 1 (
    echo ERROR: PyInstaller build failed
    pause
    exit /b 1
)

echo.
echo [4/4] Build complete!
echo.
echo ===== SUCCESS =====
echo.
echo Executable location: dist\DataMatrixChecker.exe
echo File size: ~80 MB (portable, no installation needed)
echo.
echo To run:
echo   - Double-click dist\DataMatrixChecker.exe
echo   - Or: dist\DataMatrixChecker.exe from command line
echo.
pause
