# -*- mode: python ; coding: utf-8 -*-
"""
Runtime hook for PyInstaller frozen build of DataMatrix Quality Checker.

Runs BEFORE any user code, so it must register the directory containing
libdmtx-64.dll in the Windows DLL search path. On Windows 10+ setting
PATH alone is not enough; we also call os.add_dll_directory().
"""

import os
import sys
from pathlib import Path

if getattr(sys, 'frozen', False):
    base = Path(sys._MEIPASS)
    # Register all possible DLL directories
    dll_dirs = [
        base,  # Root of bundle
        base / 'pylibdmtx',  # pylibdmtx subfolder
        base / 'cv2',  # OpenCV subfolder
    ]
    
    for dll_dir in dll_dirs:
        if dll_dir.exists():
            # Add to PATH
            os.environ['PATH'] = f'{dll_dir}{os.pathsep}{os.environ.get("PATH", "")}'
            # Register DLL search path (Windows 10+)
            if hasattr(os, 'add_dll_directory'):
                try:
                    os.add_dll_directory(str(dll_dir))
                except OSError as e:
                    pass  # Directory already registered
