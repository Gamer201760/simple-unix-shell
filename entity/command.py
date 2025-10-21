from typing import Protocol, runtime_checkable

from entity.context import CommandContext


@runtime_checkable
class UndoCommand(Protocol):
    def undo(self): ...


class Command(Protocol):
    @property
    def name(self) -> str:
        """Имя команды"""
        raise NotImplementedError

    @property
    def description(self) -> str:
        """Описание команды"""
        raise NotImplementedError

    def execute(self, args: list[str], flags: list[str], ctx: CommandContext) -> str:
        """Выполнение команды, выбрасывает DomainError при ошибке"""
        raise NotImplementedError
