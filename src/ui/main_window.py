# src/ui/main_window.py

import os
import sys
import ctypes
from pathlib import Path

# === ФИКС ДЛЯ PyInstaller ===
def load_libdmtx_dll():
    dll_name = "libdmtx-64.dll"
    if hasattr(sys, '_MEIPASS'):
        base_path = Path(sys._MEIPASS)
        dll_path = base_path / 'pylibdmtx' / dll_name
    else:
        try:
            import site
            site_packages = Path(site.getsitepackages()[0])
            dll_path = site_packages / 'pylibdmtx' / dll_name
        except Exception:
            dll_path = None
    if dll_path and dll_path.exists():
        try:
            if sys.platform == 'win32':
                os.add_dll_directory(str(dll_path.parent))
            ctypes.CDLL(str(dll_path))
            return True
        except Exception as e:
            print(f"DLL load error: {e}")
    return False

load_libdmtx_dll()

# Импорты
import cv2
import numpy as np
from PIL import Image
from pylibdmtx.pylibdmtx import decode as dmtx_decode
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QPixmap, QImage, QAction, QFont
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFileDialog, QTextEdit, QProgressBar, QMessageBox, QGroupBox
)

from src.utils.path_helper import resource_path


class DecodeThread(QThread):
    finished = Signal(dict)

    def __init__(self, image_path):
        super().__init__()
        self.image_path = image_path

    def run(self):
        try:
            img = Image.open(self.image_path)
            decoded = dmtx_decode(img)
            if not decoded:
                self.finished.emit({'success': False, 'error': "DataMatrix код не найден"})
                return
            code = decoded[0]
            data = code.data.decode('utf-8', errors='replace')
            quality = 100.0
            self.finished.emit({'success': True, 'data': data, 'quality': quality, 'raw': code})
        except Exception as e:
            self.finished.emit({'success': False, 'error': f"Ошибка: {str(e)}"})


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DataMatrix Quality Checker")
        self.setMinimumSize(900, 700)
        self.current_image_path = None
        self.decode_thread = None
        self.setup_ui()
        self.apply_styles()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)

        top_panel = QHBoxLayout()
        self.load_btn = QPushButton("📂 Загрузить изображение")
        self.load_btn.clicked.connect(self.load_image)
        self.check_btn = QPushButton("🔍 Проверить DataMatrix")
        self.check_btn.clicked.connect(self.check_datamatrix)
        self.check_btn.setEnabled(False)
        top_panel.addWidget(self.load_btn)
        top_panel.addWidget(self.check_btn)
        top_panel.addStretch()
        main_layout.addLayout(top_panel)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("border: 2px solid #cccccc; background-color: #2d2d2d;")
        self.image_label.setMinimumHeight(400)
        self.image_label.setText("Загрузите изображение с DataMatrix кодом")
        main_layout.addWidget(self.image_label, stretch=2)

        result_group = QGroupBox("Результат проверки")
        result_layout = QVBoxLayout()
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setFont(QFont("Courier New", 10))
        self.result_text.setMaximumHeight(150)
        result_layout.addWidget(self.result_text)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        result_layout.addWidget(self.progress_bar)
        result_group.setLayout(result_layout)
        main_layout.addWidget(result_group, stretch=1)

        self.status_label = QLabel("Готов")
        self.statusBar().addWidget(self.status_label)

    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e1e; }
            QPushButton {
                background-color: #3c3c3c; color: white; border: 1px solid #555;
                border-radius: 5px; padding: 8px 16px; font-size: 12pt;
            }
            QPushButton:hover { background-color: #505050; }
            QPushButton:pressed { background-color: #2d2d2d; }
            QPushButton:disabled { background-color: #2d2d2d; color: #888; }
            QGroupBox { color: #ddd; border: 1px solid #555; border-radius: 5px; margin-top: 10px; font-size: 11pt; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px 0 5px; }
            QTextEdit { background-color: #2d2d2d; color: #e0e0e0; border: 1px solid #555; border-radius: 4px; }
            QLabel { color: #ccc; }
            QProgressBar { border: 1px solid #555; border-radius: 3px; text-align: center; color: white; }
            QProgressBar::chunk { background-color: #4c8baf; border-radius: 3px; }
        """)

    def load_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите изображение", "",
            "Изображения (*.png *.jpg *.jpeg *.bmp *.tiff);;Все файлы (*.*)"
        )
        if not file_path:
            return
        self.current_image_path = file_path
        self.display_image(file_path)
        self.check_btn.setEnabled(True)
        self.result_text.clear()
        self.status_label.setText(f"Загружено: {file_path.split('/')[-1]}")

    def display_image(self, path):
        pixmap = QPixmap(path)
        if pixmap.isNull():
            self.image_label.setText("Не удалось загрузить изображение")
            return
        scaled = pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.image_label.setPixmap(scaled)
        self.image_label.setAlignment(Qt.AlignCenter)

    def check_datamatrix(self):
        if not self.current_image_path:
            QMessageBox.warning(self, "Нет изображения", "Сначала загрузите изображение.")
            return
        self.load_btn.setEnabled(False)
        self.check_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.status_label.setText("Распознавание DataMatrix...")
        self.decode_thread = DecodeThread(self.current_image_path)
        self.decode_thread.finished.connect(self.on_decode_finished)
        self.decode_thread.start()

    def on_decode_finished(self, result):
        self.progress_bar.setVisible(False)
        self.load_btn.setEnabled(True)
        self.check_btn.setEnabled(True)
        if result['success']:
            data = result['data']
            quality = result.get('quality', 0)
            report = f"✅ DataMatrix распознан!\n\n📌 Данные:\n{data}\n\n📊 Качество: {quality:.1f}%\n"
            if quality >= 80: report += "▶ Качество: ХОРОШЕЕ\n"
            elif quality >= 50: report += "▶ Качество: СРЕДНЕЕ\n"
            else: report += "▶ Качество: НИЗКОЕ\n"
            self.result_text.setText(report)
            self.status_label.setText(f"Распознано: {len(data)} символов, качество {quality:.0f}%")
        else:
            error = result['error']
            self.result_text.setText(f"❌ Ошибка:\n{error}")
            self.status_label.setText("Ошибка распознавания")
            QMessageBox.warning(self, "Ошибка", f"Не удалось прочитать DataMatrix:\n{error}")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.current_image_path:
            self.display_image(self.current_image_path)
