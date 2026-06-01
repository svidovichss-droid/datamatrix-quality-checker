""" main.py — точка входа. Запускается командой `python -m src.main`. """
from __future__ import annotations
import logging
import os
import sys
from PySide6.QtWidgets import QApplication
from src.app import MainWindow  # абсолютный импорт

def main() -> int:
    # logging
    log = logging.getLogger("dmqc")
    log.setLevel(logging.INFO)
    if not log.handlers:
        h = logging.StreamHandler()
        h.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
        log.addHandler(h)
    # High-DPI для Qt
    os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")
    os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")
    app = QApplication(sys.argv)
    app.setApplicationName("DataMatrix Quality Checker")
    app.setOrganizationName("DMQC")
    w = MainWindow()
    w.show()
    return app.exec()

if __name__ == "__main__":
    raise SystemExit(main())
