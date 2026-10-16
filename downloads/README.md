# Arabic greeting audio / التسجيل العربي

The MP3 and WAV contain the same utterance: «مرحبا كيف حالكم يا قوم». The ZIP bundles both files for a single browser-friendly download.

- `marhaba-kayf-halukum-ya-qawm.mp3`: 44.1 kHz mono MP3 (192 kbps), about 2.7 seconds.
- `marhaba-kayf-halukum-ya-qawm.wav`: 44.1 kHz mono 16-bit PCM WAV.

Generated locally with the fixed preset speaker 0 of Supertonic 3 via sherpa-onnx. This is **synthetic speech, not a human recording or a cloned individual**. The original model's weights are licensed **OpenRAIL-M**: https://huggingface.co/Supertone/supertonic-3 . The ONNX files used here came from a third-party npm repack; package checksums were verified but binary equivalence with the publisher's weights was not independently established.

## Colloquial greeting, three takes / تحية عامية بثلاث نسخ

`arabic-greeting-full-audio.zip` bundles the longer colloquial line «مرحباً، كيف حالكم يا قوم، ايش الأخبار... انشالله تمام» — fed to the engine fully diacritised — as three takes, each in WAV (44.1 kHz mono 16-bit PCM) and MP3 (192 kbps):

| File | Preset | Speed | Length |
|---|---|---|---|
| `take-1-speaker0.{wav,mp3}` | speaker 0 | 1.00 | ~6.90 s |
| `take-2-speaker2.{wav,mp3}` | speaker 2 | 1.00 | ~7.12 s |
| `take-3-speaker4-slower.{wav,mp3}` | speaker 4 | 0.95 | ~7.03 s |

Peaks were normalised to −1.5 dBFS with 20 ms fade-in and 90 ms fade-out. The archive's `README.txt` repeats this in Arabic. The same caveat applies, and is louder here: the engine is primarily MSA, so the colloquial «إيش» and «انشالله» may be read closer to Standard Arabic than to any spoken dialect. **No human has verified the pronunciation or naturalness — listen before publishing.** For a genuine human voice, record the line with the performer's consent and pass it via `--narration`.
