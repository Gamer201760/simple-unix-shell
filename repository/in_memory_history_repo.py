from entity.command import UndoCommand


class InMemoryHistory:
    def __init__(self) -> None:
        self._history: list[UndoCommand] = []

    def add(self, command: UndoCommand) -> None:
        """Добавляет команду в историю"""
        self._history.append(command)

    def last(self) -> UndoCommand | None:
        """Возвращает последнюю команду, либо None если её нет"""
        if len(self._history) == 0:
            return None
        return self._history[-1]

    def pop(self) -> UndoCommand | None:
        """Удаляет и возвращает последнюю команду, либо None если её нет"""
        if len(self._history) == 0:
            return None
        return self._history.pop()

    def all(self) -> list[UndoCommand]:
        """Возвращает список команд истории"""
        return self._history

    def clear(self) -> None:
        """Очищает историю команд"""
        self._history.clear()
