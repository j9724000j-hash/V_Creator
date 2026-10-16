"""Small, offline end-to-end checks; a synthetic test signal is NEVER production narration."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import wave

import numpy as np
import pytest

from test_spec import content, write_spec
from v_creator.audio import generate_music, generate_sfx
from v_creator.render import ffmpeg, render, validate, write_subtitles
from v_creator.spec import SpecError, load_project


def project(tmp_path: Path):
    return load_project(write_spec(tmp_path / "project", content()))


def test_final_requires_voice_before_any_export(tmp_path: Path) -> None:
    spec = project(tmp_path)
    out = tmp_path / "output"
    with pytest.raises(SpecError, match="Narration audio is missing"):
        render(spec, out, preview=False)
    assert not out.exists()
    assert not (out / "final.mp4").exists()


def test_procedural_audio_deterministic_and_no_external_samples(tmp_path: Path) -> None:
    a, b = tmp_path / "one.wav", tmp_path / "two.wav"
    generate_music(a, 1.0, seed=12)
    generate_music(b, 1.0, seed=12)
    assert a.read_bytes() == b.read_bytes()
    generate_sfx(a, 1.0, [0, 0.6], seed=22)
    generate_sfx(b, 1.0, [0, 0.6], seed=22)
    assert a.read_bytes() == b.read_bytes()
    with wave.open(str(a)) as audio:
        assert (audio.getnchannels(), audio.getsampwidth(), audio.getframerate()) == (2, 2, 32000)


def test_subtitle_timing_matches_scenes(tmp_path: Path) -> None:
    spec = project(tmp_path)
    path = tmp_path / "captions.srt"
    write_subtitles(spec, path)
    text = path.read_text(encoding="utf-8")
    assert "00:00:00,000 --> 00:00:01,000" in text
    assert "00:00:01,000 --> 00:00:02,000" in text
    assert "دخلنا البوابة." in text


def test_preview_decodes_and_cache_reuses_unchanged_scenes(tmp_path: Path) -> None:
    spec = project(tmp_path)
    out = tmp_path / "output"
    manifest = render(spec, out, preview=True)
    assert manifest["mode"] == "preview"
    assert manifest["audio"]["narration"]["status"] == "missing; preview only"
    assert all(not scene["cache_hit"] for scene in manifest["scenes"])
    assert manifest["validation"]["ok"]
    assert all(manifest["validation"]["checks"].values())
    assert (out / "score.mid").stat().st_size > 0
    assert json.loads((out / "validation-report.json").read_text())["ok"]
    again = render(spec, out, preview=True)
    assert all(scene["cache_hit"] for scene in again["scenes"])
    assert validate(out / "preview.mp4", spec)["ok"]


def _dummy_test_tone(path: Path, duration: float) -> None:
    """Signal-only CI fixture; it is intentionally not a voice or part of any release."""
    sample_rate = 16000
    t = np.arange(int(duration * sample_rate)) / sample_rate
    data = (np.sin(2 * np.pi * 220 * t) * 0.08 * 32767).astype("<i2")
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(sample_rate)
        out.writeframes(data.tobytes())


def test_final_accepts_authorized_audio_input_and_rejects_overlong(tmp_path: Path) -> None:
    spec = project(tmp_path)
    out = tmp_path / "output"
    tone = tmp_path / "ci-only-test-tone.wav"
    _dummy_test_tone(tone, 1.8)
    manifest = render(spec, out, preview=False, narrator_override=tone)
    assert manifest["audio"]["narration"]["status"] == "provided"
    assert manifest["validation"]["ok"]
    assert manifest["mode"] == "final"
    assert (out / "final.mp4").stat().st_size > 5000
    _dummy_test_tone(tone, 3.0)
    with pytest.raises(SpecError, match="exceeds the video"):
        render(spec, out, preview=False, narrator_override=tone)
    draft = tmp_path / "must-not-truncate-preview"
    with pytest.raises(SpecError, match="exceeds the video"):
        render(spec, draft, preview=True, narrator_override=tone)
    assert not draft.exists()


def test_render_records_declared_synthetic_voice_without_calling_it_human(tmp_path: Path) -> None:
    spec = project(tmp_path)
    tone = tmp_path / "ci-only-test-tone.wav"
    _dummy_test_tone(tone, 1.8)  # NOT speech; used only to check provenance propagation.
    tone.with_suffix(".voice.json").write_text(json.dumps({
        "output": str(tone.resolve()), "engine": "CI dummy signal",
        "model": "none; test-only tone", "weights_license": "not applicable",
        "synthesis_type": "synthetic TEST TONE, NOT HUMAN NOR PUBLISHABLE",
    }))
    manifest = render(spec, tmp_path / "output", preview=True, narrator_override=tone)
    prov = manifest["audio"]["narration"]["provenance"]
    assert prov["declared_model"] == "none; test-only tone"
    assert prov["declared_synthesis_type"] == "synthetic TEST TONE, NOT HUMAN NOR PUBLISHABLE"
    assert len(prov["source_sha256"]) == 64


def test_render_rejects_mismatched_voice_provenance_before_export(tmp_path: Path) -> None:
    spec = project(tmp_path)
    tone = tmp_path / "ci-only-test-tone.wav"
    _dummy_test_tone(tone, 1.8)
    tone.with_suffix(".voice.json").write_text(json.dumps({"output": "/not-the-input.wav"}))
    out = tmp_path / "must-not-export"
    with pytest.raises(SpecError, match="does not match"):
        render(spec, out, preview=False, narrator_override=tone)
    assert not out.exists()


def test_external_music_requires_and_records_provenance(tmp_path: Path) -> None:
    folder = tmp_path / "project"
    folder.mkdir()
    generate_music(folder / "my-score.wav", 1.5)
    data = content()
    data["audio"]["music"] = {"mode": "file", "path": "my-score.wav",
                                "license": "user-owned", "source": "recorded by composer"}
    spec = load_project(write_spec(folder, data))
    manifest = render(spec, tmp_path / "output", preview=True)
    assert manifest["audio"]["music"]["origin"] == "recorded by composer"
    assert manifest["audio"]["music"]["license"] == "user-owned"
    assert manifest["validation"]["ok"]


def test_validate_detects_wrong_resolution(tmp_path: Path) -> None:
    spec = project(tmp_path)
    out = tmp_path / "output"
    render(spec, out, preview=True)
    wrong = tmp_path / "wrong.mp4"
    subprocess.run([ffmpeg(), "-hide_banner", "-loglevel", "error", "-y", "-i",
                    str(out / "preview.mp4"), "-vf", "scale=640:360", "-c:v", "libx264",
                    "-c:a", "copy", str(wrong)], check=True)
    assert not validate(wrong, spec, decode=False)["ok"]
    assert not validate(wrong, spec, decode=False)["checks"]["resolution"]
