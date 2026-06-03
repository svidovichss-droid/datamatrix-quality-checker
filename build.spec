# -*- mode: python ; coding: utf-8 -*-

# PyInstaller spec для DataMatrix Quality Checker
# Сборка: pyinstaller build.spec

import sys
from pathlib import Path

block_cipher = None

# ===== 1. Добавляем ALL файлы из src =====
# Эта строчка копирует ВСЁ содержимое папки src в корень сборки
datas = [('src/*', 'src')]

# ===== 2. Явно указываем скрытые импорты =====
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

# ===== 3. Исключаем ненужные модули =====
excludes = [
    "tkinter", "test", "unittest",
    "pydoc", "doctest", "matplotlib", "scipy", "pandas",
]

# ===== 4. Основной анализ =====
a = Analysis(
    ['src/main.py'],  # Точкой входа теперь является файл внутри src
    pathex=[str(Path('.').resolve())],
    binaries=[],
    datas=datas,  # <-- ЭТО ГЛАВНОЕ! Теперь данные добавлены
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
    console=False,  # GUI-приложение, окно консоли не показываем
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.png' if Path('assets/icon.png').exists() else None,
)
