from typing import Protocol

from entity.command import Command


class FileSystemRepository(Protocol):
    def move(self, source: str, dest: str) -> None:
        """Перемещает файл из source в dest"""
        raise NotImplementedError

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
    def add(self, command: Command) -> None:
        """Добавляет команду в историю"""
        raise NotImplementedError

    def last(self, n: int) -> list[Command]:
        """Возвращает последние n команд"""
        raise NotImplementedError

    def pop(self) -> Command | None:
        """Удаляет и возвращает последнюю команду, либо None если её нет"""
        raise NotImplementedError

    def all(self) -> list[Command]:
        """Возвращает список команд истории"""
        raise NotImplementedError

    def clear(self) -> None:
        """Очищает историю команд"""
        raise NotImplementedError
