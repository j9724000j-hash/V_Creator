# Implementation status — 2026-10-08

This is the progressively layered **0.1 core release**, not a claim that every aspirational item in the source brief is complete.

| Layer | Implemented | Verification / remaining work |
|---|---|---|
| Core CPU orchestration | Typed spec, brief template, explainable planner, FFmpeg/Pillow/ImageMagick, content cache, retry, lock, provenance, preview, QC | Unit + CPU end-to-end tests and 30s demo executed locally. |
| Audio | eSpeak/local file, procedural music/SFX, sidechain/EQ/limiter/fades/pan | Local eSpeak 1.52.0 tested; synthetic quality, single-pass loudness. No MIDI/FluidSynth rendering yet. |
| Captions | SRT/VTT, embedded and burned text, wrapping | Phrase-estimated timing; no forced alignment/animated word emphasis. |
| Remotion | Structured props CLI, scene composition, reusable caption/stat/lower-third/progress components | Typechecked + rendered using Chromium software mode. Needs explicit installation and license eligibility. |
| MoviePy | Optional v2 ImageClip adapter | Rendered a CPU clip in optional integration test (v2.2.1). |
| Manim | Optional Cairo CLI adapter + generic conceptual orbit | Not executed in this environment; requires Cairo/Pango. Not a universal scientific renderer. |
| Motion Canvas | Authoring/export template and docs | Editor project build tested; automated exporter not implemented. Isolated toolchain has outstanding npm advisories; see template README. |
| Godot / Unity | Inventory + extension/fallback contract | No engine export implementation; no engine/license installed. No fake headless rendering promises. |
| External providers | Typed request/result + explicit external-use guard | No ComfyUI/Replicate/cloud adapter implemented; zero API core works. |
| GitHub Actions | Test and render YAML, caches/artifacts/permissions | Local syntax checks only until real hosted run is observed. |

## Deliberate first-release limits

- Offline language parsing handles only topic/duration/aspect templates. The assistant authors factual content.
- Image assets only (one primary raster per scene); no media search/download, footage timeline or screenshot capture.
- Cut/fade; Ken Burns/vignette/grain. Advanced crossfades, pushes, light leaks, masks and general compositing are future presets.
- Generic scientific imagery must not substitute for accurate domain-specific animation.
- No automatic semantic quality check, no claim of professional broadcast QC or perfectly measured LUFS.
- Audio/final assembly rebuild each run; only scenes are incrementally cached. Resources are reported, not auto-tuned against GitHub billing quotas.
- No bundled external assets, GPU-only tools or paid service requirement.

## Acceptance evidence

See [verification.md](verification.md) for the actual commands, tool versions, test counts, output properties and environmental caveats. Outputs/logs are intentionally ignored by Git; CI artifacts or local output directories hold media.

## Next layers

1. Add full Python transitive lockfile and packaged config resources; streaming synthesis and measured two-pass loudness.
2. Expand semantic scene templates, asset reuse/search within the local library, forced-alignment captions and timeline transitions.
3. Test/generalize Manim; implement a pinned Motion Canvas exporter with genuine integration tests.
4. Add Godot offscreen export with a verified software renderer; Unity only with user-managed license/runtime and evidence of CPU feasibility.
5. Add explicitly authorized providers with real cost/limits/provenance tests. Never represent a protocol as a completed integration.
