#!/usr/bin/env bash
# build.sh — сборка под Linux/macOS (для отладки; .exe лучше собирать на Windows).
set -e
cd "$(dirname "$0")/.."

echo "=== [1/4] Создаю venv ==="
[ -d .venv ] || python3 -m venv .venv
source .venv/bin/activate

echo "=== [2/4] Устанавливаю зависимости ==="
python -m pip install --upgrade pip
pip install -r requirements.txt pyinstaller>=6.0

echo "=== [3/4] Чищу прошлую сборку ==="
rm -rf build dist

echo "=== [4/4] Собираю бинарь ==="
pyinstaller build.spec --noconfirm

echo "=== Готово: dist/DataMatrixChecker ==="
ls -lh dist/ 2>/dev/null || true
