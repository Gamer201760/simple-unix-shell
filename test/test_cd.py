import pytest

from entity.command import Command
from entity.context import CommandContext
from entity.errors import ValidationError
from repository.in_memory_fs import InMemoryFileSystemRepository
from usecase.command.cd import Cd
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
def cd(fs: FileSystemRepository) -> Command:
    return Cd(fs)


@pytest.mark.parametrize(
    'args',
    (
        ['', ''],
        ['', '', ''],
        ['/not-a-dir'],
        ['photos'],
        ['/photos/photo1.png'],
    ),
)
def test_invalid(args: list[str], cd: Command, ctx: CommandContext):
    with pytest.raises(ValidationError):
        cd.execute(args, [], ctx)


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
def test_valid(args: list[str], cd: Command, ctx: CommandContext):
    cd.execute(args, [], ctx)


@pytest.mark.parametrize(
    'args,expected',
    [
        (['~'], '/home/test'),
        (['/home'], '/home'),
        (['/home/test2'], '/home/test2'),
        (['/home/..'], '/'),
        (['etc'], '/home/test/etc'),
        (['etc/..'], '/home/test'),
        (['etc/../..'], '/home'),
    ],
)
def test_execute(
    args: list[str],
    expected: str,
    cd: Command,
    fs: FileSystemRepository,
    ctx: CommandContext,
):
    cd.execute(args, [], ctx)
    assert fs.current == expected
