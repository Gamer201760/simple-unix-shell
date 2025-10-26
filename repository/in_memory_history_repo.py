class InMemoryHistory:
    def __init__(self) -> None:
        self._history: list[str] = []

    def add(self, name: str, args: list[str], flags: list[str]) -> None:
        """Добавляет команду в историю"""
        self._history.append(name + ' ' + ' '.join(args) + ' '.join(flags))

    def last(self, n: int) -> list[str]:
        """Возвращает последние n команд"""
        return self._history[-n:]

    def all(self) -> list[str]:
        """Возвращает последние n команд"""
        return self._history

    def clear(self) -> None:
        """Очищает историю команд"""
        self._history.clear()
