"""
pipeline.py — связывает захват кадра → декод → оценка качества → грейдер.
Использует in-memory state (стрики чтений) для decodability.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Optional

import cv2
import numpy as np

from .camera import Camera
from .config import AppConfig
from .decoder import DMResult, decode_bgr
from .grader import Grade, compute_grade
from .quality import compute_all

log = logging.getLogger(__name__)


@dataclass
class FrameAnalysis:
    found: bool
    data: str
    rect: Optional[tuple[int, int, int, int]]
    grade: Optional[Grade]
    accept: bool
    fps: float
    timestamp_ms: int


class Pipeline:
    def __init__(self, camera: Camera, config: AppConfig):
        self.camera = camera
        self.config = config
        self._last_data: str = ""
        self._success_streak: int = 0
        self._total_attempts: int = 0
        self._last_trigger_ms: int = 0
        self._frame_count: int = 0
        self._t0 = time.monotonic()

    def reset_state(self) -> None:
        self._last_data = ""
        self._success_streak = 0
        self._total_attempts = 0

    def process(self) -> tuple[Optional[np.ndarray], FrameAnalysis]:
        """
        Берёт кадр из камеры, декодирует, считает качество.
        Возвращает (frame_with_overlay, FrameAnalysis).
        """
        frame = self.camera.read()
        if frame is None:
            return None, FrameAnalysis(False, "", None, None, False, 0.0, 0)

        self._frame_count += 1
        elapsed = time.monotonic() - self._t0
        fps = self._frame_count / elapsed if elapsed > 0 else 0.0

        # ROI
        roi = None
        cfg_roi = self.config.roi
        if len(cfg_roi) == 4 and any(cfg_roi):
            roi = tuple(cfg_roi)

        # 1) Декод
        results: list[DMResult] = decode_bgr(frame, roi=roi, timeout_ms=80)
        self._total_attempts += 1

        analysis = FrameAnalysis(
            found=False, data="", rect=None, grade=None,
            accept=False, fps=fps, timestamp_ms=int(time.time() * 1000),
        )

        overlay = frame.copy()

        if not results:
            # ничего не нашли — сбрасываем стрик
            if self._success_streak > 0:
                self._success_streak = 0
            cv2.putText(overlay, f"FPS: {fps:.1f}", (12, 28),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)
            cv2.putText(overlay, "Scanning...", (12, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (180, 180, 180), 2)
            return overlay, analysis

        # Берём первый (или самый крупный) результат
        res = max(results, key=lambda r: r.rect[2] * r.rect[3])
        data = res.data
        rect = res.rect
        x, y, w, h = rect

        # Обновляем стрик decodability
        if data == self._last_data:
            self._success_streak += 1
        else:
            self._last_data = data
            self._success_streak = 1

        # 2) ROI-кадр в градациях серого → метрики
        H, W = frame.shape[:2]
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(W, x + w), min(H, y + h)
        if x1 <= x0 or y1 <= y0:
            cv2.putText(overlay, f"FPS: {fps:.1f}", (12, 28),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)
            return overlay, analysis

        roi_gray = cv2.cvtColor(frame[y0:y1, x0:x1], cv2.COLOR_BGR2GRAY)

        metrics = compute_all(
            roi_gray,
            success_streak=self._success_streak,
            total_attempts=self._total_attempts,
            required=self.config.stable_reads_required,
        )
        grade = compute_grade(metrics, self.config.weights)
        accept = grade.is_acceptable(self.config.min_grade)

        analysis = FrameAnalysis(
            found=True,
            data=data,
            rect=rect,
            grade=grade,
            accept=accept,
            fps=fps,
            timestamp_ms=int(time.time() * 1000),
        )
        return overlay, analysis
