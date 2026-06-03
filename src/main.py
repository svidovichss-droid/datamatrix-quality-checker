#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Главный модуль приложения DataMatrix Quality Checker.
Запускает GUI, настраивает иконку и глобальные параметры.
"""

import sys
import traceback
from pathlib import Path

# Добавляем корневую папку проекта в путь для импортов
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt

from src.utils.path_helper import resource_path

def show_critical_error(message: str, details: str = ""):
    """Показывает критическую ошибку в диалоговом окне и завершает приложение."""
    app = QApplication.instance()
    if app is None:
        # Если QApplication ещё не создан, создаём временный
        app = QApplication(sys.argv)
    
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Critical)
    msg.setWindowTitle("Ошибка запуска")
    msg.setText(message)
    if details:
        msg.setInformativeText(details)
    msg.setDetailedText(details)
    msg.exec()
    sys.exit(1)

def main():
    """Точка входа в приложение"""
    # Создаём приложение до возможных ошибок, чтобы можно было показать QMessageBox
    app = QApplication(sys.argv)
    app.setApplicationName("DataMatrix Quality Checker")
    app.setOrganizationName("YourCompany")

    # Иконка приложения (опционально)
    icon_path = resource_path("assets/icon.png")
    if Path(icon_path).exists():
        app.setWindowIcon(QIcon(icon_path))

    # Импорт главного окна — делаем внутри try/except, чтобы отловить ошибку
    try:
        from src.ui.main_window import MainWindow
    except ImportError as e:
        error_msg = "Не найден модуль src.ui.main_window"
        details = f"{e}\n\n{traceback.format_exc()}"
        show_critical_error(error_msg, details)
        return  # show_critical_error уже завершает, но оставим для ясности

    # Создание и показ главного окна
    try:
        window = MainWindow()
        window.show()
    except Exception as e:
        error_msg = "Ошибка при создании главного окна"
        details = f"{e}\n\n{traceback.format_exc()}"
        show_critical_error(error_msg, details)
        return

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
