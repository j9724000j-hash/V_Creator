"""Offline checks for the depth-parallax camera (`v-creator animate`)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from test_spec import content, write_spec
from v_creator import depth, parallax
from v_creator.render import probe_media, render
from v_creator.spec import SpecError, load_project
from v_creator.visuals import make_overlay


def synthetic_image(path: Path, width: int = 160, height: int = 90) -> Path:
    """Near square over a far gradient: a depth map with real structure."""
    rng = np.random.default_rng(5)
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    frame[:, :] = (40, 50, 70)
    frame[: height // 2] = (120, 130, 150)
    frame[height // 3:, width // 3: 2 * width // 3] = (200, 180, 90)
    frame = (frame.astype(np.int16) + rng.integers(0, 6, frame.shape)).clip(0, 255).astype(np.uint8)
    Image.fromarray(frame).save(path)
    return path


def test_resolve_camera_and_ease() -> None:
    assert parallax.resolve_camera("auto", 1) == parallax.AUTO_SEQUENCE[0]
    assert parallax.resolve_camera("auto", len(parallax.AUTO_SEQUENCE) + 1) == parallax.AUTO_SEQUENCE[0]
    assert parallax.resolve_camera("orbit-left", 9) == "orbit-left"
    with pytest.raises(ValueError):
        parallax.resolve_camera("drone-flyover", 1)
    assert parallax.ease(0.0) == 0.0 and parallax.ease(1.0) == 1.0
    steps = [parallax.ease(i / 20) for i in range(21)]
    assert steps == sorted(steps) and abs(steps[10] - 0.5) < 1e-9


def test_camera_state_directions() -> None:
    common = dict(strength=1.0, focus=0.5, width=640, height=360)
    start = parallax.camera_state("dolly-in", 0.0, **common)
    end = parallax.camera_state("dolly-in", 1.0, **common)
    assert end.zoom > start.zoom
    left = parallax.camera_state("orbit-left", 1.0, **common)
    right = parallax.camera_state("orbit-right", 1.0, **common)
    assert left.px * right.px < 0  # opposite parallax directions
    up = parallax.camera_state("crane-up", 1.0, **common)
    down = parallax.camera_state("crane-down", 1.0, **common)
    assert up.py * down.py < 0
    strong = parallax.camera_state("orbit-right", 1.0, strength=2.0, focus=0.5, width=640, height=360)
    assert abs(strong.px) > abs(right.px)


def test_fit_box_covers_target() -> None:
    x0, y0, x1, y1 = parallax.fit_box(1376, 768, 640, 360)
    assert (x1 - x0) / (y1 - y0) == pytest.approx(640 / 360, rel=1e-6)
    assert 0 <= x0 < x1 <= 1376 and 0 <= y0 < y1 <= 768
    assert y1 - y0 == pytest.approx(768)  # cover fit: the short side is fully used


def test_frames_are_stable_uint8_and_move() -> None:
    rng = np.random.default_rng(1)
    base = rng.integers(0, 255, (90, 160, 3), dtype=np.uint8)
    flat = np.full((90, 160), 0.5, dtype=np.float32)
    out = list(parallax.frames(base, flat, "breathe", 4, strength=1.0))
    assert len(out) == 4 and all(f.shape == (90, 160, 3) and f.dtype == np.uint8 for f in out)
    assert not np.array_equal(out[0], out[2])  # the camera actually moves


def test_encode_clip_writes_a_playable_clip(tmp_path: Path) -> None:
    rng = np.random.default_rng(2)
    base = rng.integers(0, 255, (90, 160, 3), dtype=np.uint8)
    flat = np.full((90, 160), 0.5, dtype=np.float32)
    out = tmp_path / "clip.mp4"
    log = tmp_path / "log.txt"
    log.write_text("", encoding="utf-8")
    from v_creator.render import ffmpeg
    parallax.encode_clip(parallax.frames(base, flat, "dolly-in", 12, strength=1.0),
                         width=160, height=90, fps=24, count=12, out=out,
                         ffmpeg=ffmpeg(), overlay=None, fade=None, duration=0.5,
                         preview=True, log=log)
    info = probe_media(out)
    video = next(s for s in info["streams"] if s["codec_type"] == "video")
    assert (video["width"], video["height"]) == (160, 90)
    assert abs(float(info["format"]["duration"]) - 0.5) < 0.1


def test_overlay_is_transparent_where_empty(tmp_path: Path) -> None:
    spec = load_project(write_spec(tmp_path / "overlay-spec", content()))
    plain = make_overlay(spec.scenes[0], 320, 180, 1, darken_image=False)
    assert plain.mode == "RGBA"
    assert plain.getpixel((2, 2))[3] == 0          # untouched corner stays clear
    assert plain.getpixel((160, 140))[3] > 0       # title band is painted
    tinted = make_overlay(spec.scenes[0], 320, 180, 1, darken_image=True)
    assert tinted.getpixel((2, 2))[3] > 0          # photo tint covers everything


def test_spec_camera_field_validated(tmp_path: Path) -> None:
    data = content()
    data["scenes"][0]["camera"] = "orbit-left"
    spec = load_project(write_spec(tmp_path / "ok", data))
    assert spec.scenes[0].camera == "orbit-left"
    assert spec.scenes[1].camera == "auto"
    data = content()
    data["scenes"][0]["camera"] = "drone-flyover"
    with pytest.raises(SpecError, match="camera"):
        load_project(write_spec(tmp_path / "bad", data))


@pytest.mark.skipif(not depth.model_is_installed(), reason="depth model not installed")
def test_cached_depth_is_keyed_and_reused(tmp_path: Path) -> None:
    image = synthetic_image(tmp_path / "still.png")
    first, path, hit = depth.cached_depth(image, tmp_path / "cache")
    assert not hit and path.is_file()
    assert first.dtype == np.float32 and 0.0 <= first.min() and first.max() <= 1.0
    second, path2, hit2 = depth.cached_depth(image, tmp_path / "cache")
    assert hit2 and path2 == path
    assert np.allclose(first, second, atol=2e-3)  # cache stores float16


@pytest.mark.skipif(not depth.model_is_installed(), reason="depth model not installed")
def test_animate_render_end_to_end(tmp_path: Path) -> None:
    folder = tmp_path / "project"
    folder.mkdir(parents=True)
    synthetic_image(folder / "still.png", 320, 180)
    data = content()
    data["audio"]["narration"] = {"required": False}
    data["scenes"] = [dict(data["scenes"][0], image="still.png",
                           image_license="synthetic test asset", image_source="generated by pytest",
                           camera="dolly-in")]
    spec = load_project(write_spec(folder, data))
    manifest = render(spec, tmp_path / "out", preview=True, motion="depth")
    scene = manifest["scenes"][0]
    assert scene["motion"] == "depth-parallax:dolly-in"
    assert "Depth Anything" in scene["selected_tool"]
    assert manifest["tools"]["depth_model"]["installed"] is True
    assert manifest["validation"]["ok"]
    # second run must reuse the encoded clip
    again = render(spec, tmp_path / "out", preview=True, motion="depth")
    assert again["scenes"][0]["cache_hit"] is True
