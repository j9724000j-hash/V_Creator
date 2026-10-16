#!/usr/bin/env bash
# Heavy, opt-in natural Arabic speech models in isolated environments.
# Checkpoints are intentionally NOT bundled and are downloaded by upstream on first use.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
engine="${1:-}"
case "$engine" in
  silma) package='silma-tts==1.0.5' ;;
  chatterbox) package='chatterbox-tts==0.1.7' ;;
  *) echo 'Usage: ./scripts/install-voice.sh silma|chatterbox' >&2; exit 2 ;;
esac
if [[ -r /proc/meminfo ]]; then
  ram_kb="$(awk '/MemTotal:/ {print $2}' /proc/meminfo)"
elif command -v sysctl >/dev/null && sysctl -n hw.memsize >/dev/null 2>&1; then
  ram_kb="$(( $(sysctl -n hw.memsize) / 1024 ))"
else
  ram_kb=0  # unknown; fail closed unless the user explicitly opts into the risk
fi
if (( ram_kb < 8 * 1024 * 1024 )) && [[ "${V_CREATOR_ALLOW_LOW_RAM:-0}" != 1 ]]; then
  echo "AI voice not installed: <8 GiB RAM or memory could not be detected (found $((ram_kb/1024)) MiB)." >&2
  echo 'Use a stronger CPU/GPU machine or supply a real voice WAV. Opt in to the risk with V_CREATOR_ALLOW_LOW_RAM=1.' >&2
  exit 1
fi
if (( $(df -Pk "$ROOT" | awk 'NR==2 {print $4}') < 10 * 1024 * 1024 )); then
  echo 'AI voice not installed: allow at least 10GB of free disk for dependencies and checkpoint.' >&2
  exit 1
fi
venv="$ROOT/.venv-voice-$engine"
python3 -m venv "$venv"
"$venv/bin/python" -m pip install --no-input "$package"
echo "Installed $package (Python code only); model weights need a separate download from Hugging Face."
echo "Do not clone a person's voice without consent. Use: $venv/bin/python scripts/voice.py $engine --help"
