"""
camera.py — абстракция камеры.

Поддерживает:
- Локальные UVC-камеры (web, GoPro в режиме webcam, промышленные USB3 Vision)
  → OpenCV VideoCapture(index)
- IP-камеры по RTSP / HTTP-MJPEG (GoPro WiFi-стрим, IP-камеры, Android IP Webcam)
  → OpenCV VideoCapture(url)

Пример URL для GoPro (через мобильное приложение GoPro Quik или OpenGoPro):
  rtsp://10.5.5.9:8554/live

Пример URL для Android IP Webcam:
  http://192.168.1.10:8080/video
"""
from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from typing import Iterator, Optional

import cv2
import numpy as np

log = logging.getLogger(__name__)


@dataclass
class CameraInfo:
    index: int
    name: str
    backend: str


def list_local_cameras(max_index: int = 8) -> list[CameraInfo]:
    """Пробует открыть VideoCapture(0..max_index) и возвращает те, что дали кадр."""
    found: list[CameraInfo] = []
    # Пробуем разные backend'ы (DirectShow быстрее всего на Windows)
    backends = [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY] if _is_windows() else [cv2.CAP_ANY]
    seen: set[int] = set()
    for backend in backends:
        for i in range(max_index):
            if i in seen:
                continue
            try:
                cap = cv2.VideoCapture(i, backend)
                if cap.isOpened():
                    ok, _ = cap.read()
                    if ok:
                        seen.add(i)
                        name = _camera_name(cap, i)
                        found.append(CameraInfo(index=i, name=name, backend=_backend_name(backend)))
                cap.release()
            except Exception:
                pass
        if found:
            break
    return found


def _is_windows() -> bool:
    import sys
    return sys.platform.startswith("win")


def _backend_name(b: int) -> str:
    return {
        cv2.CAP_DSHOW: "DirectShow",
        cv2.CAP_MSMF: "MediaFoundation",
        cv2.CAP_ANY: "Auto",
        cv2.CAP_V4L2: "V4L2",
        cv2.CAP_GSTREAMER: "GStreamer",
    }.get(b, f"backend-{b}")


def _camera_name(cap: cv2.VideoCapture, idx: int) -> str:
    try:
        name = cap.getBackendName()
        return f"[{idx}] {name}"
    except Exception:
        return f"[{idx}] Camera"


class Camera:
    """Потоковый захват кадров. UI читает кадры через read(); не блокирует GUI."""

    def __init__(self):
        self._cap: Optional[cv2.VideoCapture] = None
        self._lock = threading.Lock()
        self._frame: Optional[np.ndarray] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._source: str | int = 0
        self._resolution: tuple[int, int] = (1280, 720)
        self._fps_target: int = 15
        self._opened = False
        self._error: Optional[str] = None

    # ---- public ----

    @property
    def is_opened(self) -> bool:
        return self._opened

    @property
    def last_error(self) -> Optional[str]:
        return self._error

    def open(self, source: str | int, resolution: tuple[int, int] = (1280, 720),
             fps_target: int = 15) -> bool:
        """Открыть источник (int index или str URL) и запустить фоновый поток чтения."""
        self.close()
        self._source = source
        self._resolution = resolution
        self._fps_target = fps_target
        self._error = None

        # Небольшая задержка нужна на Windows — DirectShow иногда требует warm-up
        cap = self._open_capture(source)
        if cap is None or not cap.isOpened():
            self._error = f"Не удалось открыть источник: {source}"
            log.error(self._error)
            return False

        self._apply_props(cap)
        self._cap = cap
        self._opened = True
        self._running = True
        self._thread = threading.Thread(target=self._reader, daemon=True)
        self._thread.start()
        return True

    def close(self) -> None:
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None
        with self._lock:
            if self._cap is not None:
                try:
                    self._cap.release()
                except Exception:
                    pass
                self._cap = None
        self._opened = False
        self._frame = None

    def read(self) -> Optional[np.ndarray]:
        """Возвращает последний кадр (None если поток не успел)."""
        with self._lock:
            if self._frame is None:
                return None
            return self._frame.copy()

    # ---- internal ----

    def _open_capture(self, source: str | int) -> Optional[cv2.VideoCapture]:
        if isinstance(source, int):
            if _is_windows():
                # DirectShow — самый быстрый backend на Windows
                cap = cv2.VideoCapture(source, cv2.CAP_DSHOW)
                if cap.isOpened():
                    return cap
                cap.release()
            return cv2.VideoCapture(source)
        # URL
        return cv2.VideoCapture(source)

    def _apply_props(self, cap: cv2.VideoCapture) -> None:
        w, h = self._resolution
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
        cap.set(cv2.CAP_PROP_FPS, self._fps_target)
        # Уменьшаем буфер, чтобы не было лагов на конвейере
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    def _reader(self) -> None:
        cap = self._cap
        if cap is None:
            return
        while self._running:
            ok, frame = cap.read()
            if not ok or frame is None:
                # для IP-камер попробуем переподключиться
                if isinstance(self._source, str):
                    time.sleep(0.5)
                    try:
                        cap.release()
                    except Exception:
                        pass
                    cap = self._open_capture(self._source)
                    if cap is not None and cap.isOpened():
                        self._apply_props(cap)
                        self._cap = cap
                    else:
                        time.sleep(1.0)
                else:
                    time.sleep(0.05)
                continue
            with self._lock:
                self._frame = frame
        if cap is not None:
            try:
                cap.release()
            except Exception:
                pass
