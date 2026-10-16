#!/usr/bin/env bash
# Local CPU toolchain. Downloads a pinned compact voice model (~145 MB) without cloud credentials.
# Set V_CREATOR_SKIP_LOCAL_VOICE=1 only when intentionally skipping the voice model.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
command -v python3 >/dev/null || { echo 'Python 3.11/3.12 is required' >&2; exit 1; }
python3 - <<'PY'
import sys
if not (sys.version_info[:2] >= (3, 11) and sys.version_info[:2] < (3, 13)):
    raise SystemExit('Python 3.11 or 3.12 is required')
PY
python3 -m venv .venv
.venv/bin/python -m pip install --no-input -r requirements.txt
# imageio-ffmpeg distributes a CPU-ready FFmpeg binary on common platforms.
# HyperFrames uses a CLI binary rather than the Python accessor.
ffmpeg_path="$(.venv/bin/python -c 'import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())')"
if [ ! -e .venv/bin/ffmpeg ] && [ -x "$ffmpeg_path" ]; then
  ln -s "$ffmpeg_path" .venv/bin/ffmpeg
fi
if command -v npm >/dev/null && command -v node >/dev/null; then
  npm ci --no-audit --no-fund
  # ffprobe is used for stream/duration validation and by HyperFrames.
  probe_path="$(node -p "require('@ffprobe-installer/ffprobe').path")"
  if [ ! -e .venv/bin/ffprobe ] && [ -x "$probe_path" ]; then
    ln -s "$probe_path" .venv/bin/ffprobe
  fi
  ./node_modules/.bin/hyperframes telemetry disable >/dev/null 2>&1 || true
  if [[ "${V_CREATOR_SKIP_LOCAL_VOICE:-0}" != "1" ]]; then
    echo 'Installing local Arabic-capable Supertonic voice (OpenRAIL-M; third-party repack)...'
    .venv/bin/python scripts/install-local-voice.py
  else
    echo 'WARN: local Arabic voice installation explicitly skipped.' >&2
  fi
else
  echo 'Node.js 22 + npm unavailable: HyperFrames/ffprobe/voice skipped; install them for full functionality.' >&2
fi
.venv/bin/python -m v_creator doctor
printf '\nReady. Example: .venv/bin/v-creator narrate videos/fantasy-intro/voice-demo.yaml --out output/narration.wav\n'
