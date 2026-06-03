#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import traceback
from pathlib import Path

# Добавляем корень проекта в sys.path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QIcon
from src.utils.path_helper import resource_path

def show_error_and_exit(message, details=""):
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

    icon_path = resource_path("assets/icon.png")
    if Path(icon_path).exists():
        app.setWindowIcon(QIcon(icon_path))

    # Диагностика: проверяем, что видит Python
    print("sys.path:", sys.path[:3])  # временно для отладки (будет видно в консоли)

    try:
        from src.ui.main_window import MainWindow
    except ModuleNotFoundError as e:
        # Подробная диагностика
        error_msg = f"Не найден модуль: {e}"
        # Проверяем физическое существование папки и файлов
        ui_path = ROOT_DIR / "src" / "ui"
        init_file = ui_path / "__init__.py"
        main_window_file = ui_path / "main_window.py"
        details = (
            f"Ошибка импорта: {e}\n\n"
            f"Папка src/ui существует: {ui_path.exists()}\n"
            f"Файл __init__.py существует: {init_file.exists()}\n"
            f"Файл main_window.py существует: {main_window_file.exists()}\n"
            f"Содержимое папки src/ui: {list(ui_path.glob('*')) if ui_path.exists() else 'нет'}\n"
        )
        show_error_and_exit(error_msg, details)
        return

    try:
        window = MainWindow()
        window.show()
    except Exception as e:
        show_error_and_exit("Ошибка создания окна", traceback.format_exc())
        return

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
