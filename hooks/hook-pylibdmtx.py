# -*- mode: python ; coding: utf-8 -*-
"""
Hook for PyInstaller to properly bundle pylibdmtx library.
Collects all necessary data files and submodules.
"""

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Collect all data files from pylibdmtx (includes DLLs, resources)
datas = collect_data_files('pylibdmtx')

# Collect all submodules
hiddenimports = collect_submodules('pylibdmtx')
