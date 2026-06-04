@echo off
REM RECOMMENDED: Conda Build Script for DataMatrix Quality Checker
REM This method ensures proper DLL bundling and avoids libdmtx loading errors

setlocal enabledelayedexpansion

echo.
echo ===== DataMatrix Quality Checker - Conda Build (RECOMMENDED) =====
echo.
echo This script uses Conda which provides proper DLL dependencies.
echo If you don't have Conda, install Miniconda: 
echo   https://docs.conda.io/projects/miniconda/en/latest/
echo.

REM Check if conda is installed
where conda >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Conda is not installed or not in PATH
    echo Please install Miniconda from: https://docs.conda.io/projects/miniconda/en/latest/
    echo.
    pause
    exit /b 1
)

echo [1/6] Creating conda environment 'dmtx-build'...
call conda create -n dmtx-build python=3.11 -y -q
if %errorlevel% neq 0 (
    echo [INFO] Environment may already exist, continuing...
)

echo [2/6] Activating conda environment...
call conda activate dmtx-build
if %errorlevel% neq 0 (
    echo ERROR: Could not activate conda environment
    pause
    exit /b 1
)

echo [3/6] Installing conda packages (provides DLLs)...
call conda install -y -q -c conda-forge pyside6 opencv numpy pillow
if %errorlevel% neq 0 (
    echo ERROR: Failed to install conda packages
    pause
    exit /b 1
)

echo [4/6] Installing pip packages...
call pip install --upgrade pip setuptools wheel pyinstaller pylibdmtx -q
if %errorlevel% neq 0 (
    echo ERROR: Failed to install pip packages
    pause
    exit /b 1
)

echo.
echo [5/6] Cleaning previous build...
if exist dist rmdir /s /q dist 2>nul
if exist build rmdir /s /q build 2>nul

echo.
echo [6/6] Building executable...
echo [INFO] This may take 3-5 minutes...
call pyinstaller build.spec --distpath dist --buildpath build -q
if %errorlevel% neq 0 (
    echo.
    echo ERROR: PyInstaller build failed
    echo.
    echo Troubleshooting:
    echo   1. Ensure conda environment is active: conda activate dmtx-build
    echo   2. Check Python version: python --version (should be 3.11)
    echo   3. Try clean build: rmdir /s build dist
    echo.
    pause
    exit /b 1
)

echo.
echo ===== BUILD SUCCESSFUL =====
echo.
echo Executable: dist\DataMatrixChecker.exe
echo Size: ~150 MB (includes all DLLs)
echo.
echo To run:
echo   1. Keep conda environment active: conda activate dmtx-build
echo   2. Double-click dist\DataMatrixChecker.exe OR
echo   3. Run: dist\DataMatrixChecker.exe
echo.
echo To use exe elsewhere:
echo   - Copy entire dist folder
echo   - Keep conda activated or use standalone Python
echo.
echo Deactivate conda when done:
echo   conda deactivate
echo.
pause
