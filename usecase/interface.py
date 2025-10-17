from typing import Protocol, runtime_checkable

from entity.command import Command


@runtime_checkable
class UndoCommand(Protocol):
    def undo(self): ...


class HistoryRepository(Protocol):
    def to_cmd(self) -> Command:
        """Добавляет команду в shell"""
        raise NotImplementedError

    def add(self, command: UndoCommand) -> None:
        """Добавляет команду в историю"""
        raise NotImplementedError

    def last(self) -> UndoCommand | None:
        """Возвращает последнюю команду, либо None если её нет"""
        raise NotImplementedError

    def pop(self) -> UndoCommand | None:
        """Удаляет и возвращает последнюю команду, либо None если её нет"""
        raise NotImplementedError

    def all(self) -> list[UndoCommand]:
        """Возвращает список команд истории"""
        raise NotImplementedError

    def clear(self) -> None:
        """Очищает историю команд"""
        raise NotImplementedError
