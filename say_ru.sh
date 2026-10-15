#!/usr/bin/env bash
# say_ru.sh — русский текст → речь «русский с французским акцентом» (Kyutai TTS)
#
# Использование:
#   ./say_ru.sh "Здравствуйте, друг! Спасибо большое." out.wav
#   ./say_ru.sh "Привет всем!" out.wav --soft          # + мягкая обработка (без pitch-shift)
#   TEMPO=1.25 ./say_ru.sh "..." out.wav --soft         # + ускорение речи (высота та же)
#   VOICE=cml-tts/fr/1406_1028_000009-0003_enhanced.wav ./say_ru.sh "..." out.wav
set -euo pipefail
cd "$(dirname "$0")"

TEXT="${1:?текст не указан}"
OUT="${2:?укажите выходной wav}"
SOFT="${3:-}"
VOICE="${VOICE:-cml-tts/fr/10087_11650_000028-0002_enhanced.wav}"
TEMPO="${TEMPO:-1.0}"

# Python: сначала глобальное окружение (с тяжёлыми зависимостями), иначе локальное
TTS_VENV="${TTS_VENV:-$HOME/.venvs/kyutai-tts}"
if [[ ! -x "$TTS_VENV/bin/python" ]]; then
    TTS_VENV="$PWD/.venv"
fi
PY="$TTS_VENV/bin/python"
[[ -x "$PY" ]] || { echo "не найдено python-окружение (TTS_VENV или .venv)"; exit 1; }

# HF-кэш моделей: глобальный (~/.cache/hf), можно переопределить HF_HOME
export HF_HOME="${HF_HOME:-$HOME/.cache/hf}"

TMP=$(mktemp -d /tmp/opencode/sayru.XXXXXX)
trap 'rm -rf "$TMP"' EXIT

# 1. русский → французская транскрипция
printf '%s' "$TEXT" | "$PY" ru2fr.py - > "$TMP/fr.txt"
echo "транскрипция: $(cat "$TMP/fr.txt")"

# 2. TTS (Kyutai)
"$PY" dsm/scripts/tts_pytorch.py \
    "$TMP/fr.txt" "$TMP/raw.wav" --voice "$VOICE" 2>&1 | grep -E "Total|error|Error" || true

# 3. опциональная обработка: мягкость (только EQ, без pitch-shift) и/или темп
FILTERS=""
if [[ "$SOFT" == "--soft" ]]; then
    FILTERS="highpass=f=85:poles=2,treble=f=3500:g=-2:width_type=q:width=1.4,lowpass=f=6500:poles=2,loudnorm=I=-16:TP=-1.5:LRA=11,"
fi
if [[ "$TEMPO" != "1.0" && "$TEMPO" != "1" ]]; then
    FILTERS="${FILTERS}atempo=${TEMPO},"
fi
FILTERS="${FILTERS%,}"
if [[ -n "$FILTERS" ]]; then
    ffmpeg -y -hide_banner -loglevel error -i "$TMP/raw.wav" -af "$FILTERS" -ar 24000 "$OUT"
else
    cp "$TMP/raw.wav" "$OUT"
fi
echo "готово: $OUT"
