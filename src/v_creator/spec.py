"""Fail-closed local project specification; no network or executable fields."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from pathlib import Path
import re

import yaml

from .parallax import CAMERAS


class SpecError(ValueError):
    """A spec is unsafe or cannot be rendered as described."""


_ID = re.compile(r"^[a-z][a-z0-9_-]{0,63}$")
_SUPPORTED_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
_SUPPORTED_AUDIO_SUFFIXES = {".wav", ".mp3", ".flac", ".m4a", ".ogg"}
_VISUALS = {"portal", "ruins", "forest", "stars", "citadel"}


def _map(value: object, label: str) -> dict:
    if not isinstance(value, dict):
        raise SpecError(f"{label} must be a mapping")
    return value


def _fields(value: dict, allowed: set[str], label: str) -> None:
    unknown = value.keys() - allowed
    if unknown:
        raise SpecError(f"{label}: unsupported fields {', '.join(sorted(map(str, unknown)))}")


def _text(value: object, label: str, *, max_length: int = 300) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > max_length:
        raise SpecError(f"{label} must be nonempty text (up to {max_length} characters)")
    return value.strip()


def _number(value: object, label: str, lower: float, upper: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
        raise SpecError(f"{label} must be a finite number")
    if not lower <= value <= upper:
        raise SpecError(f"{label} must be between {lower} and {upper}")
    return float(value)


def local_path(root: Path, raw: object, label: str, suffixes: set[str]) -> Path:
    """Keep YAML file paths within the spec's folder (including via symlinks)."""
    name = _text(raw, label, max_length=500)
    supplied = Path(name)
    if supplied.is_absolute() or "://" in name or name.startswith("~"):
        raise SpecError(f"{label} must be a local path relative to the project folder")
    candidate = (root / supplied).resolve()
    if not candidate.is_relative_to(root) or candidate.suffix.lower() not in suffixes:
        raise SpecError(f"{label} escapes the project folder or has an unsupported extension")
    return candidate


@dataclass(frozen=True)
class Scene:
    id: str
    duration: float
    title: str
    caption: str
    narration: str  # spoken text; defaults to caption, may include pronunciation diacritics
    visual: str
    image: Path | None
    image_license: str | None
    image_source: str | None
    transition: str
    camera: str  # depth-parallax camera move; "auto" picks a calm per-scene sequence


@dataclass(frozen=True)
class Project:
    spec_path: Path
    id: str
    title: str
    width: int
    height: int
    fps: int
    seed: int
    narration_required: bool
    narration_path: Path | None
    music_mode: str
    music_path: Path | None
    music_license: str | None
    music_source: str | None
    mood: str
    bpm: int
    scenes: tuple[Scene, ...]

    @property
    def duration(self) -> float:
        return sum(s.duration for s in self.scenes)

    def resolution(self, preview: bool) -> tuple[int, int]:
        if not preview:
            return self.width, self.height
        scale = min(1.0, 640 / max(self.width, self.height))
        return max(2, round(self.width * scale / 2) * 2), max(2, round(self.height * scale / 2) * 2)


