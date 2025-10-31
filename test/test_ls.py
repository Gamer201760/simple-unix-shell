# tests/test_ls.py

import pytest

from entity.command import Command
from entity.context import CommandContext
from entity.errors import DomainError


def _setup_tree_for_ls(fs, ctx: CommandContext):
    ctx.pwd = '/vfs/home/test'
    ctx.home = '/vfs/home/test'
    ctx.user = 'test'

    fs.create_dir('/vfs')
    fs.create_dir('/vfs/home')
    fs.create_dir('/vfs/etc')
    fs.create_dir('/vfs/photos')

    fs.create_dir('/vfs/home/test')
    fs.create_dir('/vfs/home/test2')

    fs.create_dir('/vfs/home/test/etc')

    fs.create_file('/vfs/photos/photo1.png')
    fs.create_file('/vfs/photos/my.png')
    fs.create_file('/vfs/photos/Azamat.jpg')


@pytest.mark.parametrize(
    'args',
    (
        ['/vfs/not-a-dir'],
        ['photos'],
    ),
)
def test_invalid(args: list[str], ls: Command, fs, ctx: CommandContext):
    _setup_tree_for_ls(fs, ctx)
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
    _setup_tree_for_ls(fs, ctx)
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
        (['etc/../../../photos'], 'photo1.png\nmy.png\nAzamat.jpg'),
    ],
)
def test_execute(
    args: list[str],
    expected: str,
    ls: Command,
    fs,
    ctx: CommandContext,
):
    _setup_tree_for_ls(fs, ctx)
    assert ls.execute(args, [], ctx) == expected
