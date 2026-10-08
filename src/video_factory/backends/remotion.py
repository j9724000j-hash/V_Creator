import base64
import os
from . import Context
from ..util import ROOT, write_json, ffbase

class RemotionBackend:
    def render(self,c:Context):
        props=c.output.with_suffix('.props.json')
        raw=c.output.with_name('remotion-raw.mp4')
        write_json(props,{'width':c.width,'height':c.height,'fps':c.fps,'frames':c.frames,
            'image':'data:image/png;base64,'+base64.b64encode(c.asset.read_bytes()).decode(),
            'title':c.scene.title,'transition':c.scene.transition})
        c.runner.run([str(ROOT/'node_modules/.bin/remotion'),'render',
            str(ROOT/'remotion/src/index.tsx'),'Scene',str(raw),'--props',str(props),
            '--codec','h264','--pixel-format','yuv420p','--concurrency',str(c.threads),
            '--browser-executable',os.environ['VF_BROWSER'],'--gl','swangle'],cwd=ROOT)

        # Browser exports may include silent audio and full-range YUV. Normalize
        # once at this boundary so mixed-engine concatenation is predictable.
        c.runner.run(ffbase()+['-i',str(raw),'-map','0:v:0','-an',
            '-vf',f'scale={c.width}:{c.height}:out_range=tv,setsar=1,fps={c.fps}',
            '-frames:v',str(c.frames),'-c:v','libx264','-threads',str(c.threads),
            '-pix_fmt','yuv420p','-color_range','tv','-video_track_timescale','90000',str(c.output)])
