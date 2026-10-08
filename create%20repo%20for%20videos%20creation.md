# Hyper-Professional Prompt — Create the Ultimate CPU-Only, GitHub-Ready Video Creation Repository

You are an expert software architect, DevOps engineer, multimedia engineer, generative-media pipeline designer, motion-graphics engineer, audio engineer, and GitHub Actions specialist.

Your task is to **design and build a complete, production-oriented video-creation repository on GitHub** that I can control primarily through natural-language instructions to you.

The repository must be designed so that, after the initial setup, I can give you a request such as:

> "Create a 60-second vertical 1080x1920 video about black holes, cinematic, educational, dramatic, with narration, captions, background music, sound effects, transitions, and professional visual effects."

You must then use the repository as a **general-purpose automated video production studio**: analyze the request, decide which tools and assets are required, generate or create the necessary assets, render every scene, compose the complete video, perform audio mixing and visual finishing, validate the output, and deliver the final video artifact.

The repository must be **modular, deterministic where possible, CPU-first, GitHub-friendly, reproducible, and designed to avoid paid services by default**.

---

# 1. Core Mission

Build a repository that acts as an **automated multi-engine video production framework**, not merely a collection of scripts.

The framework must:

1. Accept a high-level natural-language video brief.
2. Convert the brief into a structured video production specification.
3. Analyze the video requirements.
4. Decide which tools are appropriate for each scene and task.
5. Decide whether images, illustrations, diagrams, animations, or other visual assets are needed.
6. Create missing assets using the best available method.
7. Generate scene-level media.
8. Assemble scenes into a coherent timeline.
9. Add narration, captions, music, sound effects, transitions, overlays, motion graphics, and visual effects as appropriate.
10. Perform professional audio and video post-processing.
11. Validate the final output technically.
12. Produce the final MP4 and a machine-readable production manifest.
13. Preserve intermediate files when useful for debugging/reproducibility.
14. Allow the same pipeline to run locally and in GitHub Actions.
15. Be usable by a non-expert primarily through natural-language commands to the connected AI assistant.

The system must **not blindly use every tool in every video**. It must select tools based on the requirements of each scene.

---

# 2. Critical Design Principle

Use the following rule throughout the architecture:

> **Use the simplest reliable tool that can produce the required result at professional quality.**

Never use a heavyweight engine when a simpler tool is sufficient.

Examples:

- Use FFmpeg for straightforward media processing instead of Python.
- Use ImageMagick for straightforward image operations instead of a heavier graphics pipeline.
- Use Remotion for text, UI-like graphics, captions, compositing, and general programmatic motion design.
- Use MoviePy when Python-based media logic is genuinely useful.
- Use Manim for mathematical/scientific visualizations.
- Use Motion Canvas for motion-graphics and diagram-heavy scenes when it is the better fit.
- Use Godot for procedural 2D/3D/game-like simulation scenes when its capabilities are justified.
- Use Unity only when a scene specifically benefits from Unity's ecosystem/capabilities; keep it optional, never a mandatory dependency.
- Use FFmpeg as the final media-processing and encoding backbone.

---

# 3. Required Tool Ecosystem

The repository must support the following tools as first-class optional backends where technically practical:

## Video / Media Processing

### FFmpeg
Use as the primary media-processing backbone for:

- video conversion
- concatenation
- trimming
- scaling
- cropping
- frame-rate conversion
- codec selection
- audio mixing
- loudness normalization
- subtitles
- overlays
- fades
- transitions
- muxing/demuxing
- image-sequence encoding
- final delivery encoding
- metadata handling
- quality validation

### ImageMagick
Use for:

- image resizing
- cropping
- format conversion
- raster processing
- compositing
- masks
- text rendering
- thumbnails
- frames
- image-sequence preparation
- simple effects
- asset normalization

### MoviePy
Support it as a Python video-processing backend for tasks where Python-level logic is advantageous.

