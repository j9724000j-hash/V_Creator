from . import Context
from ..effects import EFFECTS
from ..util import ffbase

def command(c: Context) -> list[str]:
    vf = [f'scale={c.width}:{c.height}:flags=lanczos,setsar=1']
    template = EFFECTS[c.scene.effect]
    if template:
        vf.append(',' + template.format(w=c.width, h=c.height, fps=c.fps, frames=c.frames))
    d = min(.35, c.scene.duration / 4)
    if c.scene.transition != 'cut':
        vf.append(f',fade=t=in:d={d},fade=t=out:st={c.scene.duration-d}:d={d}')
    video_filter = ''.join(vf)
    return ffbase() + ['-loop', '1', '-framerate', str(c.fps), '-i', str(c.asset), '-vf', video_filter,
        '-frames:v', str(c.frames), '-an', '-c:v', 'libx264', '-threads', str(c.threads),
        '-preset', 'ultrafast' if c.preset in ('draft', 'preview') else 'medium',
        '-crf', '24' if c.preset != 'high' else '18', '-pix_fmt', 'yuv420p', '-video_track_timescale', '90000', str(c.output)]

class FFmpegBackend:
    def render(self, c: Context):
        c.runner.run(command(c))
