import pytest

from entity.command import Command
from entity.context import CommandContext
from entity.errors import ValidationError
from test.conftest import setup_tree


@pytest.mark.parametrize(
    'args',
    (
        ['', ''],
        ['', '', ''],
        ['/vfs/not-a-dir'],
        ['photos'],
        ['/vfs/photos/photo1.png'],
    ),
)
def test_invalid(args: list[str], cd: Command, fs, ctx: CommandContext):
    setup_tree(fs, ctx)
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
        ['/vfs'],
        ['/vfs/home/test2/..'],
        ['etc'],
        ['etc/../..'],
    ),
)
def test_valid(args: list[str], cd: Command, fs, ctx: CommandContext):
    setup_tree(fs, ctx)
    cd.execute(args, [], ctx)


@pytest.mark.parametrize(
    'args,expected',
    [
        (['~'], '/vfs/home/test'),
        (['/vfs/home'], '/vfs/home'),
        (['/vfs/home/test2'], '/vfs/home/test2'),
        (['/vfs/home/..'], '/vfs'),
        (['etc'], '/vfs/home/test/etc'),
        (['etc/..'], '/vfs/home/test'),
        (['etc/../..'], '/vfs/home'),
    ],
)
def test_execute(
    args: list[str],
    expected: str,
    cd: Command,
    fs,
    ctx: CommandContext,
):
    setup_tree(fs, ctx)
    cd.execute(args, [], ctx)
    assert ctx.pwd == expected
