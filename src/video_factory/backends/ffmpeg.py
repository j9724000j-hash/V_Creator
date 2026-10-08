from . import Context
from ..util import ffbase

def command(c: Context) -> list[str]:
    vf=f'scale={c.width}:{c.height},setsar=1'
    if c.scene.effect=='ken_burns':
        vf+=f",zoompan=z='min(1.035,1+on*0.035/{c.frames})':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d=1:s={c.width}x{c.height}:fps={c.fps}"
    elif c.scene.effect=='vignette':
        vf+=',vignette=PI/5'
    elif c.scene.effect=='grain':
        vf+=',noise=alls=4:allf=t:all_seed=42'
    if c.scene.transition=='fade':
        d=min(.35,c.scene.duration/4)
        vf+=f',fade=t=in:d={d},fade=t=out:st={c.scene.duration-d}:d={d}'
    return ffbase()+['-loop','1','-framerate',str(c.fps),'-i',str(c.asset),'-vf',vf,
        '-frames:v',str(c.frames),'-an','-c:v','libx264','-threads',str(c.threads),
        '-preset','ultrafast' if c.preset in ('draft','preview') else 'medium',
        '-crf','24' if c.preset!='high' else '18','-pix_fmt','yuv420p','-video_track_timescale','90000',str(c.output)]

class FFmpegBackend:
    def render(self, c: Context):
        c.runner.run(command(c))
