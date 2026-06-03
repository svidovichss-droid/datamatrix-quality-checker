@echo off
echo ========================================
echo Building DataMatrix Quality Checker
echo ========================================

REM Удаляем старые сборки
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist

REM Устанавливаем зависимости
pip install -r requirements.txt

REM Запускаем PyInstaller с нашим spec-файлом
pyinstaller build.spec --clean --noconfirm

echo.
echo ========================================
echo Build finished. Check 'dist' folder.
echo ========================================
pause
