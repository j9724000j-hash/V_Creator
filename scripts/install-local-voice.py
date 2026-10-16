#!/usr/bin/env python3
"""Install a small Arabic-capable neural voice from pinned npm packages.

This is a third-party repack of Supertone's Supertonic 3 model converted for
sherpa-onnx. The original checkpoint is hosted on Hugging Face, which is not
reachable from this sandbox. The packages contain inert base64 data; we NEVER
execute their JavaScript or run npm install/postinstall scripts.

Model files remain in gitignored models/; run again after a fresh checkout.
"""

from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "models/supertonic-3"
NAME = "@3sln/donki-lle-voice-multi"
VERSION = "0.1.1"
PACKAGES = {
    NAME: "pe1OCsPhCti+EePT8G6L/jEqTuQV8uF7d0hOlyYHVGF3WSBbR+P7ffF3cNDEP/arF2OWlmbRFvbNAUmUGtAJBw==",
    NAME + "-2": "bVgNjfBfSGHl45+OTYNY9eI4qWQOa1PKlnCCWWGLiK6+w8BlhRqZI62am01bQ4F4tQkPI7AZsJXilUer1ZZR6A==",
    NAME + "-3": "nwNCbKbkSovvloXo7n649d4IbDdl76RpdC4om6PFBKKK6VtEU5w0sMSOazjmUcBQsT8QcXlJ6oyO1s//NqnvRA==",
}
FILES = {
    "duration_predictor.onnx", "text_encoder.onnx", "vector_estimator.onnx",
    "vocoder.onnx", "tts.json", "unicode_indexer.bin", "voice.bin",
}
PART_RE = re.compile(r"^(@3sln/donki-lle-voice-multi(?:-[23])?)@0\.1\.1/c/(\d{3})\.js$")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def ready() -> bool:
    try:
        manifest = json.loads((DEST / "install-manifest.json").read_text())
        if manifest["source"] != "npm/3sln/donki-lle-voice-multi@0.1.1":
            return False
        return all((DEST / f).is_file() and sha256(DEST / f) == manifest["sha256"][f]
                   for f in FILES)
    except (OSError, KeyError, ValueError, TypeError):
        return False


def read_js_as_json(tar: tarfile.TarFile, name: str):
    member = tar.getmember(name)
    if not member.isfile() or member.size > 17_000_000:
        raise ValueError(f"Invalid npm member: {name}")
    with tar.extractfile(member) as stream:
        text = stream.read().decode("ascii").strip()
    marker = "export default "
    pos = text.find(marker)
    if pos < 0 or not text.endswith(";") or any(
        line.strip() and not line.lstrip().startswith("//")
        for line in text[:pos].splitlines()
    ):
        raise ValueError(f"Unsupported package data format: {name}")
    return json.loads(text[pos + len(marker):-1])


def install() -> None:
    if ready():
        print(f"READY: verified local Supertonic 3 voice: {DEST}")
        return
    if not shutil.which("npm"):
        raise RuntimeError("npm is needed to fetch the pinned model packages from registry.npmjs.org")
    DEST.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="voice-download-", dir=DEST.parent) as scratch:
        temp = Path(scratch)
        tars = {}
        try:
            for package, integrity in PACKAGES.items():
                spec = f"{package}@{VERSION}"
                packed = subprocess.run(["npm", "pack", spec, "--ignore-scripts", "--pack-destination", str(temp), "--silent"],
                                        capture_output=True, text=True, check=True)
                archive = temp / packed.stdout.strip().splitlines()[-1]
                actual = base64.b64encode(hashlib.sha512(archive.read_bytes()).digest()).decode("ascii")
                if actual != integrity:
                    raise ValueError(f"Unexpected npm package SHA512: {spec}")
                tars[package] = tarfile.open(archive, "r:gz")
            metadata = read_js_as_json(tars[NAME], "package/voice.js")
            if (metadata["engine"] != "supertonic" or metadata["id"] != "multi"
                    or "ar" not in metadata["langs"] or set(metadata["files"]) != FILES
                    or metadata["bytes"] != 145295768):
                raise ValueError("Unexpected Supertonic voice manifest")
            staging = temp / "model"
            staging.mkdir()
            digests = {}
            for filename, item in metadata["files"].items():
                total = 0
                digest = hashlib.sha256()
                with (staging / filename).open("wb") as output:
                    for part in item["parts"]:
                        match = PART_RE.fullmatch(part)
                        if not match or match[1] not in tars:
                            raise ValueError(f"Unexpected voice model chunk: {part}")
                        payload = read_js_as_json(tars[match[1]], f"package/c/{match[2]}.js")
                        block = base64.b64decode(payload, validate=True)
                        output.write(block)
                        digest.update(block)
                        total += len(block)
                if total != item["size"]:
                    raise ValueError(f"Wrong size for {filename}: {total}")
                digests[filename] = digest.hexdigest()
                print(f"  {filename}: {total:,} bytes (verified)")
            info = {
                "source": "npm/3sln/donki-lle-voice-multi@0.1.1",
                "original_model": "https://huggingface.co/Supertone/supertonic-3",
                "runtime": "https://github.com/k2-fsa/sherpa-onnx",
                "license_package_code": "MIT (third-party package declaration)",
                "license_runtime": "Apache-2.0 (sherpa-onnx)",
                "license_weights": "OpenRAIL-M; see official model license and attribution requirements",
                "warning": "Third-party Sherpa conversion. Npm integrity checked; binary equivalence with official weights not independently verified.",
                "package_integrities": {f"{k}@{VERSION}": f"sha512-{v}" for k, v in PACKAGES.items()},
                "sha256": digests,
            }
            (staging / "install-manifest.json").write_text(json.dumps(info, indent=2) + "\n")
            if DEST.exists():
                shutil.rmtree(DEST)
            shutil.move(staging, DEST)
        finally:
            for tar in tars.values():
                tar.close()
    if not ready():
        raise RuntimeError("Local voice model verification failed after installation")
    print(f"READY: Arabic-capable CPU voice in {DEST}. Run scripts/local-voice.py --help")


if __name__ == "__main__":
    try:
        install()
    except (ValueError, KeyError, OSError, subprocess.CalledProcessError, RuntimeError) as exc:
        print(f"Local voice installation failed: {exc}", file=sys.stderr)
        sys.exit(2)
