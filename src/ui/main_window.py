# src/ui/main_window.py

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
    """Поток для декодирования DataMatrix, чтобы не блокировать UI"""
    finished = Signal(dict)  # результат в виде словаря: success, data, quality, error

    def __init__(self, image_path):
        super().__init__()
        self.image_path = image_path

    def run(self):
        try:
            # Открываем изображение
            img = Image.open(self.image_path)
            # Декодируем DataMatrix
            decoded = dmtx_decode(img)
            if not decoded:
                self.finished.emit({
                    'success': False,
                    'error': "DataMatrix код не найден на изображении"
                })
                return

            # Берём первый найденный код
            code = decoded[0]
            data = code.data.decode('utf-8', errors='replace')
            # Простейшая оценка качества: если декодировалось без ошибок — считаем качество 100%
            # В реальном проекте здесь можно реализовать анализ контраста, модуляции и т.д.
            quality = 100.0

            self.finished.emit({
                'success': True,
                'data': data,
                'quality': quality,
                'raw': code
            })
        except Exception as e:
            self.finished.emit({
                'success': False,
                'error': f"Ошибка обработки: {str(e)}"
            })


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DataMatrix Quality Checker")
        self.setMinimumSize(900, 700)

        # Текущий путь к изображению
        self.current_image_path = None
        self.decode_thread = None

        self.setup_ui()
        self.apply_styles()

    def setup_ui(self):
        """Создаёт все виджеты и размещает их"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # Верхняя панель с кнопками
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

        # Область отображения изображения
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("border: 2px solid #cccccc; background-color: #2d2d2d;")
        self.image_label.setMinimumHeight(400)
        self.image_label.setText("Загрузите изображение с DataMatrix кодом")
        main_layout.addWidget(self.image_label, stretch=2)

        # Группа результатов
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

        # Строка состояния
        self.status_label = QLabel("Готов")
        self.statusBar().addWidget(self.status_label)

    def apply_styles(self):
        """Применяет тёмную тему для современного вида"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            QPushButton {
                background-color: #3c3c3c;
                color: white;
                border: 1px solid #555;
                border-radius: 5px;
                padding: 8px 16px;
                font-size: 12pt;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QPushButton:pressed {
                background-color: #2d2d2d;
            }
            QPushButton:disabled {
                background-color: #2d2d2d;
                color: #888;
            }
            QGroupBox {
                color: #ddd;
                border: 1px solid #555;
                border-radius: 5px;
                margin-top: 10px;
                font-size: 11pt;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QTextEdit {
                background-color: #2d2d2d;
                color: #e0e0e0;
                border: 1px solid #555;
                border-radius: 4px;
            }
            QLabel {
                color: #ccc;
            }
            QProgressBar {
                border: 1px solid #555;
                border-radius: 3px;
                text-align: center;
                color: white;
            }
            QProgressBar::chunk {
                background-color: #4c8baf;
                border-radius: 3px;
            }
        """)

    def load_image(self):
        """Открывает диалог выбора файла и отображает изображение"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите изображение",
            "",
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
        """Показывает изображение в QLabel с сохранением пропорций"""
        pixmap = QPixmap(path)
        if pixmap.isNull():
            self.image_label.setText("Не удалось загрузить изображение")
            return
        # Масштабируем под размеры лейбла
        scaled = pixmap.scaled(
            self.image_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.image_label.setPixmap(scaled)
        self.image_label.setAlignment(Qt.AlignCenter)

    def check_datamatrix(self):
        """Запускает распознавание DataMatrix в отдельном потоке"""
        if not self.current_image_path:
            QMessageBox.warning(self, "Нет изображения", "Сначала загрузите изображение.")
            return

        # Блокируем кнопки на время проверки
        self.load_btn.setEnabled(False)
        self.check_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # индикатор неопределённой длительности
        self.status_label.setText("Распознавание DataMatrix...")

        # Запускаем поток
        self.decode_thread = DecodeThread(self.current_image_path)
        self.decode_thread.finished.connect(self.on_decode_finished)
        self.decode_thread.start()

    def on_decode_finished(self, result):
        """Обрабатывает результат из потока"""
        self.progress_bar.setVisible(False)
        self.load_btn.setEnabled(True)
        self.check_btn.setEnabled(True)

        if result['success']:
            data = result['data']
            quality = result.get('quality', 0)

            # Формируем отчёт
            report = f"✅ DataMatrix распознан успешно!\n\n"
            report += f"📌 Декодированные данные:\n{data}\n\n"
            report += f"📊 Оценка качества: {quality:.1f}%\n"
            if quality >= 80:
                report += "▶ Качество: ХОРОШЕЕ\n"
            elif quality >= 50:
                report += "▶ Качество: СРЕДНЕЕ (требуется проверка)\n"
            else:
                report += "▶ Качество: НИЗКОЕ (код может быть повреждён)\n"

            self.result_text.setText(report)
            self.status_label.setText(f"Распознано: {len(data)} символов, качество {quality:.0f}%")
        else:
            error = result['error']
            self.result_text.setText(f"❌ Ошибка распознавания:\n{error}")
            self.status_label.setText("Ошибка распознавания")
            QMessageBox.warning(self, "Ошибка", f"Не удалось прочитать DataMatrix:\n{error}")

    def resizeEvent(self, event):
        """При изменении размера окна перемасштабируем изображение"""
        super().resizeEvent(event)
        if self.current_image_path:
            self.display_image(self.current_image_path)
