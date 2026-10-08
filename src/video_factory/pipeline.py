from __future__ import annotations
from datetime import datetime, timezone
import fcntl
import json
from pathlib import Path
import shutil
from .assets import make_asset
from .audio import build_audio
from .backends import Context
from .backends.ffmpeg import FFmpegBackend
from .backends.remotion import RemotionBackend
from .backends.moviepy import MoviePyBackend
from .backends.manim import ManimBackend
from .captions import write_captions
from .planner import plan
from .spec import Spec, load
from .tools import doctor
from .util import ROOT, ProductionError, Runner, digest, ffbase, file_hash, probe, safe_path, write_json
from .validation import validate

BACKENDS={'ffmpeg':FFmpegBackend,'remotion':RemotionBackend,'moviepy':MoviePyBackend,'manim':ManimBackend}
PRESETS={'draft':(360,15),'preview':(540,24),'standard':(None,None),'high':(None,None)}

def resolved(spec: Spec, preset: str | None = None, resolution: str | None = None) -> Spec:
    obj=spec.model_dump(); preset=preset or spec.render.preset
    obj['render']['preset']=preset
    width,fps=PRESETS[preset]
    if width and width<spec.video.width:
        obj['video']['height']=max(160,round(spec.video.height*width/spec.video.width/2)*2)
        obj['video']['width']=width
    if resolution and resolution!='spec':
        try:
            w,h=map(int,resolution.lower().split('x'))
        except ValueError as exc:
            raise ProductionError('Resolution must be WIDTHxHEIGHT or spec') from exc
        obj['video']['width'],obj['video']['height']=w,h
    if fps:
        obj['video']['fps']=min(spec.video.fps,fps)
    for scene in obj['scenes']:
        scene['duration']=max(1,round(scene['duration']*obj['video']['fps']))/obj['video']['fps']
    obj['video']['duration']=sum(s['duration'] for s in obj['scenes'])
    return Spec.model_validate(obj)

def render(project: Path, preset=None, resolution=None, keep=None) -> Path:
    project=project.resolve()
    source=load(project)
    if project.is_file():
        project=project.parent
    spec=resolved(source,preset,resolution)
    if keep is not None:
        spec.render.keep_intermediates=keep
    output=safe_path(project,'output'); output.mkdir(exist_ok=True)
    # One writer per project prevents final/cache races; no unsafe shell locks.
    with (output/'.render.lock').open('w') as lock:
        try:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ProductionError('This project already has an active render') from exc
        try:
            return _render(project,output,source,spec)
        except Exception as exc:
            write_json(output/'failure.json',{'error':type(exc).__name__,'message':str(exc),
                       'hint':'Inspect render-log.txt; successful scenes remain cached.'})
            raise