def load_project(spec_file: str | Path) -> Project:
    spec_path = Path(spec_file).resolve(strict=True)
    if spec_path.stat().st_size > 256_000:
        raise SpecError("spec file is too large")
    try:
        content = _map(yaml.safe_load(spec_path.read_text(encoding="utf-8")), "project")
    except yaml.YAMLError as exc:
        raise SpecError(f"Invalid/suspicious YAML in {spec_path}: {exc}") from exc
    _fields(content, {"video", "audio", "scenes"}, "project")
    video = _map(content.get("video"), "video")
    _fields(video, {"id", "title", "width", "height", "fps", "seed"}, "video")
    slug = _text(video.get("id"), "video.id", max_length=64)
    if not _ID.fullmatch(slug):
        raise SpecError("video.id must be a safe lowercase slug")
    title = _text(video.get("title"), "video.title")
    width = int(_number(video.get("width"), "video.width", 160, 3840))
    height = int(_number(video.get("height"), "video.height", 160, 3840))
    fps = int(_number(video.get("fps", 24), "video.fps", 12, 60))
    if width % 2 or height % 2 or fps != video.get("fps", 24):
        raise SpecError("width and height must be even; fps must be an integer")
    seed = int(_number(video.get("seed", 2026), "video.seed", 0, 2**31 - 1))
    if seed != video.get("seed", 2026):
        raise SpecError("video.seed must be an integer")

    audio = _map(content.get("audio", {}), "audio")
    _fields(audio, {"narration", "music"}, "audio")
    narration = _map(audio.get("narration", {}), "audio.narration")
    _fields(narration, {"required", "path"}, "audio.narration")
    required = narration.get("required", False)
    if not isinstance(required, bool):
        raise SpecError("audio.narration.required must be true or false")
    root = spec_path.parent
    narration_path = (
        local_path(root, narration["path"], "audio.narration.path", _SUPPORTED_AUDIO_SUFFIXES)
        if "path" in narration else None
    )
    music = _map(audio.get("music", {}), "audio.music")
    _fields(music, {"mode", "path", "license", "source", "mood", "bpm"}, "audio.music")
    mode = music.get("mode", "procedural")
    if mode not in {"procedural", "file", "off"}:
        raise SpecError("audio.music.mode must be procedural, file or off")
    music_path = None
    music_license = music_source = None
    if mode == "file":
        music_path = local_path(root, music.get("path"), "audio.music.path", _SUPPORTED_AUDIO_SUFFIXES)
        music_license = _text(music.get("license"), "audio.music.license")
        music_source = _text(music.get("source"), "audio.music.source", max_length=600)
    elif any(k in music for k in ("path", "license", "source")):
        raise SpecError("audio.music: path/license/source require mode: file")
    mood = music.get("mood", "mysterious")
    if mood not in {"mysterious", "hopeful", "ominous"}:
        raise SpecError("audio.music.mood must be mysterious, hopeful or ominous")
    bpm = int(_number(music.get("bpm", 72), "audio.music.bpm", 40, 180))
    if bpm != music.get("bpm", 72):
        raise SpecError("audio.music.bpm must be an integer")

    records = content.get("scenes")
    if not isinstance(records, list) or not 1 <= len(records) <= 30:
        raise SpecError("scenes must contain 1–30 scenes")
    scenes = []
    used = set()
    for index, item in enumerate(records, 1):
        scene = _map(item, f"scenes[{index}]")
        _fields(scene, {"id", "duration", "title", "caption", "narration", "visual", "image", "image_license", "image_source", "transition", "camera"}, f"scenes[{index}]")
        scene_id = _text(scene.get("id"), f"scenes[{index}].id", max_length=64)
        if not _ID.fullmatch(scene_id) or scene_id in used:
            raise SpecError(f"scenes[{index}].id must be a unique safe lowercase slug")
        used.add(scene_id)
        visual = scene.get("visual", "stars")
        if visual not in _VISUALS:
            raise SpecError(f"scenes[{index}].visual must be one of {sorted(_VISUALS)}")
        transition = scene.get("transition", "fade")
        if transition not in {"fade", "cut"}:
            raise SpecError(f"scenes[{index}].transition must be fade or cut")
        camera = scene.get("camera", "auto")
        if camera not in CAMERAS:
            raise SpecError(f"scenes[{index}].camera must be one of {list(CAMERAS)}")
        image = None
        image_license = image_source = None
        if "image" in scene:
            image = local_path(root, scene["image"], f"scenes[{index}].image", _SUPPORTED_IMAGE_SUFFIXES)
            image_license = _text(scene.get("image_license"), f"scenes[{index}].image_license")
            image_source = _text(scene.get("image_source"), f"scenes[{index}].image_source", max_length=600)
            if not image.is_file():
                raise SpecError(f"Missing image asset: {image}")
        elif "image_license" in scene or "image_source" in scene:
            raise SpecError(f"scenes[{index}]: image metadata requires an image")
        duration = _number(scene.get("duration"), f"scenes[{index}].duration", 0.75, 120)
        if abs(duration * fps - round(duration * fps)) > 1e-6:
            raise SpecError(f"scenes[{index}].duration must equal a whole number of frames at {fps} fps")
        title_text = _text(scene.get("title"), f"scenes[{index}].title")
        caption_text = _text(scene.get("caption", title_text), f"scenes[{index}].caption", max_length=500)
        scenes.append(Scene(
            id=scene_id,
            duration=duration,
            title=title_text,
            caption=caption_text,
            narration=_text(scene.get("narration", caption_text), f"scenes[{index}].narration", max_length=500),
            visual=visual,
            image=image,
            image_license=image_license,
            image_source=image_source,
            transition=transition,
            camera=camera,
        ))
    project = Project(spec_path, slug, title, width, height, fps, seed, required, narration_path,
                      mode, music_path, music_license, music_source, mood, bpm, tuple(scenes))
    if project.duration > 600:
        raise SpecError("project exceeds 10-minute CPU safety limit")
    return project
