# Verification record — 2026-10-08

These are actual local results, not a promise that all optional integrations work.

## Executed successfully

- `scripts/install.sh` (venv + pinned Python dependencies + editable install + doctor), with explicit executable environment overrides for sandbox-installed FFmpeg/ffprobe/eSpeak. Required tool registry validated.
- `python -m pytest -q`: **33 passed**, including core CPU end-to-end rendering, cache reuse, per-scene changes, corrupt-cache recovery, explicit missing-TTS error, schema/path safety, command construction, provider opt-in, narration, Remotion and MoviePy CPU clips. No tests skipped in the fully configured local run.
- `npm run typecheck`: passed on pinned Remotion **4.0.534** / TypeScript 5.9.2.
- Remotion CLI rendered actual frames with Chromium **138** software rendering, then normalized H.264/YUV420 output. Not merely mocked.
- MoviePy **2.2.1** rendered an actual one-second clip.
- eSpeak NG **1.52.0** built locally from official tagged source and produced narration used by the example.
- ImageMagick **6.9.11-60** normalized generated raster assets.
- FFmpeg/ffprobe **5.0-static**, libx264/libass-capable CPU build, performed composition, xfade transitions, audio processing and full decode validation.
- Motion Canvas optional template built successfully; its `start` script is intentionally omitted because the toolchain still has legacy advisories. This is editor-template evidence only, not automated video export.
- `npm audit` in repository root: **0 reported vulnerabilities** at verification time. This is a point-in-time dependency advisory check, not a security guarantee.
- Both Actions YAML files parsed successfully; bash wrapper scripts syntax-checked. An actionlint binary download was blocked by sandbox network restrictions, so **actionlint/hosted workflow success is not claimed here**.
- `.gitignore` checked for generated outputs, caches, downloaded tools, virtualenv and node_modules. No video, tool binary or credential included in tracked deliverables.

## Example output

Command: `scripts/render.sh videos/example --preset standard`, followed by `scripts/validate.sh videos/example`.

- Duration: **29.967 / 30.000 seconds** within 1-frame rounding tolerance.
- Dimensions: **1080 × 1920**.
- FPS: **30**, constant, **899/900 frames** (one-frame rounding tolerance accepted for transitions).
- Video: H.264, YUV420p.
- Audio: AAC, 48 kHz stereo; actual local eSpeak narration + original procedural music/SFX.
- Transitions: dip-to-black, wipe right, slide right, zoom, with distinct visual effect presets per scene.
- Captions: burned plus embedded mov_text, separate SRT/VTT.
- QC: codec, dimensions, FPS, frame count, constant rate, duration, A/V sync, subtitles and full video/audio decode **passed**; initial render also checks scene outputs/assets.
- Manifest: source/effective specs, actual tools, versions, scene cache metadata, asset/audio hashes, warnings and validation state.
- A representative frame during transitions was visually inspected for layout/readability. This does not certify every frame or perceptual audio quality.

## Environment caveats

The sandbox blocks Ubuntu apt hosts and some release/browser download domains. System apt installation could not be exercised here; it remains the normal Ubuntu/GitHub runner path. Local testing used explicit ignored tools from GitHub/npm and a source-built TTS engine, not weakened TLS or committed binaries. Reproducible runtime requires installing those dependencies in your environment.

Manim was not executed: the current checkout has a local `manim/` adapter folder, which shadows ManimCommunity package imports in Python unless installed separately with Cairo/Pango. Godot, Unity, hosted GitHub Actions and external AI providers were not executed. See status.md and the optional template README before enabling any extension.
