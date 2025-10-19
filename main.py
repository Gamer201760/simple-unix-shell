from adapter.cli import CLIAdapter
from entity.command import Command
from entity.context import CommandContext
from repository.in_memory_fs import InMemoryFileSystemRepository
from repository.mock_history_repo import MockHistoryRepository
from usecase.command.cd import CdCommand
from usecase.command.ls import LsCommand
from usecase.command.pwd import PwdCommand
from usecase.command.whoami import WhoAmICommand
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


def main():
    context = CommandContext(
        pwd='/home/test',
        user='test',
        home='/home/test',
    )
    fs_repo = InMemoryFileSystemRepository(context, UNIX_TREE)
    history = MockHistoryRepository()
    commands: dict[str, Command] = {
        cmd.name: cmd
        for cmd in [
            PwdCommand(),
            WhoAmICommand(),
            LsCommand(fs_repo),
            CdCommand(fs_repo),
        ]
    }
    shell = Shell(history=history, context=context, commands=commands)
    cli = CLIAdapter(shell)
    cli.run()


if __name__ == '__main__':
    main()
