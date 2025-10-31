from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class UndoRecord:
    action: Literal['mv', 'cp', 'rm']
    src: str
    dst: str
    overwrite: bool = False
    overwritten_path: str | None = None
