import importlib.util
import os
import shutil
from pathlib import Path
import yaml
from .util import ROOT, Runner, binary

def registry() -> dict:
    data = yaml.safe_load((ROOT / 'config/tools.yaml').read_text())
    required = {'category','command','version_args','required','cpu','license','install','scene_types','fallback','status','docs'}
    for name, tool in data.items():
        if not required <= tool.keys() or tool['fallback'] not in [None, *data]:
            raise ValueError(f'Invalid registry entry: {name}')
    return data

def available(name: str) -> bool:
    if name == 'remotion':
        return (ROOT / 'node_modules/.bin/remotion').exists() and bool(os.getenv('VF_BROWSER'))
    if name in ('moviepy','manim'):
        return importlib.util.find_spec(name) is not None
    return bool(binary(registry()[name]['command']))

def doctor() -> dict:
    tools = {}
    for name, item in registry().items():
        found = available(name)
        version = None
        if found:
            cmd = str(ROOT / 'node_modules/.bin/remotion') if name == 'remotion' else binary(item['command'])
            if cmd:
                try:
                    version = Runner().run([cmd, *item['version_args']], timeout=30).strip()[:300]
                except Exception as exc:
                    version = str(exc)
        tools[name] = {'available': found, 'required': item['required'], 'version': version,
                       'status': item['status'], 'license': item['license']}
    mem = Path('/proc/meminfo')
    return {'ok': all(v['available'] for v in tools.values() if v['required']),
            'tools': tools, 'resources': {'cpus': os.cpu_count(),
                'disk_free_bytes': shutil.disk_usage(ROOT).free,
                'memory': mem.read_text().splitlines()[0] if mem.exists() else 'unknown'}}
