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

# Start Ollama if installed. Prefetching a model requires the server.
# - Set OLLAMA_ENABLE=1 to run the server even if you don't prefetch.
# - Set PREFETCH_OLLAMA_MODEL=1 (default) to pull OLLAMA_MODEL on startup.
if command -v ollama >/dev/null 2>&1; then
  if [[ "${OLLAMA_ENABLE:-0}" == "1" || "${PREFETCH_OLLAMA_MODEL:-1}" == "1" ]]; then
    ollama serve >/tmp/ollama-serve.log 2>&1 &
    # Best-effort readiness wait (avoid failing the container if Ollama is slow to start).
    for _ in $(seq 1 20); do
      if ollama list >/dev/null 2>&1; then
        break
      fi
      sleep 0.25
    done
  fi

  if [[ "${PREFETCH_OLLAMA_MODEL:-1}" == "1" ]]; then
    ollama pull "${OLLAMA_MODEL:-llama3.1:8b}" || true
    echo "[prefetch] Ollama model ready"
  fi
else
  # Keep startup resilient if the image is built without Ollama.
  if [[ "${OLLAMA_ENABLE:-0}" == "1" || "${PREFETCH_OLLAMA_MODEL:-0}" == "1" ]]; then
    echo "[warn] ollama binary not found; skipping Ollama startup"
  fi
fi

exec "$@"
