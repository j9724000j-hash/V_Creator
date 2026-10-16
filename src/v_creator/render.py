"""Offline FFmpeg assembly with cached scenes, captions, stems and validation."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from typing import Any

import imageio_ffmpeg
from PIL import Image

from . import __version__
from .audio import generate_midi, generate_music, generate_sfx
from . import depth, parallax
from .spec import Project, Scene, SpecError
from .visuals import FONTS, make_overlay, make_plate

ROOT = Path(__file__).resolve().parents[2]


def ffmpeg() -> str:
    return imageio_ffmpeg.get_ffmpeg_exe()


def ffprobe() -> str | None:
    local = ROOT / ".venv/bin/ffprobe"
    return shutil.which("ffprobe") or (str(local) if local.is_file() else None)


def _run(args: list[str], log: Path, *, acceptable: set[int] | None = None) -> subprocess.CompletedProcess[str]:
    process = subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    with log.open("a", encoding="utf-8") as stream:
        stream.write("$ " + " ".join(repr(p) for p in args) + "\n")
        stream.write(process.stdout[-4000:] + process.stderr[-12000:] + "\n")
    if process.returncode not in (acceptable or {0}):
        raise RuntimeError(f"Media command failed (code {process.returncode}): {process.stderr[-2000:]}")
    return process


def probe_media(path: Path) -> dict[str, Any]:
    binary = ffprobe()
    if not binary:
        raise RuntimeError("ffprobe unavailable; run ./scripts/install.sh (Node 22 + npm required)")
    p = subprocess.run([binary, "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
                       capture_output=True, text=True, check=True)
    return json.loads(p.stdout)


def _digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as inp:
        for part in iter(lambda: inp.read(1024 * 1024), b""):
            h.update(part)
    return h.hexdigest()


def _hash_scene(scene: Scene, project: Project, resolution: tuple[int, int], preview: bool, *,
                motion: str = "kenburns", strength: float = 1.0, clean: bool = False) -> str:
    data = {
        "scene": {"id": scene.id, "title": scene.title, "caption": scene.caption,
                  "visual": scene.visual, "duration": scene.duration, "transition": scene.transition,
                  "camera": scene.camera},
        "image_sha256": _digest(scene.image) if scene.image else None,
        "code_sha256": [_digest(Path(__file__)), _digest(ROOT / "src/v_creator/visuals.py"),
                        _digest(ROOT / "src/v_creator/parallax.py"), _digest(ROOT / "src/v_creator/depth.py")],
        "font_sha256": [_digest(FONTS / "NotoKufiArabic.ttf"), _digest(FONTS / "NotoSansArabic.ttf")],
        "resolution": resolution, "fps": project.fps, "seed": project.seed,
        "preview": preview, "ffmpeg": ffmpeg(), "version": __version__,
        "motion": motion, "strength": strength, "clean": clean,
    }
    if motion == "depth":
        data["depth_model_sha256"] = depth.MODEL_SHA256
    return hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:20]


def _srt_time(seconds: float) -> str:
    millis = round(seconds * 1000)
    hours, millis = divmod(millis, 3600000)
    minutes, millis = divmod(millis, 60000)
    secs, millis = divmod(millis, 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"


def write_subtitles(project: Project, path: Path) -> None:
    cursor = 0.0
    lines = []
    for n, scene in enumerate(project.scenes, 1):
        lines += [str(n), f"{_srt_time(cursor)} --> {_srt_time(cursor + scene.duration)}", scene.caption, ""]
        cursor += scene.duration
    path.write_text("\n".join(lines), encoding="utf-8")


def _clip(scene: Scene, project: Project, n: int, width: int, height: int, cache: Path, preview: bool,
          log: Path, *, motion: str = "kenburns", strength: float = 1.0, clean: bool = False,
          estimator: "depth.DepthEstimator | None" = None) -> tuple[Path, Path, bool]:
    digest = _hash_scene(scene, project, (width, height), preview,
                         motion=motion, strength=strength, clean=clean)
    plate = cache / f"scene_{n:02}_{scene.id}_{digest}.png"
    video = cache / f"scene_{n:02}_{scene.id}_{digest}.mp4"
    if video.is_file() and video.stat().st_size > 1000:
        return plate, video, True
    duration = scene.duration
    count = round(duration * project.fps)
    if abs(count / project.fps - duration) > 0.001:
        raise SpecError(f"{scene.id}: duration must be a whole number of frames at {project.fps} fps")
    fade = min(0.22, duration / 7) if scene.transition == "fade" else None
    if motion == "depth" and scene.image is not None:
        if not depth.model_is_installed():
            raise SpecError("The depth camera move needs the local depth model; run "
                            "./scripts/install.sh (or .venv/bin/python scripts/install-depth-model.py). "
                            "Pass --motion kenburns to render without it.")
        overlay = None if clean else cache / f"overlay_{n:02}_{scene.id}_{digest}.png"
        if overlay is not None and not overlay.exists():
            make_overlay(scene, width, height, n, darken_image=True).save(overlay, optimize=True)
        dmap, _, _ = depth.cached_depth(scene.image, cache / "depth", estimator=estimator)
        with Image.open(scene.image) as source:
            base, small = parallax.fit_image_and_depth(source.convert("RGB"), dmap, width, height)
        camera = parallax.resolve_camera(scene.camera, n)
        parallax.encode_clip(
            parallax.frames(base, small, camera, count, strength=strength),
            width=width, height=height, fps=project.fps, count=count, out=video,
            ffmpeg=ffmpeg(), overlay=overlay, fade=fade, duration=duration,
            preview=preview, log=log)
        return plate, video, False
    if not plate.exists():
        make_plate(scene, plate, width, height, project.seed + n * 7919, n)
    # zoompan evaluates the expression once per frame, regardless of source still size.
    zoom = ("zoompan=z='min(zoom+0.00045,1.095)':x='(iw-iw/zoom)/2':"
            f"y='(ih-ih/zoom)/2':d=1:s={width}x{height}:fps={project.fps}")
    filters = [zoom, "format=yuv420p"]
    if fade:
        filters += [f"fade=t=in:st=0:d={fade:.3f}",
                    f"fade=t=out:st={max(0, duration-fade):.3f}:d={fade:.3f}"]
    _run([ffmpeg(), "-hide_banner", "-loglevel", "error", "-y",
          "-loop", "1", "-framerate", str(project.fps), "-i", str(plate),
          "-vf", ",".join(filters), "-frames:v", str(count),
          "-c:v", "libx264", "-preset", "ultrafast" if preview else "medium",
          "-crf", "27" if preview else "19", "-pix_fmt", "yuv420p",
          "-an", "-movflags", "+faststart", str(video)], log)
    return plate, video, False


def _concat_path(path: Path) -> str:
    # FFmpeg concat demuxer escaping (NOT shell interpolation).
    return "file '" + str(path).replace("'", "'\\''") + "'\n"


def _mix_and_mux(project: Project, timeline: Path, music: Path | None, effects: Path,
                 narrator: Path | None, out: Path, log: Path) -> None:
    cmd = [ffmpeg(), "-hide_banner", "-loglevel", "error", "-y", "-i", str(timeline)]
    duration = project.duration
    if music is None:
        cmd += ["-f", "lavfi", "-t", str(duration), "-i", "anullsrc=r=32000:cl=stereo"]
    elif project.music_mode == "file":
        cmd += ["-stream_loop", "-1", "-i", str(music)]
    else:
        cmd += ["-i", str(music)]
    cmd += ["-i", str(effects)]
    if narrator:
        cmd += ["-i", str(narrator)]
        parts = [
            f"[1:a]aresample=48000,atrim=duration={duration},asetpts=PTS-STARTPTS,volume=1.2[m]",
            f"[3:a]aresample=48000,highpass=f=80,acompressor=threshold=-20dB:ratio=2:attack=10:release=220,"
            f"apad,atrim=duration={duration},asetpts=PTS-STARTPTS,asplit=2[vduck][vmix]",
            "[m][vduck]sidechaincompress=threshold=0.02:ratio=4:attack=25:release=450[duck]",
            f"[2:a]aresample=48000,volume=1.0,atrim=duration={duration},asetpts=PTS-STARTPTS[s]",
            f"[duck][vmix][s]amix=inputs=3:duration=longest:dropout_transition=0:normalize=0,"
            f"alimiter=limit=0.88,atrim=duration={duration},"
            "loudnorm=I=-16:TP=-1.5:LRA=11[a]",
        ]
    else:
        parts = [
            f"[1:a]aresample=48000,atrim=duration={duration},asetpts=PTS-STARTPTS,volume=1.6[m]",
            f"[2:a]aresample=48000,volume=1.0,atrim=duration={duration},asetpts=PTS-STARTPTS[s]",
            f"[m][s]amix=inputs=2:duration=longest:dropout_transition=0:normalize=0,"
            f"alimiter=limit=0.88,atrim=duration={duration}[a]",
        ]
    cmd += ["-filter_complex", ";".join(parts), "-map", "0:v:0", "-map", "[a]",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
            "-t", str(duration), "-movflags", "+faststart", str(out)]
    _run(cmd, log)


def validate(path: Path, project: Project, *, decode: bool = True) -> dict:
    metadata = probe_media(path)
    streams = metadata.get("streams", [])
    v = next((s for s in streams if s["codec_type"] == "video"), None)
    a = next((s for s in streams if s["codec_type"] == "audio"), None)
    preview = path.name == "preview.mp4"
    width, height = project.resolution(preview)
    actual_duration = float(metadata.get("format", {}).get("duration", 0))
    fps = v.get("avg_frame_rate", "0/1") if v else "0/1"
    numerator, denominator = (int(p) for p in fps.split("/"))
    actual_fps = numerator / denominator if denominator else 0
    checks = {
        "video_h264": v is not None and v["codec_name"] == "h264",
        "audio_aac": a is not None and a["codec_name"] == "aac",
        "resolution": v is not None and (v["width"], v["height"]) == (width, height),
        "fps": abs(actual_fps - project.fps) < 0.04,
        "duration": abs(actual_duration - project.duration) <= max(0.3, len(project.scenes) / project.fps),
        "subtitle_sidecar": (path.parent / "subtitles.srt").is_file(),
    }
    decode_errors = ""
    if decode:
        process = subprocess.run([ffmpeg(), "-v", "error", "-i", str(path), "-f", "null", "-"],
                                 capture_output=True, text=True, check=False)
        decode_errors = process.stderr[-1000:]
        checks["decodes"] = process.returncode == 0
    return {
        "file": str(path), "ok": all(checks.values()), "checks": checks,
        "codec": {"video": v.get("codec_name") if v else None,
                  "audio": a.get("codec_name") if a else None},
        "width": v.get("width") if v else None, "height": v.get("height") if v else None,
        "fps": actual_fps, "duration": actual_duration, "decode_errors": decode_errors,
    }


def render(project: Project, out_dir: Path, *, preview: bool = True,
           narrator_override: Path | None = None, motion: str = "kenburns",
           strength: float = 1.0, clean: bool = False) -> dict:
    narrator = narrator_override or project.narration_path
    if narrator and not narrator.is_file():
        if preview:
            narrator = None
        else:
            raise SpecError(f"Narration audio is missing: {narrator}")
    if not preview and project.narration_required and not narrator:
        raise SpecError("Final render requires Arabic narration. Add a reviewed recording or licensed preset-voice WAV under the project, or pass --narration; no substitute is generated silently.")
    if project.music_mode == "file" and (not project.music_path or not project.music_path.is_file()):
        raise SpecError(f"Music file is missing: {project.music_path}")
    # Reject overlong narration before rendering either mode; never cut a sentence.
    if narrator:
        voice_duration = float(probe_media(narrator)["format"]["duration"])
        if voice_duration > project.duration + 0.12:
            raise SpecError(f"Narration ({voice_duration:.2f}s) exceeds the video ({project.duration:.2f}s); adjust scene timings.")
    voice_provenance = None
    if narrator:
        sidecar = narrator.with_suffix(".voice.json")
        if sidecar.is_file():
            if sidecar.stat().st_size > 64_000:
                raise SpecError(f"Voice provenance sidecar is too large: {sidecar}")
            try:
                declared = json.loads(sidecar.read_text(encoding="utf-8"))
            except (ValueError, UnicodeError) as exc:
                raise SpecError(f"Invalid voice provenance sidecar: {sidecar}") from exc
            if not isinstance(declared, dict) or declared.get("output") != str(narrator.resolve()):
                raise SpecError(f"Voice provenance sidecar does not match the audio path: {sidecar}")
            voice_provenance = {
                "declared_engine": declared.get("engine"), "declared_model": declared.get("model"),
                "declared_license": declared.get("weights_license"),
                "declared_synthesis_type": declared.get("synthesis_type"),
                "declared_model_install_manifest_sha256": declared.get("model_install_manifest_sha256"),
                "source_sha256": _digest(narrator), "sidecar": str(sidecar),
            }
    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    log = out_dir / "render-log.txt"
    log.write_text(f"V Creator {__version__} | {datetime.now(timezone.utc).isoformat()}\n", encoding="utf-8")
    cache = out_dir / "cache"
    cache.mkdir(exist_ok=True)
    width, height = project.resolution(preview)
    subtitles = out_dir / "subtitles.srt"
    write_subtitles(project, subtitles)
    records = []
    clips = []
    cursor = 0.0
    estimator = depth.DepthEstimator() if motion == "depth" and depth.model_is_installed() else None
    for n, scene in enumerate(project.scenes, 1):
        plate, clip, hit = _clip(scene, project, n, width, height, cache, preview, log,
                                 motion=motion, strength=strength, clean=clean, estimator=estimator)
        clips.append(clip)
        moved = motion == "depth" and scene.image is not None
        records.append({
            "id": scene.id, "title": scene.title, "start": cursor,
            "duration": scene.duration,
            "selected_tool": ("Depth Anything V2 Small (ONNX) + OpenCV parallax + FFmpeg" if moved
                              else "Pillow + FFmpeg"),
            "selection_reason": ("Single still + monocular depth map -> 2.5D CPU camera move" if moved
                                 else "Original/owned image plate with a CPU Ken Burns camera move"),
            "motion": ("depth-parallax:" + parallax.resolve_camera(scene.camera, n)) if moved
                      else "kenburns-zoom",
            "overlay": "none (clean)" if clean and moved else ("title overlay" if moved else "baked into plate"),
            "image": str(scene.image) if scene.image else str(plate),
            "image_source": scene.image_source if scene.image else "locally generated",
            "image_license": scene.image_license if scene.image else "original/generated",
            "cache_hit": hit})
        cursor += scene.duration
    concat_file = cache / "clips.txt"
    concat_file.write_text("".join(_concat_path(c) for c in clips), encoding="utf-8")
    timeline = cache / f"{project.id}_{'preview' if preview else 'final'}_timeline.mp4"
    _run([ffmpeg(), "-hide_banner", "-loglevel", "error", "-y", "-f", "concat",
          "-safe", "0", "-i", str(concat_file), "-c", "copy", str(timeline)], log)
    audio_version = _digest(ROOT / "src/v_creator/audio.py")[:12]
    music = None
    if project.music_mode == "procedural":
        music = cache / f"music_{project.mood}_{project.bpm}_{project.seed}_{project.duration:.2f}_{audio_version}.wav"
        if not music.exists():
            generate_music(music, project.duration, project.bpm, project.mood, project.seed)
        midi = out_dir / "score.mid"
        generate_midi(midi, project.duration, project.bpm)
    elif project.music_mode == "file":
        music = project.music_path
    scene_starts = [r["start"] for r in records]
    cue_hash = hashlib.sha256(json.dumps(scene_starts).encode("utf-8")).hexdigest()[:8]
    effects = cache / f"effects_{project.seed}_{project.duration:.2f}_{cue_hash}_{audio_version}.wav"
    if not effects.exists():
        generate_sfx(effects, project.duration, scene_starts, seed=project.seed)
    output = out_dir / ("preview.mp4" if preview else "final.mp4")
    _mix_and_mux(project, timeline, music, effects, narrator, output, log)
    report = validate(output, project)
    (out_dir / "validation-report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    manifest = {
        "project_id": project.id, "specification": str(project.spec_path),
        "source_spec_sha256": _digest(project.spec_path),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "preview" if preview else "final", "output": str(output),
        "resolution": [width, height], "fps": project.fps, "duration": project.duration,
        "scenes": records,
        "audio": {
            "narration": {"status": "provided" if narrator else "missing; preview only" if project.narration_required else "none",
                          "source": str(narrator) if narrator else None,
                          "provenance": voice_provenance,
                          "consent_required_for_cloned_voice": True},
            "music": {"mode": project.music_mode, "source": str(music) if music else None,
                      "origin": project.music_source if project.music_mode == "file" else "locally generated",
                      "license": project.music_license if project.music_mode == "file" else "original/procedural"},
            "effects": {"source": str(effects), "license": "original/procedural"},
        },
        "tools": {"v_creator": __version__, "ffmpeg": ffmpeg(),
                  "ffprobe": ffprobe(), "hyperframes": "separate optional motion backend",
                  "motion": {"mode": motion, "strength": strength, "clean_overlay": clean},
                  "depth_model": {"label": depth.MODEL_LABEL, "sha256": depth.MODEL_SHA256,
                                  "runtime": "onnxruntime (CPU)",
                                  "installed": depth.model_is_installed()} if motion == "depth" else None},
        "validation": report,
        "note": "Subtitles are timed to scenes, NOT word-aligned to a voiceover. Review Arabic pronunciation and mix by ear before publishing.",
    }
    (out_dir / "production-manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if not report["ok"]:
        raise RuntimeError(f"Validation failed: {report['checks']}")
    return manifest
