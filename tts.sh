#!/usr/bin/env bash
# tts.sh — сырой Kyutai TTS (французский/английский текст напрямую, без транскрипции)
# Использование:
#   echo "Bonjour!" | ./tts.sh - out.wav
#   ./tts.sh text.txt out.wav --voice cml-tts/fr/10087_11650_000028-0002_enhanced.wav
set -euo pipefail
cd "$(dirname "$0")"

TTS_VENV="${TTS_VENV:-$HOME/.venvs/kyutai-tts}"
if [[ ! -x "$TTS_VENV/bin/python" ]]; then
    TTS_VENV="$PWD/.venv"
fi
PY="$TTS_VENV/bin/python"
export HF_HOME="${HF_HOME:-$HOME/.cache/hf}"

exec "$PY" dsm/scripts/tts_pytorch.py "$@"
