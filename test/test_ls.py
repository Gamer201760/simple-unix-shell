import pytest

from entity.command import Command
from entity.context import CommandContext
from entity.errors import DomainError
from repository.in_memory_fs import InMemoryFileSystemRepository
from usecase.command.ls import Ls
from usecase.interface import FileSystemRepository

UNIX_TREE = {
    '/': ['home', 'etc', 'photos'],
    '/home': ['test', 'test2'],
    '/home/test': ['etc'],
    '/home/test/etc': [],
    '/home/test2': [],
    '/etc': [],
    '/photos': ['photo1.png', 'my.png', 'Azamat.jpg'],
}


@pytest.fixture
def ctx() -> CommandContext:
    return CommandContext(pwd='/home/test', home='/home/test', user='test')


@pytest.fixture
def fs(ctx: CommandContext) -> FileSystemRepository:
    return InMemoryFileSystemRepository(UNIX_TREE)


@pytest.fixture
def ls(fs: FileSystemRepository) -> Command:
    return Ls(fs)


@pytest.mark.parametrize(
    'args',
    (
        ['/not-a-dir'],
        ['photos'],
    ),
)
def test_invalid(args: list[str], ls: Command, ctx: CommandContext):
    with pytest.raises(DomainError):
        ls.execute(args, [], ctx)


@pytest.mark.parametrize(
    'args',
    (
        ['.'],
        ['./'],
        ['..'],
        ['../'],
        ['../..'],
        ['../../.'],
        ['../.'],
        ['~'],
        ['/'],
        ['/home/test2/..'],
        ['/../../'],
        ['etc'],
        ['etc/../..'],
    ),
)
def test_valid(args: list[str], ls: Command, ctx: CommandContext):
    ls.execute(args, [], ctx)


@pytest.mark.parametrize(
    'args,expected',
    [
        (['~'], 'etc'),
        (['/home/test2'], ''),
        (['/home/..'], 'home\netc\nphotos'),
        (['etc'], ''),
        (['etc/..'], 'etc'),
        (['etc/../..'], 'test\ntest2'),
        (['etc/../../../photos'], 'photo1.png\nmy.png\nAzamat.jpg'),
    ],
)
def test_execute(
    args: list[str],
    expected: str,
    ls: Command,
    ctx: CommandContext,
):
    assert ls.execute(args, [], ctx) == expected
