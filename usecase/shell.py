from entity.command import Command
from entity.context import CommandContext
from entity.errors import CommandNotFoundError
from usecase.interface import HistoryRepository, UndoCommand


class Shell:
    def __init__(
        self,
        history: HistoryRepository,
        context: CommandContext,
        commands: dict[str, Command],
    ):
        self._history_repo = history
        self._context = context
        self._commands = commands

    def run(self, name: str, args: list[str]) -> str:
        cmd = self._commands.get(name)
        if not cmd:
            raise CommandNotFoundError()
        cmd.validate_args(args)
        res = cmd.execute(args, self._context)
        if isinstance(cmd, UndoCommand):
            self._history_repo.add(cmd)
        return res
