import pytest
import yaml
from pydantic import ValidationError
from video_factory.spec import Spec, load
from video_factory.brief import from_brief
from video_factory.pipeline import resolved
from video_factory.util import ProductionError

def test_parse_yaml_json(tmp_path,spec):
    for name,data in [('video.yaml',yaml.safe_dump(spec.model_dump())),('video.json',spec.model_dump_json())]:
        path=tmp_path/name; path.write_text(data)
        assert load(path)==spec

@pytest.mark.parametrize('change',[{'duration':3},{'width':321},{'fps':0},{'duration':float('nan')}])
def test_bad_video(spec,change):
    data=spec.model_dump(); data['video'].update(change)
    with pytest.raises(ValidationError): Spec.model_validate(data)

def test_unknown_field(spec):
    data=spec.model_dump();data['surprise']='unsupported'
    with pytest.raises(ValidationError): Spec.model_validate(data)

def test_duplicate_scene(spec):
    data=spec.model_dump();data['scenes'][1]['id']='intro'
    with pytest.raises(ValidationError): Spec.model_validate(data)

def test_cue_boundary(spec):
    data=spec.model_dump();data['scenes'][0]['audio_cues'][0]['time']=1
    with pytest.raises(ValidationError): Spec.model_validate(data)

def test_asset_traversal(tmp_path,spec):
    data=spec.model_dump();data['scenes'][0]['assets']=[{'path':'../secret','source':'local','license':'owned'}]
    (tmp_path/'video.yaml').write_text(yaml.safe_dump(data))
    with pytest.raises(ProductionError): load(tmp_path)

def test_brief():
    result=from_brief('Create a 60-second vertical video about black holes')
    assert result.video.duration==60 and result.video.height==1920
    assert result.assumptions and not result.audio.narration

def test_resolution(spec):
    assert resolved(spec,'draft','640x480').video.width==640
    with pytest.raises(ProductionError): resolved(spec,'draft','bad')
