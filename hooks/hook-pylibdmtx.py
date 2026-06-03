# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller hook for pylibdmtx.

pylibdmtx >= 0.1.10 ships the native libdmtx DLL/SO/dylib inside the wheel
(site-packages/pylibdmtx/libdmtx-64.dll on Windows, etc.).
This hook copies that native library into the root of the frozen bundle
(_MEIPASS) so that ctypes.CDLL can find it via PATH/os.add_dll_directory
once the runtime_hook_pylibdmtx.py kicks in.
"""

import os

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files('pylibdmtx')

binaries = []
try:
    import pylibdmtx  # noqa: F401
    pkg_dir = os.path.dirname(pylibdmtx.__file__)
    for entry in os.listdir(pkg_dir):
        if entry.lower().endswith(('.dll', '.so', '.dylib')):
            binaries.append((os.path.join(pkg_dir, entry), '.'))
except ImportError:
    # pylibdmtx is not installed in the build environment; nothing to copy.
    pass