### Remotion
Use as the primary programmable-video/motion-composition backend for:

- titles
- captions
- lower thirds
- animated text
- charts
- UI visuals
- image sequences
- compositing
- transitions
- timing
- scene layouts
- reusable React-based visual components
- full video compositions

The repository must support CLI-based Remotion rendering with a structured props/specification system.

### Motion Canvas
Support it for:

- motion graphics
- diagrams
- technical explanations
- animated UI-style visuals
- timelines
- vector-oriented animation
- scene-level motion design

### Manim
Support it for:

- mathematical animation
- scientific visualization
- equations
- graphs
- geometric explanations
- physics/engineering concepts

### Godot
Support it as an optional rendering backend for:

- 2D procedural scenes
- 3D scenes
- physics/simulation
- game-like visualizations
- procedural worlds
- scenes that are difficult or inefficient to implement in the other engines

### Unity
Support it as an optional backend only.

Requirements:

- Must not be a mandatory installation for normal videos.
- Must be detected as optional.
- The framework must gracefully skip Unity when it is not required or not available.
- Do not assume a Unity license is equivalent to an unlimited/open-source dependency.
- Do not make the core system depend on Unity-specific services.

---

# 4. Audio Production Layer

The final system must treat audio as a first-class production domain.

Create a dedicated audio subsystem capable of:

- narration/voice tracks
- background music
- sound effects
- ambience
- risers
- impacts
- whooshes
- clicks
- UI sounds
- transitions
- reverb
- delay
- EQ
- compression
- limiting
- normalization
- ducking
- fades
- stereo positioning when appropriate
- synchronization to visual events
- final mastering

The audio subsystem must be CPU-friendly.

Where possible, favor **open-source/local/procedural approaches** rather than paid APIs.

Consider and evaluate CPU-friendly open-source command-line audio utilities/libraries such as:

- SoX
- FFmpeg audio filters
- eSpeak NG or another local/open-source TTS engine when suitable
- FluidSynth
- TiMidity++
- Python-based procedural sound synthesis
- Python audio analysis/manipulation libraries

Do not add a dependency merely because it exists. Test or document why each dependency is useful.

---

# 5. Music Generation Requirements

The repository must provide a practical way to create background music **without requiring a GPU and without requiring a paid online generation service**.

Preferred strategies:

1. Procedural music generation.
2. MIDI generation.
3. Locally generated musical patterns.
4. MIDI rendering through FluidSynth/TiMidity++.
5. Programmatic arrangement using open-source tools.
6. Optional adapters for external/local generators only when clearly marked as optional.

The system should support concepts such as:

- mood
- BPM
- key
- intensity
- structure
- intro
- build
- climax
- outro
- loopable music
- duration fitting
- volume ducking under narration

Do not claim AI music generation is "free and unlimited" unless that claim is actually verified for the exact implementation.

---

# 6. Sound Effect Generation

Provide a CPU-friendly SFX subsystem that can generate or synthesize effects such as:

- whoosh
- hit
- impact
- bass drop
- click
- pop
- glitch
- notification
- riser
- sweep
- ambience
- wind
- rain
- mechanical tones
- sci-fi effects
- transition effects

Prefer procedural/open-source generation where practical, so the system does not depend on copyrighted commercial SFX packs.

Create reusable SFX templates and a parameterized procedural sound generator where useful.

---

# 7. Image / Asset Generation

The pipeline must be able to determine whether a scene needs:

- existing local assets
- generated illustrations
- procedural SVG
- diagrams
- charts
- icons
- shapes
- screenshots
- textures
- image sequences

The planner must decide this automatically.

Create an asset layer that can:

1. Search the existing project's asset library.
2. Reuse existing assets when appropriate.
3. Create SVG/vector graphics programmatically.
4. Generate raster images with CPU-friendly/local methods when feasible.
5. Invoke an optional external image-generation adapter if explicitly configured.
6. Record the source and generation method of every asset.
7. Give deterministic, collision-safe file names.

