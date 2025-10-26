from entity.command import Command, UndoCommand
from entity.context import CommandContext
from entity.errors import CommandNotFoundError
from usecase.interface import HistoryRepository, UndoRepository


class Shell:
    def __init__(
        self,
        history: HistoryRepository,
        undo_repo: UndoRepository,
        context: CommandContext,
        commands: dict[str, Command],
    ):
        self._history_repo = history
        self._undo_repo = undo_repo
        self._context = context
        self._commands = commands

    @property
    def user(self) -> str:
        return self._context.user

    @property
    def pwd(self) -> str:
        return self._context.pwd

    def run(self, name: str, args: list[str], flags: list[str]) -> str:
        cmd = self._commands.get(name)
        if not cmd:
            raise CommandNotFoundError(f'Команда {name} не найдена')
        if '-h' in flags:
            res = cmd.description
        else:
            res = cmd.execute(args, flags, self._context)
            if isinstance(cmd, UndoCommand):
                self._undo_repo.add(cmd.undo())
        self._history_repo.add(name, args, flags)
        return res
