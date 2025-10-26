from typing import Protocol, Sequence

from entity.undo import UndoRecord


class FileSystemRepository(Protocol):
    def delete(self, source: str) -> str:
        """Удаляет файл source"""
        raise NotImplementedError

    def move(self, source: str, dest: str) -> None:
        """Перемещает файл из source в dest"""
        raise NotImplementedError

    def exists(self, path: str) -> bool:
        """Проверяет существования файла"""
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


class UndoRepository(Protocol):
    def add(self, record: Sequence[UndoRecord]) -> None:
        """Добавить одну или несколько UndoRecord в стек истории undo"""
        ...

    def pop(self) -> Sequence[UndoRecord] | None:
        """Извлечь последнюю пачку UndoRecord для отката"""
        ...

    def last(self) -> Sequence[UndoRecord] | None:
        """Получить последнюю пачку UndoRecord без удаления"""
        ...

    def clear(self) -> None:
        """Очистить всю историю undo"""
        ...

    def all(self) -> list[Sequence[UndoRecord]]:
        """Получить весь стек undo, для истории или сериализации"""
        ...
