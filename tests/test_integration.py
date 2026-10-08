import json
from pathlib import Path
import pytest
import yaml
from video_factory.pipeline import render
from video_factory.util import binary

@pytest.mark.integration
def test_cpu_smoke_and_incremental_cache(tmp_path,spec):
    if not binary('ffmpeg') or not binary('ffprobe'):
        pytest.skip('Install FFmpeg and ffprobe for CPU smoke test')
    (tmp_path/'video.yaml').write_text(yaml.safe_dump(spec.model_dump()))
    final=render(tmp_path)
    assert final.stat().st_size>1000
    output=tmp_path/'output'
    manifest=json.loads((output/'production-manifest.json').read_text())
    assert manifest['validation_status']
    assert not any(s['cache_hit'] for s in manifest['scenes'])
    render(tmp_path)
    manifest=json.loads((output/'production-manifest.json').read_text())
    assert all(s['cache_hit'] for s in manifest['scenes'])
    spec.scenes[1].title='Changed only scene two'
    (tmp_path/'video.yaml').write_text(yaml.safe_dump(spec.model_dump()))
    render(tmp_path)
    manifest=json.loads((output/'production-manifest.json').read_text())
    assert [s['cache_hit'] for s in manifest['scenes']]==[True,False]
    # Corruption must invalidate cache, not pass through to final encode.
    Path(manifest['scenes'][0]['path']).write_bytes(b'broken')
    render(tmp_path,keep=False)
    manifest=json.loads((output/'production-manifest.json').read_text())
    assert not manifest['scenes'][0]['cache_hit']
    assert not (tmp_path/'work').exists()
    assert (output/'preview.mp4').exists()

@pytest.mark.integration
def test_missing_narration_fails_explicitly(tmp_path,spec,monkeypatch):
    from video_factory.audio import build_audio
    from video_factory.util import ProductionError, Runner
    monkeypatch.setattr('video_factory.audio.binary',lambda name:None)
    spec.audio.narration=True;spec.scenes[0].narration='Hello'
    with pytest.raises(ProductionError,match='Narration requested'):
        build_audio(spec,tmp_path,tmp_path,Runner())