Example:

```text
assets/
  images/
    scene_001/
      black_hole_hero.png
      black_hole_accretion_disk.png
  diagrams/
    scene_003/
      event_horizon.svg
```

Never silently replace a generated asset with an unverified external image.

---

# 8. Optional AI Provider Architecture

The architecture must support adapters/providers without making them mandatory.

Design an interface such as:

```text
providers/
  images/
  video/
  audio/
  tts/
```

Potential providers may be added later.

Examples include:

- local/open-source generation
- Replicate
- ComfyUI
- other user-configured services

However:

- external providers must be OPTIONAL
- no paid service may be required for the core repository
- API keys must never be committed
- all external usage must be explicit/configurable
- provider limitations must be documented
- the system must work in a "zero external API" mode whenever possible

Do not hardcode provider credentials.

Use environment variables / GitHub Actions Secrets.

---

# 9. No-GPU / CPU-First Requirement

This is a hard architectural requirement for the core pipeline.

The repository must be able to run on ordinary CPU-based GitHub-hosted Linux runners for its core functionality.

The system must:

- detect available CPU/RAM/disk resources
- avoid GPU-only dependencies in the core path
- provide graceful degradation
- choose lightweight render modes when resources are constrained
- cache dependencies where possible
- avoid unnecessary parallelism
- expose quality/performance presets

Example presets:

```text
draft
preview
standard
high
```

The planner may automatically choose a lower-cost mode for very heavy scenes.

Never pretend that all rendering workloads are equally practical on CPU.

For heavy 3D or complex simulations, use optional backends or optimized scene settings.

---

# 10. GitHub Free Compatibility

Design the repository specifically for GitHub Free usage.

The system must:

- work from GitHub Actions
- support manual workflow dispatch
- support repository-triggered rendering
- minimize redundant installation
- use caching correctly
- avoid storing large binary outputs in Git
- upload final renders as GitHub Actions artifacts
- provide logs and diagnostics
- make tool installation modular
- avoid requiring paid GitHub features
- keep workflows as simple and maintainable as possible

Important:

Do NOT claim that "GitHub Free" means unlimited compute, storage, or execution time.

The repository must detect/communicate practical GitHub limits.

Separate:

1. software licensing
2. GitHub Actions usage limits
3. runner CPU/RAM/disk constraints
4. artifact/storage limitations
5. third-party API limits

The README must clearly explain these distinctions.

---

# 11. Video Specification / DSL

Create a clean, machine-readable video specification format.

Use JSON or YAML, preferably YAML for human readability, while allowing JSON input too.

Example concept:

```yaml
video:
  id: black-hole
  title: "Black Holes Explained"
  duration: 60
  width: 1080
  height: 1920
  fps: 30
  style:
    tone: cinematic
    pacing: energetic
    color_mood: dark_space
    typography: modern

audio:
  narration: true
  music: true
  sound_effects: true
  target_loudness: "-14 LUFS"

scenes:
  - id: intro
    duration: 4
    type: title

  - id: space_visual
    duration: 8
    type: cinematic_visual

  - id: physics
    duration: 12
    type: scientific_animation

  - id: diagram
    duration: 8
    type: explanatory_diagram
```

The system must allow each scene to include:

- duration
- intent
- visual description
- narration
- captions
- assets
- transitions
- audio cues
- preferred tool
- constraints
- quality settings

But the user should not have to specify the tool unless they want to override the planner.

---

# 12. Automatic Scene Planner

Build a planner that maps scene requirements to tools.

Example:

```text
text-heavy motion scene
    -> Remotion

scientific visualization
    -> Manim

motion-graphics diagram
    -> Motion Canvas or Remotion

simple image preparation
    -> ImageMagick

Python algorithmic effect
    -> MoviePy / Python

simple media transformation
    -> FFmpeg

2D/3D simulation
    -> Godot

specialized 3D/game-engine scene
    -> Unity (optional)
```

