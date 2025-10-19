from usecase.interface import UndoCommand


class MockHistoryRepository:
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
