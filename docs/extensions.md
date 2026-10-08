# Extension contracts: engines and providers

Implement a `Backend.render(Context) -> None` adapter to produce an exact scene video. Requirements:
- CPU feasibility checked; explicit optional install/license detection.
- No network, browser downloads, user script execution or credentials in scene YAML.
- Frame-accurate duration, dimensions/FPS, H.264 limited-range yuv420p, no scene audio, consistent sample aspect/time base (90 kHz).
- Subprocess argv through Runner, timeout, logged errors and an actual CPU integration test.
- Declare intent mapping, allow_fallback semantics and actual implementation status in registry/planner.
- Normalize engine output once at the adapter boundary. Do not stream-copy incompatible streams.

## Godot

Do not assume `--headless` produces usable 3D viewport pixels: a headless/dummy rendering driver may not render them. A real adapter needs a project with a verified offscreen/software graphics path, deterministic timestep, frame readback and image-sequence encoding. Resource feasibility on GitHub runners must be demonstrated. Registry detection is not a completed exporter.

## Unity

License activation, project version, Editor installation and software-rendering feasibility are user-managed. Batch mode is not synonymous with GPU-free rendering. No activation credentials/services are built in. An adapter must be optional and tested on a properly licensed setup; otherwise fail or use an explicitly acceptable pre-rendered raster. Core cannot represent general simulation output with a generic title card.

## Providers

`providers.Provider` returns `Result` with existing path, source, license, provider and model; `invoke` rejects external use unless Request.allow_external is true. No stock downloader or external generator is wired in this release. Providers must validate their own output path/content, avoid URL/credential logging, document costs, bound retries and prevent implicit downloads. Keep API secrets in environment variables or GitHub Secrets, never specs/Git.

This design is intentionally a tested core plus honest extension boundary, not a set of placeholder methods pretending to support unavailable engines.
