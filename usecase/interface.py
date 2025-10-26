from typing import Protocol, Sequence

from entity.undo import UndoRecord


class FileSystemRepository(Protocol):
    def walk(self, path: str) -> list[str]:
        """
        Возвращает список всех файлов и директорий,
        начиная с path рекурсивно
        """
        raise NotImplementedError

    def mkdir(self, path: str) -> None:
        """Создаёт директорию"""
        raise NotImplementedError

    def read(self, path: str) -> str:
        """Читает содержимое файла как строку"""
        raise NotImplementedError

    def write(self, path: str, data: str) -> None:
        """Перезаписывает (или создаёт) файл"""
        raise NotImplementedError

    def stat(self, path: str) -> dict:
        """Возвращает информацию о файле/директории"""
        raise NotImplementedError

    def copy(self, source: str, dest: str) -> None:
        """Копирует файл из source в dest"""
        raise NotImplementedError

    def delete(self, path: str) -> str:
        """Удаляет файл path"""
        raise NotImplementedError

    def move(self, source: str, dest: str) -> None:
        """Перемещает файл из source в dest"""
        raise NotImplementedError

    def is_file(self, path: str) -> bool:
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
