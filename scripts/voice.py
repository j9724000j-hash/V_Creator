"""Isolated opt-in SILMA/Chatterbox inference; never a robotic fallback.

Run this with the matching .venv-voice-* Python, NOT the small core venv.
SILMA's upstream API expects a reference transcript; Chatterbox V3's API does not.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a short Arabic line using a licensed, consented reference voice")
    parser.add_argument("engine", choices=["silma", "chatterbox"])
    parser.add_argument("--text-file", type=Path, required=True, help="UTF-8 Arabic text, one short passage (<=500 chars)")
    parser.add_argument("--reference-audio", type=Path, required=True, help="Only your own/consensually licensed voice")
    parser.add_argument("--reference-text-file", type=Path, help="SILMA: exact transcript of reference audio")
    parser.add_argument("--output", type=Path, required=True, help="WAV destination (outside Git)!")
    parser.add_argument("--consent-confirmed", action="store_true", help="Confirm legal right to clone the reference speaker")
    args = parser.parse_args()
    if not args.consent_confirmed:
        parser.error("Voice cloning requires --consent-confirmed and an authorized reference recording")
    if not args.reference_audio.is_file() or args.reference_audio.suffix.lower() not in {".wav", ".mp3", ".flac"}:
        parser.error("Provide a readable WAV/MP3/FLAC reference clip with consent")
    if args.output.suffix.lower() != ".wav":
        parser.error("Output must be a .wav file")
    if not args.text_file.is_file():
        parser.error("--text-file does not exist")
    text = args.text_file.read_text(encoding="utf-8").strip()
    if not 1 <= len(text) <= 500:
        parser.error("Choose a short passage (1–500 characters); review every line by ear")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.engine == "silma":
        if not args.reference_text_file or not args.reference_text_file.is_file():
            parser.error("SILMA requires --reference-text-file with the exact reference transcription")
        from silma_tts.api import SilmaTTS  # optional heavy package, separate venv
        model = SilmaTTS()
        model.infer(
            ref_file=str(args.reference_audio),
            ref_text=args.reference_text_file.read_text(encoding="utf-8").strip(),
            gen_text=text,
            file_wave=str(args.output),
            seed=2026,
            speed=1,
        )
    else:
        import torch
        import torchaudio as ta
        from chatterbox.mtl_tts import ChatterboxMultilingualTTS
        device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
        model = ChatterboxMultilingualTTS.from_pretrained(device=device, t3_model="v3")
        wav = model.generate(text, language_id="ar", audio_prompt_path=str(args.reference_audio))
        ta.save(str(args.output), wav.cpu(), model.sr)
    print(f"Generated {args.output}. Listen with an Arabic speaker; fix pronunciation, timing and rights before publishing.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ImportError, OSError) as exc:
        print(f"TTS backend unavailable: {exc}. Install with ./scripts/install-voice.sh on a compatible machine.", file=sys.stderr)
        raise SystemExit(2)
