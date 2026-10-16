"""Local Supertonic 3 Arabic narration via sherpa-onnx (CPU, no cloud calls).

The model is a fixed synthetic preset voice, not a recording or a clone. The
weights are licensed OpenRAIL-M and installed separately (not tracked in Git).
"""

from __future__ import annotations

from pathlib import Path
import hashlib
import json
import wave

from .spec import Project

import numpy as np

MODEL_DIR = Path(__file__).resolve().parents[2] / "models/supertonic-3"
MODEL_FILES = (
    "duration_predictor.onnx", "text_encoder.onnx", "vector_estimator.onnx",
    "vocoder.onnx", "tts.json", "unicode_indexer.bin", "voice.bin",
)


def model_is_installed() -> bool:
    """Check all seven model files against the hashes saved by the pinned installer."""
    try:
        info = json.loads((MODEL_DIR / "install-manifest.json").read_text(encoding="utf-8"))
        if info.get("source") != "npm/3sln/donki-lle-voice-multi@0.1.1":
            return False
        for name in MODEL_FILES:
            digest = hashlib.sha256()
            with (MODEL_DIR / name).open("rb") as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(block)
            if digest.hexdigest() != info["sha256"][name]:
                return False
        return True
    except (OSError, KeyError, TypeError, ValueError):
        return False


def create_tts(threads: int = 2):
    """Load the local CPU-only model once. Call before generating multiple scenes."""
    if not 1 <= threads <= 4:
        raise ValueError("threads must be 1–4")
    if not model_is_installed():
        raise FileNotFoundError(
            "Local voice weights missing. Run .venv/bin/python scripts/install-local-voice.py"
        )
    import sherpa_onnx

    config = sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(
        supertonic=sherpa_onnx.OfflineTtsSupertonicModelConfig(
            duration_predictor=str(MODEL_DIR / MODEL_FILES[0]),
            text_encoder=str(MODEL_DIR / MODEL_FILES[1]),
            vector_estimator=str(MODEL_DIR / MODEL_FILES[2]),
            vocoder=str(MODEL_DIR / MODEL_FILES[3]),
            tts_json=str(MODEL_DIR / MODEL_FILES[4]),
            unicode_indexer=str(MODEL_DIR / MODEL_FILES[5]),
            voice_style=str(MODEL_DIR / MODEL_FILES[6]),
        ),
        num_threads=threads,
        debug=False,
        provider="cpu",
    ))
    if not config.validate():
        raise RuntimeError("The local Supertonic model is incomplete or invalid")
    return sherpa_onnx.OfflineTts(config)


def generate(tts, text: str, *, speaker: int = 0, steps: int = 8,
             speed: float = 1.0) -> tuple[np.ndarray, int]:
    """Return validated mono samples and sample rate for a short Arabic passage."""
    if not 0 <= speaker < tts.num_speakers:
        raise ValueError(f"Model has {tts.num_speakers} speakers; requested {speaker}")
    if not 4 <= steps <= 12 or not 0.7 <= speed <= 1.5:
        raise ValueError("steps must be 4–12; speed 0.7–1.5")
    if not 1 <= len(text) <= 500 or not any("\u0600" <= c <= "\u06ff" for c in text):
        raise ValueError("Provide a short passage of Arabic text (1–500 characters)")
    import sherpa_onnx

    cfg = sherpa_onnx.GenerationConfig()
    cfg.sid = speaker
    cfg.num_steps = steps
    cfg.speed = speed
    cfg.extra["lang"] = "ar"
    audio = tts.generate(text, cfg)
    signal = np.asarray(audio.samples, dtype=np.float32)
    if (len(signal) == 0 or audio.sample_rate < 16000 or not np.isfinite(signal).all()
            or float(np.max(np.abs(signal))) < 0.001):
        raise RuntimeError("TTS did not produce a valid, audible speech signal")
    return signal, audio.sample_rate


def write_wav(path: Path, signal: np.ndarray, sample_rate: int) -> None:
    """Save a 16-bit mono PCM WAV, suitable for FFmpeg or direct listening."""
    if path.suffix.lower() != ".wav":
        raise ValueError("output path must end in .wav")
    path.parent.mkdir(parents=True, exist_ok=True)
    samples = (np.clip(signal, -1.0, 1.0) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(samples.tobytes())


def narrate_project(project: Project, output: Path, *, speaker: int = 0,
                    steps: int = 8, speed: float = 1.0, threads: int = 2) -> dict:
    """Make one WAV with each scene's whole spoken line timed to that scene.

    Never truncate a word or silently spill audio into the next scene: refuse
    to export when a line doesn't fit. Increase scene duration, shorten its
    narration or adjust speed; for best naturalness favour longer scenes.
    """
    if output.suffix.lower() != ".wav":
        raise ValueError("narration output must end in .wav")
    tts = create_tts(threads)
    utterances = []
    sample_rate = None
    for scene in project.scenes:
        signal, rate = generate(tts, scene.narration, speaker=speaker, steps=steps, speed=speed)
        if sample_rate is not None and rate != sample_rate:
            raise RuntimeError("TTS changed sample rate between scenes")
        sample_rate = rate
        frame_count = round(scene.duration * rate)
        remaining = frame_count - len(signal)
        if remaining < round(0.06 * rate):
            raise ValueError(
                f"Scene '{scene.id}': speech takes {len(signal) / rate:.2f}s of "
                f"{scene.duration:.2f}s; leave >=0.06s between scenes. "
                "Extend the scene, shorten its narration, or try --speed up to 1.5."
            )
        utterances.append((scene, signal, remaining))
    assert sample_rate is not None  # validated project always has at least one scene
    timeline = np.zeros(sum(round(s.duration * sample_rate) for s in project.scenes), dtype=np.float32)
    scene_start = 0
    timing = []
    for scene, signal, remaining in utterances:
        frame_count = round(scene.duration * sample_rate)
        # For roomier scenes add a brief visual lead-in, while preserving the full line.
        lead = min(round(0.18 * sample_rate), max(0, remaining - round(0.06 * sample_rate)) // 2)
        softened = signal.copy()
        edge = min(round(0.01 * sample_rate), len(signal) // 2)
        if edge:
            softened[:edge] *= np.linspace(0, 1, edge, dtype=np.float32)
            softened[-edge:] *= np.linspace(1, 0, edge, dtype=np.float32)
        timeline[scene_start + lead:scene_start + lead + len(softened)] = softened
        timing.append({"scene": scene.id, "start_seconds": round((scene_start + lead) / sample_rate, 2),
                       "speech_seconds": round(len(signal) / sample_rate, 2),
                       "scene_seconds": scene.duration})
        scene_start += frame_count
    output = output.resolve()
    write_wav(output, timeline, sample_rate)
    details = {
        "output": str(output), "duration_seconds": round(len(timeline) / sample_rate, 2),
        "sample_rate": sample_rate, "language": "ar", "scenes": timing,
        "engine": "sherpa-onnx 1.13.8", "model": "Supertone Supertonic 3 (third-party npm repack)",
        "weights_license": "OpenRAIL-M", "speaker": speaker, "steps": steps, "speed": speed,
        "model_install_manifest_sha256": (
            hashlib.sha256((MODEL_DIR / "install-manifest.json").read_bytes()).hexdigest()
            if (MODEL_DIR / "install-manifest.json").is_file() else None
        ),
        "synthesis_type": "fixed-preset neural synthetic voice; NOT a human performance or voice clone",
        "review": "Listen for Arabic pronunciation, naturalness and mix before publishing. Check model use restrictions and attribution.",
    }
    output.with_suffix(".voice.json").write_text(
        json.dumps(details, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return details
