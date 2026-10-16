"""Voice wrapper safety can be checked without fetching huge models or a real speaker."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "scripts/voice.py"


def test_voice_help_is_available_without_models() -> None:
    result = subprocess.run([sys.executable, str(WRAPPER), "silma", "--help"],
                            capture_output=True, text=True, check=True)
    assert "--consent-confirmed" in result.stdout
    assert "--reference-text-file" in result.stdout


def test_refuse_clone_without_explicit_consent(tmp_path: Path) -> None:
    text = tmp_path / "line.txt"
    reference = tmp_path / "my-reference.wav"
    output = tmp_path / "do-not-generate.wav"
    text.write_text("مرحباً في مدينة الأبواب.", encoding="utf-8")
    reference.write_bytes(b"not a real voice; model must never be called")
    for engine in ("silma", "chatterbox"):
        result = subprocess.run([sys.executable, str(WRAPPER), engine, "--text-file", str(text),
                                 "--reference-audio", str(reference), "--output", str(output)],
                                capture_output=True, text=True, check=False)
        assert result.returncode == 2
        assert "--consent-confirmed" in result.stderr
        assert not output.exists()


def test_refuse_missing_reference_even_with_consent(tmp_path: Path) -> None:
    text = tmp_path / "line.txt"
    text.write_text("حارس البوابة", encoding="utf-8")
    result = subprocess.run([sys.executable, str(WRAPPER), "chatterbox", "--text-file", str(text),
                             "--reference-audio", str(tmp_path / "missing.wav"),
                             "--output", str(tmp_path / "unused.wav"), "--consent-confirmed"],
                            capture_output=True, text=True, check=False)
    assert result.returncode == 2
    assert "reference clip" in result.stderr
