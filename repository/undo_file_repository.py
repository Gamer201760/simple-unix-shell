import json
from dataclasses import asdict
from pathlib import Path
from typing import Sequence

from entity.undo import UndoRecord


class UndoJsonRepository:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def add(self, record: Sequence[UndoRecord]) -> None:
        data = self._read_raw()
        batch = [asdict(r) for r in record]
        data.append(batch)
        self._write_raw(data)

    def pop(self) -> Sequence[UndoRecord] | None:
        data = self._read_raw()
        if not data:
            return None
        batch_dicts = data.pop()
        self._write_raw(data)
        return tuple(self._from_dict(d) for d in batch_dicts)

    def last(self) -> Sequence[UndoRecord] | None:
        data = self._read_raw()
        if not data:
            return None
        batch_dicts = data[-1]
        return tuple(self._from_dict(d) for d in batch_dicts)

    def clear(self) -> None:
        self._write_raw([])

    def all(self) -> list[Sequence[UndoRecord]]:
        data = self._read_raw()
        return [tuple(self._from_dict(d) for d in batch) for batch in data]

    def _read_raw(self) -> list[list[dict]]:
        if not self.path.exists():
            return []
        with self.path.open('r', encoding='utf-8') as f:
            return json.load(f)

    def _write_raw(self, obj: list[list[dict]]) -> None:
        with self.path.open('w', encoding='utf-8') as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)

    @staticmethod
    def _from_dict(d: dict) -> UndoRecord:
        return UndoRecord(**d)
