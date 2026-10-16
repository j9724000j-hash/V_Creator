"""CLI: plan first, render only with explicit files, report missing natural voice."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

from .audio import generate_midi, generate_music
from .render import ROOT, ffmpeg, ffprobe, render, validate
from .spec import SpecError, load_project
from .voice_local import model_is_installed, narrate_project


def doctor() -> dict:
    def version(command: list[str]) -> str | None:
        try:
            p = subprocess.run(command, capture_output=True, text=True, timeout=10, check=False)
            if p.returncode == 0:
                return (p.stdout or p.stderr).splitlines()[0]
        except (OSError, subprocess.TimeoutExpired):
            pass
        return None

    venv = ROOT / ".venv"
    mem_gb = None
    if Path("/proc/meminfo").exists():
        mem_gb = round(int(Path("/proc/meminfo").read_text().splitlines()[0].split()[1]) / 1024**2, 2)
    disk_gb = round(shutil.disk_usage(ROOT).free / 1024**3, 2)
    return {
        "core": {
            "python": sys.version.split()[0],
            "ffmpeg": version([ffmpeg(), "-version"]),
            "ffprobe": version([ffprobe(), "-version"]) if ffprobe() else None,
            "pillow": importlib.util.find_spec("PIL") is not None,
            "numpy": importlib.util.find_spec("numpy") is not None,
            "arabic_reshaper": importlib.util.find_spec("arabic_reshaper") is not None,
            "arabic_fonts": (ROOT / "assets/fonts/NotoKufiArabic.ttf").is_file(),
            "sherpa_onnx": importlib.util.find_spec("sherpa_onnx") is not None,
            "supertonic_voice_weights": model_is_installed(),
        },
        "optional": {
            "imagemagick": version(["convert", "-version"]) if shutil.which("convert") else None,
            "node": version(["node", "-v"]) if shutil.which("node") else None,
            "hyperframes": (ROOT / "node_modules/.bin/hyperframes").exists(),
            "bundled_chromium": (ROOT / "node_modules/@sparticuz/chromium/bin/chromium.br").exists(),
            "silma_voice": (ROOT / ".venv-voice-silma/bin/python").exists(),
            "chatterbox_voice": (ROOT / ".venv-voice-chatterbox/bin/python").exists(),
            "kdenlive": shutil.which("kdenlive") is not None,
            "blender": shutil.which("blender") is not None,
            "manim": shutil.which("manim") is not None,
            "godot": shutil.which("godot") is not None,
        },
        "hardware": {"ram_gb": mem_gb, "free_disk_gb": disk_gb,
                     "gpu": shutil.which("nvidia-smi") is not None},
        "note": "Local Supertonic voice requires separately downloaded OpenRAIL-M weights. It is synthetic, not a human recording; audition before publication.",
    }


def plan(project) -> dict:
    return {
        "project": project.id, "duration": project.duration,
        "final_resolution": [project.width, project.height],
        "preview_resolution": list(project.resolution(True)), "fps": project.fps,
        "scenes": [
            {"id": s.id, "duration": s.duration, "intent": s.visual,
             "backend": "Pillow plate + FFmpeg zoompan/fades",
             "asset": str(s.image) if s.image else "deterministically generated original",
             "fallback": "Original scene plate if no image is provided"}
            for s in project.scenes
        ],
        "narration": {"required_for_final": project.narration_required,
                      "provided": bool(project.narration_path and project.narration_path.is_file()),
                      "policy": "human recording, licensed preset neural voice, or consensual clone; listen before release; no eSpeak/gTTS substitute"},
        "music": {"mode": project.music_mode, "mood": project.mood, "bpm": project.bpm,
                  "backend": "procedural WAV + editable MIDI" if project.music_mode == "procedural" else project.music_mode},
        "sound_effects": "original procedural whoosh and impact",
        "editing": "FFmpeg H.264/AAC, scene-level SRT, validation report and manifest",
        "motion": "HyperFrames available as an independent optional HTML/WAAPI backend",
    }


def main() -> int:
    parser = argparse.ArgumentParser(prog="v-creator", description="CPU-first cinematic video preparation")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor", help="Report required and optional installed tools")
    p_plan = sub.add_parser("plan", help="Validate spec and explain the offline render plan")
    p_plan.add_argument("spec", type=Path)
    p_render = sub.add_parser("render", help="Render a draft or a voice-gated final MP4")
    p_render.add_argument("spec", type=Path)
    p_render.add_argument("--out", type=Path)
    mode = p_render.add_mutually_exclusive_group()
    mode.add_argument("--preview", action="store_true", help="640px draft; natural voice may be missing (default)")
    mode.add_argument("--final", action="store_true", help="Full resolution; require voice when specified")
    p_render.add_argument("--narration", type=Path, help="Explicit human/consensual AI voice file (WAV, MP3, FLAC etc.)")
    p_validate = sub.add_parser("validate", help="Probe/decode an existing output video")
    p_validate.add_argument("spec", type=Path)
    p_validate.add_argument("file", type=Path)
    p_narrate = sub.add_parser("narrate", help="Generate offline Arabic voice from scene narration; no words are cut")
    p_narrate.add_argument("spec", type=Path)
    p_narrate.add_argument("--out", type=Path, required=True, help="Narration .wav path (provenance sidecar saved alongside)")
    p_narrate.add_argument("--speaker", type=int, choices=range(10), default=0, metavar="0..9")
    p_narrate.add_argument("--speed", type=float, default=1.0, help="0.7–1.5; prefer lengthening scenes over rushing voice")
    p_narrate.add_argument("--steps", type=int, choices=range(4, 13), default=8, metavar="4..12")
    p_narrate.add_argument("--threads", type=int, default=2, help="CPU threads (1–4)")
    p_music = sub.add_parser("music", help="Generate a short original procedural WAV + MIDI score")
    p_music.add_argument("output", type=Path)
    p_music.add_argument("--duration", type=float, default=15.0)
    p_music.add_argument("--bpm", type=int, default=72)
    p_music.add_argument("--mood", choices=["mysterious", "hopeful", "ominous"], default="mysterious")
    p_music.add_argument("--seed", type=int, default=2026)
    args = parser.parse_args()
    try:
        if args.command == "doctor":
            result = doctor()
        elif args.command == "plan":
            result = plan(load_project(args.spec))
        elif args.command == "render":
            project = load_project(args.spec)
            narration = args.narration.resolve() if args.narration else None
            if narration and (not narration.is_file() or narration.suffix.lower() not in {".wav", ".mp3", ".m4a", ".ogg", ".flac"}):
                raise SpecError(f"Explicit narration file missing or unsupported: {narration}")
            result = render(project, args.out or ROOT / "output" / project.id,
                            preview=not args.final, narrator_override=narration)
        elif args.command == "validate":
            result = validate(args.file, load_project(args.spec))
            if not result["ok"]:
                print(json.dumps(result, ensure_ascii=False, indent=2))
                return 1
        elif args.command == "narrate":
            result = narrate_project(load_project(args.spec), args.out,
                                     speaker=args.speaker, steps=args.steps,
                                     speed=args.speed, threads=args.threads)
        else:
            if not (0.75 <= args.duration <= 600 and 40 <= args.bpm <= 180):
                raise SpecError("music duration must be 0.75–600 seconds, BPM 40–180")
            generate_music(args.output, args.duration, args.bpm, args.mood, args.seed)
            midi = args.output.with_suffix(".mid")
            generate_midi(midi, args.duration, args.bpm)
            result = {"wav": str(args.output), "midi": str(midi), "license": "original/procedural"}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (SpecError, FileNotFoundError, ImportError, RuntimeError, subprocess.CalledProcessError, ValueError) as exc:
        print(f"V Creator: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
