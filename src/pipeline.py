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
    found: bool
    data: str
    rect: Optional[tuple[int, int, int, int]]
    grade: Optional[Grade]
    accept: bool
    fps: float
    timestamp_ms: int

class Pipeline:
    # ... (остальной код класса Pipeline остаётся без изменений) ...
