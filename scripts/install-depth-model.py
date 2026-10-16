#!/usr/bin/env python3
"""Install the Depth Anything V2 *Small* ONNX model used by `v-creator animate`.

Why this source: Hugging Face and GitHub release downloads are blocked in the
Arena sandbox, while plain `git` blobs on github.com are reachable. The file is
taken from a pinned commit of a third-party GitHub repository that stores, as a
normal Git blob, a copy of `depth_anything_v2_vits_dynamic.onnx` from
fabio-sim/Depth-Anything-ONNX v2.0.0 (byte size identical: 99,092,268). The
Small checkpoint is Apache-2.0 (Base/Large are CC-BY-NC and NOT used here).

Only the model is downloaded (sparse, blob-filtered fetch); no code from that
repository is executed. Weights live in gitignored models/; rerun after a fresh
checkout. Exit code 0 means the file is present and its SHA-256 matches.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "models/depth-anything-v2-small"
FILE = "depth_anything_v2_vits_dynamic.onnx"
REPO = "https://github.com/jnulzl/depth_anything_v2_onnx_without_layer_normalization.git"
COMMIT = "4e3eb41616e2ddc4ba08430b8386c3e8c33ef6b1"
SIZE = 99_092_268
SHA256 = "46c4e8eeda3a27f34701831b6a2ec7753d7b38779b215acb5633424703deed8f"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def ready() -> bool:
    model = DEST / FILE
    return model.is_file() and model.stat().st_size == SIZE and sha256(model) == SHA256


def main() -> int:
    if ready():
        print(f"OK   depth model already installed: {DEST / FILE}")
        return 0
    if not shutil.which("git"):
        print("FAIL: git is required to fetch the pinned depth model", file=sys.stderr)
        return 1
    DEST.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "GIT_LFS_SKIP_SMUDGE": "1"}
    with tempfile.TemporaryDirectory(prefix="depth-model-") as tmp:
        def git(*args: str) -> None:
            subprocess.run(["git", "-C", tmp, *args], check=True, env=env,
                           stdout=subprocess.DEVNULL)
        git("init", "-q")
        git("remote", "add", "origin", REPO)
        git("sparse-checkout", "set", "--no-cone", f"weights/{FILE}")
        git("fetch", "-q", "--depth", "1", "--filter=blob:none", "origin", COMMIT)
        git("checkout", "-q", "FETCH_HEAD")
        source = Path(tmp) / "weights" / FILE
        if not source.is_file() or source.stat().st_size != SIZE:
            print(f"FAIL: unexpected download size for {FILE}", file=sys.stderr)
            return 1
        actual = sha256(source)
        if actual != SHA256:
            print(f"FAIL: SHA-256 mismatch for {FILE}: {actual}", file=sys.stderr)
            return 1
        shutil.move(str(source), DEST / FILE)
    (DEST / "install-manifest.json").write_text(json.dumps({
        "model": "Depth Anything V2 Small (ViT-S), dynamic-shape ONNX export",
        "file": FILE, "size": SIZE, "sha256": SHA256,
        "source": f"git {REPO} @ {COMMIT} (weights/{FILE})",
        "upstream_export": "https://github.com/fabio-sim/Depth-Anything-ONNX/releases/tag/v2.0.0 (same byte size)",
        "upstream_model": "https://github.com/DepthAnything/Depth-Anything-V2",
        "weights_license": "Apache-2.0 (Small checkpoint only)",
        "note": "Third-party export; binary identity with the upstream release asset not independently verified (release hash unavailable from this sandbox).",
    }, indent=2) + "\n", encoding="utf-8")
    print(f"OK   depth model installed: {DEST / FILE} ({SIZE / 1e6:.1f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
