"""
quality.py — расчёт параметров качества DataMatrix по упрощённой модели ISO/IEC 15415.

Параметры:
- decodability  : стабильность чтения (0..1)
- contrast      : нормированный контраст (0..1)
- modulation    : резкость края / Laplacian variance (0..1)
- print_growth  : отклонение площади модуля от эталона (0..1, где 1 = идеал)
- axial_nonuniformity : геометрические искажения (0..1)
- fixed_pattern_damage : % повреждённых ячеек (0..1, где 1 = без повреждений)

Все метрики приведены к диапазону [0, 1], где 1 = идеал.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import cv2
import numpy as np

log = logging.getLogger(__name__)


@dataclass
class QualityMetrics:
    decodability: float = 0.0
    contrast: float = 0.0
    modulation: float = 0.0
    print_growth: float = 0.0
    axial_nonuniformity: float = 0.0
    fixed_pattern_damage: float = 0.0

    def to_dict(self) -> dict[str, float]:
        return {
            "decodability": self.decodability,
            "contrast": self.contrast,
            "modulation": self.modulation,
            "print_growth": self.print_growth,
            "axial_nonuniformity": self.axial_nonuniformity,
            "fixed_pattern_damage": self.fixed_pattern_damage,
        }


def contrast_score(roi_gray: np.ndarray) -> float:
    """
    Нормированный контраст = (max - min) / 255.
    Типично хорошая печать: 0.6–0.9.
    """
    if roi_gray is None or roi_gray.size == 0:
        return 0.0
    lo = float(np.min(roi_gray))
    hi = float(np.max(roi_gray))
    return float(np.clip((hi - lo) / 255.0, 0.0, 1.0))


def modulation_score(roi_gray: np.ndarray) -> float:
    """
    Резкость края — variance of Laplacian.
    Сигма 0 = идеально резкий, шум/мыло снижают.
    Возвращаем нормализованную метрику (логистическая привязка к типичному диапазону).
    """
    if roi_gray is None or roi_gray.size == 0:
        return 0.0
    lap = cv2.Laplacian(roi_gray, cv2.CV_64F)
    var = float(np.var(lap))
    # Типичный диапазон для DataMatrix в реальных условиях: 50–2000
    # Логистическая нормализация: 1 / (1 + exp(-(x - center)/scale))
    score = 1.0 / (1.0 + np.exp(-(var - 200.0) / 300.0))
    return float(np.clip(score, 0.0, 1.0))


def estimate_module_grid(roi_gray: np.ndarray, rect: Optional[tuple[int, int, int, int]] = None) -> Optional[tuple[int, int, int, int, int]]:
    """
    Пытается оценить параметры регулярной сетки модулей (cell pitch) внутри ROI.

    Возвращает (rows, cols, cell_w, cell_h, module_size_px) или None, если не нашли.
    """
    if roi_gray is None or roi_gray.size == 0:
        return None

    # Бинаризуем по Отсу
    _, bw = cv2.threshold(roi_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # FFT-пик — оценка средней частоты (модуля)
    f = np.fft.fft2(bw.astype(np.float32) / 255.0)
    fshift = np.fft.fftshift(f)
    mag = 20.0 * np.log(np.abs(fshift) + 1e-6)

    h, w = mag.shape
    cy, cx = h // 2, w // 2
    # маска — игнорируем DC-пик
    yy, xx = np.ogrid[:h, :w]
    r = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    mag[r < 5] = 0

    peak = np.unravel_index(np.argmax(mag), mag.shape)
    py, px = peak
    # расстояние от центра в пикселях (частота)
    dy = abs(py - cy)
    dx = abs(px - cx)
    if dy < 1 and dx < 1:
        return None

    # оценим pitch: период = N / freq
    if dy > dx:
        period = h / max(dy, 1)
    else:
        period = w / max(dx, 1)
    period = float(np.clip(period, 4.0, min(h, w) / 2.0))

    # Оценим сколько модулей по каждой оси
    rows = int(round(h / period))
    cols = int(round(w / period))
    rows = max(8, min(rows, 144))
    cols = max(8, min(cols, 144))
    return rows, cols, period, period, period


def print_growth_score(roi_gray: np.ndarray) -> float:
    """
    Print Growth — отклонение реальной площади чёрных модулей от эталона 50%.
    Идеал: 50/50 → score = 1.0. Сильный завал краски (больше чёрного) → score падает.

    Допуск: ±0.2 от идеала (у реальных DM 35–65% чёрного — это нормально).
    """
    if roi_gray is None or roi_gray.size == 0:
        return 0.0
    _, bw = cv2.threshold(roi_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    black_ratio = float(np.mean(bw == 0))
    # Идеал — 0.5. Допуск ±0.2 → score ~ 1.0, дальше плавно падает до 0 при ±0.5.
    deviation = abs(black_ratio - 0.5)
    score = 1.0 - min(max(deviation - 0.20, 0.0) / 0.30, 1.0)
    return float(np.clip(score, 0.0, 1.0))


def axial_nonuniformity_score(roi_gray: np.ndarray) -> float:
    """
    Axial Non-Uniformity — мера отклонения проекций модулей по осям.
    Упрощённо: считаем, насколько горизонтальная и вертикальная проекции близки
    к регулярной сетке (через FFT-анализ).
    """
    if roi_gray is None or roi_gray.size == 0:
        return 0.0
    _, bw = cv2.threshold(roi_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    proj_h = np.mean(bw, axis=0)  # 1D по X
    proj_v = np.mean(bw, axis=1)  # 1D по Y

    # нормируем
    proj_h = (proj_h - proj_h.mean()) / (proj_h.std() + 1e-6)
    proj_v = (proj_v - proj_v.mean()) / (proj_v.std() + 1e-6)

    # автокорреляция — у регулярной сетки будут чёткие пики
    def acf(x: np.ndarray) -> np.ndarray:
        x = x - x.mean()
        return np.correlate(x, x, mode="full")[len(x) - 1:]

    a_h = np.abs(acf(proj_h.astype(np.float32)))
    a_v = np.abs(acf(proj_v.astype(np.float32)))
    # нормируем
    a_h = a_h / (a_h[0] + 1e-6)
    a_v = a_v / (a_v[0] + 1e-6)

    # чем «острее» второй пик относительно максимума — тем регулярнее
    def second_peak_sharpness(a: np.ndarray) -> float:
        if len(a) < 8:
            return 0.0
        # пропускаем первый пик (нулевой лаг)
        a2 = a[2:]
        if a2.size == 0:
            return 0.0
        peak = float(np.max(a2))
        return float(np.clip(peak, 0.0, 1.0))

    s_h = second_peak_sharpness(a_h)
    s_v = second_peak_sharpness(a_v)
    return float(np.clip(0.5 * (s_h + s_v), 0.0, 1.0))


def fixed_pattern_damage_score(roi_gray: np.ndarray) -> float:
    """
    Оценка «целостности» тайла: ищем компоненты связности, дырки, разрывы.
    Упрощённо: считаем долю пикселей в маленьких компонентах (шум/разрывы).
    """
    if roi_gray is None or roi_gray.size == 0:
        return 0.0
    _, bw = cv2.threshold(roi_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    inv = cv2.bitwise_not(bw)  # чёрное = 255

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(inv, connectivity=8)
    if num_labels <= 1:
        return 1.0
    total = float(roi_gray.size)
    small = 0
    huge = 0
    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        if area < 20:  # мелкий шум / разрывы
            small += area
        if area > 0.4 * total:
            huge += area
    damage_ratio = (small + 0.5 * huge) / total
    score = 1.0 - min(damage_ratio * 3.0, 1.0)
    return float(np.clip(score, 0.0, 1.0))


def decodability_score(success_streak: int, total_attempts: int, required: int = 3) -> float:
    """
    Decodability: 0 → если ни разу не прочитали,
    плавно растёт до 1.0 при required подряд удачных чтений.
    """
    if total_attempts <= 0:
        return 0.0
    base = min(success_streak / max(required, 1), 1.0)
    # бонус за стабильность — отношение успехов к попыткам
    stability = success_streak / max(total_attempts, 1)
    return float(np.clip(0.7 * base + 0.3 * stability, 0.0, 1.0))


def compute_all(roi_gray: np.ndarray, success_streak: int, total_attempts: int,
                required: int = 3) -> QualityMetrics:
    """Считает все 6 метрик разом."""
    return QualityMetrics(
        decodability=decodability_score(success_streak, total_attempts, required),
        contrast=contrast_score(roi_gray),
        modulation=modulation_score(roi_gray),
        print_growth=print_growth_score(roi_gray),
        axial_nonuniformity=axial_nonuniformity_score(roi_gray),
        fixed_pattern_damage=fixed_pattern_damage_score(roi_gray),
    )
