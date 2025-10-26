from entity.command import Command
from entity.context import CommandContext
from entity.errors import CommandNotFoundError
from usecase.interface import HistoryRepository


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
            self._history_repo.add(name, args, flags)  # TODO: refactor
            return cmd.description
        res = cmd.execute(args, flags, self._context)
        self._history_repo.add(name, args, flags)
        return res
