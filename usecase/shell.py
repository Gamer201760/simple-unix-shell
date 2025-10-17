from logging import getLogger

from entity.command import Command
from entity.errors import CommandNotFoundError, DomainError
from usecase.interface import HistoryRepository, UndoCommand

logger = getLogger(__name__)


class Shell:
    def __init__(self, history: HistoryRepository):
        self._history_repo = history
        self.commands: dict[str, Command] = {}
        self.commands['undo'] = self._history_repo.to_cmd()  # TODO: refactor

    def add_command(self, name, command: Command):
        self.commands[name] = command

    def run(self, name, args):
        cmd = self.commands.get(name)
        if not cmd:
            raise CommandNotFoundError()
        try:
            cmd.validate_args(args)
            cmd.execute(args)
            if isinstance(cmd, UndoCommand):
                self._history_repo.add(cmd)
        except DomainError as e:
            logger.error(e)
