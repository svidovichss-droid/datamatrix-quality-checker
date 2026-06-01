""" pipeline.py — связывает захват кадра → декод → оценка качества → грейдер. """
from __future__ import annotations
import logging
import time
from dataclasses import dataclass
from typing import Optional
import cv2
import numpy as np
from src.camera import Camera      # абсолютный импорт
from src.config import AppConfig    # абсолютный импорт
from src.decoder import DMResult, decode_bgr  # абсолютный импорт
from src.grader import Grade, compute_grade   # абсолютный импорт
from src.quality import compute_all           # абсолютный импорт

log = logging.getLogger(__name__)

@dataclass
class FrameAnalysis:
    """Результат анализа одного кадра."""
    found: bool
    data: str
    rect: Optional[tuple[int, int, int, int]]
    grade: Optional[Grade]
    accept: bool
    fps: float
    timestamp_ms: int

class Pipeline:
    """Основной пайплайн обработки: кадр -> декодирование -> качество -> оценка."""

    def __init__(self, config: AppConfig, camera: Camera):
        self.config = config
        self.camera = camera
        self.last_frame_time = time.perf_counter()
        self.fps = 0.0
        self._frame_count = 0

    def process_frame(self) -> Optional[FrameAnalysis]:
        """
        Захватывает кадр, декодирует DM, вычисляет метрики качества и оценку.
        Возвращает FrameAnalysis или None, если кадр не получен.
        """
        frame = self.camera.read()
        if frame is None:
            return None

        now = time.perf_counter()
        dt = now - self.last_frame_time
        if dt > 0:
            self.fps = 0.9 * self.fps + 0.1 / dt if self.fps > 0 else 1.0 / dt
        self.last_frame_time = now
        self._frame_count += 1

        # Декодирование Data Matrix
        result: DMResult = decode_bgr(frame)
        found = result.success
        data = result.data or ""
        rect = result.rect  # (x, y, w, h) или None

        # Если не нашли, но нужно показать кадр без оценки
        if not found:
            grade = None
            accept = False
        else:
            # Вычисление метрик качества (обводка, контраст, модуляция и т.д.)
            quality_metrics = compute_all(frame, rect) if rect else {}
            # Вычисление итоговой оценки (A, B, C, D, F) на основе метрик и порогов из config
            grade = compute_grade(quality_metrics, self.config)
            accept = grade is not None and grade.value >= self.config.accept_threshold

        return FrameAnalysis(
            found=found,
            data=data,
            rect=rect,
            grade=grade,
            accept=accept,
            fps=round(self.fps, 1),
            timestamp_ms=int(now * 1000),
        )

    def stop(self) -> None:
        """Остановка (освобождение ресурсов при необходимости)."""
        # Здесь можно добавить логику остановки, если потребуется
        pass
