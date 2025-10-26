from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class UndoRecord:
    action: Literal['mv', 'cp', 'rm']
    src: str  # исходный путь (откуда перемещали или копировали, или что удаляли)
    dst: str  # целевой путь (куда перемещали/копировали или куда клали файл при rm)
    overwrite: bool = False  # была ли перезапись (для mv, cp)
    overwritten_path: str | None = None  # путь перезаписанного объекта
