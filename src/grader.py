"""
grader.py — превращает метрики качества в итоговый score (0..100) и Grade A..F.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .quality import QualityMetrics


GRADE_THRESHOLDS = [
    (90, "A"),
    (75, "B"),
    (60, "C"),
    (40, "D"),
    (0,  "F"),
]

# Цвета BGR (OpenCV) для overlay
GRADE_COLOR_BGR = {
    "A": (76, 175, 80),    # зелёный
    "B": (66, 165, 245),   # синий
    "C": (255, 235, 59),   # жёлтый
    "D": (255, 152, 0),    # оранжевый
    "F": (244, 67, 54),    # красный
}

# Тот же набор в RGB/HEX для Qt
GRADE_COLOR_HEX = {
    "A": "#4CAF50",
    "B": "#42A5F5",
    "C": "#FFEB3B",
    "D": "#FF9800",
    "F": "#F44336",
}

MIN_GRADE_ORDER = {"A": 5, "B": 4, "C": 3, "D": 2, "F": 1}


@dataclass
class Grade:
    score: int            # 0..100
    letter: str           # A/B/C/D/F
    metrics: QualityMetrics

    def is_acceptable(self, min_grade: str) -> bool:
        return MIN_GRADE_ORDER.get(self.letter, 0) >= MIN_GRADE_ORDER.get(min_grade, 3)


def compute_grade(metrics: QualityMetrics, weights: Mapping[str, float]) -> Grade:
    """Взвешенная сумма → score 0..100 → letter."""
    s = 0.0
    for key, w in weights.items():
        v = getattr(metrics, key, 0.0)
        s += float(v) * float(w)
    s = max(0.0, min(1.0, s))
    score = int(round(s * 100))

    letter = "F"
    for thr, l in GRADE_THRESHOLDS:
        if score >= thr:
            letter = l
            break
    return Grade(score=score, letter=letter, metrics=metrics)
