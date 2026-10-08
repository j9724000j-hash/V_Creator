from fractions import Fraction
from pathlib import Path
from .spec import Spec
from .captions import cues
from .util import ProductionError, Runner, ffbase, probe

def validate(path: Path, spec: Spec, scene_paths: list[Path] | None = None,
             assets: list[Path] | None = None, decode=True) -> dict:
    checks={}; info={}; errors=[]
    checks['exists']=path.is_file() and path.stat().st_size>0
    try:
        info=probe(path)
        streams=info.get('streams',[])
        video=next((s for s in streams if s['codec_type']=='video'),{})
        audio=next((s for s in streams if s['codec_type']=='audio'),{})
        tolerance=max(.15,2/spec.video.fps)
        checks.update(codec=video.get('codec_name')=='h264',
            resolution=(video.get('width'),video.get('height'))==(spec.video.width,spec.video.height),
            fps=abs(float(Fraction(video.get('avg_frame_rate','0/1')))-spec.video.fps)<.01,
            duration=abs(float(info['format']['duration'])-spec.video.duration)<=tolerance,
            audio=audio.get('codec_name')=='aac',
            av_sync=abs(float(audio.get('duration',0))-float(video.get('duration',0)))<=tolerance,
            pixel_format=video.get('pix_fmt')=='yuv420p',
            frame_count=abs(int(video.get('nb_frames',0))-round(spec.video.duration*spec.video.fps))<=1,
            constant_frame_rate=video.get('r_frame_rate')==video.get('avg_frame_rate'),
            subtitles=not cues(spec) or any(s['codec_name']=='mov_text' for s in streams))
        checks['caption_timing']=all(0<=c['start']<c['end']<=spec.video.duration+.001 for c in cues(spec))
        if scene_paths is not None:
            checks['scenes']=len(scene_paths)==len(spec.scenes) and all(p.is_file() and p.stat().st_size>0 for p in scene_paths)
        if assets is not None:
            checks['assets']=all(p.is_file() and p.stat().st_size>0 for p in assets)
        if decode:
            Runner().run(ffbase()+['-xerror','-i',str(path),'-map','0:v:0','-map','0:a:0','-f','null','-'])
            checks['decode']=True
    except (ProductionError,ValueError,KeyError,ZeroDivisionError) as exc:
        checks['readable_decode']=False; errors.append(str(exc))
    return {'ok':bool(checks) and all(checks.values()),'checks':checks,'errors':errors,'media':info}
