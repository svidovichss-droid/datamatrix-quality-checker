@echo off
REM build.bat — локальная сборка .exe под Windows
REM Требует Python 3.10+ в PATH.

setlocal enabledelayedexpansion
cd /d "%~dp0\.."

echo === [1/4] Создаю виртуальное окружение ===
if not exist ".venv" (
    python -m venv .venv
) else (
    echo .venv уже существует
)

call .venv\Scripts\activate.bat

echo === [2/4] Обновляю pip и ставлю зависимости ===
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller>=6.0

echo === [3/4] Чищу предыдущую сборку ===
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo === [4/4] Собираю DataMatrixChecker.exe ===
pyinstaller build.spec --noconfirm

if exist "dist\DataMatrixChecker.exe" (
    echo.
    echo === ГОТОВО ===
    echo Файл: dist\DataMatrixChecker.exe
    dir dist\DataMatrixChecker.exe
) else (
    echo.
    echo === ОШИБКА СБОРКИ ===
    exit /b 1
)

endlocal
