"""
test_quality.py — быстрый smoke-test для модулей quality + decoder без GUI.

Запуск:
    python scripts/test_quality.py samples/dm_clean.png
"""
from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np

from src.decoder import decode_bgr
from src.quality import compute_all
from src.grader import compute_grade


def main(path: str) -> int:
    img = cv2.imread(path)
    if img is None:
        print(f"не удалось загрузить {path}")
        return 1

    results = decode_bgr(img)
    if not results:
        print("DataMatrix НЕ найден в изображении")
        return 2

    res = results[0]
    x, y, w, h = res.rect
    print(f"DataMatrix: '{res.data}' bbox=({x},{y},{w},{h})")

    roi_gray = cv2.cvtColor(img[y:y + h, x:x + w], cv2.COLOR_BGR2GRAY)
    metrics = compute_all(roi_gray, success_streak=5, total_attempts=5, required=3)
    weights = {
        "decodability": 0.30, "contrast": 0.20, "modulation": 0.15,
        "print_growth": 0.15, "axial_nonuniformity": 0.10, "fixed_pattern_damage": 0.10,
    }
    grade = compute_grade(metrics, weights)
    print(f"Score: {grade.score}  Grade: {grade.letter}")
    for k, v in metrics.to_dict().items():
        print(f"  {k:24s} = {v:.3f}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python scripts/test_quality.py <image.png>")
        raise SystemExit(1)
    raise SystemExit(main(sys.argv[1]))
