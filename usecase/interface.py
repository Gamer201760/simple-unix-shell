from pathlib import Path
from typing import Protocol, runtime_checkable


@runtime_checkable
class UndoCommand(Protocol):
    def undo(self): ...


class FileSystemRepository(Protocol):
    def get_current(self) -> Path:
        """Возвращает текущий абсолютный путь"""
        raise NotImplementedError

    def set_current(self, path: Path) -> None:
        """Устанавливает текущий каталог (абсолютный путь)"""
        raise NotImplementedError


class HistoryRepository(Protocol):
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


class CommandContext:
    def __init__(
        self,
        path_repo: FileSystemRepository,
        history_repo: HistoryRepository,
    ) -> None:
        self.path_repo = path_repo
        self.history_repo = history_repo
