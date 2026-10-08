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

def test_optional_detection_uses_installed_distribution(monkeypatch):
    import importlib.metadata
    from video_factory.tools import available
    def missing(name):
        raise importlib.metadata.PackageNotFoundError(name)
    monkeypatch.setattr(importlib.metadata,'version',missing)
    # Local manim/ source folder is a namespace, not an installed engine.
    assert not available('manim')
    assert not available('moviepy')
