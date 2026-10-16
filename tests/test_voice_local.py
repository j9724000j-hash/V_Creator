"""Offline Arabic voice: scene timing, provenance, no silent truncation, real WAV smoke."""

from __future__ import annotations

import json
from pathlib import Path
import wave

import numpy as np
import pytest

from test_spec import content, write_spec
from v_creator import voice_local
from v_creator.spec import load_project


def test_narration_field_is_separate_from_subtitles(tmp_path: Path) -> None:
    data = content()
    data["scenes"][0]["narration"] = "دَخَلْنا البَوَّابَةَ."
    spec = load_project(write_spec(tmp_path, data))
    assert spec.scenes[0].caption == "دخلنا البوابة."
    assert spec.scenes[0].narration == "دَخَلْنا البَوَّابَةَ."
    assert spec.scenes[1].narration == spec.scenes[1].caption


def test_narrate_project_tracks_scenes_and_declares_synthetic_origin(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec = load_project(write_spec(tmp_path, content()))
    monkeypatch.setattr(voice_local, "create_tts", lambda threads: object())
    monkeypatch.setattr(voice_local, "generate", lambda *a, **kw: (np.ones(2400, np.float32) * 0.1, 16000))
    path = tmp_path / "out/narration.wav"
    result = voice_local.narrate_project(spec, path)
    with wave.open(str(path)) as audio:
        assert (audio.getnframes(), audio.getframerate(), audio.getnchannels()) == (32000, 16000, 1)
    assert result["duration_seconds"] == 2.0
    assert len(result["scenes"]) == 2
    assert result["scenes"][0]["start_seconds"] == 0.18
    assert result["scenes"][1]["start_seconds"] == 1.18
    assert "NOT a human" in json.loads(path.with_suffix(".voice.json").read_text())["synthesis_type"]


def test_narrate_refuses_to_cut_words_and_writes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec = load_project(write_spec(tmp_path, content()))
    monkeypatch.setattr(voice_local, "create_tts", lambda threads: object())
    monkeypatch.setattr(voice_local, "generate", lambda *a, **kw: (np.ones(20000, np.float32) * 0.1, 16000))
    path = tmp_path / "too-short.wav"
    with pytest.raises(ValueError, match="Extend the scene"):
        voice_local.narrate_project(spec, path)
    assert not path.exists()
    assert not path.with_suffix(".voice.json").exists()


def test_generate_rejects_invalid_input_before_inference() -> None:
    class FakeTts:
        num_speakers = 10

        def generate(self, *args, **kwargs):
            raise AssertionError("should not reach the model")

    with pytest.raises(ValueError, match="Arabic text"):
        voice_local.generate(FakeTts(), "hello")
    with pytest.raises(ValueError, match="speakers"):
        voice_local.generate(FakeTts(), "مرحبا", speaker=10)


@pytest.mark.skipif(not voice_local.model_is_installed(), reason="model weights not installed")
def test_real_cpu_inference_produces_arabic_pcm_wav(tmp_path: Path) -> None:
    tts = voice_local.create_tts(threads=2)
    samples, rate = voice_local.generate(tts, "خلف البوابة، تبدأ الحكاية.", steps=8)
    path = tmp_path / "arabic.wav"
    voice_local.write_wav(path, samples, rate)
    with wave.open(str(path)) as audio:
        assert audio.getnchannels() == 1
        assert audio.getsampwidth() == 2
        assert audio.getframerate() >= 16000
        assert audio.getnframes() > audio.getframerate() * 0.7
    assert 0.001 < float(np.max(np.abs(samples))) <= 1
