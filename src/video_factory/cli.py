import argparse
import json
from pathlib import Path
import shutil
import sys
from pydantic import ValidationError
from .brief import create, from_brief
from .pipeline import render
from .planner import plan
from .spec import Spec, load
from .tools import doctor
from .util import ROOT, ProductionError, safe_path, write_json
from .validation import validate

def parser():
    p=argparse.ArgumentParser(prog='video-factory',description='CPU-first local video studio; zero implicit external API calls')
    sub=p.add_subparsers(dest='command',required=True)
    sub.add_parser('doctor')
    for name in ('plan','render','preview','validate','clean'):
        q=sub.add_parser(name); q.add_argument('project',help='Project directory, YAML/JSON spec, or brief for plan/render')
        if name in ('render','preview'):
            q.add_argument('--preset',choices=['draft','preview','standard','high'])
            q.add_argument('--resolution',default='spec')
            q.add_argument('--keep-intermediates',action=argparse.BooleanOptionalAction,default=None)
        if name=='clean':
            q.add_argument('--yes',action='store_true',help='Delete generated work/cache, never source or final output')
    q=sub.add_parser('create'); q.add_argument('--topic',required=True)
    q.add_argument('--duration',type=int,default=30); q.add_argument('--width',type=int,default=1080)
    q.add_argument('--height',type=int,default=1920); q.add_argument('--project',required=True)
    return p

def main(argv=None):
    args=parser().parse_args(argv)
    try:
        if args.command=='doctor':
            report=doctor(); print(json.dumps(report,indent=2)); return 0 if report['ok'] else 1
        if args.command=='create':
            spec=from_brief(args.topic,args.duration,args.width,args.height,args.topic)
            project=safe_path(ROOT,args.project); create(project,spec); print(project); return 0
        project=safe_path(ROOT,args.project)
        if not project.exists():
            if args.command not in ('plan','render') or not any(c.isspace() for c in args.project):
                raise ProductionError(f'Project does not exist: {args.project}')
            spec=from_brief(args.project)
            if args.command=='plan':
                print(json.dumps({'specification':spec.model_dump(),'plan':plan(spec)},indent=2)); return 0
            project=ROOT/'videos'/spec.video.id
            if not project.exists():
                create(project,spec)
            elif load(project).brief!=args.project:
                raise ProductionError('Generated project collision; use create --project explicitly')
        if args.command=='plan':
            print(json.dumps(plan(load(project)),indent=2)); return 0
        if args.command in ('render','preview'):
            print(render(project,args.preset or ('preview' if args.command=='preview' else None),
                         args.resolution,args.keep_intermediates)); return 0
        if project.is_file():
            project=project.parent
        if args.command=='validate':
            manifest=json.loads((project/'output/production-manifest.json').read_text())
            report=validate(project/'output/final.mp4',Spec.model_validate(manifest['effective_specification']))
            write_json(project/'output/validation-report.json',report)
            print(json.dumps({'ok':report['ok'],'checks':report['checks']},indent=2)); return 0 if report['ok'] else 1
        if args.command=='clean':
            load(project)
            if not args.yes:
                raise ProductionError('Use --yes to remove work/ and .cache/; output/ is preserved')
            for name in ('work','.cache'):
                target=safe_path(project,name)
                if target.exists():
                    shutil.rmtree(target)
            return 0
    except (ProductionError,ValidationError,ValueError,OSError) as exc:
        print(json.dumps({'error':type(exc).__name__,'message':str(exc)},ensure_ascii=False),file=sys.stderr)
        return 1
    return 0
