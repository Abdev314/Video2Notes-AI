#!/usr/bin/env bash
set -euo pipefail

cd /app

# Persist caches in /app/.cache (can be mounted as a volume in production).
export XDG_CACHE_HOME="${XDG_CACHE_HOME:-/app/.cache}"
export HF_HOME="${HF_HOME:-/app/.cache/huggingface}"

# Prefetch Whisper model at container start (so a fresh host "pulls the model").
# This avoids long first-request latency in production.
if [[ "${PREFETCH_WHISPER_MODEL:-1}" == "1" ]]; then
  python - <<'PY'
import os
from pathlib import Path

model_size = os.environ.get("WHISPER_MODEL_SIZE", "base")
device = os.environ.get("WHISPER_DEVICE", "cpu")
compute_type = os.environ.get("WHISPER_COMPUTE_TYPE", "int8")

Path(os.environ.get("XDG_CACHE_HOME", "/app/.cache")).mkdir(parents=True, exist_ok=True)

try:
    from faster_whisper import WhisperModel
except Exception as e:
    raise SystemExit(f"faster-whisper import failed: {e}")

print(f"[prefetch] faster-whisper model={model_size} device={device} compute_type={compute_type}")
# Instantiating the model triggers download into the cache if missing.
WhisperModel(model_size, device=device, compute_type=compute_type)
print("[prefetch] done")
PY
fi

exec "$@"

