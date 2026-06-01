# Быстрый старт

## 1. Локальный запуск (Windows / Linux / macOS)

```bash
# 1) Создать репозиторий
git init
git add .
git commit -m "Initial commit"
# 2) Создать пустой репо на GitHub, затем:
git remote add origin https://github.com/<you>/datamatrix-quality-checker.git
git branch -M main
git push -u origin main
```

## 2. Сборка .exe

### Вариант A — локально (Windows)

```powershell
scripts\build.bat
```

Результат: `dist\DataMatrixChecker.exe` (≈ 80 МБ, **portable**, без установки).

### Вариант B — GitHub Actions (рекомендуется)

1. Запушьте код в GitHub (см. выше).
2. Откройте вкладку **Actions** — увидите ран «build-windows».
3. Скачайте артефакт `DataMatrixChecker-windows` (см. низ страницы рана).
4. Для автоматического релиза:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```
   Создастся GitHub Release с прикреплённым `.exe`.

## 3. Запуск

Двойной клик по `DataMatrixChecker.exe`. Приложение портабельное, никаких
зависимостей на целевой машине не нужно.

## 4. Подключение камеры

- **Web-камера** — выберите в списке «Камера», нажмите ▶ Start.
- **GoPro (USB webcam)** — включите «GoPro Webcam», камера появится в списке.
- **GoPro (WiFi)** — введите `rtsp://10.5.5.9:8554/live` в поле «URL».
- **Промышленная UVC** — как web-камера.
- **Промышленная GigE / IP** — введите RTSP/HTTP URL.

Подробности: [docs/cameras.md](docs/cameras.md).

## 5. Тестовые изображения

```bash
pip install pylibdmtx Pillow
python scripts/gen_sample.py
```

Создаст 4 тестовых DataMatrix в `samples/`.

## 6. Smoke-test без GUI

```bash
python scripts/test_quality.py samples/dm_clean.png
```

Напечатает метрики и оценку для конкретного изображения.
