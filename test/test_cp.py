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
    return InMemoryFileSystemRepository(UNIX_TREE)


@pytest.fixture
def cp(fs: FileSystemRepository) -> Command:
    return Cp(fs)


# 1) Копирование директории в несуществующий путь: создаётся новый корень назначения (dst)
def test_cp_r_dir_to_new_path_creates_root(
    cp: Command, fs: FileSystemRepository, ctx: CommandContext
):
    assert not fs.is_dir('/backup')
    # добавим содержимое в исходные файлы, чтобы проверить перезапись содержимого
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


# 2) Копирование директории в существующую директорию: src размещается внутри dst/basename(src)
def test_cp_r_dir_into_existing_dir_places_inside(
    cp: Command, fs: FileSystemRepository, ctx: CommandContext
):
    # /home уже существует
    cp.execute(['/photos', '/home'], ['-r'], ctx)
    assert fs.is_dir('/home/photos')
    assert fs.is_file('/home/photos/photo1.png')
    assert fs.is_file('/home/photos/my.png')
    assert fs.is_file('/home/photos/Azamat.jpg')


# 3) Копирование директории без -r должно быть ошибкой
def test_cp_dir_without_r_is_error(
    cp: Command, fs: FileSystemRepository, ctx: CommandContext
):
    with pytest.raises(ValidationError):
        cp.execute(['/photos', '/home/new_photos'], [], ctx)


# 4) Нельзя перезаписать существующий файл директорией
def test_cp_r_dir_over_file_is_error(
    cp: Command, fs: FileSystemRepository, ctx: CommandContext
):
    # сделаем файл-назначение
    fs.write('/photos/my.png', 'OLD_FILE')
    with pytest.raises(ValidationError):
        cp.execute(
            ['/home'],
            ['-r'],
            ctx,
        )  # dst отсутствует в списке -> недостаточно аргументов
    # корректный вызов c явным dst-файлом
    with pytest.raises(ValidationError):
        cp.execute(['/home', '/photos/my.png'], ['-r'], ctx)


# 5) Перезапись файлов внутри существующей директории с undo
def test_cp_r_overwrite_with_undo_records(
    cp: Command, fs: FileSystemRepository, ctx: CommandContext
):
    # подготовим исходник с контентом
    fs.write('/photos/photo1.png', 'SRC1')
    fs.write('/photos/my.png', 'SRC2')

    # подготовим существующий dst с конкурентными файлами
    if not fs.is_dir('/backup/photos/'):
        fs.mkdir('/backup/photos')
    fs.write('/backup/photos/photo1.png', 'OLD1')
    # файл my.png в dst отсутствует, чтобы проверить смешанный сценарий overwrite/new

    cp.execute(['/photos', '/backup'], ['-r'], ctx)
    # проверяем содержимое
    assert fs.read('/backup/photos/photo1.png') == 'SRC1'
    assert fs.read('/backup/photos/my.png') == 'SRC2'

    # проверяем undo-записи
    # ожидается по одной записи
    undo = getattr(cp, 'undo')()
    print(undo)
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
    # источник: /src/docs/readme (файл)
    if not fs.is_dir('/src'):
        fs.mkdir('/src')
    if not fs.is_dir('/src/docs'):
        fs.mkdir('/src/docs')
    fs.write('/src/docs/readme', 'TEXT')

    # приёмник: /dst/docs/readme (директория)
    if not fs.is_dir('/dst'):
        fs.mkdir('/dst')
    if not fs.is_dir('/dst/src'):
        fs.mkdir('/dst/src')
    if not fs.is_dir('/dst/src/docs'):
        fs.mkdir('/dst/src/docs')
    if not fs.is_dir('/dst/src/docs/readme'):
        fs.mkdir('/dst/src/docs/readme')

    with pytest.raises(ValidationError):
        cp.execute(['/src', '/dst'], ['-r'], ctx)


# 7) Множественные источники директорий — только в существующую директорию
def test_cp_r_multiple_sources_into_existing_dir(
    cp: Command, fs: FileSystemRepository, ctx: CommandContext
):
    # создадим пустую директорию назначения
    if not fs.is_dir('/mnt'):
        fs.mkdir('/mnt')

    cp.execute(['/etc', '/photos', '/mnt'], ['-r'], ctx)
    # обе директории должны оказаться внутри /mnt
    assert fs.is_dir('/mnt/etc')
    assert fs.is_dir('/mnt/photos')
    assert fs.is_file('/mnt/photos/photo1.png')

    # если dst не директория — ошибка
    with pytest.raises(ValidationError):
        cp.execute(['/etc', '/photos', '/mnt/new_place'], ['-r'], ctx)
