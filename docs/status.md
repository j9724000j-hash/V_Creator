# Implementation status — 2026-10-08

This is a progressively layered **0.2 core-and-enhancement release**, not a claim that every aspirational item in the source brief is complete.

## Status table

| Layer | Implemented | Verification / remaining work |
|---|---|---|
| Core CPU orchestration | Typed spec, brief template, explainable planner, FFmpeg/Pillow/ImageMagick, content cache, retry, lock, provenance, preview, QC, explicit overrides/fallbacks | 33 local tests passed, including CPU smoke and corrupt-cache recovery. |
| Transitions | cut, fade/crossfade, dip_to_black/white, slide, wipe, circle/vert/horz open/close, dissolve, pixelize, zoom, blur, diagonals, squeezes, grays/radial/smooth aliases | Verified with FFmpeg xfade durations; AV-synced final encodes. |
| Visual effects | Ken Burns, vignette, grain, glow, film grain, scanlines, chroma split approximation, color grade, sharpen, light leak | Implemented as named FFmpeg presets, validated via command construction + render smoke. |
| Audio | eSpeak/local file, procedural music/SFX, sidechain/EQ/limiter/fades/pan | Local eSpeak 1.52.0 tested; synthetic quality, single-pass loudness. No MIDI/FluidSynth rendering yet. |
| Captions | SRT/VTT, embedded and burned captions, wrapping, safe margins, readable outline/shadow defaults | Phrase-estimated timing; no forced alignment/animated word emphasis. |
| Remotion | Structured props CLI, scene composition, reusable Caption, LowerThird, SectionHeader, QuoteCard, StatCard, Arrow, Progress components with motion accents | Typechecked + rendered using Chromium software mode. Needs explicit installation and license eligibility. |
| MoviePy | Optional v2 ImageClip adapter | Rendered a CPU clip in optional integration test. |
| Manim | Optional Cairo CLI adapter + generic conceptual orbit | Not executed here because local Python `manim` is our source folder, not ManimCommunity. Install real Manim with Cairo/Pango, then retest. |
| Motion Canvas | Authoring/export template and docs | Editor project build tested; automated exporter not implemented. Isolated toolchain has documented upstream advisories and no exposed dev-server script. |
| Godot / Unity | Inventory + extension/fallback contract | No engine export implementation; no engine/license installed. No fake headless rendering promises. |
| External providers | Typed request/result + explicit external-use guard | No ComfyUI/Replicate/cloud adapter implemented; zero API core works. |
| GitHub Actions | Test and render YAML, caches/artifacts/permissions/updated action versions | First CI run succeeded after initial push; local actionlint binary unavailable in this sandbox. |

## Deliberate release limits

- Offline language parsing handles only topic/duration/aspect templates. The assistant authors factual content.
- Image assets only (one primary raster per scene); no media search/download, footage timeline or screenshot capture.
- 20+ CPU transitions and effects are implemented; motion blur, particles, glitch mask reveals and general compositing remain future presets.
- Generic scientific imagery must not substitute for accurate domain-specific animation.
- No automatic semantic quality check, no claim of professional broadcast QC or perfectly measured two-pass LUFS.
- Audio/final assembly rebuild each run; only scenes are incrementally cached. Resources are reported, not auto-tuned against GitHub billing quotas.
- No bundled external assets, GPU-only tools or paid service requirement.

## Acceptance evidence

See [verification.md](verification.md) for the actual commands, tool versions, test counts, output properties and environmental caveats. Outputs/logs are intentionally ignored by Git; CI artifacts or local output directories hold media.

## Next layers

1. Two-pass measured loudness and better caption timing.
2. Test/generalize Manim after verified installation; implement a pinned Motion Canvas exporter with official API integration tests.
3. Add Godot offscreen export with a verified software renderer; Unity only with user-managed license/runtime and evidence of CPU feasibility.
4. Add explicitly authorized providers with real cost/limits/provenance tests. Never represent a protocol as a completed integration.
