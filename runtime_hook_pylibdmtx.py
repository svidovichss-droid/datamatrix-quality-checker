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
    # _MEIPASS may put the DLL at the root (thanks to hook-pylibdmtx.py)
    # or inside pylibdmtx/ subfolder; register both just in case.
    for sub in ('.', 'pylibdmtx'):
        d = base / sub
        if d.exists():
            os.environ['PATH'] = f'{d}{os.pathsep}{os.environ.get("PATH", "")}'
            if hasattr(os, 'add_dll_directory'):
                try:
                    os.add_dll_directory(str(d))
                except OSError:
                    pass
