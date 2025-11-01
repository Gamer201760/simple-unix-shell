from dataclasses import dataclass
from typing import Literal, Protocol, Sequence, runtime_checkable


@dataclass(frozen=True)
class UndoRecord:
    action: Literal['mv', 'cp', 'rm']
    src: str
    dst: str
    overwrite: bool = False
    overwritten_path: str | None = None


@runtime_checkable
class UndoCommand(Protocol):
    def undo(self) -> Sequence[UndoRecord]: ...
