from .spec import Spec
from .tools import available
from .util import ProductionError

IMPLEMENTED = {'ffmpeg','remotion','moviepy','manim'}
INTENTS = {'title':'remotion','text':'remotion','chart':'remotion',
           'explanatory_diagram':'remotion','scientific_animation':'manim',
           'python_effect':'moviepy','simulation':'godot','unity_scene':'unity'}

def plan(spec: Spec, availability: dict[str, bool] | None = None) -> dict:
    result = []
    for scene in spec.scenes:
        wanted = scene.tool or (spec.planner.prefer[0] if spec.planner.prefer else INTENTS.get(scene.type,'ffmpeg'))
        candidates = [wanted, *spec.planner.prefer, 'remotion', 'ffmpeg'] if scene.allow_fallback else [wanted]
        selected = None
        for tool in dict.fromkeys(candidates):
            enabled = tool == 'ffmpeg' or tool in spec.planner.enable or scene.tool == tool
            found = availability.get(tool, False) if availability is not None else available(tool)
            if enabled and found and tool in IMPLEMENTED:
                selected = tool
                break
        if not selected:
            raise ProductionError(f'{scene.id}: required backend {wanted} unavailable/disabled; enable fallback explicitly')
        if scene.type in ('simulation','unity_scene') and selected != wanted and not scene.assets:
            raise ProductionError(f'{scene.id}: cannot approximate simulation semantics; supply a pre-rendered image or implement the backend')
        result.append({'scene_id':scene.id,'requested_tool':wanted,'selected_tool':selected,
            'reason':f'{scene.type}: ' + ('intent/override matched' if wanted == selected else f'{wanted} unavailable, disabled or extension-only; labeled 2D approximation'),
            'fallback':None if wanted == selected else selected,
            'duration':scene.duration,'assets': [a.model_dump() for a in scene.assets] or ['procedural diagram/title raster + SVG'],
            'audio': {'narration': bool(scene.narration or scene.narration_asset) and spec.audio.narration,
                      'cues':len(scene.audio_cues)}})
    return {'project_id':spec.video.id,'brief':spec.brief,'assumptions':spec.assumptions,
            'scenes':result,'audio':spec.audio.model_dump(),'render':spec.render.model_dump(),
            'validation':['codec','resolution','fps','duration','audio sync','subtitles','decode','assets'],
            'graph':['spec -> assets -> scenes','script -> narration','music + cues + narration -> mix',
                     'scenes + mix + captions -> encode -> validate -> manifest']}
