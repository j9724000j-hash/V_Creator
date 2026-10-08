# Pipeline and specification

1. `create` produces an editable template, never factually researched narration. Assistant writes the script in YAML.
2. `load` validates shapes, bounds, finite numeric values, unique IDs, total/frame durations, local asset existence and traversal safety.
3. `plan` runs without creating media. Prefer/override/enable settings control backend selection.
4. Resolve preset, generate semantic hash-named raster/SVG assets and normalize with ImageMagick when installed.
5. Render changed scenes, retry once on backend failure, then optional explicit approximation. Strict overrides never fall back. Cache stores actual backend and errors.
6. Generate/fix narration timing, synthesize seeded music/SFX, duck and master audio.
7. Write SRT/VTT. Captions distribute phrases over scene duration; there is no forced alignment.
8. Concat with stream copy. Burn captions only when requested; otherwise preserve video with stream copy in final mux. H.264/AAC fast-start MP4, optional mov_text subtitle track.
9. Full decode/ffprobe checks. Write report and manifest; make low-resolution preview.

## Supported spec fields

See `config/video.schema.json` for exact enums/defaults and `videos/example/video.yaml` for a complete example.

- `video`: ID, title, dimensions, FPS, duration; `style` is descriptive metadata, not arbitrary effect code.
- `scene`: ID, duration, type, intent, visual_description, title, narration, optional captions override (`""` disables), optional one local raster `assets` entry, local `narration_asset`, tool, allow_fallback, transition (cut/fade), effect (none/ken_burns/vignette/grain), audio_cues, quality, chart values. Nonempty custom constraints are rejected until an adapter supports them.
- Assets: project-relative `path`, nonempty `source`, nonempty `license`. No URLs are fetched. Raster assets are Pillow-readable images; SVG is generated/exported but not accepted as an arbitrary untrusted input raster. No arbitrary Python/JS is read from YAML.
- Audio: narration/music/sound_effects booleans, missing_tts policy, voice, speaking_rate, target_loudness, bpm, key, mood, intensity, music_gain, reverb.
- Render: preset, threads 1–8, keep_intermediates, burn_captions.
- Planner: prefer ordered list, enable list. `ffmpeg` remains the reliable baseline.

Scene fades are **dip-to-black**, not overlapping dissolves, so specified durations remain additive. Whole-frame durations are enforced; draft presets round boundaries and record the effective spec. Cues that no longer fit after rounding fail validation rather than being silently moved.

## Incremental work

Key material: scene spec, source asset hash, effective dimensions/FPS, render settings, selected engine/version, implementation/theme hashes. Per-scene keys do not depend on other scenes' script/title. Corrupt cache entries re-render. Audio/manifest/final composition regenerate on every run. `clean --yes` removes caches/work only; final outputs remain.

Generated source/props/voice files reside in `work/` or scene cache; `--no-keep-intermediates` removes `work/`, not reusable scene caches. The manifest records whether referenced intermediates were retained.
