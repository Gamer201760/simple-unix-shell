from typing import Protocol


class Command(Protocol):
    @property
    def name(self) -> str:
        """Имя команды"""
        raise NotImplementedError

    @property
    def description(self) -> str:
        """Описание команды"""
        raise NotImplementedError

    def validate_args(self, args: list[str]) -> None:
        """Валидация аргументов, выбрасывает DomainError при ошибке"""
        raise NotImplementedError

    def execute(self, args: list[str]) -> str:
        """Выполнение команды, выбрасывает DomainError при ошибке"""
        raise NotImplementedError
