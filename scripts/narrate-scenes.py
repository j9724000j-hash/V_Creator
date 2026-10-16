#!/usr/bin/env python3
"""Per-scene Arabic narration files from a project spec, plus the full timeline.

Synthesises one clean WAV per scene (no timing baked in), the scripted dialogue
lines with separate speakers, and the continuous timeline through the repo's
own `narrate_project()` so the fit guard and provenance file are reused.

The voice is a fixed preset neural voice (synthetic). It is NOT a human
recording and must not be presented as one; see docs/voice-ar.md.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

import yaml

from v_creator.spec import load_project
from v_creator.voice_local import create_tts, generate, narrate_project, write_wav

MARGIN_SECONDS = 0.45  # speech + lead-in + breath that must fit inside a scene


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def wav_info(path: Path) -> tuple[float, int]:
    import wave

    with wave.open(str(path), "rb") as handle:
        frames = handle.getnframes()
        rate = handle.getframerate()
    return frames / rate, rate


def words(text: str) -> int:
    return len([token for token in text.split() if token.strip()])


def synthesize(tts, text: str, *, speaker: int, steps: int, speed: float) -> tuple:
    return generate(tts, text, speaker=speaker, steps=steps, speed=speed)


def fit_speed(tts, scenes, *, speaker: int, steps: int, threads: int, log) -> tuple[float, dict]:
    """Pick the slowest speed whose slowest line still fits its own scene."""
    available = min(scene.duration for scene in scenes) - MARGIN_SECONDS

    def measure(speed_value: float) -> dict:
        measured = {}
        for scene in scenes:
            signal, rate = synthesize(tts, scene.narration, speaker=speaker,
                                      steps=steps, speed=speed_value)
            measured[scene.id] = len(signal) / rate
        return measured

    durations = measure(1.0)
    slowest = max(durations.values())
    speed = 1.0
    if slowest > available:
        speed = min(1.5, slowest / available)
        log(f"lines overflow the {available:.2f}s slot; raising speed to {speed:.3f}")
    elif slowest + 1.2 <= available:
        speed = 0.95
        log("room to spare; slowing delivery to 0.95")
    return speed, measure(speed)


def encode_mp3(wav_path: Path, mp3_path: Path) -> bool:
    try:
        import imageio_ffmpeg

        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:  # noqa: BLE001 - optional convenience output
        return False
    result = subprocess.run(
        [ffmpeg, "-y", "-loglevel", "error", "-i", str(wav_path),
         "-codec:a", "libmp3lame", "-q:a", "2", str(mp3_path)],
        capture_output=True, text=True)
    return result.returncode == 0 and mp3_path.is_file()


def main() -> None:
    parser = argparse.ArgumentParser(description="Per-scene Arabic narration files from a project spec")
    parser.add_argument("--spec", type=Path, required=True, help="project YAML")
    parser.add_argument("--outdir", type=Path, required=True, help="destination folder for the audio set")
    parser.add_argument("--dialogue", type=Path, help="optional dialogue YAML with per-line speakers")
    parser.add_argument("--speaker", type=int, default=0, help="narrator preset voice 0..9")
    parser.add_argument("--steps", type=int, default=8, help="diffusion steps 4..12")
    parser.add_argument("--threads", type=int, default=2, help="CPU threads 1..4")
    parser.add_argument("--skip-timeline", action="store_true", help="do not build the continuous timeline")
    args = parser.parse_args()

    def log(message: str) -> None:
        print(f"[audios] {message}", flush=True)

    project = load_project(args.spec)
    outdir = args.outdir.resolve()
    narration_dir = outdir / "narration"
    dialogue_dir = outdir / "dialogue"
    narration_dir.mkdir(parents=True, exist_ok=True)

    started = time.monotonic()
    tts = create_tts(args.threads)
    log(f"voice loaded ({time.monotonic() - started:.1f}s)")

    speed, durations = fit_speed(tts, project.scenes, speaker=args.speaker,
                                 steps=args.steps, threads=args.threads, log=log)
    log(f"delivery speed {speed:.3f}")

    entries: list[dict] = []
    for index, scene in enumerate(project.scenes, 1):
        signal, rate = synthesize(tts, scene.narration, speaker=args.speaker,
                                  steps=args.steps, speed=speed)
        name = f"scene{index:02d}_{scene.id.split('-', 1)[1]}_narration.wav"
        path = narration_dir / name
        write_wav(path, signal, rate)
        duration, sample_rate = wav_info(path)
        start = 12 * (index - 1)
        end = start + 12
        entries.append({
            "file": f"narration/{name}",
            "kind": "scene_narration",
            "scene": scene.id,
            "scene_index": index,
            "timecode": f"{start // 60:02d}:{start % 60:02d}-{end // 60:02d}:{end % 60:02d}",
            "text": scene.narration,
            "speaker": args.speaker,
            "speed": round(speed, 3),
            "duration_seconds": round(duration, 2),
            "sample_rate": sample_rate,
            "words": words(scene.narration),
            "words_per_minute": round(words(scene.narration) / duration * 60, 1),
            "fits_scene_slot": duration <= scene.duration - 0.1,
            "sha256": sha256(path),
            "bytes": path.stat().st_size,
        })
        log(f"scene {index:02d}/{len(project.scenes)} {name} ({duration:.2f}s)")

    if args.dialogue:
        spec = yaml.safe_load(args.dialogue.read_text(encoding="utf-8"))
        dialogue_dir.mkdir(parents=True, exist_ok=True)
        for line in spec.get("lines", []):
            speaker = int(line.get("speaker", args.speaker))
            signal, rate = synthesize(tts, line["text"], speaker=speaker,
                                      steps=args.steps, speed=speed)
            name = f"{spec.get('scene', 'scene')}_{line.get('role', 'line')}_speaker{speaker}.wav"
            path = dialogue_dir / name
            write_wav(path, signal, rate)
            duration, sample_rate = wav_info(path)
            entries.append({
                "file": f"dialogue/{name}",
                "kind": "dialogue_line",
                "scene": spec.get("scene"),
                "role": line.get("role"),
                "text": line["text"],
                "speaker": speaker,
                "speed": round(speed, 3),
                "duration_seconds": round(duration, 2),
                "sample_rate": sample_rate,
                "words": words(line["text"]),
                "sha256": sha256(path),
                "bytes": path.stat().st_size,
            })
            log(f"dialogue {name} ({duration:.2f}s, speaker {speaker})")

    timeline = None
    if not args.skip_timeline:
        timeline = outdir / "narration_full_120s.wav"
        details = narrate_project(project, timeline, speaker=args.speaker, steps=args.steps,
                                  speed=speed, threads=args.threads)
        log(f"timeline {timeline.name} ({details['duration_seconds']}s)")
        entries.append({
            "file": timeline.name,
            "kind": "timeline",
            "text": "continuous narration across all scenes, scene-aligned",
            "speaker": args.speaker,
            "speed": round(speed, 3),
            "duration_seconds": details["duration_seconds"],
            "sample_rate": details["sample_rate"],
            "sha256": sha256(timeline),
            "bytes": timeline.stat().st_size,
            "provenance_file": timeline.with_suffix(".voice.json").name,
        })
        mp3 = outdir / "narration_full_120s.mp3"
        if encode_mp3(timeline, mp3):
            entries.append({
                "file": mp3.name,
                "kind": "timeline_mp3",
                "duration_seconds": details["duration_seconds"],
                "sha256": sha256(mp3),
                "bytes": mp3.stat().st_size,
            })
            log(f"timeline mp3 {mp3.name}")

    manifest = {
        "package": "ghost-hassan-al-saghir",
        "spec": str(args.spec),
        "engine": "sherpa-onnx 1.13.8 + Supertone Supertonic 3 (third-party npm repack)",
        "weights_license": "OpenRAIL-M (see docs/voice-ar.md for attribution and use terms)",
        "voice_type": "fixed preset neural synthetic voice",
        "is_human_recording": False,
        "human_narration_required_for_human_claim": True,
        "note": "Synthetic speech. Not a human performance and not a voice clone. "
                "Audition pronunciation, pacing and mix before publishing.",
        "narrator_speaker": args.speaker,
        "delivery_speed": round(speed, 3),
        "steps": args.steps,
        "threads": args.threads,
        "sample_rate": 44100,
        "files": entries,
    }
    (outdir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                                          encoding="utf-8")
    log(f"wrote {outdir / 'manifest.json'} with {len(entries)} entries")
    log(f"done in {time.monotonic() - started:.1f}s")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ImportError, OSError, ValueError) as exc:
        print(f"Audio generation failed: {exc}", file=sys.stderr)
        raise SystemExit(2)
