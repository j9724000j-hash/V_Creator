import pytest
from video_factory.planner import plan
from video_factory.tools import registry
from video_factory.util import ProductionError

def test_registry():
    assert registry()['ffmpeg']['required']
    assert not registry()['unity']['required']

def test_fallback(spec):
    p=plan(spec,{'ffmpeg':True})
    assert p['scenes'][0]['selected_tool']=='ffmpeg'
    assert p['scenes'][0]['fallback']=='ffmpeg'

def test_override(spec):
    spec.scenes[0].tool='remotion'
    assert plan(spec,{'ffmpeg':True,'remotion':True})['scenes'][0]['selected_tool']=='remotion'

def test_strict(spec):
    spec.scenes[0].tool='unity';spec.scenes[0].allow_fallback=False
    with pytest.raises(ProductionError): plan(spec,{'ffmpeg':True,'unity':True})

def test_unacceptable_simulation(spec):
    spec.scenes[0].type='simulation'
    with pytest.raises(ProductionError): plan(spec,{'ffmpeg':True})

def test_preference(spec):
    spec.planner.prefer=['ffmpeg']
    assert plan(spec,{'ffmpeg':True,'remotion':True})['scenes'][0]['selected_tool']=='ffmpeg'
