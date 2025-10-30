from adapter.cli import CLIAdapter
from entity.command import Command
from entity.context import CommandContext
from repository.in_memory_fs import InMemoryFileSystemRepository
from repository.in_memory_history_repo import InMemoryHistory
from repository.in_memory_undo_repo import InMemoryUndoRepository
from usecase.command.cat import Cat
from usecase.command.cd import Cd
from usecase.command.cp import Cp
from usecase.command.history import History
from usecase.command.ls import Ls
from usecase.command.mv import Mv
from usecase.command.pwd import Pwd
from usecase.command.rm import Rm
from usecase.command.undo import Undo
from usecase.command.whoami import WhoAmI
from usecase.shell import Shell

UNIX_TREE = {
    '/': ['home', 'etc', 'photos'],
    '/home': ['test', 'test2'],
    '/home/test': ['etc'],
    '/home/test/etc': [],
    '/home/test2': [],
    '/etc': [],
    '/photos': ['photo1.png', 'my.png', 'Azamat.jpg'],
}


def main() -> None:
    fs_repo = InMemoryFileSystemRepository(UNIX_TREE)
    undo_repo = InMemoryUndoRepository()
    history = InMemoryHistory()
    list_cmds: list[Command] = [
        Pwd(),
        WhoAmI(),
        Ls(fs_repo),
        Cd(fs_repo),
        Mv(fs_repo),
        Cp(fs_repo),
        Rm(fs_repo),
        Cat(fs_repo),
        Undo(undo_repo, fs_repo),
        History(history),
    ]
    commands: dict[str, Command] = {cmd.name: cmd for cmd in list_cmds}
    context = CommandContext(
        pwd='/home/test',
        user='test',
        home='/home/test',
    )
    shell = Shell(
        history=history, undo_repo=undo_repo, context=context, commands=commands
    )
    cli = CLIAdapter(shell)
    cli.run()


if __name__ == '__main__':
    main()
