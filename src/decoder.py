"""
decoder.py — обёртка над pylibdmtx.

Возвращает список найденных в кадре кодов с bbox + данные.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import cv2
import numpy as np

log = logging.getLogger(__name__)


@dataclass
class DMResult:
    data: str                    # декодированный текст
    rect: tuple[int, int, int, int]  # (x, y, w, h) bbox на кадре
    confidence: float            # 0..1 (если поддерживается)


def _try_pylibdmtx():
    try:
        from pylibdmtx.pylibdmtx import decode_from_image, EncodedMessage  # type: ignore
        return decode_from_image, EncodedMessage
    except Exception as e:  # noqa: BLE001
        log.warning("pylibdmtx недоступен: %s", e)
        return None, None


_decode_from_image, _EncodedMessage = _try_pylibdmtx()


def is_available() -> bool:
    return _decode_from_image is not None


def decode_bgr(frame_bgr: np.ndarray,
               roi: Optional[tuple[int, int, int, int]] = None,
               timeout_ms: int = 100) -> list[DMResult]:
    """
    Декодирует DataMatrix в кадре (или ROI).
    Возвращает список DMResult. Пустой = ничего не нашли.
    """
    if _decode_from_image is None or frame_bgr is None:
        return []

    if roi is not None and len(roi) == 4 and any(roi):
        x, y, w, h = roi
        H, W = frame_bgr.shape[:2]
        x = max(0, min(x, W - 1))
        y = max(0, min(y, H - 1))
        w = max(1, min(w, W - x))
        h = max(1, min(h, H - y))
        crop = frame_bgr[y:y + h, x:x + w]
    else:
        crop = frame_bgr
        x = y = 0

    if crop is None or crop.size == 0:
        return []

    # pylibdmtx принимает PIL Image
    from PIL import Image
    img = Image.fromarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB))

    try:
        # pylibdmtx не принимает напрямую timeout; но можно использовать несколько проходов
        msgs = _decode_from_image(img, timeout=timeout_ms)
    except Exception as e:  # noqa: BLE001
        log.debug("decode error: %s", e)
        return []

    results: list[DMResult] = []
    for m in msgs:
        try:
            data = m.data.decode("utf-8", errors="replace") if isinstance(m.data, (bytes, bytearray)) else str(m.data)
        except Exception:
            data = str(m.data)
        # bbox: m.rect = (left, top, width, height)
        l, t, w_, h_ = m.rect
        rect = (int(x + l), int(y + t), int(w_), int(h_))
        # у dmtx нет confidence; ставим 1.0 при успешном декоде
        results.append(DMResult(data=data, rect=rect, confidence=1.0))
    return results


def decode_gray(gray: np.ndarray, timeout_ms: int = 100) -> list[DMResult]:
    """Декодирует одноканальный кадр."""
    if _decode_from_image is None or gray is None:
        return []
    from PIL import Image
    img = Image.fromarray(gray)
    try:
        msgs = _decode_from_image(img, timeout=timeout_ms)
    except Exception:
        return []
    results: list[DMResult] = []
    for m in msgs:
        try:
            data = m.data.decode("utf-8", errors="replace") if isinstance(m.data, (bytes, bytearray)) else str(m.data)
        except Exception:
            data = str(m.data)
        l, t, w_, h_ = m.rect
        results.append(DMResult(data=data, rect=(int(l), int(t), int(w_), int(h_)), confidence=1.0))
    return results
