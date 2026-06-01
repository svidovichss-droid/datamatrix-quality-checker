#!/usr/bin/env python3
"""Точка входа для запуска из корня проекта: python main.py"""

import sys
import os
from pathlib import Path

# ===== 1. Настройка путей =====
# Корень проекта — папка, где находится этот файл
PROJECT_ROOT = Path(__file__).resolve().parent

# Добавляем корень в sys.path, если его там нет
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ===== 2. Проверка структуры src =====
src_path = PROJECT_ROOT / "src"
init_file = src_path / "__init__.py"

if not src_path.exists():
    raise RuntimeError(
        f"Папка 'src' не найдена в {PROJECT_ROOT}.\n"
        f"Убедитесь, что файл main.py лежит в одной папке с src/."
    )

if not init_file.exists():
    # Автоматически создаём __init__.py, чтобы src считался пакетом
    init_file.touch()
    print(f"[INFO] Создан недостающий файл: {init_file}")

# ===== 3. Импорт модулей =====
try:
    from src.app import MainWindow
except ImportError as e:
    print(f"[ERROR] Не удалось импортировать src.app: {e}")
    print(f"[DEBUG] sys.path = {sys.path}")
    print(f"[DEBUG] Содержимое папки src: {list(src_path.iterdir())}")
    raise

from PySide6.QtWidgets import QApplication
import logging

# ===== 4. Логирование =====
def setup_logging():
    log = logging.getLogger("dmqc")
    log.setLevel(logging.INFO)
    if not log.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        ))
        log.addHandler(handler)
    return log

# ===== 5. Запуск приложения =====
def main():
    setup_logging()
    
    # High-DPI для Qt
    os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")
    os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")
    
    app = QApplication(sys.argv)
    app.setApplicationName("DataMatrix Quality Checker")
    app.setOrganizationName("DMQC")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