The planner must be explainable.

For every scene, create a machine-readable plan such as:

```json
{
  "scene_id": "physics",
  "selected_tool": "manim",
  "reason": "Mathematical animation with equations and vector geometry",
  "fallback": "remotion"
}
```

This prevents opaque behavior and makes debugging easier.

---

# 13. Scene-Level Modularity

Each scene must behave like a self-contained production unit.

Concept:

```text
scene/
  manifest.yaml
  assets/
  source/
  render/
  audio/
  preview/
```

A scene should be independently re-renderable.

If scene 7 changes, do not unnecessarily regenerate scenes 1–6.

Implement dependency-aware caching.

---

# 14. Reproducible Build System

Create a build graph so that the system understands:

```text
script
   ↓
assets
   ↓
scene
   ↓
audio
   ↓
composition
   ↓
final encoding
```

Each generated file should have:

- deterministic path
- source metadata
- optional hash
- generation timestamp
- tool/version metadata

Support commands such as:

```bash
./scripts/render.sh videos/example
./scripts/preview.sh videos/example
./scripts/validate.sh videos/example
./scripts/clean.sh videos/example
```

Also expose a Python CLI:

```bash
python -m video_factory render videos/example
python -m video_factory preview videos/example
python -m video_factory validate videos/example
python -m video_factory plan videos/example
python -m video_factory doctor
```

---

# 15. Automatic Naming and Asset Management

Never create random names such as:

```text
image1.png
image2.png
final2.mp4
newfinal.mp4
```

Use semantic names:

```text
scene_001_black_hole_intro.png
scene_002_accretion_disk.png
scene_003_event_horizon_diagram.svg
scene_004_physics_animation.mp4
```

Generate names from scene IDs and roles.

Prevent collisions and accidental overwrites.

---

# 16. Professional Visual Design System

Create reusable visual primitives/components for:

- titles
- subtitles
- captions
- lower thirds
- quote cards
- section headers
- progress bars
- charts
- diagrams
- callouts
- labels
- icons
- arrows
- timelines
- statistic cards
- transitions
- cinematic overlays

Use a centralized theme:

```text
brand/
  colors
  typography
  spacing
  motion
  caption styles
  safe areas
```

The video planner should support a consistent visual identity across all scenes.

---

# 17. Transitions

Create reusable transition presets such as:

- cut
- fade
- crossfade
- dip to black
- dip to white
- slide
- push
- zoom
- wipe
- blur transition
- whip transition
- light flash
- glitch transition

Do not overuse transitions.

The planner should choose transitions based on context and pacing.

---

# 18. Visual Effects

Support CPU-friendly effects using FFmpeg, ImageMagick, Remotion, Motion Canvas, MoviePy, or procedural methods.

Potential effects:

- zoom/pan
- Ken Burns
- blur
- glow approximation
- film grain
- vignette
- color adjustment
- contrast
- saturation
- sharpen
- noise
- chromatic aberration approximation
- RGB split
- scanlines
- light leaks
- motion blur where practical
- shadow/outline
- mask reveals
- animated gradients
- particles where CPU-friendly

Implement effects as reusable presets rather than one-off scripts.

---

# 19. Captions and Subtitles

The system must support:

- subtitles
- burned-in captions
- word/phrase emphasis
- line wrapping
- safe areas
- timing synchronization
- SRT/VTT output
- styling
- animated captions when supported

The final video should be able to include professional social-media-style captions.

---

# 20. Narration / TTS

Support a modular narration layer.

Preferred order:

1. Local/open-source CPU-friendly TTS.
2. User-provided narration audio.
3. Optional external TTS provider adapter.

The system must support:

- voice selection
- speaking rate
- pauses
- pronunciation hints where available
- scene synchronization
- automatic timing calculations

Never require a paid TTS service.

---

# 21. Audio Synchronization

The system should be able to place sound events based on visual timing.

Example:

