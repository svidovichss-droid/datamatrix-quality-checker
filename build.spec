# -*- mode: python ; coding: utf-8 -*-

import sys
import site
from pathlib import Path
from PyInstaller.building.api import Tree
from PyInstaller.utils.hooks import collect_dynamic_libs

block_cipher = None

# ===== 1. Рекурсивно добавляем всю папку src =====
datas = [('assets/*', 'assets')] + Tree('src', prefix='src')

# ===== 2. Добавляем DLL из pylibdmtx =====
# Способ 1: автоматический сбор всех динамических библиотек
binaries = []
try:
    # collect_dynamic_libs возвращает список (src, dest) для всех .dll/.so
    dlls = collect_dynamic_libs('pylibdmtx')
    binaries.extend(dlls)
except Exception:
    # Если автоматика не сработала, делаем вручную
    try:
        site_packages = Path(site.getsitepackages()[0])
        libdmtx_dll = site_packages / 'pylibdmtx' / 'libdmtx-64.dll'
        if libdmtx_dll.exists():
            binaries.append((str(libdmtx_dll), 'pylibdmtx'))
    except Exception:
        pass

# Способ 2 (резервный): ищем в виртуальном окружении
if not binaries:
    # Ищем в текущем окружении
    import sysconfig
    import subprocess
    try:
        # Получаем путь к site-packages через pip show
        result = subprocess.run([sys.executable, '-m', 'pip', 'show', 'pylibdmtx'],
                                capture_output=True, text=True)
        for line in result.stdout.splitlines():
            if line.startswith('Location:'):
                loc = line.split(':', 1)[1].strip()
                dll_path = Path(loc) / 'pylibdmtx' / 'libdmtx-64.dll'
                if dll_path.exists():
                    binaries.append((str(dll_path), 'pylibdmtx'))
                break
    except Exception:
        pass

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
    "ctypes",           # важно для загрузки DLL
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
    binaries=binaries,       # <-- добавлены DLL
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
    console=False,          # GUI без консоли (для отладки временно можно True)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.png' if Path('assets/icon.png').exists() else None,
)
