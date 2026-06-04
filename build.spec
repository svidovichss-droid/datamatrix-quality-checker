# -*- mode: python ; coding: utf-8 -*-
# Build spec for DataMatrix Quality Checker
# CRITICAL FIX: Use Conda environment for proper libdmtx DLL bundling
# See: scripts/build_conda.bat

import sys
import os
from pathlib import Path
from PyInstaller.building.api import Tree

block_cipher = None

# ===== 1. Data: src/ tree + assets/ =====
datas = [('assets', 'assets')] + Tree('src', prefix='src')

# ===== 2. Binaries: Use conda-provided DLLs =====
binaries = []

# In conda environment, DLLs are automatically found and bundled
# No manual DLL collection needed - conda handles library dependencies

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
    ['main.py'],
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
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.png' if Path('assets/icon.png').exists() else None,
)
