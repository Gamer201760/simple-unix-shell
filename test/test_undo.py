from copy import deepcopy

import pytest

from entity.context import CommandContext
from entity.errors import DomainError, ValidationError
from repository.in_memory_fs import InMemoryFileSystemRepository
from repository.in_memory_undo_repo import InMemoryUndoRepository
from usecase.command.cp import Cp
from usecase.command.mv import Mv
from usecase.command.rm import Rm
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
def rm(fs: FileSystemRepository) -> Rm:
    return Rm(fs)


@pytest.fixture
def undo(undo_repo: UndoRepository, fs: FileSystemRepository) -> Undo:
    return Undo(undo_repo, fs)


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
    undo.execute([], [], ctx)
    assert not fs.is_file('/home/test/newfile.png')


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
    undo.execute([], [], ctx)
    assert fs.read('/home/test/exist.png') == 'OLDVAL'


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
    undo.execute([], [], ctx)
    assert fs.is_file('/photos/photo1.png')
    assert not fs.is_file('/home/test/restored.png')


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
    undo.execute([], [], ctx)
    assert fs.read('/home/test/exist.png') == 'ORIGINAL'


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
    undo.execute([], [], ctx)
    assert not fs.is_file('/home/test/photo1.png')
    assert not fs.is_file('/home/test/my.png')


def test_undo_no_records(undo: Undo, ctx: CommandContext) -> None:
    with pytest.raises(DomainError):
        undo.execute([], [], ctx)


def test_undo_rm_file_restore(
    fs: FileSystemRepository,
    rm: Rm,
    undo_repo: UndoRepository,
    undo: Undo,
    ctx: CommandContext,
) -> None:
    assert fs.is_file('/photos/my.png')
    rm.execute(['/photos/my.png'], ['-y'], ctx)
    undo_repo.add(rm.undo())
    assert not fs.is_file('/photos/my.png')
    undo.execute([], [], ctx)
    assert fs.is_file('/photos/my.png')


def test_undo_rm_r_dir_restore_tree(
    fs: FileSystemRepository,
    rm: Rm,
    undo_repo: UndoRepository,
    undo: Undo,
    ctx: CommandContext,
) -> None:
    if not fs.is_dir('/photos/album'):
        fs.mkdir('/photos/album')
    fs.write('/photos/album/p1.jpg', 'X')
    fs.write('/photos/album/p2.jpg', 'Y')
    assert fs.is_dir('/photos')
    rm.execute(['/photos'], ['-r', '-y'], ctx)
    undo_repo.add(rm.undo())
    assert not fs.is_dir('/photos')
    undo.execute([], [], ctx)
    assert fs.is_dir('/photos')
    assert fs.is_file('/photos/photo1.png')
    assert fs.is_file('/photos/my.png')
    assert fs.is_file('/photos/Azamat.jpg')
    assert fs.is_dir('/photos/album')
    assert fs.is_file('/photos/album/p1.jpg')


def test_undo_rm_multiple_files_restore(
    fs: FileSystemRepository,
    rm: Rm,
    undo_repo: UndoRepository,
    undo: Undo,
    ctx: CommandContext,
) -> None:
    assert fs.is_file('/photos/photo1.png')
    assert fs.is_file('/photos/Azamat.jpg')
    rm.execute(['/photos/photo1.png', '/photos/Azamat.jpg'], ['-y'], ctx)
    undo_repo.add(rm.undo())
    assert not fs.is_file('/photos/photo1.png')
    assert not fs.is_file('/photos/Azamat.jpg')
    undo.execute([], [], ctx)
    assert fs.is_file('/photos/photo1.png')
    assert fs.is_file('/photos/Azamat.jpg')


def test_undo_rm_mixed_dir_and_file_restore(
    fs: FileSystemRepository,
    rm: Rm,
    undo_repo: UndoRepository,
    undo: Undo,
    ctx: CommandContext,
) -> None:
    if not fs.is_dir('/etc/conf'):
        fs.mkdir('/etc/conf')
    fs.write('/etc/conf/app.ini', 'CFG')
    with pytest.raises(ValidationError):
        rm.execute(['/etc/conf', '/photos/my.png'], [], ctx)
    rm.execute(['/etc/conf', '/photos/my.png'], ['-r', '-y'], ctx)
    undo_repo.add(rm.undo())
    assert not fs.is_dir('/etc/conf')
    assert not fs.is_file('/photos/my.png')
    undo.execute([], [], ctx)
    assert fs.is_dir('/etc/conf')
    assert fs.is_file('/etc/conf/app.ini')
    assert fs.is_file('/photos/my.png')


def test_rm_r_undo_returns_apply_ready_order(
    fs: FileSystemRepository,
    rm: Rm,
    ctx: CommandContext,
):
    if not fs.is_dir('/tmpdata'):
        fs.mkdir('/tmpdata')
    if not fs.is_dir('/tmpdata/a'):
        fs.mkdir('/tmpdata/a')
    if not fs.is_dir('/tmpdata/a/b'):
        fs.mkdir('/tmpdata/a/b')
    fs.write('/tmpdata/f1', '1')
    fs.write('/tmpdata/a/f2', '2')
    fs.write('/tmpdata/a/b/f3', '3')

    rm.execute(['/tmpdata'], ['-r', '-y'], ctx)
    records = rm.undo()

    dirs = [r for r in records if fs.is_dir(r.dst)]
    files = [r for r in records if not fs.is_dir(r.dst)]
    assert records[: len(dirs)] == dirs
    assert records[len(dirs) :] == files

    def depth(p: str) -> int:
        return len([seg for seg in p.split('/') if seg])

    dir_depths = [depth(r.src) for r in dirs]
    assert dir_depths == sorted(dir_depths)

    assert dirs[0].src == '/tmpdata'
