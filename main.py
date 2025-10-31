import getpass
import os
from pathlib import Path

from adapter.cli import CLIAdapter
from entity.command import Command
from entity.context import CommandContext
from repository.command.cat import Cat
from repository.command.cd import Cd
from repository.command.cp import Cp
from repository.command.exit import Exit
from repository.command.history import History
from repository.command.ls import Ls
from repository.command.mkdir import Mkdir
from repository.command.mv import Mv
from repository.command.pwd import Pwd
from repository.command.rm import Rm
from repository.command.undo import Undo
from repository.command.unzip import Unzip
from repository.command.whoami import WhoAmI
from repository.command.zip import Zip
from repository.in_memory_history_repo import InMemoryHistory
from repository.in_memory_undo_repo import InMemoryUndoRepository
from usecase.shell import Shell

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))


def main() -> None:
    undo_repo = InMemoryUndoRepository()
    history = InMemoryHistory()
    trash_dir = os.path.join(ROOT_DIR, '.trash')
    list_cmds: list[Command] = [
        Exit(),
        Pwd(),
        WhoAmI(),
        Ls(),
        Cd(),
        Mv(),
        Cp(),
        Mkdir(),
        Zip(),
        Unzip(),
        Rm(trash_dir),
        Cat(),
        Undo(undo_repo),
        History(history),
    ]
    commands: dict[str, Command] = {cmd.name: cmd for cmd in list_cmds}
    context = CommandContext(
        pwd=os.getcwd(),
        user=getpass.getuser(),
        home=str(Path.home()),
    )
    shell = Shell(
        history=history, undo_repo=undo_repo, context=context, commands=commands
    )
    cli = CLIAdapter(shell)
    cli.run()


if __name__ == '__main__':
    main()
