"""Offline brief parser, intentionally not advertised as an LLM."""
import re
from pathlib import Path
import yaml
from .spec import Spec
from .util import ProductionError, digest, slug

def from_brief(brief: str, duration=None, width=None, height=None, topic=None) -> Spec:
    match=re.search(r'(\d+)\s*[- ]?\s*(?:seconds?|sec|ثانية|ثوان)',brief,re.I)
    seconds=duration or (int(match.group(1)) if match else 30)
    vertical=bool(re.search(r'vertical|portrait|عمودي',brief,re.I))
    size=re.search(r'(\d{3,4})\s*[x×]\s*(\d{3,4})',brief)
    w=width or (int(size.group(1)) if size else (1080 if vertical else 1920))
    h=height or (int(size.group(2)) if size else (1920 if vertical else 1080))
    topic_match=re.search(r'(?:about|عن)\s+(.+)',brief,re.I)
    title=topic or (topic_match.group(1).split('.')[0][:100] if topic_match else 'Video brief')
    per=seconds/3
    scenes=[]
    for i,label in enumerate(('Introduction','Explanation','Takeaway')):
        scenes.append({'id':f'scene-{i+1:03}','title':f'{label}: {title}'[:100],
            'duration':per,'type':'title' if i==0 else 'explanatory_diagram',
            'intent':label,'visual_description':'Replace with reviewed, topic-specific visual direction.',
            'narration':'','captions':title})
    return Spec.model_validate({'video':{'id':slug(title)+'-'+digest(brief)[:8],
        'title':title,'duration':seconds,'width':w,'height':h},'scenes':scenes,
        'audio':{'narration':False},'brief':brief,
        'assumptions':['Offline template parser only: topic, duration, aspect ratio extracted.',
        'No factual script invented. Assistant/human must review and supply narration and scene-specific imagery.',
        'Narration disabled until script supplied. Music and captions enabled.']})

def create(project: Path,spec: Spec):
    if project.exists():
        raise ProductionError(f'Refusing to overwrite existing project: {project}')
    project.mkdir(parents=True)
    (project/'video.yaml').write_text(yaml.safe_dump(spec.model_dump(),sort_keys=False,allow_unicode=True),encoding='utf-8')
    (project/'script.md').write_text('# '+spec.video.title+'\n\nReview script and visuals before rendering.\n',encoding='utf-8')
