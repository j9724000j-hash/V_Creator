# Audio production

No commercial samples, neural model or online music API is bundled. NumPy generates PCM locally at 24 kHz; FFmpeg masters at 48 kHz stereo. Music uses key, BPM, mood, intensity, arpeggio/chord progression and a simple intro/build/outro amplitude structure; duration is fitted precisely. This is procedural background scoring, not an AI composer. Seamless looping, MIDI export, multi-instrument arrangements and professional human voice quality are not promised.

Local narration uses eSpeak NG (`-v`, `-s`, `-f`, `-w`) or eSpeak; alternatively provide scene.narration_asset with provenance. TTS is independent of the voice tools in the chat UI. Speech is padded or sped up to fit the scene; required speed above 2× fails instead of truncating speech. Default missing-TTS behavior is an error. Only explicit `missing_tts: skip` allows caption-only output, with warnings.

Narration bus: high-pass (70 Hz) → compressor → voice + sidechain split.
Music bus: gain → sidechain compressor keyed from narration.
SFX bus: seeded stereo procedural cues with scene-local time, duration, gain and equal-power pan.
Master: sum (no implicit normalization) → optional short echo → fades → single-pass loudnorm (-16 LUFS default, -1.5 dBTP) → limiter → AAC 192 kbps.

Supported SFX: whoosh, hit, impact, bass_drop, click, pop, glitch, notification, riser, sweep, ambience, wind, rain, mechanical, scifi. Some share noise/oscillator templates; these are approximations, not recorded environmental realism. The final limiter protects headroom. A/V timing is validated; exact integrated loudness after limiting is not currently measured/reported, and single-pass normalization may not hit its target exactly. Listen before publishing.

SoX is detected but not needed: FFmpeg supplies current effects. FluidSynth/TiMidity++ are detected and documented for future MIDI/SoundFont work, not falsely presented as integrated. SoundFont redistribution licenses must be reviewed separately. Avoiding them keeps the default installation small.

Audio synthesis is bounded to 600 seconds; several whole-track arrays are held in memory. Long-form projects should be split until block streaming is implemented. eSpeak voice/language availability depends on the installation. Arabic text requires a supported voice and fonts; captions are phrase-estimated, not linguistic word alignment.