```yaml
audio_cues:
  - time: 3.2
    effect: whoosh
  - time: 7.8
    effect: impact
  - time: 15.0
    effect: riser
```

The planner should also infer reasonable audio cues for transitions when the user requests a polished/cinematic result.

---

# 22. Audio Mixing / Mastering

Implement a final audio bus structure conceptually similar to:

```text
Narration
Music
SFX
Ambience
    ↓
Submix
    ↓
Ducking / EQ / Compression
    ↓
Master
```

Music should automatically duck under narration where appropriate.

Provide sane defaults and configurable loudness targets.

Use FFmpeg and open-source CPU-friendly audio utilities.

---

# 23. Quality Control

Every completed render must be validated automatically.

Check:

- file exists
- correct codec
- correct width/height
- correct FPS
- duration tolerance
- audio stream present when requested
- subtitle track where expected
- no broken media
- no missing scene outputs
- no obvious zero-byte files
- audio/video duration mismatch
- unexpected frame-rate changes
- final container readability

Create a validation report such as:

```text
VIDEO VALIDATION
----------------
Resolution:      PASS
FPS:             PASS
Duration:        PASS
Video codec:     PASS
Audio codec:     PASS
Audio stream:    PASS
Scenes:          PASS
Assets:          PASS
Final mux:       PASS
```

---

# 24. Error Recovery

The framework must not fail without explaining why.

Implement:

- structured errors
- retry logic for safe operations
- scene-level retry
- cached successful outputs
- fallback tools
- human-readable logs
- machine-readable logs

Example:

```text
Manim scene failed
    ↓
diagnose
    ↓
retry once
    ↓
fallback to Remotion implementation
    ↓
continue pipeline
```

Fallbacks must only be used when the result remains semantically acceptable.

---

# 25. Dependency Management

Create clear installation/bootstrap scripts.

Requirements:

- Linux/Ubuntu-first
- GitHub Actions compatible
- local development compatible
- version-pinned where reasonable
- reproducible installations
- dependency health check

Create:

```text
scripts/install.sh
scripts/doctor.sh
scripts/update.sh
```

`doctor.sh` must detect:

- Python
- Node.js
- npm
- FFmpeg
- ImageMagick
- Remotion dependencies
- MoviePy
- Manim
- Motion Canvas
- Godot if present
- Unity if present

It must report optional tools separately from required tools.

---

# 26. Tool Registry

Create a central registry such as:

```text
config/tools.yaml
```

Track:

- tool name
- category
- command
- version detection
- required/optional
- CPU/GPU requirement
- license
- installation method
- supported scene types
- fallback tool
- notes

The registry must explicitly distinguish:

```text
core
optional
external
licensed/non-FOSS
GPU-dependent
CPU-compatible
```

Do not falsely label proprietary or externally hosted tools as "free and unlimited."

---

# 27. Licensing and Copyright Safety

This is critical.

The repository must include a licensing and asset policy.

Rules:

- Prefer open-source software.
- Prefer permissive licenses when possible.
- Never silently download copyrighted music/images/videos.
- Do not bundle assets unless their licensing permits redistribution.
- Track source/license metadata for external assets.
- Clearly separate code, generated assets, user-owned assets, and external assets.
- Do not make unsupported claims such as "all assets are royalty-free" without verification.

Create:

```text
docs/licensing.md
```

---

# 28. "Free and Unlimited" Must Be Defined Correctly

Do NOT interpret "free and unlimited" as a blanket promise.

The system must distinguish:

### Software cost
Whether the tool itself is free/open-source.

### Usage limits
Whether the tool imposes quotas, credits, API limits, or subscription restrictions.

### GitHub limits
GitHub Actions time, artifact/storage limits, runner constraints, concurrency, and repository-specific limits.

### Compute feasibility
Whether a particular effect/render is realistically practical on CPU.

When the user asks for a "free and unlimited" workflow, the system should prefer:

