# Licensing, costs and asset safety

Project code is MIT. This does not relicense its dependencies or outputs incorporating third-party assets.

| Component | License / restriction |
|---|---|
| FFmpeg / ffprobe | LGPL/GPL depends on build; libx264-enabled binaries are generally GPL builds. Codec/patent obligations can depend on use/jurisdiction. |
| ImageMagick | ImageMagick License (permissive with its conditions). |
| Pillow | HPND; bundled dependency notices also matter. |
| NumPy | BSD-3-Clause. |
| Pydantic / PyYAML | MIT. |
| eSpeak NG | GPL-3.0 family plus bundled-data notices; inspect exact version. |
| Remotion | Source-available Remotion license, **not unrestricted FOSS**. Eligibility-based free use; company license may be required. |
| MoviePy / Manim / Motion Canvas / Godot | MIT upstream; media/add-ons/fonts retain their own terms. |
| Unity | Proprietary, optional, separately licensed; no license/service bundled. |
| FluidSynth / TiMidity++ / SoX | LGPL/GPL variants; SoundFonts and libraries have separate licenses. Detected only. |
| DejaVu fonts | Bitstream Vera-derived font terms and notices; use your distribution's licensed copy. |

Remotion upstream LICENSE.md was inspected on 2026-10-08: it describes free eligibility for individuals, qualifying small organizations, nonprofits and evaluation, with a company license otherwise. Check the **license shipped with the pinned version** and your actual eligibility before enabling it; do not rely on this summary as legal advice. It is disabled by default precisely because CPU capability does not imply unrestricted free use.

Official upstream sources are in `config/tools.yaml` and `docs/tools.md`. Unverified optional integration details are isolated, never required.

No stock music/images/video or downloaded fonts are bundled in Git. Assets must record source and license; “found online” is not permission. User-owned and external assets keep their own terms. Procedural generation is not a blanket promise of royalty-free outputs. Do not upload private material to third-party providers without explicit consent.

## Four distinct limits

1. Software license / price: whether this use is legally permitted without purchase.
2. Service quotas: API credits, paid plans and provider conditions, if explicitly configured later.
3. GitHub account limits: hosted runner minutes, concurrency, artifact/storage allowance and retention.
4. Compute limits: CPU/RAM/disk/time and practical render complexity.

No component is marketed as “free and unlimited.” Default offline generation has no API quota, but it consumes finite hardware resources. Review current GitHub plan usage instead of assuming a public/private repository gets unlimited execution.
