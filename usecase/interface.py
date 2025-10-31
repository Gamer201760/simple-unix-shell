from typing import Protocol, Sequence

from entity.undo import UndoRecord


class HistoryRepository(Protocol):
    def add(self, name: str, args: list[str], flags: list[str]) -> None:
        """Добавляет команду в историю"""
        raise NotImplementedError

    def last(self, n: int) -> list[str]:
        """Возвращает последние n команд"""
        raise NotImplementedError

    def all(self) -> list[str]:
        """Возвращает все последние команды"""
        raise NotImplementedError

    def clear(self) -> None:
        """Очищает историю команд"""
        raise NotImplementedError


class UndoRepository(Protocol):
    def add(self, record: Sequence[UndoRecord]) -> None:
        """Добавить одну или несколько UndoRecord в стек истории undo"""
        raise NotImplementedError

    def pop(self) -> Sequence[UndoRecord] | None:
        """Извлечь последнюю пачку UndoRecord для отката"""
        raise NotImplementedError

    def last(self) -> Sequence[UndoRecord] | None:
        """Получить последнюю пачку UndoRecord без удаления"""
        raise NotImplementedError

    def clear(self) -> None:
        """Очистить всю историю undo"""
        raise NotImplementedError

    def all(self) -> list[Sequence[UndoRecord]]:
        """Получить весь стек undo, для истории или сериализации"""
        raise NotImplementedError
