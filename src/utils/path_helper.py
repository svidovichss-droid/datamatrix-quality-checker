#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Вспомогательные функции для работы с путями в PyInstaller.
"""

import sys
import os
from pathlib import Path

def resource_path(relative_path: str) -> str:
    """
    Возвращает абсолютный путь к ресурсу.
    Работает как в режиме разработки, так и в собранном .exe (PyInstaller).
    
    Аргументы:
        relative_path (str): путь относительно корня проекта (например, 'assets/icon.png')
    
    Возвращает:
        str: абсолютный путь к файлу
    """
    try:
        # PyInstaller создаёт временную папку _MEIxxxxxx и хранит там ресурсы
        base_path = Path(sys._MEIPASS)
    except AttributeError:
        # Обычный запуск из интерпретатора
        base_path = Path(__file__).parent.parent.parent  # корень проекта
    
    return str(base_path / relative_path)

def get_src_path(relative_path: str = "") -> str:
    """
    Возвращает путь к файлу внутри папки src.
    """
    src_base = Path(resource_path("src"))
    return str(src_base / relative_path)
