#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Главный модуль приложения DataMatrix Quality Checker.
"""

import sys
import traceback
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QIcon

from src.utils.path_helper import resource_path

def show_critical_error(message: str, details: str = ""):
    """Показывает критическую ошибку и завершает приложение."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Critical)
    msg.setWindowTitle("Ошибка запуска")
    msg.setText(message)
    msg.setInformativeText("Приложение будет закрыто.")
    if details:
        msg.setDetailedText(details)
    msg.exec()
    sys.exit(1)

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("DataMatrix Quality Checker")

    # Иконка (опционально)
    icon_path = resource_path("assets/icon.png")
    if Path(icon_path).exists():
        app.setWindowIcon(QIcon(icon_path))

    # Пытаемся импортировать главное окно
    try:
        from src.ui.main_window import MainWindow
    except ModuleNotFoundError as e:
        # Уточнённое сообщение об отсутствии модуля ui
        error_msg = "Не найден модуль 'src.ui' или 'src.ui.main_window'"
        details = (
            f"Ошибка импорта: {e}\n\n"
            "Проверьте, что в папке 'src/ui' есть файл 'main_window.py'.\n"
            "А также что папка 'ui' содержит файл '__init__.py' (может быть пустым)."
        )
        show_critical_error(error_msg, details + "\n\n" + traceback.format_exc())
        return

    try:
        window = MainWindow()
        window.show()
    except Exception as e:
        error_msg = "Ошибка при создании главного окна"
        show_critical_error(error_msg, traceback.format_exc())
        return

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
