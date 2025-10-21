from typing import Protocol

from entity.command import UndoCommand


class FileSystemRepository(Protocol):
    def list_dir(self, path: str) -> list[str]:
        """Возвращает список объектов в директории"""
        raise NotImplementedError

    def is_dir(self, path: str) -> bool:
        """Проверяет является ли путь директорией"""
        raise NotImplementedError

    @property
    def current(self) -> str:
        """Возвращает текущий абсолютный путь"""
        raise NotImplementedError

    def set_current(self, path: str) -> None:
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
