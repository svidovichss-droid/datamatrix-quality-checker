#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Главный модуль приложения DataMatrix Quality Checker.
"""

import sys
import os
from pathlib import Path

# Добавляем корневую папку проекта в путь
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

# Импортируем утилиту для работы с ресурсами (см. следующий файл)
from src.utils.path_helper import resource_path

# Далее идут обычные импорты PySide6, cv2 и т.д.
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
# ... остальные ваши импорты

def main():
    """Запуск приложения"""
    app = QApplication(sys.argv)
    
    # Пример: загрузка иконки через resource_path
    icon_path = resource_path("assets/icon.png")
    if Path(icon_path).exists():
        app.setWindowIcon(QIcon(icon_path))
    
    # Создаём и показываем главное окно (ваш класс из src/ui/main_window.py)
    # Предположим, он называется MainWindow
    from src.ui.main_window import MainWindow
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
