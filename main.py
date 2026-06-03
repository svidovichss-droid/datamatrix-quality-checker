#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Точка входа для PyInstaller.
Перенаправляет запуск в src/main.py, корректируя пути для ресурсов.
"""

import sys
import os
from pathlib import Path

# Добавляем текущую папку в sys.path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from src.main import main
except ImportError as e:
    # Не можем показать QMessageBox, так как Qt ещё не инициализирован.
    # В GUI-режиме просто завершаем без вывода, так как консоли нет.
    # Для отладки можно записать в файл, но обычно это не нужно.
    # Пользователь просто увидит, что приложение не запустилось.
    sys.exit(1)

if __name__ == "__main__":
    main()
