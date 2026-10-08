import pytest
from video_factory.spec import Spec

@pytest.fixture
def spec():
    return Spec.model_validate({'video':{'id':'tiny','title':'Test','duration':2,'width':320,'height':240,'fps':15},
        'audio':{'narration':False},'render':{'preset':'draft'},
        'scenes':[{'id':'intro','duration':1,'title':'Hello','captions':'A tiny CPU-only test.',
                   'audio_cues':[{'time':.1,'duration':.2,'effect':'click'}]},
                  {'id':'outro','duration':1,'title':'Goodbye','captions':'No external services.'}]})