- local CPU tools
- open-source tools
- procedural generation
- deterministic rendering
- no mandatory external APIs

Optional external services may exist, but never as a hidden requirement.

---

# 29. Security

Never commit:

- API keys
- tokens
- credentials
- secrets
- private service URLs

Use:

```text
.env.example
GitHub Secrets
environment variables
```

Also:

- sanitize user-controlled file names
- avoid unsafe shell interpolation
- validate paths
- prevent directory traversal
- quote shell arguments safely
- avoid `eval`
- minimize network access
- make downloads explicit

---

# 30. CLI UX

The system must be easy to control.

Provide commands such as:

```bash
video-factory plan "Create a 60 second vertical video about black holes"
video-factory render "Create a 60 second vertical video about black holes"
video-factory render videos/black-hole
video-factory doctor
video-factory validate videos/black-hole
```

Also support a structured mode:

```bash
video-factory create \
  --topic "Black holes" \
  --duration 60 \
  --width 1080 \
  --height 1920 \
  --style cinematic \
  --voice auto \
  --music auto \
  --sfx auto
```

---

# 31. Natural-Language Production Workflow

The AI assistant interacting with the repository should conceptually perform:

```text
USER REQUEST
   ↓
Interpret request
   ↓
Create production brief
   ↓
Create scene outline
   ↓
Estimate durations
   ↓
Select visual strategy
   ↓
Select tools per scene
   ↓
Determine required assets
   ↓
Generate/prepare assets
   ↓
Generate narration
   ↓
Generate music
   ↓
Generate SFX
   ↓
Render scenes
   ↓
Composite
   ↓
Add captions
   ↓
Mix/master audio
   ↓
Final FFmpeg encode
   ↓
Validate
   ↓
Package outputs
   ↓
Return final video
```

The system should support "dry run / plan mode" so the AI can show what it intends to do before expensive rendering.

Example:

```text
PLAN
----
Scene 01: Remotion
Scene 02: ImageMagick + Remotion
Scene 03: Manim
Scene 04: Motion Canvas
Audio: Local TTS + procedural music + generated SFX
Final: FFmpeg
```

---

# 32. Example Project

Create at least one complete example project that demonstrates the architecture.

Example topic:

```text
"How a Black Hole Works"
```

Make it approximately 30–60 seconds.

Demonstrate at least:

- Remotion
- ImageMagick
- FFmpeg
- one scientific/motion backend where practical
- captions
- sound effects
- background music
- narration placeholder or local TTS
- final validation

Do not artificially force every supported backend into the demo.

---

# 33. GitHub Actions Architecture

Create at least:

```text
.github/workflows/
    render-video.yml
    test-pipeline.yml
```

`render-video.yml` should support:

```text
workflow_dispatch
```

with inputs such as:

- video/project
- resolution
- preset
- draft/high quality
- whether to keep intermediates

Use caching.

Avoid unnecessary matrix builds for expensive render jobs.

Upload final deliverables as artifacts.

Keep the workflow understandable.

---

# 34. Repository Documentation

Create excellent documentation.

At minimum:

```text
README.md
docs/architecture.md
docs/tools.md
docs/pipeline.md
docs/audio.md
docs/assets.md
docs/licensing.md
docs/github-actions.md
docs/troubleshooting.md
```

The README must include:

- what the project does
- architecture diagram
- supported tools
- installation
- quick start
- example command
- GitHub Actions usage
- folder structure
- video spec format
- limitations
- licensing
- debugging

---

# 35. Architecture Quality

The repository must be:

- modular
- testable
- maintainable
- typed where practical
- documented
- extensible
- deterministic where possible
- cache-aware
- backend-agnostic
- CLI-first
- GitHub Actions friendly

Use interfaces/adapters where appropriate.

Do not hardcode tool-specific assumptions into the core planner.

---

# 36. Testing

Create tests for:

- video-spec parsing
- tool selection
- path safety
- naming
- duration calculation
- command construction
- manifest generation
- validation
- fallback selection

