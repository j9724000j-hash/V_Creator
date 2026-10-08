"""Backends share a normalized H.264 scene-output contract."""
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from ..spec import Scene
from ..util import Runner

@dataclass
class Context:
    scene: Scene
    width: int
    height: int
    fps: int
    frames: int
    threads: int
    preset: str
    asset: Path
    output: Path
    runner: Runner

class Backend(Protocol):
    def render(self, context: Context) -> None: ...
