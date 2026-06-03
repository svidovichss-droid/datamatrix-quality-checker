#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Главный модуль приложения DataMatrix Quality Checker.
Запускает GUI, настраивает иконку и глобальные параметры.
"""

import sys
import os
from pathlib import Path

# Добавляем корневую папку проекта в путь для импортов
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon          # <-- ИСПРАВЛЕНО: добавлен импорт QIcon
from PySide6.QtCore import Qt

# Импорт утилиты для корректных путей к ресурсам (работает и в .exe)
from src.utils.path_helper import resource_path

# Предполагается, что у вас есть главное окно в src/ui/main_window.py
# Если класс называется иначе — замените на свой
try:
    from src.ui.main_window import MainWindow
except ImportError:
    # Заглушка, если файла нет — выводим сообщение и выходим
    print("Ошибка: не найден модуль src.ui.main_window")
    print("Убедитесь, что папка src/ui/main_window.py существует")
    input("Нажмите Enter для выхода...")
    sys.exit(1)

def main():
    """Точка входа в приложение"""
    app = QApplication(sys.argv)
    app.setApplicationName("DataMatrix Quality Checker")
    app.setOrganizationName("YourCompany")

    # Загрузка иконки приложения через resource_path
    icon_path = resource_path("assets/icon.png")
    if Path(icon_path).exists():
        app.setWindowIcon(QIcon(icon_path))
    else:
        print(f"Предупреждение: иконка не найдена по пути {icon_path}")

    # Создание и показ главного окна
    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
