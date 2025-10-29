from copy import deepcopy

import pytest

from entity.command import Command
from entity.context import CommandContext
from entity.errors import ValidationError
from repository.in_memory_fs import InMemoryFileSystemRepository
from usecase.command.rm import Rm  # команда для теста
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
def rm(fs: FileSystemRepository) -> Command:
    return Rm(fs)


# Удаление одного файла
def test_rm_file_deletes_and_moves_to_trash(
    rm: Command, fs: FileSystemRepository, ctx: CommandContext
):
    assert fs.is_file('/photos/photo1.png')
    rm.execute(['/photos/photo1.png'], [], ctx)
    assert not fs.is_file('/photos/photo1.png')
    # проверяем, что в .trash появился элемент с префиксом "photo1.png."
    assert '/.trash' in fs._tree
    assert any(name.startswith('photo1.png.') for name in fs._tree['/.trash'])
    # undo-запись содержит dst в .trash
    undo = getattr(rm, 'undo')()
    assert len(undo) == 1
    assert undo[0].action == 'rm'
    assert undo[0].src == '/photos/photo1.png'
    assert undo[0].dst.startswith('/.trash/')


# Удаление директории без -r должно быть ошибкой
def test_rm_dir_without_r_is_error(
    rm: Command, fs: FileSystemRepository, ctx: CommandContext
):
    with pytest.raises(ValidationError):
        rm.execute(['/photos'], [], ctx)


# Рекурсивное удаление директории
def test_rm_r_dir_deletes_recursively(
    rm: Command, fs: FileSystemRepository, ctx: CommandContext
):
    # создаём вложенную структуру
    if not fs.is_dir('/photos/album'):
        fs.mkdir('/photos/album')
    fs.write('/photos/album/p1.jpg', 'X')
    fs.write('/photos/album/p2.jpg', 'Y')

    assert fs.is_dir('/photos')
    assert fs.is_file('/photos/photo1.png')
    assert fs.is_file('/photos/my.png')
    assert fs.is_file('/photos/Azamat.jpg')
    assert fs.is_dir('/photos/album')
    assert fs.is_file('/photos/album/p1.jpg')

    rm.execute(['/photos'], ['-r'], ctx)
    # всё дерево удалено
    assert not fs.is_dir('/photos')
    # в undo должно быть несколько записей (файлы + каталоги)
    undo = getattr(rm, 'undo')()
    assert len(undo) >= 4
    assert all(u.action == 'rm' and u.dst.startswith('/.trash/') for u in undo)


# Пакетное удаление нескольких файлов
def test_rm_multiple_files(rm: Command, fs: FileSystemRepository, ctx: CommandContext):
    assert fs.is_file('/photos/photo1.png')
    assert fs.is_file('/photos/my.png')
    rm.execute(['/photos/photo1.png', '/photos/my.png'], [], ctx)
    assert not fs.is_file('/photos/photo1.png')
    assert not fs.is_file('/photos/my.png')
    undo = getattr(rm, 'undo')()
    dsts = {u.dst for u in undo}
    # оба файла должны быть в .trash
    assert any(d.startswith('/.trash/photo1.png.') for d in dsts)
    assert any(d.startswith('/.trash/my.png.') for d in dsts)


# Пакетное удаление: файл и директория вместе (нужен -r)
def test_rm_r_mixed_file_and_dir(
    rm: Command, fs: FileSystemRepository, ctx: CommandContext
):
    # создаём дополнительную директорию
    if not fs.is_dir('/etc/conf'):
        fs.mkdir('/etc/conf')
    fs.write('/etc/conf/app.ini', 'CFG')

    # без -r должно упасть
    with pytest.raises(ValidationError):
        rm.execute(['/etc/conf', '/photos/my.png'], [], ctx)

    # с -r проходит
    rm.execute(['/etc/conf', '/photos/my.png'], ['-r'], ctx)
    assert not fs.is_dir('/etc/conf')
    assert not fs.is_file('/photos/my.png')
    undo = getattr(rm, 'undo')()
    assert len(undo) >= 2
    assert all(u.action == 'rm' for u in undo)


# Ошибка, если путь не существует
def test_rm_nonexistent_path_is_error(
    rm: Command, fs: FileSystemRepository, ctx: CommandContext
):
    with pytest.raises(ValidationError):
        rm.execute(['/no/such/file'], [], ctx)
