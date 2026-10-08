from . import Context

class MoviePyBackend:
    def render(self,c:Context):
        # MoviePy v2 API: lazy imports keep it optional.
        from moviepy import ImageClip, vfx
        clip=ImageClip(str(c.asset)).with_duration(c.frames/c.fps)
        if c.scene.transition=='fade':
            clip=clip.with_effects([vfx.FadeIn(.25),vfx.FadeOut(.25)])
        try:
            clip.write_videofile(str(c.output),fps=c.fps,codec='libx264',audio=False,
                                 threads=c.threads,preset='medium',ffmpeg_params=['-pix_fmt','yuv420p','-video_track_timescale','90000'])
        finally:
            clip.close()
