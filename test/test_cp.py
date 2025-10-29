from copy import deepcopy

import pytest

from entity.command import Command
from entity.context import CommandContext
from entity.errors import ValidationError
from repository.in_memory_fs import InMemoryFileSystemRepository
from usecase.command.cp import Cp  # команда для теста
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
    return InMemoryFileSystemRepository(deepcopy(UNIX_TREE))


@pytest.fixture
def cp(fs: FileSystemRepository) -> Command:
    return Cp(fs)


# Копирование директории в несуществующий путь
def test_cp_r_dir_to_new_path_creates_root(
    cp: Command, fs: FileSystemRepository, ctx: CommandContext
):
    assert not fs.is_dir('/backup')
    fs.write('/photos/photo1.png', 'SRC1')
    fs.write('/photos/my.png', 'SRC2')
    fs.write('/photos/Azamat.jpg', 'SRC3')

    cp.execute(['/photos', '/backup'], ['-r'], ctx)
    assert fs.is_dir('/backup')
    assert fs.is_file('/backup/photo1.png')
    assert fs.read('/backup/photo1.png') == 'SRC1'
    assert fs.is_file('/backup/my.png')
    assert fs.read('/backup/my.png') == 'SRC2'
    assert fs.is_file('/backup/Azamat.jpg')
    assert fs.read('/backup/Azamat.jpg') == 'SRC3'


# Копирование директории в существующую директорию
def test_cp_r_dir_into_existing_dir_places_inside(
    cp: Command, fs: FileSystemRepository, ctx: CommandContext
):
    cp.execute(['/photos', '/home'], ['-r'], ctx)
    assert fs.is_dir('/home/photos')
    assert fs.is_file('/home/photos/photo1.png')
    assert fs.is_file('/home/photos/my.png')
    assert fs.is_file('/home/photos/Azamat.jpg')


# Копирование директории без -r должно быть ошибкой
def test_cp_dir_without_r_is_error(
    cp: Command, fs: FileSystemRepository, ctx: CommandContext
):
    with pytest.raises(ValidationError):
        cp.execute(['/photos', '/home/new_photos'], [], ctx)


# Нельзя перезаписать существующий файл директорией
def test_cp_r_dir_over_file_is_error(
    cp: Command, fs: FileSystemRepository, ctx: CommandContext
):
    fs.write('/photos/my.png', 'OLD_FILE')
    with pytest.raises(ValidationError):
        cp.execute(
            ['/home'],
            ['-r'],
            ctx,
        )
    with pytest.raises(ValidationError):
        cp.execute(['/home', '/photos/my.png'], ['-r'], ctx)


# Перезапись файлов внутри существующей директории с undo
def test_cp_r_overwrite_with_undo_records(
    cp: Command, fs: FileSystemRepository, ctx: CommandContext
):
    fs.write('/photos/photo1.png', 'SRC1')
    fs.write('/photos/my.png', 'SRC2')

    if not fs.is_dir('/backup'):
        fs.mkdir('/backup')
    if not fs.is_dir('/backup/photos/'):
        fs.mkdir('/backup/photos')
    fs.write('/backup/photos/photo1.png', 'OLD1')

    cp.execute(['/photos', '/backup'], ['-r'], ctx)
    assert fs.read('/backup/photos/photo1.png') == 'SRC1'
    assert fs.read('/backup/photos/my.png') == 'SRC2'

    undo = getattr(cp, 'undo')()
    copied_targets = {u.dst for u in undo}
    assert '/backup/photos/photo1.png' in copied_targets
    assert '/backup/photos/my.png' in copied_targets
    assert '/backup/photos/Azamat.jpg' in copied_targets

    over = [u for u in undo if u.dst == '/backup/photos/photo1.png']
    for x in over:
        assert x and x.overwrite is True and x.overwritten_path


def test_cp_r_conflict_file_vs_dir_in_tree(
    cp: Command, fs: FileSystemRepository, ctx: CommandContext
):
    if not fs.is_dir('/src'):
        fs.mkdir('/src')
    if not fs.is_dir('/src/docs'):
        fs.mkdir('/src/docs')
    fs.write('/src/docs/readme', 'TEXT')

    if not fs.is_dir('/dst'):
        fs.mkdir('/dst')
    if not fs.is_dir('/dst/docs'):
        fs.mkdir('/dst/docs')
    if not fs.is_dir('/dst/docs/readme'):
        fs.mkdir('/dst/docs/readme')

    with pytest.raises(ValidationError):
        cp.execute(['/src/*', '/dst'], ['-r'], ctx)


# несколько директорий только в существующую директорию
def test_cp_r_multiple_sources_into_existing_dir(
    cp: Command, fs: FileSystemRepository, ctx: CommandContext
):
    if not fs.is_dir('/mnt'):
        fs.mkdir('/mnt')

    cp.execute(['/etc', '/photos', '/mnt'], ['-r'], ctx)
    # обе директории должны оказаться в /mnt
    assert fs.is_dir('/mnt/etc')
    assert fs.is_dir('/mnt/photos')
    assert fs.is_file('/mnt/photos/photo1.png')

    # если dst не директория это ошибка
    with pytest.raises(ValidationError):
        cp.execute(['/etc', '/photos', '/mnt/new_place'], ['-r'], ctx)
