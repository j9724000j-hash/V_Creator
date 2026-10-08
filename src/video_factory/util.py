from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

class ProductionError(RuntimeError):
    pass

def safe_path(root: Path, name: str) -> Path:
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ProductionError(f"Path escapes project: {name}")
    return path

def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60] or "project"

def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:20]

def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def write_json(path: Path, value: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding='utf-8')
    temp.replace(path)

def binary(name: str) -> str | None:
    override = os.getenv('VF_' + name.upper().replace('-', '_'))
    return shutil.which(override or name)

class Runner:
    def __init__(self, log: Path | None = None):
        self.log = log

    def run(self, args: list[str], *, cwd: Path | None = None, timeout: int = 1800) -> str:
        args = [str(a) for a in args]
        try:
            result = subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                                    timeout=timeout, check=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ProductionError(f"Could not run {args[0]}: {exc}") from exc
        if self.log:
            with self.log.open('a', encoding='utf-8') as f:
                f.write(json.dumps({'command': args, 'returncode': result.returncode}) + '\n')
                f.write(result.stdout + result.stderr + '\n')
        if result.returncode:
            raise ProductionError(f"{args[0]} exited {result.returncode}: {result.stderr[-3000:]}")
        return result.stdout

def ffmpeg() -> str:
    path = binary('ffmpeg')
    if not path:
        raise ProductionError('FFmpeg missing. Run scripts/install.sh --system or set VF_FFMPEG.')
    return path

def probe(path: Path) -> dict:
    cmd = binary('ffprobe')
    if not cmd:
        raise ProductionError('ffprobe missing; install alongside FFmpeg or set VF_FFPROBE.')
    return json.loads(Runner().run([cmd, '-v', 'error', '-show_format', '-show_streams',
                                   '-of', 'json', str(path)], timeout=60))

def ffbase() -> list[str]:
    return [ffmpeg(), '-hide_banner', '-loglevel', 'warning', '-y',
            '-filter_threads', '1', '-filter_complex_threads', '1']
