#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Точка входа для PyInstaller.
Перенаправляет запуск в src/main.py, корректируя пути для ресурсов.
"""

import sys
import os
from pathlib import Path

# Добавляем текущую папку в sys.path, чтобы импортировать src
sys.path.insert(0, str(Path(__file__).parent))

try:
    from src.main import main
except ImportError as e:
    print(f"Ошибка импорта src.main: {e}")
    print("Убедитесь, что папка src существует и содержит main.py")
    input("Нажмите Enter для выхода...")
    sys.exit(1)

if __name__ == "__main__":
    main()
