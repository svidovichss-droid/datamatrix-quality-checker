"""
logger.py — запись результатов в CSV + сохранение скриншотов отбраковки.
"""
from __future__ import annotations

import csv
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

from .grader import Grade

log = logging.getLogger(__name__)

CSV_FIELDS = [
    "timestamp", "data", "score", "grade",
    "decodability", "contrast", "modulation",
    "print_growth", "axial_nonuniformity", "fixed_pattern_damage",
    "accept", "screenshot",
]


class ResultLogger:
    def __init__(self, csv_path: str, reject_dir: str, save_screenshots: bool = True):
        self.csv_path = csv_path
        self.reject_dir = reject_dir
        self.save_screenshots = save_screenshots
        self._fh = None
        self._writer = None
        self._ensure()

    def _ensure(self) -> None:
        try:
            p = Path(self.csv_path)
            p.parent.mkdir(parents=True, exist_ok=True)
            new_file = not p.exists()
            self._fh = open(p, "a", newline="", encoding="utf-8")
            self._writer = csv.DictWriter(self._fh, fieldnames=CSV_FIELDS)
            if new_file:
                self._writer.writeheader()
                self._fh.flush()
        except OSError as e:
            log.error("Не удалось открыть CSV-лог: %s", e)
            self._fh = None
            self._writer = None

    def log(self, grade: Grade, data: str, frame: Optional[np.ndarray] = None,
            accept: bool = True) -> None:
        if self._writer is None:
            return
        ts = datetime.now().isoformat(timespec="milliseconds")
        m = grade.metrics
        screenshot = ""
        if not accept and self.save_screenshots and frame is not None:
            screenshot = self._save_reject(frame, data, grade)
        try:
            self._writer.writerow({
                "timestamp": ts,
                "data": data,
                "score": grade.score,
                "grade": grade.letter,
                "decodability": f"{m.decodability:.3f}",
                "contrast": f"{m.contrast:.3f}",
                "modulation": f"{m.modulation:.3f}",
                "print_growth": f"{m.print_growth:.3f}",
                "axial_nonuniformity": f"{m.axial_nonuniformity:.3f}",
                "fixed_pattern_damage": f"{m.fixed_pattern_damage:.3f}",
                "accept": "yes" if accept else "no",
                "screenshot": screenshot,
            })
            self._fh.flush()
        except Exception as e:  # noqa: BLE001
            log.error("Ошибка записи в CSV: %s", e)

    def _save_reject(self, frame: np.ndarray, data: str, grade: Grade) -> str:
        try:
            d = Path(self.reject_dir)
            d.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            safe = "".join(c if c.isalnum() else "_" for c in data)[:24] or "empty"
            name = f"{ts}_{grade.letter}_{grade.score}_{safe}.jpg"
            path = d / name
            cv2.imwrite(str(path), frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            return str(path)
        except OSError as e:
            log.error("Не удалось сохранить reject-скриншот: %s", e)
            return ""

    def close(self) -> None:
        if self._fh is not None:
            try:
                self._fh.close()
            except Exception:
                pass
        self._fh = None
        self._writer = None
