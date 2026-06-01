# DataMatrix Quality Checker

Лёгкое **кросс-платформенное** Windows-приложение (собирается в **один `.exe`**) для
**оценки качества печати DataMatrix** на конвейере в реальном времени.

> Сканер + грейдер по упрощённой модели **ISO/IEC 15415 / AIM DPM-1-2006**:
> оценка **A–F** + числовой score 0–100, с цветовой индикацией.

---

## 🚀 Что делает

- Захват видео с **любой UVC-камеры**: USB-вебка, GoPro (режим вебкамеры),
  промышленные USB3-Vision камеры (Basler, IDS, FLIR, The Imaging Source и т.п.).
- Захват с **IP-камер** по **RTSP / HTTP-MJPEG** (GoPro WiFi-стрим, промышленные
  GigE-камеры с RTSP).
- Декодирование **DataMatrix (ECC200)** в реальном времени.
- Расчёт параметров качества:
  - **Contrast** (контраст печати)
  - **Modulation** (модуляция сигнала)
  - **Print Growth** (завал краски / уход точек)
  - **Axial Non-Uniformity** (геометрические искажения)
  - **Fixed Pattern Damage** (повреждения тайла)
  - **Decodability / Readability** (стабильность чтения)
- Итоговый **Grade A–F** + числовой 0–100.
- Лог в CSV + скриншот каждого отбракованного кода.
- Режим конвейера: автоматический триггер по появлению кода в кадре.

---

## 🖥️ Поддерживаемые камеры

| Тип | Как подключить | Примечание |
|---|---|---|
| **Web-камера** | выбрать индекс 0/1/… | Любая UVC-совместимая |
| **GoPro** | USB (режим Webcam) **или** WiFi-стрим (RTSP) | См. [docs/cameras.md](docs/cameras.md) |
| **Промышленная USB3 Vision** | установить драйвер производителя | OpenCV видит её как обычную UVC |
| **Промышленная GigE Vision** | RTSP/HTTP стрим с контроллера камеры | URL вида `rtsp://…` |
| **IP-камера / смартфон** | приложение типа _IP Webcam_ (Android) | URL `http://…/video` |

---

## 📦 Скачать готовый `.exe`

Перейдите во вкладку [**Releases**](../../releases) — там лежит собранный
`DataMatrixChecker.exe` (≈ 80 МБ, **portable**, без установки).

> Если релизов нет — соберите сами: см. раздел [Сборка](#сборка).

---

## 🏃 Запуск из исходников

```powershell
git clone https://github.com/<your-username>/datamatrix-quality-checker.git
cd datamatrix-quality-checker
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python -m src.main
```

Требуется **Python 3.10+** (тестировалось на 3.11, 3.12, 3.13) и ОС Windows 10/11
64-bit. На Linux/macOS тоже работает, но сборка `.exe` только под Windows.

---

## 🔨 Сборка `.exe` локально

```powershell
.\scripts\build.bat
```

Готовый файл: `dist\DataMatrixChecker.exe`.

### Самосборка на GitHub Actions

Каждый push в `main` собирает `.exe` воркфлоу
[`.github/workflows/build.yml`](.github/workflows/build.yml).
Артефакт `DataMatrixChecker-windows` скачивается из Actions → выбранный ран → Artifacts.

Чтобы релиз привязался к тегу:

```bash
git tag v1.0.0
git push origin v1.0.0
```

Запустится воркфлоу [`.github/workflows/release.yml`](.github/workflows/release.yml),
соберёт `.exe` и прикрепит к GitHub Release.

---

## 🎯 Использование на конвейере

1. Подключите камеру, выберите её в выпадающем списке **«Камера»**.
2. Нажмите **▶ Start** — начнётся непрерывный захват.
3. Когда DataMatrix попадёт в кадр, появится overlay с расшифровкой и оценкой:

   | Цвет рамки | Grade | Значение |
   |---|---|---|
   | 🟢 Зелёный | **A** (90–100) | Отлично, печать стабильна |
   | 🔵 Синий | **B** (75–89)  | Хорошо, в допуске |
   | 🟡 Жёлтый | **C** (60–74)  | Граница, рекомендуется проверка |
   | 🟠 Оранжевый | **D** (40–59) | Плохо, отбраковка |
   | 🔴 Красный | **F** (0–39)   | Не читается / брак |

4. Срабатывает «звуковой сигнал» + запись в `logs/results.csv` (настраивается).
5. Включите **Auto-screenshot on reject** — каждый «F» сохранит кадр в `logs/rejects/`.

---

## ⚙️ Настройки

В GUI → **Settings** (или `config.json` в каталоге рядом с `.exe`):

```json
{
  "camera_index": 0,
  "camera_url": "",
  "resolution": [1280, 720],
  "fps_target": 15,
  "conveyor_mode": true,
  "min_grade": "C",
  "save_screenshots": true,
  "log_csv": "logs/results.csv",
  "reject_dir": "logs/rejects",
  "roi": [0, 0, 0, 0],
  "trigger_cooldown_ms": 500
}
```

---

## 🧠 Модель оценки (упрощённая ISO/IEC 15415)

Итоговый **score ∈ [0, 100]** считается как взвешенная сумма:

| Параметр | Вес | Источник |
|---|---|---|
| **Decodability** (успешные чтения подряд) | 30% | счётчик стабильных декодов |
| **Contrast** (Δ между тёмным и светлым) | 20% | OpenCV minMaxLoc на ROI |
| **Modulation** (резкость края) | 15% | Laplacian variance на ROI |
| **Print Growth** (отклонение площади модуля) | 15% | сравнение с теоретическим тайлом |
| **Axial Non-Uniformity** | 10% | на основе bounding box модулей |
| **Fixed Pattern Damage** | 10% | % повреждённых ячеек тайла |

Grade по score:

| Score | Grade |
|---|---|
| 90–100 | A |
| 75–89  | B |
| 60–74  | C |
| 40–59  | D |
| 0–39   | F |

> Это **скрининговый** грейдер для конвейера, **не** замена сертифицированным
> верификаторам (Cognex, Microscan, Omron). Точность достаточна для отсева явного
> брака и мониторинга тренда качества печати.

---

## 🗂️ Структура проекта

```
datamatrix-quality-checker/
├── .github/workflows/        # CI / Release workflows
├── assets/                    # иконка, звуки
├── docs/                      # документация
├── samples/                   # тестовые изображения
├── scripts/                   # build.bat / build.sh
├── src/
│   ├── main.py                # точка входа
│   ├── app.py                 # главное окно
│   ├── camera.py              # захват видео
│   ├── decoder.py             # DataMatrix декодер
│   ├── quality.py             # расчёт параметров качества
│   ├── grader.py              # итоговый score + grade
│   ├── logger.py              # CSV-лог
│   └── config.py              # конфиг
├── requirements.txt
├── pyproject.toml
├── build.spec                 # PyInstaller spec
└── README.md
```

---

## 📝 Лицензия

MIT — делайте что хотите, только упомяните авторство.

## 🤝 Контрибьютинг

PR приветствуются. Особенно: новые типы камер, новые метрики качества, ML-классификатор
грейда, локализация GUI.
