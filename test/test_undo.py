from copy import deepcopy

import pytest

from entity.context import CommandContext
from entity.errors import DomainError
from repository.in_memory_fs import InMemoryFileSystemRepository
from repository.in_memory_undo_repo import InMemoryUndoRepository
from usecase.command.cp import Cp
from usecase.command.mv import Mv
from usecase.command.undo import Undo
from usecase.interface import FileSystemRepository, UndoRepository

UNIX_TREE: dict[str, list[str]] = {
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
    fs = InMemoryFileSystemRepository(deepcopy(UNIX_TREE), home=ctx.home, pwd=ctx.pwd)
    # Наполняем примерные файлы содержимым
    fs.write('/photos/photo1.png', 'SRC1')
    fs.write('/photos/my.png', 'SRC2')
    fs.write('/photos/Azamat.jpg', 'SRC3')
    return fs


@pytest.fixture
def undo_repo() -> UndoRepository:
    return InMemoryUndoRepository()


@pytest.fixture
def cp(fs: FileSystemRepository) -> Cp:
    return Cp(fs)


@pytest.fixture
def mv(fs: FileSystemRepository) -> Mv:
    return Mv(fs)


@pytest.fixture
def undo(undo_repo: UndoRepository, fs: FileSystemRepository) -> Undo:
    return Undo(undo_repo, fs)


# Откат cp: обычное копирование файла
def test_undo_cp_new_file(
    fs: FileSystemRepository,
    cp: Cp,
    undo_repo: UndoRepository,
    undo: Undo,
    ctx: CommandContext,
) -> None:
    cp.execute(['/photos/photo1.png', '/home/test/newfile.png'], [], ctx)
    undo_repo.add(cp.undo())
    assert fs.is_file('/home/test/newfile.png')
    res = undo.execute([], [], ctx)
    assert not fs.is_file('/home/test/newfile.png')
    assert 'Откат: удалена скопированная копия /home/test/newfile.png' in res


# Откат cp с перезаписью: должен вернуться старый файл, а копия быть удалена
def test_undo_cp_overwrite(
    fs: FileSystemRepository,
    cp: Cp,
    undo_repo: UndoRepository,
    undo: Undo,
    ctx: CommandContext,
) -> None:
    fs.write('/home/test/exist.png', 'OLDVAL')
    cp.execute(['/photos/photo1.png', '/home/test/exist.png'], [], ctx)
    undo_repo.add(cp.undo())
    assert fs.read('/home/test/exist.png') == 'SRC1'
    result = undo.execute([], [], ctx)
    assert fs.read('/home/test/exist.png') == 'OLDVAL'
    assert 'Откат: восстановлен старый /home/test/exist.png; копия удалена' in result


# Откат mv: файл возвращается на исходное место
def test_undo_mv(
    fs: FileSystemRepository,
    mv: Mv,
    undo_repo: UndoRepository,
    undo: Undo,
    ctx: CommandContext,
) -> None:
    mv.execute(['/photos/photo1.png', '/home/test/restored.png'], [], ctx)
    undo_repo.add(mv.undo())
    assert fs.is_file('/home/test/restored.png')
    assert not fs.is_file('/photos/photo1.png')
    res = undo.execute([], [], ctx)
    assert fs.is_file('/photos/photo1.png')
    assert not fs.is_file('/home/test/restored.png')
    assert 'Откат: /home/test/restored.png -> /photos/photo1.png' in res


# Откат mv с overwrite: оригинальный файл должен быть полностью восстановлен
def test_undo_mv_overwrite(
    fs: FileSystemRepository,
    mv: Mv,
    undo_repo: UndoRepository,
    undo: Undo,
    ctx: CommandContext,
) -> None:
    fs.write('/home/test/exist.png', 'ORIGINAL')
    mv.execute(['/photos/my.png', '/home/test/exist.png'], [], ctx)
    undo_repo.add(mv.undo())
    assert fs.read('/home/test/exist.png') == 'SRC2'
    result = undo.execute([], [], ctx)
    assert fs.read('/home/test/exist.png') == 'ORIGINAL'
    assert 'Откат: /home/test/exist.png -> /photos/my.png' in result
    assert 'восстановлен оригинал по /home/test/exist.png' in result


# Откат cp с несколькими файлами (batch): все копии удалятся
def test_undo_cp_batch(
    fs: FileSystemRepository,
    cp: Cp,
    undo_repo: UndoRepository,
    undo: Undo,
    ctx: CommandContext,
) -> None:
    cp.execute(['/photos/photo1.png', '/photos/my.png', '/home/test'], [], ctx)
    undo_repo.add(cp.undo())
    assert fs.is_file('/home/test/photo1.png')
    assert fs.is_file('/home/test/my.png')
    res = undo.execute([], [], ctx)
    assert not fs.is_file('/home/test/photo1.png')
    assert not fs.is_file('/home/test/my.png')
    assert 'Откат: удалена скопированная копия /home/test/photo1.png' in res
    assert 'Откат: удалена скопированная копия /home/test/my.png' in res


# Если нет истории undo — выбрасывается ошибка
def test_undo_no_records(undo: Undo, ctx: CommandContext) -> None:
    with pytest.raises(DomainError):
        undo.execute([], [], ctx)
