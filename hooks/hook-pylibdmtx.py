# -*- mode: python ; coding: utf-8 -*-
"""
Hook for PyInstaller to properly bundle pylibdmtx library.
Collects all necessary data files, DLLs, and submodules.
"""

from PyInstaller.utils.hooks import collect_data_files, collect_submodules, get_module_file_attribute
from pathlib import Path

# Collect all data files from pylibdmtx (includes DLLs, resources)
datas = collect_data_files('pylibdmtx')

# Collect all submodules
hiddenimports = collect_submodules('pylibdmtx')

# Explicitly add DLLs
binaries = []

try:
    import pylibdmtx
    pylibdmtx_path = Path(pylibdmtx.__file__).parent
    
    # Find and add all DLLs
    for dll_file in pylibdmtx_path.glob('*.dll'):
        binaries.append((str(dll_file), 'pylibdmtx'))
except Exception:
    pass
