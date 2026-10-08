# Tool setup and verified interfaces

The authoritative inventory is `config/tools.yaml`. `doctor` distinguishes required/optional/extension-only tools and reports CPU, memory and disk. Required: Python 3.11+, FFmpeg + ffprobe with libx264, AAC, libass subtitle filter and relevant audio filters. FFmpeg availability is not proof every filter is compiled in; render failures include diagnostics.

| Backend | Install / use | Actual readiness |
|---|---|---|
| FFmpeg/ffprobe | Ubuntu `apt-get install ffmpeg` | Tested full pipeline, static FFmpeg 5.0 locally; Ubuntu CI uses distro build. |
| ImageMagick | `apt-get install imagemagick` | Tested `convert <png> -strip <png>` on 6.9; generator also recognizes `magick`. |
| eSpeak NG | `apt-get install espeak-ng` | Built/tested upstream 1.52.0 locally; narration in example verified. |
| Remotion | `npm ci`, explicit Chromium + `VF_BROWSER`; opt into planner.enable | 4.0.534 typechecked and rendered with software Chromium 138. No implicit browser install. |
| MoviePy | `pip install -e '.[moviepy]'` | v2.2.1 adapter tested with a CPU clip; uses `ImageClip.with_duration`, `with_effects`, `write_videofile`. |
| Manim | Cairo/Pango development packages, `pip install -e '.[manim]'` | Optional Cairo adapter + fixed orbit demo; not installed/tested here; generic illustration, no LaTeX. |
| Motion Canvas | Standalone template in motion-canvas/ | Manual authoring/export only; not selected as automated CLI backend. |
| Godot / Unity | Manual, separately licensed/setup | Extension contract, no automatic engine export. Simulation fallback fails without a supplied pre-rendered raster. |

Commands were verified against installed CLI help/source where available, not guessed. Remotion flags (`--props`, `--codec`, `--pixel-format`, `--concurrency`, `--browser-executable`, `--gl`) were confirmed in pinned npm package source and an actual render. FFmpeg filters were checked with `ffmpeg -h filter=...`. eSpeak CLI/source from tag 1.52.0 was inspected and exercised. Optional unexecuted adapters must be validated in their target environment before reliance.

Official references (upstream documentation/source):
- https://github.com/FFmpeg/FFmpeg/tree/master/doc
- https://github.com/ImageMagick/ImageMagick
- https://github.com/remotion-dev/remotion (also pinned node_modules @remotion CLI/renderer source)
- https://github.com/espeak-ng/espeak-ng/blob/1.52.0/docs/guide.md
- https://github.com/espeak-ng/espeak-ng/blob/1.52.0/src/espeak-ng.1.ronn
- https://github.com/Zulko/moviepy
- https://github.com/ManimCommunity/manim
- https://github.com/motion-canvas/motion-canvas
- https://github.com/godotengine/godot

`VF_FFMPEG`, `VF_FFPROBE`, `VF_ESPEAK_NG` can point to explicit executables. They are administrator configuration, not executable strings from YAML. Keep external binaries out of Git. System dependencies are distro-managed, Python direct requirements and npm packages are pinned; Python transitive dependencies are not a fully hashed lockfile. Byte-identical media across FFmpeg/font/browser versions is not guaranteed.
