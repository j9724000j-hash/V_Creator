from pathlib import Path
import numpy as np
import pytest
from video_factory.audio import effect,music
from video_factory.captions import cues,timestamp,write_captions
from video_factory.spec import Cue
from video_factory.backends import Context
from video_factory.backends.ffmpeg import command
from video_factory.util import Runner
from video_factory.validation import validate

def test_caption_timing(spec,tmp_path):
    result=write_captions(spec,tmp_path)
    assert result[0]['start']==0 and result[-1]['end']==2
    assert timestamp(59.9996)=='00:01:00,000'
    assert (tmp_path/'subtitles.vtt').read_text().startswith('WEBVTT')

def test_synthesis(spec):
    for name in ('whoosh','hit','impact','bass_drop','click','pop','glitch','notification','riser','sweep','ambience','wind','rain','mechanical','scifi'):
        cue=Cue(time=0,effect=name,duration=.1)
        a=effect(cue,42)
        assert a.shape==(2400,2) and np.isfinite(a).all()
        assert np.array_equal(a,effect(cue,42))
    assert np.array_equal(music(spec),music(spec))

def test_command(spec,tmp_path,monkeypatch):
    monkeypatch.setattr('video_factory.util.ffmpeg',lambda:'ffmpeg')
    c=Context(spec.scenes[0],320,240,15,15,2,'draft',tmp_path/'a space.png',tmp_path/'out.mp4',Runner())
    cmd=command(c)
    assert 'libx264' in cmd and str(c.asset) in cmd
    assert '-threads' in cmd and 'yuv420p' in cmd

def test_validation_failure(spec,tmp_path):
    report=validate(tmp_path/'missing.mp4',spec)
    assert not report['ok'] and not report['checks']['exists']

def test_wrong_dimensions_rejected(spec,tmp_path,monkeypatch):
    fake=tmp_path/'test.mp4';fake.write_bytes(b'x')
    streams=[{'codec_type':'video','codec_name':'h264','width':640,'height':480,
              'avg_frame_rate':'15/1','r_frame_rate':'15/1','duration':'2','pix_fmt':'yuv420p','nb_frames':'30'},
             {'codec_type':'audio','codec_name':'aac','duration':'2'},
             {'codec_type':'subtitle','codec_name':'mov_text'}]
    monkeypatch.setattr('video_factory.validation.probe',lambda p:{'streams':streams,'format':{'duration':'2'}})
    report=validate(fake,spec,decode=False)
    assert not report['ok'] and not report['checks']['resolution']
