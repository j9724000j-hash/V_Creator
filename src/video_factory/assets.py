"""Deterministic procedural visuals. No network asset discovery."""
import html
import json
import math
from pathlib import Path
import textwrap
from PIL import Image, ImageDraw, ImageFont, ImageOps
from .spec import Scene
from .util import ROOT, Runner, binary, digest, file_hash, safe_path

THEME = json.loads((ROOT / 'brand/theme.json').read_text())

def font(size: int, bold=False):
    suffix = '-Bold' if bold else ''
    path = Path(f'/usr/share/fonts/truetype/dejavu/DejaVuSans{suffix}.ttf')
    return ImageFont.truetype(str(path), max(10,size)) if path.exists() else ImageFont.load_default(size=max(10,size))

def make_asset(scene: Scene, project: Path, work: Path, width: int, height: int) -> dict:
    source_hashes = [file_hash(safe_path(project,a.path)) for a in scene.assets]
    key = digest([scene.model_dump(),width,height,THEME,source_hashes])
    path = work / f'{scene.id}_hero_{key}.png'
    svg = path.with_suffix('.svg')
    margin = int(width * THEME['safe_margin'])
    image = Image.new('RGB',(width,height),THEME['background'])
    d = ImageDraw.Draw(image)
    # Sparse deterministic star field, no randomly named files.
    import random
    rng = random.Random(key)
    for _ in range(90):
        x,y=rng.randrange(width),rng.randrange(height)
        d.ellipse((x,y,x+1,y+1), fill='#3d4b69')
    cx,cy=width//2,int(height*.48)
    radius=int(min(width,height)*.19)
    scientific = scene.type in ('scientific_animation','explanatory_diagram','cinematic_visual')
    if scene.assets:
        asset = safe_path(project,scene.assets[0].path)
        with Image.open(asset) as supplied:
            tile=ImageOps.fit(supplied.convert('RGB'),(width-2*margin,int(height*.48)))
        image.paste(tile,(margin,int(height*.26)))
        method='local-image-fit'
    elif scene.type == 'chart':
        vmax=max([abs(v) for v in scene.values]+[1])
        step=(width-2*margin)/max(1,len(scene.values))
        for i,v in enumerate(scene.values):
            x=margin+i*step
            top=cy+radius-abs(v)/vmax*radius*2
            d.rounded_rectangle((x,top,x+step*.65,cy+radius),radius=4,fill=THEME['accent'])
        method='procedural-chart'
    elif scientific:
        for i in range(7,0,-1):
            r=radius+i*4
            d.ellipse((cx-r,cy-r*.42,cx+r,cy+r*.42),outline=THEME['secondary'],width=max(1,width//250))
        d.ellipse((cx-radius*.62,cy-radius*.62,cx+radius*.62,cy+radius*.62),fill='#010309',outline=THEME['accent'],width=2)
        d.text((margin,int(height*.72)),'CONCEPTUAL DIAGRAM · NOT TO SCALE',font=font(width//40),fill=THEME['muted'])
        method='procedural-conceptual-diagram'
    else:
        d.rounded_rectangle((margin,cy-radius,width-margin,cy+radius),radius=20,outline=THEME['accent'],width=3)
        d.text((margin*1.4,cy-radius*.4),scene.intent[:28] or 'DISCOVER',font=font(width//14,True),fill=THEME['accent'])
        method='procedural-title-card'
    d.rectangle((margin,int(height*.08),margin+width*.12,int(height*.08)+3),fill=THEME['accent'])
    d.text((margin,int(height*.105)),'V / FACTORY     •     FIELD NOTES',font=font(width//36),fill=THEME['muted'])
    title=scene.title or scene.id.replace('-',' ').title()
    for i,line in enumerate(textwrap.wrap(title,24)[:3]):
        d.text((margin,int(height*.17)+i*width*.068),line,font=font(width//18,True),fill=THEME['foreground'])
    desc=scene.visual_description or scene.intent
    for i,line in enumerate(textwrap.wrap(desc,46)[:3]):
        d.text((margin,int(height*.79)+i*width*.042),line,font=font(width//30),fill=THEME['muted'])
    image.save(path)
    # A reusable vector counterpart, explicitly distinct from the raster artwork.
    svg.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"><rect width="100%" height="100%" fill="{THEME["background"]}"/><circle cx="{cx}" cy="{cy}" r="{radius}" fill="none" stroke="{THEME["accent"]}"/><text x="{margin}" y="{height*.18}" fill="white" font-size="{width//20}">{html.escape(title)}</text></svg>',encoding='utf-8')
    image_tool = binary('magick') or binary('convert')
    if image_tool:
        Runner().run([image_tool,str(path),'-strip',str(path)])
    return {'path':str(path),'sha256':file_hash(path),'vector':str(svg),'method':method,
            'normalizer':'imagemagick' if image_tool else 'pillow','source': [a.model_dump() for a in scene.assets],
            'license':'project-generated geometry; local image rights remain with their owners'}
