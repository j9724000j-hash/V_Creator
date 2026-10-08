from __future__ import annotations
import math
from pathlib import Path
from typing import Literal
import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator
from .util import ProductionError, safe_path

Tool = Literal['ffmpeg', 'remotion', 'moviepy', 'manim', 'motion-canvas', 'godot', 'unity']

class Model(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)

class Video(Model):
    id: str = Field(pattern=r'^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$')
    title: str = Field(min_length=1, max_length=200)
    duration: float = Field(gt=0, le=3600)
    width: int = Field(default=1080, ge=160, le=3840, multiple_of=2)
    height: int = Field(default=1920, ge=160, le=3840, multiple_of=2)
    fps: int = Field(default=30, ge=1, le=60)
    style: dict[str, str] = Field(default_factory=dict)

class Asset(Model):
    path: str
    source: str = Field(min_length=1)
    license: str = Field(min_length=1)

class Cue(Model):
    time: float = Field(ge=0)
    effect: Literal['whoosh','hit','impact','bass_drop','click','pop','glitch',
                    'notification','riser','sweep','ambience','wind','rain','mechanical','scifi']
    duration: float = Field(default=.5, gt=0, le=30)
    gain: float = Field(default=.2, ge=0, le=1)
    pan: float = Field(default=0, ge=-1, le=1)

class Scene(Model):
    id: str = Field(pattern=r'^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$')
    duration: float = Field(gt=0, le=600)
    type: Literal['title','text','chart','explanatory_diagram','scientific_animation',
                  'cinematic_visual','image','python_effect','simulation','unity_scene'] = 'text'
    intent: str = ''
    visual_description: str = ''
    title: str = ''
    narration: str = ''
    narration_asset: Asset | None = None
    captions: str | None = None
    assets: list[Asset] = Field(default_factory=list, max_length=1)
    tool: Tool | None = None
    allow_fallback: bool = True
    transition: Literal['cut', 'fade'] = 'fade'
    effect: Literal['none','ken_burns','vignette','grain'] = 'ken_burns'
    audio_cues: list[Cue] = Field(default_factory=list)
    constraints: dict[str, str] = Field(default_factory=dict)
    quality: Literal['draft','preview','standard','high'] | None = None
    values: list[float] = Field(default_factory=lambda: [2, 5, 8, 4])

    @model_validator(mode='after')
    def cues_fit(self):
        if self.constraints:
            raise ValueError('Custom scene constraints require a dedicated adapter; do not silently ignore them')
        if any(c.time + c.duration > self.duration + .001 for c in self.audio_cues):
            raise ValueError('Audio cue extends past scene boundary')
        return self

class Audio(Model):
    narration: bool = True
    music: bool = True
    sound_effects: bool = True
    missing_tts: Literal['error','skip'] = 'error'
    voice: str = 'en'
    speaking_rate: int = Field(default=155, ge=80, le=350)
    target_loudness: float = Field(default=-16, ge=-24, le=-9)
    bpm: int = Field(default=84, ge=40, le=200)
    key: Literal['C','D','E','F','G','A','B'] = 'A'
    mood: Literal['cinematic','calm','bright'] = 'cinematic'
    intensity: float = Field(default=.5, ge=0, le=1)
    music_gain: float = Field(default=.18, ge=0, le=1)
    reverb: bool = False

class Render(Model):
    preset: Literal['draft','preview','standard','high'] = 'standard'
    threads: int = Field(default=2, ge=1, le=8)
    keep_intermediates: bool = True
    burn_captions: bool = True

class Planner(Model):
    prefer: list[Tool] = Field(default_factory=list)
    enable: list[Tool] = Field(default_factory=lambda: ['ffmpeg'])

class Spec(Model):
    video: Video
    audio: Audio = Field(default_factory=Audio)
    render: Render = Field(default_factory=Render)
    planner: Planner = Field(default_factory=Planner)
    scenes: list[Scene] = Field(min_length=1, max_length=200)
    brief: str = ''
    assumptions: list[str] = Field(default_factory=list)

    @model_validator(mode='after')
    def consistent(self):
        if len({s.id for s in self.scenes}) != len(self.scenes):
            raise ValueError('Scene IDs must be unique')
        if not math.isclose(sum(s.duration for s in self.scenes), self.video.duration, abs_tol=.01):
            raise ValueError('Sum of scene durations must equal video.duration')
        for scene in self.scenes:
            if not math.isclose(scene.duration*self.video.fps, round(scene.duration*self.video.fps), abs_tol=1e-6):
                raise ValueError('Scene durations must align to whole frames')
        return self

def load(project: Path) -> Spec:
    file = project / 'video.yaml' if project.is_dir() else project
    if not file.is_file():
        raise ProductionError(f'Spec not found: {file}')
    if file.stat().st_size > 1_000_000:
        raise ProductionError('Specification exceeds 1 MB')
    spec = Spec.model_validate(yaml.safe_load(file.read_text(encoding='utf-8')))
    for s in spec.scenes:
        for a in s.assets + ([s.narration_asset] if s.narration_asset else []):
            if not safe_path(file.parent, a.path).is_file():
                raise ProductionError(f'Missing asset: {a.path}')
    return spec
