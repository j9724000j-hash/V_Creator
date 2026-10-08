#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="$PWD/src${PYTHONPATH:+:$PYTHONPATH}"
python="${VF_PYTHON:-$PWD/.venv/bin/python}"
[[ -x "$python" ]] || python=python3
exec "$python" -m video_factory clean "$@"
