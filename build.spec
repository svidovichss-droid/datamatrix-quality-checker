# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec для DataMatrix Quality Checker
# Сборка: pyinstaller build.spec

import sys
from pathlib import Path

block_cipher = None

# Qt + OpenCV плагины, которые нужно включить явно
datas = [
    # ничего дополнительного пока; logs/ создаются рантаймом
]

# Qt platform plugins (если PyInstaller не подхватит автоматически)
hiddenimports = [
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
    "cv2",
    "numpy",
    "PIL",
    "PIL.Image",
    "pylibdmtx.pylibdmtx",
    "pylibdmtx",
    "libdmtx",
]

# Уберём лишние модули для уменьшения размера
excludes = [
    "tkinter",
    "test",
    "unittest",
    "pydoc",
    "doctest",
    "matplotlib",
    "scipy",
    "pandas",
]

a = Analysis(
    ['src/main.py'],
    pathex=[str(Path('.').resolve())],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='DataMatrixChecker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,            # сжатие UPX (если установлен)
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,       # GUI-приложение
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.png' if Path('assets/icon.png').exists() else None,
)