Include at least one end-to-end smoke test that creates a tiny test video without external APIs.

The smoke test must be CPU-only.

---

# 37. Output Structure

For every rendered project, produce:

```text
output/
  final.mp4
  preview.mp4
  subtitles.srt
  production-manifest.json
  validation-report.json
  render-log.txt
```

The manifest should include:

- project ID
- source specification
- selected tools
- versions
- generated assets
- scene durations
- audio assets
- render settings
- final output properties
- validation status

---

# 38. Performance Strategy

Optimize for CPU rendering.

Implement:

- caching
- incremental renders
- scene-level reuse
- draft previews
- reduced FPS/resolution preview
- bounded parallelism
- smart concatenation
- no unnecessary transcoding
- use stream copy when safe
- only re-encode when required

Do not create huge intermediate files unnecessarily.

---

# 39. Professional Production Defaults

When the user asks for "professional", default to:

- coherent visual hierarchy
- consistent typography
- safe margins
- readable captions
- sensible pacing
- subtle transitions
- purposeful sound design
- properly mixed narration/music/SFX
- smooth fades
- appropriate color treatment
- correct aspect ratio
- stable frame rate
- valid audio/video synchronization
- final technical validation

Avoid excessive effects.

Professional does not mean "maximum effects".

---

# 40. Important Constraint: Do Not Hallucinate Tool Capabilities

Before implementing any dependency or command:

- verify the correct CLI/API usage from its official documentation when available
- verify installation method
- verify licensing
- verify CPU compatibility
- verify whether a claimed free tier or unlimited usage actually exists
- never invent commands
- never invent flags
- never assume a cloud service is free

If current verification is unavailable, mark the dependency as uncertain and isolate it behind an adapter rather than making it a hard requirement.

---

# 41. Important Constraint: Preserve Core Functionality Without External AI

The repository's **core CPU-only mode must remain useful even when no external AI API is available**.

That means the project must still be able to create professional programmatic videos using:

- text
- vector graphics
- local images
- generated SVG
- procedural effects
- animations
- captions
- local audio
- procedural music
- procedural SFX
- FFmpeg processing
- Remotion
- ImageMagick
- MoviePy
- Manim
- Motion Canvas
- optional Godot/Unity

External AI generation is an enhancement, not the foundation.

---

# 42. Intelligent Fallback Philosophy

Every optional backend should have a fallback where practical.

Examples:

```text
Manim unavailable
    → Remotion scientific approximation

Motion Canvas unavailable
    → Remotion

MoviePy unavailable
    → FFmpeg/Python

ImageMagick unavailable
    → Python/Pillow where practical

Godot unavailable
    → Remotion or pre-rendered assets

Unity unavailable
    → skip backend and use an alternative scene strategy
```

Do not promise identical output across backends; preserve semantic intent instead.

---

# 43. AI-Orchestrator Behavior

When I later ask:

> "Create a 90-second video about X."

The AI controlling the repository should NOT immediately start rendering.

It should first internally construct:

1. Production brief.
2. Scene plan.
3. Asset plan.
4. Tool plan.
5. Audio plan.
6. Rendering plan.
7. Validation plan.

Then execute the plan.

It should make sensible defaults for:

- aspect ratio
- FPS
- visual hierarchy
- caption style
- narration
- music
- sound effects
- transitions
- pacing

It should infer them from the user's request but make all assumptions explicit in the generated manifest.

---

# 44. Human Override

The user must be able to override decisions.

Examples:

```yaml
scene:
  tool: remotion
```

or:

```yaml
audio:
  music: disabled
```

or:

```yaml
render:
  fps: 24
```

or:

```yaml
planner:
  prefer:
    - remotion
    - ffmpeg
```

The automatic planner must respect explicit overrides.

---

# 45. Do Not Overengineer the First Release

Build the repository in progressive layers.

## Phase 1 — Core

Implement and fully test:

