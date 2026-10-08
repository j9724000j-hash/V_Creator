# Optional Motion Canvas authoring template

This is a **manual authoring/export template**, not a fake headless CLI adapter.

```sh
cd motion-canvas
npm ci
npm run build # build-only template; see security note below
```

Open the editor, review the scene and use its installed exporter/image-sequence workflow. `npm run build` builds the editor project; **it does not render a video**. To encode an explicitly exported sequence, use FFmpeg with the actual export filenames/frame rate, then validate the result. The core currently accepts primary raster assets, not a general pre-rendered clip timeline.

The pipeline deliberately marks motion-canvas `extension-only` and chooses a labeled FFmpeg/Remotion approximation instead. Wiring an exporter requires version-specific official API verification and an integration test, not an invented `motion-canvas render` command. Core imports/installations never depend on this folder.

Official source/docs: https://github.com/motion-canvas/motion-canvas (MIT; review asset/exporter dependency licenses separately).

## Security note

The pinned optional Motion Canvas upstream toolchain still has unresolved npm advisories (Vite/esbuild and glob/braces). It is **not installed by core/CI** and no development server is started or exposed by this repository. Build only trusted source, never accept untrusted XML/glob input, and resolve upstream advisories before deploying an editor. The `start` script is intentionally omitted. `npm audit` provides exact current findings. The XML parser has been overridden to patched 0.9.12. This template is not production-ready automation.
