from entity.command import Command


class MockHistoryRepository:
    def add(self, command: Command) -> None:
        """Добавляет команду в историю"""
        raise NotImplementedError

    def last(self) -> Command | None:
        """Возвращает последнюю команду, либо None если её нет"""
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