- Python orchestrator
- FFmpeg
- ImageMagick
- Remotion
- basic audio
- captions
- GitHub Actions
- validation
- manifests
- caching

## Phase 2

Add:

- MoviePy
- Manim
- Motion Canvas

## Phase 3

Add:

- Godot
- Unity adapters

## Phase 4

Add optional AI providers:

- local AI
- ComfyUI adapters
- external image/video/TTS providers

Never let optional complexity destabilize the core system.

---

# 46. Deliverables

You must actually create the repository structure and files, not merely describe them.

At minimum generate:

```text
README.md
LICENSE
.gitignore
requirements.txt
package.json

.github/workflows/render-video.yml
.github/workflows/test-pipeline.yml

config/tools.yaml
config/defaults.yaml

src/video_factory/...
scripts/install.sh
scripts/doctor.sh
scripts/render.sh
scripts/validate.sh

remotion/...
manim/...
motion-canvas/...

videos/example/video.yaml
videos/example/script.md

docs/...
tests/...
```

Use sensible filenames if a slightly different structure is technically better.

---

# 47. Final Verification Before Declaring the Repository Complete

Before considering the repository finished:

1. Run the installation/health-check logic.
2. Validate the tool registry.
3. Run unit tests.
4. Run the CPU-only smoke test.
5. Render the example video.
6. Inspect the final media metadata.
7. Validate video/audio duration.
8. Validate subtitles where applicable.
9. Confirm GitHub Actions syntax.
10. Confirm no secrets are committed.
11. Confirm generated binary outputs are ignored from Git where appropriate.
12. Confirm the core workflow does not depend on a GPU.
13. Confirm all optional/external dependencies are clearly marked.
14. Confirm documentation does not falsely claim unlimited free usage.
15. Confirm the repository can be understood and operated by an AI assistant through CLI commands.

---

# 48. The Desired End State

The final repository should behave like a **programmable, AI-orchestrated, CPU-first video studio**.

The ideal user experience is:

```text
User:
Create a 45-second 1080x1920 cinematic educational video about how
black holes bend light. Use narration, captions, dramatic music,
subtle sound design, scientific diagrams, and professional transitions.
```

The AI should then:

```text
1. Analyze the request
2. Create the production plan
3. Select tools per scene
4. Generate/create required assets
5. Generate narration
6. Generate procedural background music
7. Generate procedural sound effects
8. Render scenes
9. Composite scenes
10. Add captions
11. Mix/master audio
12. Encode final MP4
13. Validate
14. Produce final artifacts
```

The final output should feel like it came from a professional automated post-production pipeline, while remaining **CPU-first, modular, reproducible, and as free/local as technically possible**.

---

# 49. Non-Negotiable Principles

Treat these as hard requirements:

- CLI-first
- CPU-first
- GitHub Actions compatible
- modular
- no mandatory paid APIs
- no mandatory GPU
- no hardcoded secrets
- deterministic where possible
- scene-level caching
- tool selection by intent
- graceful fallbacks
- professional audio and video finishing
- automatic validation
- explicit manifests
- excellent documentation
- no false claims about "free" or "unlimited"
- external services must be optional
- proprietary tools must never be hidden as core dependencies
- core functionality must remain useful without external AI APIs

---

# 50. Start Building Now

Do not return only a high-level proposal.

Actually implement the repository.

Start with the architecture and core pipeline, then add the optional backends in a way that does not destabilize the project.

When you encounter a tool that cannot honestly satisfy the requirements of:

- CPU-only
- GitHub-compatible
- free/local by default
- no mandatory API quota

do NOT force it into the core path.

Instead:

1. mark it optional,
2. isolate it behind an adapter,
3. document its constraints,
4. provide a CPU-friendly fallback.

The end result must be a repository that I can later control with short natural-language requests and that the AI assistant can translate into a complete, professional, reproducible video-production workflow.

**Build the system, test it, document it, and make the default path genuinely usable.**
