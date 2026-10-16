"""YAML validation is the trust boundary for paths, licensing and voice policy."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from v_creator.spec import SpecError, load_project


def content() -> dict:
    return {
        "video": {"id": "test-story", "title": "ليلة النجوم", "width": 320,
                  "height": 180, "fps": 24, "seed": 7},
        "audio": {"narration": {"required": True, "path": "private/narration.wav"},
                  "music": {"mode": "procedural", "mood": "mysterious", "bpm": 72}},
        "scenes": [{"id": "first", "duration": 1, "visual": "portal",
                    "title": "البوابة", "caption": "دخلنا البوابة.", "transition": "fade"},
                   {"id": "second", "duration": 1, "visual": "ruins",
                    "title": "الطريق", "caption": "ها هو الطريق.", "transition": "cut"}],
    }


def write_spec(folder: Path, data: dict | str) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "video.yaml"
    path.write_text(data if isinstance(data, str) else yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
    return path


def test_valid_spec_and_preview_scale(tmp_path: Path) -> None:
    spec = load_project(write_spec(tmp_path, content()))
    assert spec.duration == 2
    assert spec.resolution(False) == (320, 180)
    assert spec.resolution(True) == (320, 180)
    assert spec.narration_required
    assert spec.scenes[0].title == "البوابة"


@pytest.mark.parametrize("field,bad", [
    ("fps", 0), ("fps", "twenty-four"), ("width", 321), ("height", 181),
    ("seed", -1),
])
def test_reject_bad_canvas(tmp_path: Path, field: str, bad: object) -> None:
    d = content()
    d["video"][field] = bad
    with pytest.raises(SpecError):
        load_project(write_spec(tmp_path, d))


def test_reject_unknown_fields_and_non_frame_aligned_durations(tmp_path: Path) -> None:
    d = content()
    d["scenes"][0]["duration"] = 1.01
    with pytest.raises(SpecError, match="whole number of frames"):
        load_project(write_spec(tmp_path, d))
    d = content()
    d["scenes"][0]["mystery"] = "untracked"
    with pytest.raises(SpecError, match="unsupported fields"):
        load_project(write_spec(tmp_path, d))


def test_reject_unsafe_yaml_tag_without_execution(tmp_path: Path) -> None:
    marker = tmp_path / "should_not_exist"
    payload = f"!!python/object/apply:os.system ['touch {marker}']\n"
    with pytest.raises(SpecError, match="Invalid/suspicious YAML"):
        load_project(write_spec(tmp_path, payload))
    assert not marker.exists()


@pytest.mark.parametrize("image", ["../some-image.png", "/tmp/some-image.png"])
def test_reject_unsafe_image_path(tmp_path: Path, image: str) -> None:
    d = content()
    d["scenes"][0].update(image=image, image_license="user-owned", image_source="self")
    with pytest.raises(SpecError, match="relative|escapes"):
        load_project(write_spec(tmp_path, d))


def test_reject_symlink_leaving_project(tmp_path: Path) -> None:
    external = tmp_path / "outside.png"
    external.write_bytes(b"fake PNG")
    folder = tmp_path / "project"
    folder.mkdir()
    (folder / "scene.png").symlink_to(external)
    d = content()
    d["scenes"][0].update(image="scene.png", image_license="user-owned", image_source="self")
    with pytest.raises(SpecError, match="escapes"):
        load_project(write_spec(folder, d))


def test_require_image_license_and_source(tmp_path: Path) -> None:
    folder = tmp_path / "project"
    folder.mkdir()
    (folder / "scene.png").write_bytes(b"fake PNG")
    d = content()
    d["scenes"][0]["image"] = "scene.png"
    with pytest.raises(SpecError, match="image_license"):
        load_project(write_spec(folder, d))
    d["scenes"][0]["image_license"] = "CC0"
    with pytest.raises(SpecError, match="image_source"):
        load_project(write_spec(folder, d))
    d["scenes"][0]["image_source"] = "self"
    assert load_project(write_spec(folder, d)).scenes[0].image_license == "CC0"


def test_music_file_requires_explicit_provenance(tmp_path: Path) -> None:
    d = content()
    (tmp_path / "score.wav").write_bytes(b"fake WAV")
    d["audio"]["music"] = {"mode": "file", "path": "score.wav"}
    with pytest.raises(SpecError, match="audio.music.license"):
        load_project(write_spec(tmp_path, d))
    d["audio"]["music"].update(license="user-owned", source="my composition")
    assert load_project(write_spec(tmp_path, d)).music_source == "my composition"


def test_voice_path_must_be_local(tmp_path: Path) -> None:
    d = content()
    d["audio"]["narration"]["path"] = "../../private.wav"
    with pytest.raises(SpecError, match="escapes"):
        load_project(write_spec(tmp_path, d))
