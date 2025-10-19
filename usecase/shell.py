from entity.command import Command
from entity.context import CommandContext
from entity.errors import CommandNotFoundError
from usecase.interface import FileSystemRepository, HistoryRepository, UndoCommand


class Shell:
    def __init__(
        self,
        history: HistoryRepository,
        fs: FileSystemRepository,
        user: str,
    ):
        self._history_repo = history
        self._fs_repo = fs
        self._context = CommandContext(
            pwd=self._fs_repo.current,
            home=self._fs_repo.home,
            user=user,
        )
        self._commands: dict[str, Command] = {}

    def add_command(self, name, command: Command):
        self._commands[name] = command

    def run(self, name, args):
        cmd = self._commands.get(name)
        if not cmd:
            raise CommandNotFoundError()
        cmd.validate_args(args)
        cmd.execute(args, self._context)
        if isinstance(cmd, UndoCommand):
            self._history_repo.add(cmd)
