# Troubleshooting

- **FFmpeg/ffprobe missing:** `./scripts/install.sh --system`, or point `VF_FFMPEG` / `VF_FFPROBE` at trusted executables. A restricted sandbox may block apt; do not disable TLS verification. Install/build tools explicitly outside Git. `doctor` exits nonzero for missing required tools.
- **Python import/config missing:** install editable with `pip install -e .` from the checkout or use scripts, which set PYTHONPATH. A standalone wheel is not supported yet.
- **Subtitles filter missing:** install FFmpeg built with libass. Otherwise use `render.burn_captions: false`; SRT/VTT and mov_text still work. Never silently pretend captions were burned.
- **Narration missing:** inspect manifest warnings. The demo allows `missing_tts: skip`; production projects default to error. Install eSpeak NG or provide owned narration audio. Voice availability is installation-dependent.
- **Speech too long:** extend the scene or shorten the script. The fitter rejects >2× speed rather than cutting off the narrator.
- **Remotion unavailable:** `npm ci`, installed Chromium and `VF_BROWSER` are all needed. Check its license, then enable it in planner. Chromium needs OS NSS/NSPR/graphics/font dependencies even with software rendering; do not assume headless means no shared libraries.
- **Optional backend failed:** logs show both retry errors and final fallback; set allow_fallback=false for fidelity-sensitive work. A generic conceptual image is not a simulation. Manim/Motion Canvas/Godot/Unity availability is not implied by registry presence.
- **Cache surprise:** content hashes include engine/version/implementation. A code/theme/tool change can invalidate many scenes intentionally. Source asset changes invalidate dependent scenes. `clean --yes` clears work/cache only; never manually delete repository root.
- **Resource pressure:** use draft, threads=1–2, short projects. Core synthesis refuses >600 seconds; divide long projects. Very large local raster inputs may trigger Pillow safety checks.
- **Failed QC:** inspect validation-report.json and render-log.txt; partial outputs are not promoted to final.mp4. An older final may still be present; failure.json makes that explicit. Run `validate` and inspect manifest timestamps before delivery.
- **Arabic/text layout:** use a shaping-capable font/FFmpeg build, validate glyphs visually, supply appropriate eSpeak voice or recorded narration. No word-level alignment or guaranteed multi-language typography in this release.
- **Safe paths:** specs/assets are project-relative; traversal and symlink escape paths are rejected. Filesystem clean is restricted to validated work/cache directories.
