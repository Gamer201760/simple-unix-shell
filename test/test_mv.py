# tests/test_mv.py

from pathlib import Path

import pytest

from entity.command import Command
from entity.context import CommandContext
from entity.errors import ValidationError


def _setup_tree_for_mv(fs, ctx: CommandContext):
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

    fs.create_file('/vfs/photos/photo1.png', contents='IMG1')
    fs.create_file('/vfs/photos/my.png', contents='IMG2')
    fs.create_file('/vfs/photos/Azamat.jpg', contents='IMG3')
    fs.create_file('/vfs/photos/new photo.png', contents='IMG4')


@pytest.mark.parametrize(
    'args',
    (
        ['not-exist.png', 'photos/my.png'],
        ['/vfs/photos', '/vfs/photos/photo1.png'],
        ['/vfs/photos/photo1.png'],
    ),
)
def test_invalid_mv(args: list[str], mv: Command, fs, ctx: CommandContext):
    _setup_tree_for_mv(fs, ctx)
    with pytest.raises(ValidationError):
        mv.execute(args, [], ctx)


@pytest.mark.parametrize(
    'src, dst, expected_path',
    [
        (
            '/vfs/photos/photo1.png',
            '/vfs/photos/new_photo.png',
            '/vfs/photos/new_photo.png',
        ),
        (
            '/vfs/photos/my.png',
            '/vfs/home/test/etc/my.png',
            '/vfs/home/test/etc/my.png',
        ),
        (
            '/vfs/photos/Azamat.jpg',
            '/vfs/home/test/Azamat.jpg',
            '/vfs/home/test/Azamat.jpg',
        ),
        ('/vfs/photos/new photo.png', '~', '/vfs/home/test/new photo.png'),
        # move dir into another dir
        ('/vfs/home/test/etc', '/vfs/photos/etc', '/vfs/photos/etc'),
    ],
)
def test_valid_mv(
    src: str,
    dst: str,
    expected_path: str,
    mv: Command,
    fs,
    ctx: CommandContext,
):
    _setup_tree_for_mv(fs, ctx)
    mv.execute([src, dst], [], ctx)
    assert Path(expected_path).exists()


@pytest.mark.parametrize(
    'src, dst',
    [
        (
            '/vfs/photos/photo1.png',
            '/vfs/home/test/etc/photo1.png',
        ),
    ],
)
def test_mv_remove_from_src_and_appear_in_dst(
    src: str,
    dst: str,
    mv: Command,
    fs,
    ctx: CommandContext,
):
    _setup_tree_for_mv(fs, ctx)
    mv.execute([src, dst], [], ctx)
    assert not Path(src).exists()
    assert Path(dst).exists()
