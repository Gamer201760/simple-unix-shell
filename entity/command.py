from typing import Protocol, Sequence, runtime_checkable

from entity.context import CommandContext
from entity.undo import UndoRecord


@runtime_checkable
class UndoCommand(Protocol):
    def undo(self) -> Sequence[UndoRecord]: ...


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
