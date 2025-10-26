from typing import Protocol


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
