import os
from . import Context
from ..util import ROOT, ffbase

class ManimBackend:
    def render(self,c:Context):
        # No user-supplied Python is executed. Scene uses no LaTeX.
        folder=c.output.parent/'manim'
        config=c.output.with_suffix('.cfg')
        config.write_text('[CLI]\nframe_rate = '+str(c.fps)+'\npixel_width = '+str(c.width)+'\npixel_height = '+str(c.height)+'\n')
        c.runner.run(['manim','--renderer','cairo','--disable_caching','--config_file',str(config),
            '--media_dir',str(folder),'-o','concept',str(ROOT/'manim/concept.py'),'OrbitDiagram'])
        candidates=list(folder.rglob('concept.mp4'))
        if not candidates:
            raise RuntimeError('Manim returned no scene output')
        c.runner.run(ffbase()+['-i',str(candidates[0]),'-vf',
            f'tpad=stop_mode=clone:stop_duration={c.scene.duration},fps={c.fps},scale={c.width}:{c.height},setsar=1',
            '-frames:v',str(c.frames),'-an','-c:v','libx264','-threads',str(c.threads),'-pix_fmt','yuv420p','-video_track_timescale','90000',str(c.output)])
