from entity.command import Command
from entity.errors import CommandNotFoundError
from usecase.interface import FileSystemRepository, HistoryRepository, UndoCommand


class Shell:
    def __init__(
        self,
        history: HistoryRepository,
        file: FileSystemRepository,
    ):
        self._history_repo = history
        self._file_repo = file
        self.commands: dict[str, Command] = {}

    def add_command(self, name, command: Command):
        self.commands[name] = command

    def run(self, name, args):
        cmd = self.commands.get(name)
        if not cmd:
            raise CommandNotFoundError()
        cmd.validate_args(args)
        cmd.execute(args)
        if isinstance(cmd, UndoCommand):
            self._history_repo.add(cmd)
