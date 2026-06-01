"""
config.py — загрузка/сохранение пользовательских настроек.

Конфиг живёт в файле `config.json` рядом с .exe (или в CWD при запуске из исходников).
"""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


def _config_path() -> Path:
    """Путь к config.json — рядом с exe или в CWD."""
    if getattr(os.sys, "frozen", False):  # PyInstaller bundle
        base = Path(os.sys.executable).parent
    else:
        base = Path.cwd()
    return base / "config.json"


@dataclass
class AppConfig:
    # Camera
    camera_index: int = 0
    camera_url: str = ""        # для RTSP/HTTP (GoPro WiFi, IP-камеры)
    resolution: list[int] = field(default_factory=lambda: [1280, 720])
    fps_target: int = 15

    # Conveyor / grading
    conveyor_mode: bool = True
    min_grade: str = "C"         # A/B/C/D/F — ниже = отбраковка
    trigger_cooldown_ms: int = 500
    stable_reads_required: int = 3  # подряд удачных чтений для подтверждения

    # Logging
    log_csv: str = "logs/results.csv"
    reject_dir: str = "logs/rejects"
    save_screenshots: bool = True

    # Quality grader weights (sum should be 1.0)
    weights: dict[str, float] = field(default_factory=lambda: {
        "decodability": 0.30,
        "contrast": 0.20,
        "modulation": 0.15,
        "print_growth": 0.15,
        "axial_nonuniformity": 0.10,
        "fixed_pattern_damage": 0.10,
    })

    # ROI (region of interest): x, y, w, h. 0 = full frame
    roi: list[int] = field(default_factory=lambda: [0, 0, 0, 0])

    # ---- I/O ----

    def save(self) -> None:
        try:
            p = _config_path()
            p.parent.mkdir(parents=True, exist_ok=True)
            with open(p, "w", encoding="utf-8") as f:
                json.dump(asdict(self), f, indent=2, ensure_ascii=False)
        except OSError:
            pass  # не критично

    @classmethod
    def load(cls) -> "AppConfig":
        p = _config_path()
        if not p.exists():
            cfg = cls()
            cfg.save()
            return cfg
        try:
            with open(p, "r", encoding="utf-8") as f:
                data: dict[str, Any] = json.load(f)
            # filter unknown keys
            valid_keys = {f for f in cls.__dataclass_fields__}
            data = {k: v for k, v in data.items() if k in valid_keys}
            # recurse into dicts with defaults
            cfg = cls()
            for k, v in data.items():
                if k == "weights" and isinstance(v, dict):
                    cfg.weights.update(v)
                else:
                    setattr(cfg, k, v)
            return cfg
        except (OSError, json.JSONDecodeError, TypeError):
            return cls()
