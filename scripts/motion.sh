#!/usr/bin/env bash
# Use the locally installed Apache-2.0 HyperFrames CLI without cloud/browser downloads.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
[ -x "$ROOT/node_modules/.bin/hyperframes" ] || { echo 'Run ./scripts/install.sh first' >&2; exit 1; }
if [ -d "$ROOT/.venv/bin" ]; then export PATH="$ROOT/.venv/bin:$PATH"; fi
if [[ "$(uname -s)" == Linux ]] && [ -d "$ROOT/node_modules/@sparticuz/chromium" ]; then
  export HYPERFRAMES_BROWSER_PATH="$(node "$ROOT/scripts/browser-path.mjs")"
  export LD_LIBRARY_PATH="$ROOT/.cache/chromium-libs/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
fi
exec "$ROOT/node_modules/.bin/hyperframes" "$@"
