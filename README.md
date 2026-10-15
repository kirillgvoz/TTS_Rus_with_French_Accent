# TTS_Rus_with_French_Accent — русский с французским акцентом (Kyutai TTS)

Озвучка русского текста голосом, говорящим по-французски: русская фраза
транскрибируется в «французскую орфографию» и подаётся в мультиязычную
модель **Kyutai TTS 1.6B** (en/fr), которая читает её французскими
звуками → получается русская речь с французским акцентом.

```
русский текст ─→ [epitran: G2P → IPA] ─→ [IPA → франц. орфография] ─→ [Kyutai TTS] ─→ [EQ] ─→ wav
                   весь язык                                  ru2fr.py                say_ru.sh
```

Пример: `example.wav` (raw-генерация дефолтным голосом).

## Установка

Нужны: Python 3.12, [uv](https://docs.astral.sh/uv/), `ffmpeg`, GPU с CUDA
(или терпимое терпение — на CPU тоже работает).

```bash
# 1. глобальное окружение с тяжёлыми зависимостями (~8 GB: torch+moshi+...)
uv venv --python 3.12 ~/.venvs/kyutai-tts
uv pip install --python ~/.venvs/kyutai-tts/bin/python -r requirements.txt

# 2. официальные скрипты Kyutai (инференс TTS)
git clone --depth 1 https://github.com/kyutai-labs/delayed-streams-modeling.git dsm

# 3. (для разработки) локальный лёгкий venv с pip
uv venv --seed .venv
.venv/bin/pip install -r requirements.txt   # по желанию: полный стек и локально
```

Веса модели (~4 GB) скачиваются автоматически при первом запуске в
`~/.cache/hf` — в проект не попадают.

Скрипты сами находят окружение: сначала `~/.venvs/kyutai-tts`
(переопределяется `TTS_VENV=...`), затем `.venv`.

## Быстрый старт

```bash
# базовый вызов (raw-звук, без обработки)
./say_ru.sh "Здравствуйте, друг!" out.wav

# с мягкой обработкой (убирает rumble, смягчает верх)
./say_ru.sh "Здравствуйте, друг!" out.wav --soft

# ускорение речи x1.25 (высота голоса не меняется)
TEMPO=1.25 ./say_ru.sh "Привет всем!" out.wav --soft

# другой голос
VOICE=cml-tts/fr/1406_1028_000009-0003_enhanced.wav ./say_ru.sh "Привет!" out.wav
```

## Скрипты

### `say_ru.sh "русский текст" out.wav [--soft]`

Полный пайплайн: транскрипция → TTS → опциональная обработка.

| Переменная | По умолчанию | Назначение |
|---|---|---|
| `TEMPO` | `1.0` | скорость речи (atempo, без смены тона) |
| `VOICE` | `cml-tts/fr/10087_..._enhanced.wav` | эмбеддинг голоса в репо `kyutai/tts-voices` |
| `TTS_VENV` | `~/.venvs/kyutai-tts` | python-окружение с зависимостями |
| `HF_HOME` | `~/.cache/hf` | кэш весов моделей |

### `ru2fr.py` — транслитератор русский → французская запись

```bash
~/.venvs/kyutai-tts/bin/python ru2fr.py "Привет! Меня зовут Алиса."
# priviét ! miénia zovout alisa.

echo "Любой текст" | .../bin/python ru2fr.py -
.../bin/python ru2fr.py --phon другой   # другой → /druk/ → drouque
```

Как работает (покрывает весь язык, без словаря):

1. **epitran** (`rus-Cyrl`) — rule-based G2P: аканье, оглушения на конце,
   твёрдость/мягкость (`друг → /druk/`, `здравствуйте → /zdrafstvujtʲe/`)
2. **IPA → французская орфография** (правила `MAP` в `ru2fr.py`):
   `ʂ→ch`, `ou=у`, `é/è=е`, `ʲ→i`-iotация, финальный `/k→que` (→ `drouque`),
   `j→ï` после гласной (`май → maï`)
3. **анти-liaison**: слово на `s` после гласной → `ç` (лечит «зпазибо»/«звидания»)
4. французская типографика: пробел перед `! ? : ;`

Если слово коверкается — добавь/поправь правило в `MAP` или проверь
разбор: `ru2fr.py --phon слово`.

### `tts.sh` — сырой Kyutai (без транскрипции)

Для французского/английского текста напрямую:

```bash
echo "Bonjour!" | ./tts.sh - out.wav
./tts.sh text.txt out.wav --voice cml-tts/fr/10087_11650_000028-0002_enhanced.wav
# список голосов:
~/.venvs/kyutai-tts/bin/python -c "from huggingface_hub import list_repo_files; [print(f) for f in list_repo_files('kyutai/tts-voices') if f.endswith('.wav')]"
```

## Обработка звука (`--soft`)

Цепочка: `highpass 85 Hz → treble −2dB @3.5k (wide Q) → lowpass 6.5k → loudnorm (−16 LUFS)`.

**Чего здесь сознательно нет** (проверено на слух и спектрально):

- **pitch-shift (rubberband)** — артефакты, портит голос → отказались от смены тона
- **bass-boost** — резонанс-гул на 146 Hz
- **treble с дефолтным width** — свист на 3328 Hz; лечится `width_type=q:width=1.4`
- темп делает `atempo` (WSOLA) — качество чистое

## Структура

| Путь | В git? | Назначение |
|---|---|---|
| `say_ru.sh`, `tts.sh`, `ru2fr.py` | ✓ | весь пайплайн |
| `requirements.txt`, `LICENSE`, `.gitignore` | ✓ | установка и лицензия |
| `dsm/` | нет (clone при установке) | официальные скрипты Kyutai |
| `.venv/` | нет | лёгкий dev-venv (pip) |
| `~/.venvs/kyutai-tts/` | — | глобальный стек: torch, moshi, epitran (~8 GB) |
| `~/.cache/hf/` | — | веса моделей (~4 GB) |

## Лицензии

| Компонент | Лицензия |
|---|---|
| **Код проекта** | **MIT** (см. `LICENSE`) |
| **Веса Kyutai TTS** (`kyutai/tts-1.6b-en_fr`) | **CC-BY 4.0** — указывать авторство Kyutai |
| Голоса `cml-tts/fr` (дефолтный) | CC-BY 4.0 |
| Голоса `vctk`, `alba-mackenna` | CC-BY 4.0 |
| Голоса `voice-donations` | CC0 |
| Голоса `expresso`, `ears` | **CC-BY-NC 4.0 — только некоммерция!** |
| Скрипты `dsm/` (Kyutai) | MIT (Python) / Apache-2.0 (Rust) |
| epitran | MIT-Modern-Variant |
| moshi | MIT |
| torch | BSD-3-Clause |

⚠️ Дефолтный голос `cml-tts/fr/10087...` — CC-BY 4.0 (можно и коммерчески
с указанием авторства). Используешь `expresso/*` или `ears/*` — это
**некоммерческие** лицензии.

## Скорость

Генерация быстрее реального времени на RTX 3060: ~5-7 секунд моделирования
на 5-9 секунд аудио.
