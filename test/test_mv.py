from copy import deepcopy

import pytest

from entity.command import Command
from entity.context import CommandContext
from entity.errors import ValidationError
from repository.in_memory_fs import InMemoryFileSystemRepository
from usecase.command.mv import Mv
from usecase.interface import FileSystemRepository

UNIX_TREE = {
    '/': ['home', 'etc', 'photos'],
    '/home': ['test', 'test2'],
    '/home/test': ['etc'],
    '/home/test/etc': [],
    '/home/test2': [],
    '/etc': [],
    '/photos': ['photo1.png', 'my.png', 'Azamat.jpg', 'new photo.png'],
}


@pytest.fixture
def ctx() -> CommandContext:
    return CommandContext(pwd='/home/test', home='/home/test', user='test')


@pytest.fixture
def fs(ctx: CommandContext) -> FileSystemRepository:
    return InMemoryFileSystemRepository(deepcopy(UNIX_TREE))


@pytest.fixture
def mv(fs: FileSystemRepository) -> Command:
    return Mv(fs)


@pytest.mark.parametrize(
    'args',
    (
        ['not-exist.png', 'photos/my.png'],
        ['photos', 'not-dir'],
        ['photos', 'photos/photo1.png'],  # dest — это файл, а source — директория
        ['photos/photo1.png'],  # мало аргументов
    ),
)
def test_invalid_mv(args: list[str], mv: Command, ctx: CommandContext):
    with pytest.raises(ValidationError):
        mv.execute(args, [], ctx)


@pytest.mark.parametrize(
    'src, dst, expected',
    [
        ('/photos/photo1.png', '/photos/new_photo.png', ('/photos', 'new_photo.png')),
        ('/photos/my.png', '/home/test/etc/my.png', ('/home/test/etc', 'my.png')),
        ('/photos/Azamat.jpg', '/home/test/Azamat.jpg', ('/home/test', 'Azamat.jpg')),
        ('/photos/new photo.png', '~', ('/home/test', 'new photo.png')),
        # move dir into another dir
        ('/home/test/etc', '/photos/etc', ('/photos', 'etc')),
    ],
)
def test_valid_mv(
    src: str,
    dst: str,
    expected: tuple[str, str],
    mv: Command,
    fs: FileSystemRepository,
    ctx: CommandContext,
):
    mv.execute([src, dst], [], ctx)
    # expected: (dir, name) should exist after mv
    target_dir, target_name = expected
    assert target_dir in fs._tree
    assert target_name in fs._tree[target_dir]


@pytest.mark.parametrize(
    'args, assert_src, assert_dst',
    [
        # mv file: should disappear from src, appear at dst
        (
            ['/photos/photo1.png', '/home/test/etc/photo1.png'],
            ('/photos', 'photo1.png', False),  # file gone from src_dir
            ('/home/test/etc', 'photo1.png', True),  # file appeared in dst_dir
        ),
    ],
)
def test_mv_remove_from_src_and_appear_in_dst(
    args: list[str],
    assert_src: tuple[str, str, bool],
    assert_dst: tuple[str, str, bool],
    mv: Command,
    fs: FileSystemRepository,
    ctx: CommandContext,
):
    mv.execute(args, [], ctx)
    src_dir, src_name, src_should_exist = assert_src
    dst_dir, dst_name, dst_should_exist = assert_dst
    assert (src_name in fs._tree[src_dir]) == src_should_exist
    assert (dst_name in fs._tree[dst_dir]) == dst_should_exist