def _render(project:Path, output:Path, source:Spec, spec:Spec) -> Path:
    if spec.video.duration>600:
        raise ProductionError('Core synthesis is bounded to 600 seconds; split long projects before rendering.')
    production=plan(spec)
    health=doctor()
    if not health['ok']:
        raise ProductionError('Required tools missing; run video-factory doctor')
    work=safe_path(project,'work'); cache=safe_path(project,'.cache/scenes')
    work.mkdir(exist_ok=True); cache.mkdir(parents=True,exist_ok=True)
    (output/'render-log.txt').write_text('Video Factory CPU render\n')
    runner=Runner(output/'render-log.txt')
    write_json(output/'production-plan.json',production)
    implementation=digest({str(p.relative_to(ROOT)):file_hash(p) for folder in ('src','remotion','manim','brand')
                           for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in str(p)})
    scenes=[]; asset_records=[]; scene_records=[]; warnings=[]
    for scene,decision in zip(spec.scenes,production['scenes']):
        asset=make_asset(scene,project,work,spec.video.width,spec.video.height)
        asset_records.append(asset)
        tool=decision['selected_tool']
        key=digest({'scene':scene.model_dump(),'asset':asset['sha256'],'video':[spec.video.width,spec.video.height,spec.video.fps],
                    'render':[spec.render.preset,spec.render.threads],'tool':tool,'version':health['tools'][tool]['version'],
                    'implementation':implementation})
        folder=cache/f'{scene.id}_{key}'; folder.mkdir(exist_ok=True)
        path=folder/'scene.mp4'; metadata=folder/'cache.json'
        reused=False
        if path.exists() and metadata.exists():
            try:
                reused=json.loads(metadata.read_text())['sha256']==file_hash(path)
            except (ValueError,KeyError):
                pass
        if not reused:
            temporary=folder/'partial.mp4'
            context=Context(scene,spec.video.width,spec.video.height,spec.video.fps,
                round(scene.duration*spec.video.fps),spec.render.threads,scene.quality or spec.render.preset,
                Path(asset['path']),temporary,runner)
            errors=[]
            for attempt in range(2):
                try:
                    BACKENDS[tool]().render(context)
                    break
                except Exception as exc:
                    errors.append(str(exc))
            else:
                if not scene.allow_fallback or tool=='ffmpeg':
                    raise ProductionError(f'{scene.id}: scene failed twice: {errors[-1]}')
                warnings.append(f'{scene.id}: {tool} failed twice; using conceptual FFmpeg fallback: {errors[-1]}')
                tool='ffmpeg'; FFmpegBackend().render(context)
            info=probe(temporary)
            video=next(s for s in info['streams'] if s['codec_type']=='video')
            if (video['width'],video['height'])!=(spec.video.width,spec.video.height) or abs(float(info['format']['duration'])-scene.duration)>.15:
                raise ProductionError(f'{scene.id}: backend violated scene dimensions/duration contract')
            temporary.replace(path)
            write_json(metadata,{'sha256':file_hash(path),'tool':tool,'errors':errors})
        cached=json.loads(metadata.read_text())
        tool=cached['tool']
        if cached.get('errors'):
            warnings.append(f'{scene.id}: cached backend recovery: {cached["errors"][-1]}')
        scenes.append(path)
        scene_records.append({'id':scene.id,'duration':scene.duration,'tool':tool,'cache_key':key,
                              'cache_hit':reused,'path':str(path),'sha256':file_hash(path)})
    captions=write_captions(spec,output)
    master,audio_records,audio_warnings=build_audio(spec,project,work,runner)
    for record in audio_records:
        if record.get('path'):
            record['sha256']=file_hash(Path(record['path']))
    warnings.extend(audio_warnings)
    # Concat uses relative generated names only, never interpolated user paths.
    for i,path in enumerate(scenes):
        target=work/f'scene_{i:04}.mp4'
        shutil.copyfile(path,target)
    concat=work/'concat.txt'
    concat.write_text(''.join(f"file 'scene_{i:04}.mp4'\n" for i in range(len(scenes))))
    assembled=work/'assembled.mp4'
    runner.run(ffbase()+['-f','concat','-safe','1','-i',str(concat),'-c','copy',str(assembled)])
    args=ffbase()+['-i',str(assembled),'-i',str(master)]
    if captions:
        args+=['-i','subtitles.srt']
    args+=['-map','0:v:0','-map','1:a:0']
    if captions:
        args+=['-map','2:0','-c:s','mov_text']
    if captions and spec.render.burn_captions:
        args+=['-vf',"subtitles=subtitles.srt:force_style='FontName=DejaVu Sans,FontSize=17,Outline=2,MarginV=24'",
               '-c:v','libx264','-threads',str(spec.render.threads),'-preset','veryfast' if spec.render.preset in ('draft','preview') else 'medium',
               '-crf','18' if spec.render.preset=='high' else '22','-pix_fmt','yuv420p']
    else:
        args+=['-c:v','copy']
    partial=output/'final.partial.mp4'
    args+=['-c:a','aac','-b:a','192k','-ar','48000','-t',str(spec.video.duration),
           '-movflags','+faststart','-metadata',f'title={spec.video.title}',str(partial)]
    runner.run(args,cwd=output)
    report=validate(partial,spec,scenes,[Path(a['path']) for a in asset_records])
    write_json(output/'validation-report.json',report)
    if not report['ok']:
        raise ProductionError('Final validation failed. Inspect validation-report.json')
    final=output/'final.mp4'; partial.replace(final)
    runner.run(ffbase()+['-i',str(final),'-vf',"scale='min(360,iw)':-2,fps=15",'-c:v','libx264',
                        '-threads',str(spec.render.threads),'-preset','ultrafast','-crf','28',
                        '-c:a','aac','-b:a','96k','-movflags','+faststart',str(output/'preview.mp4')])
    write_json(output/'production-manifest.json',{
        'schema_version':1,'project_id':spec.video.id,'created_at':datetime.now(timezone.utc).isoformat(),
        'source_specification':source.model_dump(),'effective_specification':spec.model_dump(),
        'plan':production,'selected_tools':sorted({s['tool'] for s in scene_records}),
        'versions':health,'assets':asset_records,'scenes':scene_records,'audio_assets':audio_records,
        'render_settings':spec.render.model_dump(),'final_output':{'path':str(final),'sha256':file_hash(final),
        'properties':report['media']},'validation_status':report['ok'],'warnings':warnings,
        'assumptions':spec.assumptions+['Captions use estimated phrase timing, not word alignment.',
        'Scientific fallback diagrams are conceptual, not physical simulations.'],
        'intermediates_retained':spec.render.keep_intermediates})
    (output/'failure.json').unlink(missing_ok=True)
    if not spec.render.keep_intermediates:
        shutil.rmtree(work)
    return final
