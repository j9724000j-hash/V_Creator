"""Opt-in provider contract. Core never instantiates a network provider."""
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Literal
from ..util import ProductionError

@dataclass(frozen=True)
class Request:
    kind: Literal['images','video','audio','tts']
    prompt: str
    output: Path
    allow_external: bool = False

@dataclass(frozen=True)
class Result:
    path: Path
    source: str
    license: str
    provider: str
    model: str

class Provider(Protocol):
    external: bool
    def generate(self, request: Request) -> Result: ...

def invoke(provider: Provider, request: Request) -> Result:
    if provider.external and not request.allow_external:
        raise ProductionError('External generation requires explicit opt-in; no implicit paid usage.')
    result=provider.generate(request)
    if not result.path.is_file() or not result.source or not result.license:
        raise ProductionError('Provider must return an existing asset with provenance and license')
    return result
