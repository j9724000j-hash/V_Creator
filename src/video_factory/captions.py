import textwrap
from pathlib import Path
from .spec import Spec

def timestamp(seconds: float, vtt=False) -> str:
    ms=round(seconds*1000)
    h,ms=divmod(ms,3600000); m,ms=divmod(ms,60000); s,ms=divmod(ms,1000)
    return f'{h:02}:{m:02}:{s:02}{"." if vtt else ","}{ms:03}'

def cues(spec: Spec) -> list[dict]:
    out=[]; start=0.0
    for scene in spec.scenes:
        text=scene.captions if scene.captions is not None else scene.narration
        # Phrase timing is estimated, not forced-aligned or word-accurate.
        phrases=textwrap.wrap(' '.join(text.split()),72)
        for i,phrase in enumerate(phrases):
            out.append({'start':start+i*scene.duration/len(phrases),
                        'end':start+(i+1)*scene.duration/len(phrases),
                        'text':'\n'.join(textwrap.wrap(phrase,36))})
        start+=scene.duration
    return out

def write_captions(spec: Spec, output: Path) -> list[dict]:
    items=cues(spec)
    for suffix in ('srt','vtt'):
        text='WEBVTT\n\n' if suffix=='vtt' else ''
        for i,c in enumerate(items,1):
            text+=f'{i}\n{timestamp(c["start"],suffix=="vtt")} --> {timestamp(c["end"],suffix=="vtt")}\n{c["text"]}\n\n'
        (output/f'subtitles.{suffix}').write_text(text,encoding='utf-8')
    return items
