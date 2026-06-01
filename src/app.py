""" app.py — главное окно приложения (PySide6). """
from __future__ import annotations
import logging
import os
import sys
from pathlib import Path
from typing import Optional
import cv2
import numpy as np
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QAction, QColor, QFont, QImage, QKeySequence, QPalette, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QStatusBar,
    QStyle,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from src.camera import Camera, CameraInfo, list_local_cameras  # абсолютный импорт
from src.config import AppConfig                                 # абсолютный импорт
from src.grader import GRADE_COLOR_BGR, GRADE_COLOR_HEX          # абсолютный импорт
from src.logger import ResultLogger                              # абсолютный импорт
from src.pipeline import FrameAnalysis, Pipeline                 # абсолютный импорт

log = logging.getLogger(__name__)

# ---------- утилиты конвертации BGR -> QImage ----------
def bgr_to_qimage(bgr: np.ndarray) -> QImage:
    if bgr is None or bgr.size == 0:
        return QImage()
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    h, w, ch = rgb.shape
    return QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888).copy()

# ---------- главное окно ----------
class MainWindow(QMainWindow):
    # ... (остальной код класса MainWindow остаётся без изменений) ...
