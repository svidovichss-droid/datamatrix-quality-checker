# -*- mode: python ; coding: utf-8 -*-
# Build spec for DataMatrix Quality Checker.
#
# Layout expected in repo root:
#   build.spec
#   hooks/hook-pylibdmtx.py
#   runtime_hook_pylibdmtx.py
#   assets/
#   src/

import sys
from pathlib import Path
from PyInstaller.building.api import Tree

block_cipher = None

# ===== 1. Data: src/ tree + assets/ =====
datas = [('assets/*', 'assets')] + Tree('src', prefix='src')

# ===== 2. Binaries: native DLL =====
# hook-pylibdmtx.py takes care of bundling libdmtx-64.dll from the installed
# pylibdmtx wheel, so we don't need to ship it manually.
binaries = []

# ===== 3. Hidden imports =====
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
    "pylibdmtx.wrapper",
    "pylibdmtx.dmtx_library",
    "libdmtx",
    "ctypes",
    "ctypes.util",
]

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

# ===== 4. Analysis =====
a = Analysis(
    ['src/main.py'],
    pathex=[str(Path('.').resolve())],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=['hooks'],
    hooksconfig={},
    runtime_hooks=['runtime_hook_pylibdmtx.py'],
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
    console=False,        # switch to True temporarily if you want a console for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.png' if Path('assets/icon.png').exists() else None,
)
