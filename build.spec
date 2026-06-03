# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path
from PyInstaller.building.api import Tree

block_cipher = None

# ===== 1. Данные (папки src и assets) =====
datas = [('assets/*', 'assets')] + Tree('src', prefix='src')

# ===== 2. Бинарные файлы (DLL) =====
# Указываем явный путь к скопированной DLL
dll_path = Path('dll') / 'libdmtx-64.dll'
if dll_path.exists():
    binaries = [(str(dll_path), 'pylibdmtx')]   # копируется в папку pylibdmtx внутри _MEI
else:
    print("ВНИМАНИЕ: libdmtx-64.dll не найдена в папке dll/")
    binaries = []

# ===== 3. Скрытые импорты =====
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
    "ctypes",
    "ctypes.util",
]

excludes = [
    "tkinter", "test", "unittest",
    "pydoc", "doctest", "matplotlib", "scipy", "pandas",
]

# ===== 4. Анализ =====
a = Analysis(
    ['src/main.py'],
    pathex=[str(Path('.').resolve())],
    binaries=binaries,
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
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Можно временно поставить True для отладки
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.png' if Path('assets/icon.png').exists() else None,
)
