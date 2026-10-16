"""Monocular depth (Depth Anything V2 Small, ONNX on CPU) with an on-disk cache.

The network predicts *relative inverse depth*: larger values are closer to the
camera. We normalise robustly to [0, 1] where 1 = nearest. Maps are cached as
float16 .npy keyed by the image bytes, the model hash and the inference size,
so re-rendering a scene never re-runs the network.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
MODEL_DIR = ROOT / "models/depth-anything-v2-small"
MODEL_FILE = MODEL_DIR / "depth_anything_v2_vits_dynamic.onnx"
MODEL_SIZE = 99_092_268
MODEL_SHA256 = "46c4e8eeda3a27f34701831b6a2ec7753d7b38779b215acb5633424703deed8f"
MODEL_LABEL = "Depth Anything V2 Small (ViT-S) ONNX, Apache-2.0"
# The ViT-S patch size is 14; 518 is the training resolution of the short side.
PATCH = 14
SHORT_SIDE = 518
_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)


def model_is_installed() -> bool:
    """Cheap check (size + install manifest written only after a SHA-256 match)."""
    try:
        manifest = json.loads((MODEL_DIR / "install-manifest.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return (MODEL_FILE.is_file() and MODEL_FILE.stat().st_size == MODEL_SIZE
            and manifest.get("sha256") == MODEL_SHA256)


def inference_size(width: int, height: int, short_side: int = SHORT_SIDE) -> tuple[int, int]:
    """Keep aspect ratio; both sides multiples of the ViT patch size."""
    scale = short_side / min(width, height)
    def snap(v: float) -> int:
        return max(PATCH, int(round(v * scale / PATCH)) * PATCH)
    return snap(width), snap(height)


def normalise(raw: np.ndarray) -> np.ndarray:
    """Percentile stretch to [0, 1] (1 = near); robust to a few extreme pixels."""
    raw = raw.astype(np.float32)
    lo, hi = np.percentile(raw, [1.0, 99.0])
    if not np.isfinite(lo) or not np.isfinite(hi) or hi - lo < 1e-6:
        return np.full(raw.shape, 0.5, dtype=np.float32)
    return np.clip((raw - lo) / (hi - lo), 0.0, 1.0).astype(np.float32)


class DepthEstimator:
    def __init__(self, threads: int = 2) -> None:
        if not model_is_installed():
            raise FileNotFoundError(
                "Depth model missing; run: .venv/bin/python scripts/install-depth-model.py")
        import onnxruntime as ort  # imported lazily: only `animate` needs it

        options = ort.SessionOptions()
        options.intra_op_num_threads = max(1, min(8, threads))
        options.inter_op_num_threads = 1
        options.log_severity_level = 3
        self.session = ort.InferenceSession(str(MODEL_FILE), options,
                                            providers=["CPUExecutionProvider"])
        self.input_name = self.session.get_inputs()[0].name

    def predict(self, image: Image.Image) -> np.ndarray:
        """Return an HxW float32 map in [0, 1] at the model's inference size."""
        rgb = image.convert("RGB")
        size = inference_size(*rgb.size)
        x = np.asarray(rgb.resize(size, Image.Resampling.BICUBIC), dtype=np.float32) / 255.0
        x = ((x - _MEAN) / _STD).transpose(2, 0, 1)[None].astype(np.float32)
        raw = self.session.run(None, {self.input_name: x})[0]
        return normalise(np.squeeze(raw))


def _digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def cached_depth(image_path: Path, cache_dir: Path, *, threads: int = 2,
                 estimator: DepthEstimator | None = None) -> tuple[np.ndarray, Path, bool]:
    """Depth for an image file at inference resolution; returns (map, cache file, cache_hit)."""
    with Image.open(image_path) as probe:
        size = inference_size(*probe.size)
    key = hashlib.sha256(json.dumps({
        "image": _digest(image_path), "model": MODEL_SHA256, "size": size, "norm": "p1-p99",
    }, sort_keys=True).encode()).hexdigest()[:20]
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_dir / f"depth_{image_path.stem}_{key}.npy"
    if path.is_file():
        try:
            return np.load(path).astype(np.float32), path, True
        except (OSError, ValueError):
            path.unlink(missing_ok=True)
    estimator = estimator or DepthEstimator(threads)
    with Image.open(image_path) as source:
        depth = estimator.predict(source)
    np.save(path, depth.astype(np.float16))
    return depth, path, False


def save_depth_preview(depth: np.ndarray, dest: Path, size: tuple[int, int] | None = None) -> None:
    """Greyscale PNG (white = near) for checking a depth map by eye."""
    image = Image.fromarray(np.clip(depth * 255.0, 0, 255).astype(np.uint8), mode="L")
    if size:
        image = image.resize(size, Image.Resampling.BICUBIC)
    dest.parent.mkdir(parents=True, exist_ok=True)
    image.save(dest)
