from typing import Sequence

from entity.undo import UndoRecord


class InMemoryUndoRepository:
    def __init__(self):
        self._history: list[Sequence[UndoRecord]] = []

    def add(self, record: Sequence[UndoRecord]) -> None:
        """Добавить одну пачку UndoRecord (один или несколько)"""
        self._history.append(record)

    def pop(self) -> Sequence[UndoRecord] | None:
        """Извлечь последнюю пачку UndoRecord (undo-операцию), вернуть или None"""
        if not self._history:
            return None
        return self._history.pop()

    def last(self) -> Sequence[UndoRecord] | None:
        """Получить последнюю пачку UndoRecord без удаления"""
        if not self._history:
            return None
        return self._history[-1]

    def clear(self) -> None:
        """Очистить весь стек undo"""
        self._history.clear()

    def all(self) -> list[Sequence[UndoRecord]]:
        """Получить весь стек undo"""
        return self._history
