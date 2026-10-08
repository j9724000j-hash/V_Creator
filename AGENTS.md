# Operating this studio as an AI assistant

1. Read README, docs/status.md and the existing project YAML. Do not assume optional engines are installed.
2. Translate the request into a brief, fact-checked script, scene/asset/tool/audio/render/validation plans. Natural-language CLI parsing is only a template convenience.
3. Use safe semantic project and scene IDs. Set total duration and frame-aligned scene durations; keep scripts short enough to speak comfortably.
4. Use `python -m video_factory doctor`, then `plan <project>`. No rendering before a structured plan exists.
5. Prefer the simplest reliable engine. Explicitly enable optional engines only after license/dependency checks. Never invent backend commands.
6. Use local/procedural assets by default. External assets require source and license. No fetching/costs without explicit authorization. Never embed secrets in a spec.
7. Set `missing_tts: error` unless the user accepts silent/caption-only narration fallback. eSpeak is synthetic; do not imply a human voice.
8. Set `allow_fallback: false` where approximation would change the meaning. Do not use generic orbit diagrams as verified physics simulations.
9. Render draft, inspect representative frames and listen to audio, then render standard/high if appropriate. Always inspect actual tool selection, warnings and validation report.
10. Deliver final.mp4 and its manifest/report. Explain remaining limitations honestly; don't claim tests that were skipped passed.
11. Do not commit outputs, caches, tools, credentials or downloaded binary assets. Keep the current working branch.

Useful commands:
`video-factory plan videos/example`
`video-factory render videos/example --preset draft`
`video-factory validate videos/example`

The implementation is progressively layered. See docs/status.md for actual readiness; provider protocols or templates are not completed integrations.
