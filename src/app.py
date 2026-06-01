"""
app.py — главное окно приложения (PySide6).
"""
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
    QApplication, QCheckBox, QComboBox, QDoubleSpinBox, QFileDialog, QFormLayout,
    QGroupBox, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox, QPushButton,
    QSizePolicy, QSpinBox, QSplitter, QStatusBar, QStyle, QTextEdit, QVBoxLayout, QWidget,
)

from .camera import Camera, CameraInfo, list_local_cameras
from .config import AppConfig
from .grader import GRADE_COLOR_BGR, GRADE_COLOR_HEX
from .logger import ResultLogger
from .pipeline import FrameAnalysis, Pipeline

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
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DataMatrix Quality Checker")
        self.setMinimumSize(1100, 680)

        self.config = AppConfig.load()
        self.camera = Camera()
        self.pipeline = Pipeline(self.camera, self.config)
        self.logger = ResultLogger(
            self.config.log_csv,
            self.config.reject_dir,
            self.config.save_screenshots,
        )

        self._running = False
        self._last_analysis: Optional[FrameAnalysis] = None
        self._last_frame: Optional[np.ndarray] = None

        self._build_ui()
        self._build_menu()
        self._apply_config_to_ui()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.setInterval(66)  # ~15 fps UI

        self._refresh_cameras()

    # ---- UI construction ----

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(8, 8, 8, 8)

        splitter = QSplitter(Qt.Horizontal)
        root.addWidget(splitter)

        # --- левая часть: видео ---
        left = QWidget()
        left_lay = QVBoxLayout(left)
        left_lay.setContentsMargins(0, 0, 0, 0)

        self.video_label = QLabel("Камера не запущена")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("background:#111; color:#aaa;")
        self.video_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.video_label.setMinimumSize(640, 480)
        left_lay.addWidget(self.video_label, 1)

        ctrl = QHBoxLayout()
        self.btn_start = QPushButton("▶ Start")
        self.btn_start.setMinimumHeight(36)
        self.btn_stop = QPushButton("■ Stop")
        self.btn_stop.setMinimumHeight(36)
        self.btn_stop.setEnabled(False)
        self.btn_start.clicked.connect(self._on_start)
        self.btn_stop.clicked.connect(self._on_stop)
        ctrl.addWidget(self.btn_start)
        ctrl.addWidget(self.btn_stop)

        self.lbl_fps = QLabel("FPS: 0.0")
        self.lbl_fps.setStyleSheet("color:#888; padding-left:12px;")
        ctrl.addWidget(self.lbl_fps, 1)

        left_lay.addLayout(ctrl)
        splitter.addWidget(left)

        # --- правая часть: настройки + лог ---
        right = QWidget()
        right_lay = QVBoxLayout(right)
        right_lay.setContentsMargins(0, 0, 0, 0)

        # камера
        gb_cam = QGroupBox("Камера")
        form = QFormLayout(gb_cam)
        self.cmb_camera = QComboBox()
        self.cmb_camera.setMinimumWidth(220)
        self.btn_refresh = QPushButton("↻")
        self.btn_refresh.setFixedWidth(32)
        self.btn_refresh.clicked.connect(self._refresh_cameras)
        cam_row = QHBoxLayout()
        cam_row.addWidget(self.cmb_camera, 1)
        cam_row.addWidget(self.btn_refresh)
        form.addRow("Источник:", _wrap(cam_row))

        self.edt_url = QLineEdit()
        self.edt_url.setPlaceholderText("rtsp:// или http://… (если IP-камера)")
        form.addRow("URL (опц.):", self.edt_url)

        self.sp_res_w = QSpinBox()
        self.sp_res_w.setRange(160, 7680)
        self.sp_res_h = QSpinBox()
        self.sp_res_h.setRange(120, 4320)
        res_row = QHBoxLayout()
        res_row.addWidget(self.sp_res_w)
        res_row.addWidget(QLabel("×"))
        res_row.addWidget(self.sp_res_h)
        form.addRow("Разрешение:", _wrap(res_row))

        self.sp_fps = QSpinBox()
        self.sp_fps.setRange(1, 60)
        form.addRow("FPS цель:", self.sp_fps)
        right_lay.addWidget(gb_cam)

        # grading
        gb_g = QGroupBox("Грейдер")
        gl = QFormLayout(gb_g)
        self.cmb_min_grade = QComboBox()
        self.cmb_min_grade.addItems(["A", "B", "C", "D", "F"])
        gl.addRow("Минимальный Grade:", self.cmb_min_grade)

        self.sp_cooldown = QSpinBox()
        self.sp_cooldown.setRange(0, 10000)
        self.sp_cooldown.setSuffix(" мс")
        gl.addRow("Cooldown:", self.sp_cooldown)

        self.sp_stable = QSpinBox()
        self.sp_stable.setRange(1, 30)
        gl.addRow("Стабильных чтений:", self.sp_stable)

        self.chk_screenshots = QCheckBox("Сохранять скриншоты отбраковки")
        gl.addRow("", self.chk_screenshots)
        right_lay.addWidget(gb_g)

        # результат
        gb_res = QGroupBox("Результат")
        rl = QVBoxLayout(gb_res)
        self.lbl_grade = QLabel("—")
        self.lbl_grade.setAlignment(Qt.AlignCenter)
        f = QFont()
        f.setPointSize(48)
        f.setBold(True)
        self.lbl_grade.setFont(f)
        self.lbl_grade.setStyleSheet("color:#888; padding:8px;")
        rl.addWidget(self.lbl_grade)

        self.lbl_data = QLabel("Data: —")
        self.lbl_data.setWordWrap(True)
        self.lbl_data.setStyleSheet("color:#ddd;")
        rl.addWidget(self.lbl_data)

        self.lbl_score = QLabel("Score: —")
        self.lbl_score.setStyleSheet("color:#ddd;")
        rl.addWidget(self.lbl_score)

        self.txt_metrics = QTextEdit()
        self.txt_metrics.setReadOnly(True)
        self.txt_metrics.setStyleSheet(
            "background:#1a1a1a; color:#bbb; font-family:Consolas, monospace; font-size:11px;")
        self.txt_metrics.setMaximumHeight(140)
        rl.addWidget(self.txt_metrics)
        right_lay.addWidget(gb_res, 1)

        right.setMaximumWidth(420)
        splitter.addWidget(right)
        splitter.setSizes([800, 360])

        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Готов")

    def _build_menu(self) -> None:
        m_file = self.menuBar().addMenu("&Файл")
        a_open_csv = QAction("Открыть папку логов", self)
        a_open_csv.triggered.connect(self._open_log_dir)
        m_file.addAction(a_open_csv)

        a_open_rej = QAction("Открыть папку отбраковки", self)
        a_open_rej.triggered.connect(self._open_reject_dir)
        m_file.addAction(a_open_rej)

        m_file.addSeparator()
        a_quit = QAction("Выход", self)
        a_quit.setShortcut(QKeySequence.Quit)
        a_quit.triggered.connect(self.close)
        m_file.addAction(a_quit)

        m_help = self.menuBar().addMenu("&Помощь")
        a_about = QAction("О программе", self)
        a_about.triggered.connect(self._about)
        m_help.addAction(a_about)

    # ---- config <-> UI ----

    def _apply_config_to_ui(self) -> None:
        self.edt_url.setText(self.config.camera_url)
        self.sp_res_w.setValue(self.config.resolution[0])
        self.sp_res_h.setValue(self.config.resolution[1])
        self.sp_fps.setValue(self.config.fps_target)
        self.cmb_min_grade.setCurrentText(self.config.min_grade)
        self.sp_cooldown.setValue(self.config.trigger_cooldown_ms)
        self.sp_stable.setValue(self.config.stable_reads_required)
        self.chk_screenshots.setChecked(self.config.save_screenshots)

    def _read_ui_to_config(self) -> None:
        url = self.edt_url.text().strip()
        if url:
            self.config.camera_url = url
        else:
            self.config.camera_url = ""
        self.config.resolution = [self.sp_res_w.value(), self.sp_res_h.value()]
        self.config.fps_target = self.sp_fps.value()
        self.config.min_grade = self.cmb_min_grade.currentText()
        self.config.trigger_cooldown_ms = self.sp_cooldown.value()
        self.config.stable_reads_required = self.sp_stable.value()
        self.config.save_screenshots = self.chk_screenshots.isChecked()
        # если выбран URL — camera_index игнорируется
        idx = self.cmb_camera.currentIndex()
        if idx >= 0 and not self.config.camera_url:
            data = self.cmb_camera.itemData(idx)
            if isinstance(data, int):
                self.config.camera_index = data
        self.config.save()

    # ---- actions ----

    def _refresh_cameras(self) -> None:
        self.cmb_camera.clear()
        cams = list_local_cameras(max_index=6)
        if not cams:
            self.cmb_camera.addItem("Камеры не найдены", -1)
            self.statusBar().showMessage("Камеры не найдены", 4000)
            return
        for c in cams:
            self.cmb_camera.addItem(c.name, c.index)
        # выберем ранее сохранённый, если есть
        for i in range(self.cmb_camera.count()):
            if self.cmb_camera.itemData(i) == self.config.camera_index:
                self.cmb_camera.setCurrentIndex(i)
                break
        self.statusBar().showMessage(f"Найдено камер: {len(cams)}", 3000)

    def _on_start(self) -> None:
        self._read_ui_to_config()

        source: str | int
        if self.config.camera_url:
            source = self.config.camera_url
        else:
            idx = self.config.camera_index
            if idx < 0:
                QMessageBox.warning(self, "Камера", "Камера не выбрана")
                return
            source = idx

        ok = self.camera.open(
            source,
            resolution=tuple(self.config.resolution),  # type: ignore[arg-type]
            fps_target=self.config.fps_target,
        )
        if not ok:
            err = self.camera.last_error or "Неизвестная ошибка"
            QMessageBox.critical(self, "Ошибка камеры", err)
            return

        self.pipeline.reset_state()
        self._running = True
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.timer.start()
        self.statusBar().showMessage("Захват запущен")

    def _on_stop(self) -> None:
        self._running = False
        self.timer.stop()
        self.camera.close()
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.video_label.setText("Камера остановлена")
        self.statusBar().showMessage("Остановлено")

    def _tick(self) -> None:
        if not self._running:
            return
        try:
            overlay, analysis = self.pipeline.process()
        except Exception as e:  # noqa: BLE001
            log.exception("pipeline error: %s", e)
            return
        if overlay is None:
            return
        self._last_frame = overlay
        self._last_analysis = analysis
        self._update_video(overlay)
        self._update_right_panel(analysis)

        # запись в лог (cooldown для стабильности)
        if analysis.found and analysis.grade is not None:
            now = analysis.timestamp_ms
            if now - self.pipeline._last_trigger_ms > self.config.trigger_cooldown_ms:
                self.pipeline._last_trigger_ms = now
                self.logger.log(analysis.grade, analysis.data, frame=overlay,
                                accept=analysis.accept)

    def _update_video(self, frame_bgr: np.ndarray) -> None:
        # рисуем bbox и метки
        a = self._last_analysis
        if a is not None and a.found and a.grade is not None and a.rect is not None:
            x, y, w, h = a.rect
            color = GRADE_COLOR_BGR.get(a.grade.letter, (255, 255, 255))
            cv2.rectangle(frame_bgr, (x, y), (x + w, y + h), color, 3)
            label = f"{a.grade.letter} {a.grade.score}/100"
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.9, 2)
            ty = max(y - 10, th + 4)
            cv2.rectangle(frame_bgr, (x, ty - th - 6), (x + tw + 8, ty + 4), color, -1)
            cv2.putText(frame_bgr, label, (x + 4, ty - 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 2)

        # привести к размеру label
        h, w = frame_bgr.shape[:2]
        target_w = self.video_label.width()
        target_h = self.video_label.height()
        if target_w <= 0 or target_h <= 0:
            return
        scale = min(target_w / w, target_h / h)
        if scale < 1.0:
            new_w = int(w * scale)
            new_h = int(h * scale)
            frame_bgr = cv2.resize(frame_bgr, (new_w, new_h), interpolation=cv2.INTER_AREA)
        qimg = bgr_to_qimage(frame_bgr)
        self.video_label.setPixmap(QPixmap.fromImage(qimg))

    def _update_right_panel(self, a: FrameAnalysis) -> None:
        self.lbl_fps.setText(f"FPS: {a.fps:.1f}")
        if not a.found or a.grade is None:
            self.lbl_grade.setText("—")
            self.lbl_grade.setStyleSheet("color:#666; padding:8px;")
            return
        self.lbl_grade.setText(f"{a.grade.letter}  {a.grade.score}")
        color = GRADE_COLOR_HEX.get(a.grade.letter, "#888")
        self.lbl_grade.setStyleSheet(f"color:{color}; padding:8px;")
        self.lbl_data.setText(f"Data: {a.data if len(a.data) < 200 else a.data[:200] + '…'}")
        self.lbl_score.setText(f"Score: {a.grade.score}/100  —  {'PASS' if a.accept else 'REJECT'}")
        m = a.grade.metrics
        self.txt_metrics.setPlainText(
            f"Decodability   : {m.decodability:.3f}\n"
            f"Contrast       : {m.contrast:.3f}\n"
            f"Modulation     : {m.modulation:.3f}\n"
            f"Print Growth   : {m.print_growth:.3f}\n"
            f"Axial Non-Unif.: {m.axial_nonuniformity:.3f}\n"
            f"Fixed P. Damage: {m.fixed_pattern_damage:.3f}\n"
        )

    def _open_log_dir(self) -> None:
        p = Path(self.config.log_csv).parent
        p.mkdir(parents=True, exist_ok=True)
        self._reveal(p)

    def _open_reject_dir(self) -> None:
        p = Path(self.config.reject_dir)
        p.mkdir(parents=True, exist_ok=True)
        self._reveal(p)

    def _reveal(self, p: Path) -> None:
        try:
            if sys.platform.startswith("win"):
                os.startfile(str(p))  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                os.system(f'open "{p}"')
            else:
                os.system(f'xdg-open "{p}"')
        except Exception as e:  # noqa: BLE001
            QMessageBox.warning(self, "Открыть папку", str(e))

    def _about(self) -> None:
        QMessageBox.information(
            self, "О программе",
            "<b>DataMatrix Quality Checker</b><br>"
            "Лёгкий скрининг-грейдер DataMatrix по упрощённой ISO/IEC 15415.<br><br>"
            "MIT License. Использует OpenCV, PySide6 и pylibdmtx."
        )

    # ---- lifecycle ----

    def closeEvent(self, e):  # noqa: N802
        try:
            self._read_ui_to_config()
            self._on_stop()
            self.logger.close()
        finally:
            super().closeEvent(e)


def _wrap(layout) -> QWidget:
    w = QWidget()
    w.setLayout(layout)
    layout.setContentsMargins(0, 0, 0, 0)
    return w
