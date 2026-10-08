# Architecture

The checkout is the deployment unit; editable Python installation keeps shared config/backend projects discoverable. `Spec` is a Pydantic v2 typed boundary. CLI/project validation rejects unsupported fields and unsafe filenames. `config/video.schema.json` is generated from these models; `config/defaults.yaml` is a human-readable reference, not a second competing settings source.

`planner.plan()` maps intent and user overrides to enabled, installed and implemented adapters. An optional engine's presence alone does not opt it in. Every decision records the requested/selected tool, reason and approximation. Nontrivial simulation cannot fall back without a supplied asset. `allow_fallback: false` fails closed. The engine registry includes licensing, install method, support state, fallbacks and CPU compatibility; extension entries are never invoked as fictitious commands.

`Context`/`Backend` form the scene interface. A backend receives validated scene data, a raster asset and output settings, and must return constant-frame-rate H.264. Browser output is normalized to limited-range YUV420 with no scene audio. Final audio is handled centrally. Remotion has structured props and reusable React components. Core uses Pillow with optional ImageMagick, then FFmpeg.

Build graph: source spec → asset hashes → scene cache → concat; script → TTS; seed/settings → music/SFX; buses → master; scene timeline + master + captions → encoded deliverable → QC → manifest. Nodes run sequentially; expensive scene rendering is incremental. Audio/mux are intentionally rebuilt, not falsely advertised as cached.

A project lock prevents concurrent writers; subprocesses are argv lists with timeouts (never shell evaluation). Output paths are resolved inside the project. Scene outputs are staged before cache publication, hashes detect corruption, final.mp4 is only replaced after validation. Logs/failure reports preserve diagnostics. Cache uses implementation hashes; modifying unrelated implementation may conservatively invalidate all scenes.

Limits: not a distributed scheduler, semantic NLP engine or general 3D simulator. Python API accepts trusted caller paths; the CLI confines projects to the checkout. Executable source/adapters are trusted code, not sandboxed plugins. User asset files should be trusted or inspected before decoding.
