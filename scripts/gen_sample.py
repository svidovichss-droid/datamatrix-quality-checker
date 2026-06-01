"""
gen_sample.py — генерирует тестовое изображение DataMatrix и сохраняет в samples/.

Использование:
    python scripts/gen_sample.py
"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    from pylibdmtx.pylibdmtx import encode_dmtx_image  # type: ignore
    from PIL import Image, ImageDraw, ImageFont
except ImportError as e:
    print("Нужны: pip install pylibdmtx Pillow")
    raise SystemExit(1) from e


def main() -> int:
    out = Path("samples")
    out.mkdir(exist_ok=True)

    payloads = [
        ("dm_clean.png",      "PROD-2026-001-ABC123",        "clean"),
        ("dm_dirty.png",      "PROD-2026-002-DEF456",        "dirty"),
        ("dm_lowcontrast.png","PROD-2026-003-GHI789",        "lowcontrast"),
        ("dm_rotated.png",    "PROD-2026-004-JKL012",        "rotated"),
    ]

    for fname, data, mode in payloads:
        encoded = encode_dmtx_image(data.encode("utf-8"), size="SquareAuto")
        # encode_dmtx_image возвращает (PIL.Image, ...) в новых версиях, иначе PIL.Image
        img = encoded[0] if isinstance(encoded, tuple) else encoded
        img = img.convert("1")  # 1-bit
        # приведём к RGB
        rgb = img.convert("RGB")
        # нарисуем белый quiet zone
        canvas = Image.new("RGB", (rgb.width + 60, rgb.height + 60), (255, 255, 255))
        canvas.paste(rgb, (30, 30))

        draw = ImageDraw.Draw(canvas)

        if mode == "dirty":
            # кляксы поверх
            for _ in range(30):
                x = 30 + (hash((data, _)) & 0xFFFF) % max(1, rgb.width - 5)
                y = 30 + (hash((_, data)) & 0xFFFF) % max(1, rgb.height - 5)
                r = 2 + (_ % 4)
                draw.ellipse((x - r, y - r, x + r, y + r), fill=(0, 0, 0))
        elif mode == "lowcontrast":
            canvas = canvas.point(lambda p: int(128 + (p - 128) * 0.4))
        elif mode == "rotated":
            canvas = canvas.rotate(15, fillcolor=(255, 255, 255), expand=True)

        # caption
        try:
            font = ImageFont.truetype("arial.ttf", 18)
        except Exception:
            font = ImageFont.load_default()
        draw.text((10, 5), f"{data}  [{mode}]", fill=(0, 0, 0), font=font)

        path = out / fname
        canvas.save(path)
        print(f"  saved {path}")

    print("Готово. Запустите приложение и откройте эти файлы, чтобы проверить декодер.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
