from pathlib import Path

import pytest

from entity.command import Command
from entity.context import CommandContext
from entity.errors import ValidationError
from test.conftest import setup_tree


@pytest.mark.parametrize(
    'args',
    (
        ['not-exist.png', 'photos/my.png'],
        ['/vfs/photos', '/vfs/photos/photo1.png'],
        ['/vfs/photos/photo1.png'],
    ),
)
def test_invalid_mv(args: list[str], mv: Command, fs, ctx: CommandContext):
    setup_tree(fs, ctx)
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
    setup_tree(fs, ctx)
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
    setup_tree(fs, ctx)
    mv.execute([src, dst], [], ctx)
    assert not Path(src).exists()
    assert Path(dst).exists()
