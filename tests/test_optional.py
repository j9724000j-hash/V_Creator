"""Executable optional tests: skip honestly when backend dependencies are absent."""
from pathlib import Path
import pytest
from video_factory.assets import make_asset
from video_factory.backends import Context
from video_factory.backends.remotion import RemotionBackend
from video_factory.audio import build_audio
from video_factory.tools import available
from video_factory.util import binary, Runner, probe

@pytest.mark.integration
def test_remotion_cpu(tmp_path,spec):
    if not available('remotion') or not binary('ffmpeg'):
        pytest.skip('Remotion + VF_BROWSER + FFmpeg required')
    asset=make_asset(spec.scenes[0],tmp_path,tmp_path,320,240)
    c=Context(spec.scenes[0],320,240,15,15,1,'draft',Path(asset['path']),tmp_path/'scene.mp4',Runner())
    RemotionBackend().render(c)
    media=probe(c.output)
    assert len(media['streams'])==1
    assert media['streams'][0]['pix_fmt']=='yuv420p'
    assert abs(float(media['format']['duration'])-1)<.08

@pytest.mark.integration
def test_local_tts(tmp_path,spec):
    if not (binary('espeak-ng') or binary('espeak')) or not binary('ffmpeg'):
        pytest.skip('eSpeak and FFmpeg required')
    spec.audio.narration=True
    spec.scenes[0].narration='Hello.'
    master,records,warnings=build_audio(spec,tmp_path,tmp_path,Runner())
    assert master.is_file() and not warnings
    assert any(r['method']=='espeak-local' for r in records)

@pytest.mark.integration
def test_moviepy_cpu(tmp_path,spec):
    if not available('moviepy') or not binary('ffprobe'):
        pytest.skip('MoviePy and ffprobe required')
    from video_factory.backends.moviepy import MoviePyBackend
    asset=make_asset(spec.scenes[0],tmp_path,tmp_path,320,240)
    c=Context(spec.scenes[0],320,240,15,15,1,'draft',Path(asset['path']),tmp_path/'moviepy.mp4',Runner())
    MoviePyBackend().render(c)
    media=probe(c.output)
    assert media['streams'][0]['width']==320
    assert abs(float(media['format']['duration'])-1)<.08
