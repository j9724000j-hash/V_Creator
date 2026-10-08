#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# System installation is explicit; render never installs/downloads anything.
if [[ "${1:-}" == --system ]]; then
  sudo apt-get update
  sudo apt-get install -y python3-venv ffmpeg imagemagick espeak-ng fonts-dejavu-core
  shift
fi
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip install -e '.[test]'
if [[ "${1:-}" == --remotion ]]; then
  npm ci
  echo 'Install Chromium explicitly and set VF_BROWSER=/absolute/path/to/chromium.'
  echo 'Review docs/licensing.md before enabling Remotion.'
fi
.venv/bin/python -m video_factory doctor
