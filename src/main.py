#!/usr/bin/env python3
"""Точка входа для запуска из корня проекта: python main.py"""

import sys
import os
from pathlib import Path

# Добавляем корневую папку проекта в sys.path,
# чтобы импорты вида 'from src.app import ...' работали.
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

# Теперь импорты из src работают
from src.app import MainWindow
from PySide6.QtWidgets import QApplication
import logging

def setup_logging():
    """Настройка логирования для основного процесса."""
    log = logging.getLogger("dmqc")
    log.setLevel(logging.INFO)
    if not log.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        ))
        log.addHandler(handler)
    return log

def main():
    """Запуск GUI приложения."""
    setup_logging()
    
    # Включаем High-DPI поддержку для Qt
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
