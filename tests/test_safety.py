import pytest
from video_factory.util import ProductionError, safe_path, slug, digest, Runner
from video_factory.providers import Request, invoke

def test_path_traversal(tmp_path):
    with pytest.raises(ProductionError): safe_path(tmp_path,'../outside')
    with pytest.raises(ProductionError): safe_path(tmp_path,'/etc/passwd')
    (tmp_path/'escape').symlink_to('/etc',target_is_directory=True)
    with pytest.raises(ProductionError): safe_path(tmp_path,'escape/passwd')

def test_naming():
    assert slug('../../Some Topic!')=='some-topic'
    assert digest({'a':1,'b':2})==digest({'b':2,'a':1})
    assert digest('a')!=digest('b')

def test_no_shell(tmp_path):
    text='$(touch owned); echo bad'
    assert Runner().run(['printf','%s',text])==text
    assert not (tmp_path/'owned').exists()

def test_provider_denied(tmp_path):
    class External:
        external=True
        def generate(self,req): raise AssertionError('must not run')
    with pytest.raises(ProductionError): invoke(External(),Request('images','test',tmp_path/'test.png'))

def test_output_symlink_escape(tmp_path,spec):
    import yaml
    from video_factory.pipeline import render
    (tmp_path/'video.yaml').write_text(yaml.safe_dump(spec.model_dump()))
    (tmp_path/'output').symlink_to('/tmp',target_is_directory=True)
    with pytest.raises(ProductionError): render(tmp_path)
