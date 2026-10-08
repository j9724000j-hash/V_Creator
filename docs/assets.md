# Assets and provenance

Use the project itself as the local library: put owned/permitted images in `videos/<project>/assets/` and reference them explicitly from a scene. The generator reuses referenced files and hashes their contents; it does not do semantic image search, screenshots, stock downloads or infer usage rights.

An asset record has project-relative path, source and license. Paths are resolved and traversal/symlink escapes rejected. One primary raster per scene is supported. If no raster is supplied, deterministic Pillow geometry/title/chart artwork is generated, with a simple reusable SVG counterpart. Their content is intentionally not claimed to be identical. Output names combine scene ID, role and 20-character content digest. Optional ImageMagick strips raster metadata; Pillow handles preparation if unavailable.

The generic scientific visual is a conceptual black-hole/orbit illustration, not a universal science renderer. For other topics provide reviewed imagery or author a domain-specific adapter. Do not use an attractive diagram as evidence that a scientific simulation occurred.

Every generated asset is hashed and recorded in the manifest with generation method and original asset metadata. Nothing silently swaps in an external image. Generated geometry is original project output, but composition rights still depend on supplied assets, fonts and jurisdiction.

Provider contract (`providers.Request/Result`) requires provenance and explicit external opt-in. There are **no working Replicate/ComfyUI/cloud connectors yet**. Adding a provider requires authentication via environment/secrets, timeout/retry policy, cost/limits disclosure, license tracking and tests; network use is never default.
