#!/usr/bin/env bash
# Report what is actually usable in this checkout. Never downloads model weights.
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ ! -x .venv/bin/python ]]; then
  echo 'FAIL: Python environment missing. Run ./scripts/install.sh' >&2
  exit 1
fi
.venv/bin/python - <<'PY'
from pathlib import Path
import os, shutil, subprocess, sys

missing = []
for name in ("PIL", "yaml", "arabic_reshaper", "bidi", "numpy", "mido", "imageio_ffmpeg", "sherpa_onnx", "onnxruntime", "cv2"):
    try:
        __import__(name)
        print("OK   Python module:", name)
    except ImportError:
        missing.append(name)
if missing:
    sys.exit("FAIL: modules missing: " + ", ".join(missing) + "; rerun ./scripts/install.sh")
from imageio_ffmpeg import get_ffmpeg_exe
ffmpeg = get_ffmpeg_exe()
probe = shutil.which("ffprobe") or (".venv/bin/ffprobe" if Path(".venv/bin/ffprobe").exists() else None)
print("OK   FFmpeg:", ffmpeg)
print("OK   ffprobe:", probe or "MISSING")
if not probe:
    sys.exit("FAIL: ffprobe missing; rerun ./scripts/install.sh")
encoders = subprocess.run([ffmpeg, "-hide_banner", "-encoders"], capture_output=True, text=True, check=True).stdout
if not all(codec in encoders for codec in ("libx264", "aac")):
    sys.exit("FAIL: FFmpeg build needs libx264 and AAC")
print("OK   codecs: libx264 + AAC")
for name in ("NotoSansArabic.ttf", "NotoKufiArabic.ttf"):
    path = Path("assets/fonts") / name
    if not path.is_file():
        sys.exit(f"FAIL: font missing: {path}")
    print("OK   font:", path)
print(f"Disk free: {shutil.disk_usage('.').free // (1024**3)} GiB")
mem = Path("/proc/meminfo")
if mem.exists():
    total = int(mem.read_text().split("MemTotal:")[1].split()[0]) / (1024**2)
    print(f"RAM installed: ~{total:.2f} GiB; Supertonic works on CPU; larger optional TTS models recommend 8+ GiB")
from v_creator.voice_local import model_is_installed
if model_is_installed() and Path("models/supertonic-3/install-manifest.json").is_file():
    print("OK   Local Arabic-capable Supertonic voice: weights installed; generated WAV must be heard for naturalness")
elif os.environ.get("V_CREATOR_SKIP_LOCAL_VOICE") == "1":
    print("WARN Local voice explicitly skipped; narration generation unavailable")
else:
    sys.exit("FAIL: local voice missing; run .venv/bin/python scripts/install-local-voice.py")
from v_creator import depth as depth_mod
if depth_mod.model_is_installed():
    print("OK   Depth Anything V2 Small (ONNX):", depth_mod.MODEL_SHA256[:16] + "...", "ready for v-creator animate")
elif os.environ.get("V_CREATOR_SKIP_DEPTH") == "1":
    print("WARN depth model explicitly skipped; v-creator animate unavailable, render still works")
else:
    sys.exit("FAIL: depth model missing; run .venv/bin/python scripts/install-depth-model.py")
PY
if command -v node >/dev/null 2>&1 && [[ -x node_modules/.bin/hyperframes ]]; then
  echo "OK   Node: $(node --version); HyperFrames package installed"
else
  echo 'WARN Node or HyperFrames missing (motion graphics only); rerun ./scripts/install.sh' >&2
fi
