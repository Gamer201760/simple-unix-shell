import pytest

from entity.command import Command
from entity.context import CommandContext
from entity.errors import DomainError
from test.conftest import setup_tree


@pytest.mark.parametrize(
    'args',
    (
        ['/vfs/not-a-dir'],
        ['photos'],
    ),
)
def test_invalid(args: list[str], ls: Command, fs, ctx: CommandContext):
    setup_tree(fs, ctx)
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
        ['/vfs'],
        ['/vfs/home/test2/..'],
        ['etc'],
        ['etc/../..'],
    ),
)
def test_valid(args: list[str], ls: Command, fs, ctx: CommandContext):
    setup_tree(fs, ctx)
    ls.execute(args, [], ctx)


@pytest.mark.parametrize(
    'args,expected',
    [
        (['~'], 'etc'),
        (['/vfs/home/test2'], ''),
        (['../..'], 'home\netc\nphotos'),
        (['etc'], ''),
        (['etc/..'], 'etc'),
        (['etc/../..'], 'test\ntest2'),
        (['etc/../../../photos'], 'photo1.png\nmy.png\nAzamat.jpg\nnew photo.png'),
    ],
)
def test_execute(
    args: list[str],
    expected: str,
    ls: Command,
    fs,
    ctx: CommandContext,
):
    setup_tree(fs, ctx)
    assert ls.execute(args, [], ctx) == expected
