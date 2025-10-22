from entity.context import CommandContext
from usecase.interface import HistoryRepository


class UndoCmd:
    def __init__(self, hs: HistoryRepository) -> None:
        self._hs = hs

    @property
    def name(self) -> str:
        """Имя команды"""
        return 'undo'

    @property
    def description(self) -> str:
        """Описание команды"""
        return 'Отменяет последнюю команду'

    def execute(self, args: list[str], flags: list[str], ctx: CommandContext) -> str:
        """Выполнение команды, выбрасывает DomainError при ошибке"""
        return ''
