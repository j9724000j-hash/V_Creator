"""Original procedural score + SFX. WAV is rendered without models, APIs or soundfonts."""

from __future__ import annotations

from math import ceil
from pathlib import Path
import wave

import mido
import numpy as np

SAMPLE_RATE = 32000
# Minor-key harmony; melodies are intentionally sparse to leave room for dialogue.
CHORDS = ((45, 52, 57, 60), (41, 48, 53, 57), (48, 55, 60, 64), (43, 50, 55, 59))


def _hz(midi_note: int) -> float:
    return 440.0 * 2.0 ** ((midi_note - 69) / 12)


def _write_pcm(path: Path, left: np.ndarray, right: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    stereo = np.stack((left, right), axis=-1)
    stereo = np.clip(stereo, -0.92, 0.92)
    with wave.open(str(path), "wb") as out:
        out.setnchannels(2)
        out.setsampwidth(2)
        out.setframerate(SAMPLE_RATE)
        out.writeframes((stereo * 32767).astype("<i2").tobytes())


def generate_music(path: Path, duration: float, bpm: int = 72, mood: str = "mysterious", seed: int = 2026) -> None:
    n = ceil(duration * SAMPLE_RATE)
    left = np.zeros(n, np.float32)
    right = np.zeros(n, np.float32)
    beat = 60 / bpm
    bar_length = beat * 4
    brightness = {"mysterious": 0.78, "hopeful": 1.0, "ominous": 0.57}[mood]
    for bar in range(ceil(duration / bar_length)):
        offset = int(bar * bar_length * SAMPLE_RATE)
        length = min(n - offset, int(bar_length * SAMPLE_RATE))
        if length <= 0:
            break
        t = np.arange(length, dtype=np.float32) / SAMPLE_RATE
        chord = CHORDS[bar % len(CHORDS)]
        env = np.minimum(t / 0.45, 1) * np.minimum((bar_length - t) / 0.60, 1)
        env = np.maximum(env, 0).astype(np.float32)
        pad = np.zeros(length, dtype=np.float32)
        for j, note in enumerate(chord[1:]):
            freq = _hz(note)
            pad += np.sin(2 * np.pi * freq * t + 0.4 * np.sin(2 * np.pi * 0.13 * t + j))
            pad += 0.22 * np.sin(2 * np.pi * (freq * 2.003) * t)
        pad = pad * env * (0.025 * brightness)
        left[offset:offset + length] += pad
        right[offset:offset + length] += pad * (0.91 + 0.07 * np.sin(2 * np.pi * 0.23 * t))
        # The low-register pulse is quiet enough to live below a narrator.
        for quarter in (0, 2):
            begin = offset + int(quarter * beat * SAMPLE_RATE)
            width = min(n - begin, int(beat * 0.9 * SAMPLE_RATE))
            if width <= 0:
                continue
            tt = np.arange(width, dtype=np.float32) / SAMPLE_RATE
            envelope = np.exp(-3.0 * tt / beat)
            bass = 0.072 * np.sin(2 * np.pi * _hz(chord[0]) * tt) * envelope
            left[begin:begin + width] += bass
            right[begin:begin + width] += bass
        # Sparse plucked motif. It evolves but does not impersonate orchestral music.
        for eighth in range(8):
            begin = offset + int(eighth * beat * 0.5 * SAMPLE_RATE)
            width = min(n - begin, int(beat * 0.4 * SAMPLE_RATE))
            if width <= 0:
                continue
            note = chord[(eighth + bar) % 3 + 1] + 12
            tt = np.arange(width, dtype=np.float32) / SAMPLE_RATE
            pluck = (0.018 * brightness) * (np.sin(2 * np.pi * _hz(note) * tt) +
                         0.20 * np.sin(4 * np.pi * _hz(note) * tt)) * np.exp(-9 * tt / beat)
            if (eighth + bar) % 2:
                left[begin:begin + width] += pluck * 0.4
                right[begin:begin + width] += pluck
            else:
                left[begin:begin + width] += pluck
                right[begin:begin + width] += pluck * 0.4
    # Master fade: no hard edges and no accidental clipping.
    fade_len = min(n // 2, int(0.6 * SAMPLE_RATE))
    if fade_len:
        fade = np.linspace(0, 1, fade_len, dtype=np.float32)
        left[:fade_len] *= fade
        right[:fade_len] *= fade
        left[-fade_len:] *= fade[::-1]
        right[-fade_len:] *= fade[::-1]
    _write_pcm(path, left, right)


def generate_sfx(path: Path, duration: float, scene_starts: list[float], seed: int = 2026) -> None:
    count = ceil(duration * SAMPLE_RATE)
    left = np.zeros(count, np.float32)
    right = np.zeros(count, np.float32)
    rng = np.random.default_rng(seed)
    for index, start in enumerate(scene_starts[1:], 1):
        # Short deterministic whoosh preceding each cut (synthetic noise envelope).
        at = max(0, int((start - 0.36) * SAMPLE_RATE))
        length = min(count - at, int(0.63 * SAMPLE_RATE))
        if length < 1:
            continue
        t = np.arange(length, dtype=np.float32) / SAMPLE_RATE
        env = np.sin(np.pi * np.minimum(t / 0.63, 1)) ** 2
        white = rng.standard_normal(length).astype(np.float32)
        # Smooth the noise into a windy texture; each transition has its own profile.
        filtered = np.convolve(white, np.ones(11, dtype=np.float32) / 11, mode="same")
        sweep = 0.043 * filtered * env
        left[at:at + length] += sweep
        right[at:at + length] -= sweep * 0.65
        impact_at = int(start * SAMPLE_RATE)
        hit_len = min(count - impact_at, int(0.75 * SAMPLE_RATE))
        if hit_len <= 0:
            continue
        ht = np.arange(hit_len, dtype=np.float32) / SAMPLE_RATE
        hit = 0.085 * np.sin(2 * np.pi * (74 * ht - 22 * ht * ht)) * np.exp(-7 * ht)
        left[impact_at:impact_at + hit_len] += hit
        right[impact_at:impact_at + hit_len] += hit * (0.75 if index % 2 else 0.95)
    _write_pcm(path, left, right)


def generate_midi(path: Path, duration: float, bpm: int = 72) -> None:
    """Also export an editable arrangement. WAV uses our own synthesizer, not MIDI playback."""
    ticks = 480
    file = mido.MidiFile(ticks_per_beat=ticks)
    track = mido.MidiTrack()
    file.tracks.append(track)
    track.append(mido.MetaMessage("track_name", name="Original cinematic motif", time=0))
    track.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(bpm), time=0))
    events: list[tuple[int, int, int, int]] = []
    bars = ceil(duration * bpm / 240)
    for bar in range(bars):
        chord = CHORDS[bar % len(CHORDS)]
        for note in chord[1:]:
            events.append((bar * 4 * ticks, 1, note, 43))
            events.append(((bar + 1) * 4 * ticks, 0, note, 0))
        for eighth in range(8):
            pos = bar * 4 * ticks + eighth * (ticks // 2)
            note = chord[(eighth + bar) % 3 + 1] + 12
            events.extend(((pos, 1, note, 58), (pos + ticks // 4, 0, note, 0)))
    previous = 0
    for pos, on, note, velocity in sorted(events):
        track.append(mido.Message("note_on" if on else "note_off", note=note,
                                  velocity=velocity, channel=0, time=pos - previous))
        previous = pos
    track.append(mido.MetaMessage("end_of_track", time=0))
    path.parent.mkdir(parents=True, exist_ok=True)
    file.save(path)
