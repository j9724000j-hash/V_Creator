#!/usr/bin/env python3
"""Generate a local, synthetic Arabic narration sample; no account or network.

First run scripts/install-local-voice.py. Preset neural voices, NOT human
recordings or clones. Model terms: OpenRAIL-M (see docs/voice-ar.md).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time

import numpy as np

from v_creator.voice_local import create_tts, generate, write_wav


def main() -> None:
    parser = argparse.ArgumentParser(description="Local CPU Arabic neural voice: no account, no GPU")
    text_input = parser.add_mutually_exclusive_group(required=True)
    text_input.add_argument("--text", help="Arabic sentence, up to 500 characters")
    text_input.add_argument("--text-file", type=Path, help="UTF-8 plain-text Arabic narration")
    parser.add_argument("--output", type=Path, required=True, help="Local .wav destination")
    parser.add_argument("--speaker", type=int, default=0, choices=range(10), metavar="0..9",
                        help="One of 10 fixed speaker styles; 0 is the default")
    parser.add_argument("--steps", type=int, default=8, choices=range(4, 13), metavar="4..12",
                        help="Diffusion steps (8 recommended; more is slower)")
    parser.add_argument("--speed", type=float, default=1.0, help="Speech speed between 0.7 and 1.5")
    parser.add_argument("--threads", type=int, default=2, help="CPU threads (1–4 recommended here)")
    args = parser.parse_args()
    if not 0.7 <= args.speed <= 1.5 or not 1 <= args.threads <= 4:
        parser.error("--speed must be 0.7–1.5 and --threads 1–4")
    if args.output.suffix.lower() != ".wav":
        parser.error("--output must end in .wav")
    if args.text_file:
        if not args.text_file.is_file() or args.text_file.stat().st_size > 3000:
            parser.error("--text-file must be a UTF-8 file of at most 3000 bytes")
        text = args.text_file.read_text(encoding="utf-8").strip()
    else:
        text = args.text.strip()

    start = time.monotonic()
    signal, sample_rate = generate(create_tts(args.threads), text, speaker=args.speaker,
                                   steps=args.steps, speed=args.speed)
    write_wav(args.output, signal, sample_rate)
    result = {
        "output": str(args.output.resolve()), "language": "ar",
        "preset_voice": f"Supertonic3 speaker {args.speaker}",
        "note": "Neural synthetic voice, not a human recording or consented clone. Audition pronunciation and naturalness before release.",
        "duration_seconds": round(len(signal) / sample_rate, 2),
        "synthesis_seconds": round(time.monotonic() - start, 2),
        "sample_rate": sample_rate,
        "peak": round(float(np.max(np.abs(signal))), 4),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ImportError, OSError, ValueError) as exc:
        print(f"Local Arabic voice failed: {exc}", file=sys.stderr)
        raise SystemExit(2)
