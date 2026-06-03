# src/ui/main_window.py

import os
import sys
import ctypes
from pathlib import Path

# === ФИКС ДЛЯ PyInstaller: загружаем libdmtx-64.dll вручную ===
def load_libdmtx_dll():
    """Принудительно загружает libdmtx-64.dll из папки pylibdmtx внутри _MEIPASS или из окружения."""
    dll_name = "libdmtx-64.dll"
    
    # Если запущено из PyInstaller
    if hasattr(sys, '_MEIPASS'):
        base_path = Path(sys._MEIPASS)
        dll_path = base_path / 'pylibdmtx' / dll_name
    else:
        # Обычный запуск: ищем в site-packages
        try:
            import site
            site_packages = Path(site.getsitepackages()[0])
            dll_path = site_packages / 'pylibdmtx' / dll_name
        except Exception:
            dll_path = None
    
    if dll_path and dll_path.exists():
        try:
            # Для Windows 8+ нужно добавить директорию в поиск DLL
            if sys.platform == 'win32':
                os.add_dll_directory(str(dll_path.parent))
            ctypes.CDLL(str(dll_path))
            print(f"Загружена DLL: {dll_path}")
            return True
        except Exception as e:
            print(f"Ошибка загрузки DLL: {e}")
    else:
        print(f"DLL не найдена по пути {dll_path}")
    return False

# Загружаем DLL до импорта pylibdmtx
load_libdmtx_dll()

# Теперь безопасно импортируем pylibdmtx
from pylibdmtx.pylibdmtx import decode as dmtx_decode

# Остальные импорты (PIL, cv2, PySide6...)
from PIL import Image
# ... ваш остальной код ...
