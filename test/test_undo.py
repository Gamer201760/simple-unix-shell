from pathlib import Path

import pytest

from entity.context import CommandContext
from entity.errors import DomainError
from repository.command.cp import Cp
from repository.command.mv import Mv
from repository.command.rm import Rm
from repository.command.undo import Undo
from repository.in_memory_undo_repo import InMemoryUndoRepository
from test.conftest import setup_tree
from usecase.interface import UndoRepository


@pytest.fixture
def undo_repo() -> UndoRepository:
    return InMemoryUndoRepository()


@pytest.fixture
def undo(undo_repo: UndoRepository, fs) -> Undo:
    return Undo(undo_repo)


def test_undo_cp_new_file(
    fs, cp: Cp, undo_repo: UndoRepository, undo: Undo, ctx: CommandContext
) -> None:
    setup_tree(fs, ctx)
    cp.execute(['/vfs/photos/photo1.png', '/vfs/home/test/newfile.png'], [], ctx)
    undo_repo.add(cp.undo())
    assert Path('/vfs/home/test/newfile.png').is_file()
    undo.execute([], [], ctx)
    assert not Path('/vfs/home/test/newfile.png').exists()


def test_undo_cp_overwrite(
    fs, cp: Cp, undo_repo: UndoRepository, undo: Undo, ctx: CommandContext
) -> None:
    setup_tree(fs, ctx)
    Path('/vfs/home/test').mkdir(parents=True, exist_ok=True)
    Path('/vfs/home/test/exist.png').write_text('OLDVAL')
    cp.execute(['/vfs/photos/photo1.png', '/vfs/home/test/exist.png'], [], ctx)
    undo_repo.add(cp.undo())
    assert Path('/vfs/home/test/exist.png').read_text() == 'IMG1'
    undo.execute([], [], ctx)
    assert Path('/vfs/home/test/exist.png').read_text() == 'OLDVAL'


def test_undo_mv(
    fs, mv: Mv, undo_repo: UndoRepository, undo: Undo, ctx: CommandContext
) -> None:
    setup_tree(fs, ctx)
    mv.execute(['/vfs/photos/photo1.png', '/vfs/home/test/restored.png'], [], ctx)
    undo_repo.add(mv.undo())
    assert Path('/vfs/home/test/restored.png').is_file()
    assert not Path('/vfs/photos/photo1.png').exists()
    undo.execute([], [], ctx)
    assert Path('/vfs/photos/photo1.png').is_file()
    assert not Path('/vfs/home/test/restored.png').exists()


def test_undo_mv_overwrite(
    fs, mv: Mv, undo_repo: UndoRepository, undo: Undo, ctx: CommandContext
) -> None:
    setup_tree(fs, ctx)
    Path('/vfs/home/test/exist.png').write_text('ORIGINAL')
    mv.execute(['/vfs/photos/my.png', '/vfs/home/test/exist.png'], [], ctx)
    undo_repo.add(mv.undo())
    assert Path('/vfs/home/test/exist.png').read_text() == 'IMG2'
    undo.execute([], [], ctx)
    assert Path('/vfs/home/test/exist.png').read_text() == 'ORIGINAL'


def test_undo_cp_batch(
    fs, cp: Cp, undo_repo: UndoRepository, undo: Undo, ctx: CommandContext
) -> None:
    setup_tree(fs, ctx)
    cp.execute(
        ['/vfs/photos/photo1.png', '/vfs/photos/my.png', '/vfs/home/test'], [], ctx
    )
    undo_repo.add(cp.undo())
    assert Path('/vfs/home/test/photo1.png').is_file()
    assert Path('/vfs/home/test/my.png').is_file()
    undo.execute([], [], ctx)
    assert not Path('/vfs/home/test/photo1.png').exists()
    assert not Path('/vfs/home/test/my.png').exists()


def test_undo_no_records(undo: Undo, ctx: CommandContext) -> None:
    with pytest.raises(DomainError):
        undo.execute([], [], ctx)


def test_undo_rm_file_restore(
    fs, rm: Rm, undo_repo: UndoRepository, undo: Undo, ctx: CommandContext
) -> None:
    setup_tree(fs, ctx)
    assert Path('/vfs/photos/my.png').is_file()
    rm.execute(['/vfs/photos/my.png'], ['-y'], ctx)
    undo_repo.add(rm.undo())
    assert not Path('/vfs/photos/my.png').exists()
    undo.execute([], [], ctx)
    assert Path('/vfs/photos/my.png').is_file()


def test_undo_rm_r_dir_restore_tree(
    fs, rm: Rm, undo_repo: UndoRepository, undo: Undo, ctx: CommandContext
) -> None:
    setup_tree(fs, ctx)
    Path('/vfs/photos/album').mkdir(parents=True, exist_ok=True)
    Path('/vfs/photos/album/p1.jpg').write_text('X')
    Path('/vfs/photos/album/p2.jpg').write_text('Y')
    assert Path('/vfs/photos').is_dir()
    rm.execute(['/vfs/photos'], ['-r', '-y'], ctx)
    undo_repo.add(rm.undo())
    assert not Path('/vfs/photos').exists()
    undo.execute([], [], ctx)
    assert Path('/vfs/photos').is_dir()
    assert Path('/vfs/photos/photo1.png').is_file()
    assert Path('/vfs/photos/my.png').is_file()
    assert Path('/vfs/photos/Azamat.jpg').is_file()
    assert Path('/vfs/photos/album').is_dir()
    assert Path('/vfs/photos/album/p1.jpg').is_file()


def test_undo_rm_multiple_files_restore(
    fs, rm: Rm, undo_repo: UndoRepository, undo: Undo, ctx: CommandContext
) -> None:
    setup_tree(fs, ctx)
    assert Path('/vfs/photos/photo1.png').is_file()
    assert Path('/vfs/photos/Azamat.jpg').is_file()
    rm.execute(['/vfs/photos/photo1.png', '/vfs/photos/Azamat.jpg'], ['-y'], ctx)
    undo_repo.add(rm.undo())
    assert not Path('/vfs/photos/photo1.png').exists()
    assert not Path('/vfs/photos/Azamat.jpg').exists()
    undo.execute([], [], ctx)
    assert Path('/vfs/photos/photo1.png').is_file()
    assert Path('/vfs/photos/Azamat.jpg').is_file()


def test_rm_r_undo_returns_apply_ready_order(fs, rm: Rm, ctx: CommandContext):
    setup_tree(fs, ctx)
    Path('/vfs/tmpdata/a/b').mkdir(parents=True, exist_ok=True)
    Path('/vfs/tmpdata/f1').write_text('1')
    Path('/vfs/tmpdata/a/f2').write_text('2')
    Path('/vfs/tmpdata/a/b/f3').write_text('3')

    rm.execute(['/vfs/tmpdata'], ['-r', '-y'], ctx)
    records = rm.undo()

    dirs = [r for r in records if Path(r.dst).is_dir()]
    files = [r for r in records if not Path(r.dst).is_dir()]
    assert records[: len(dirs)] == dirs
    assert records[len(dirs) :] == files

    def depth(p: str) -> int:
        return len([seg for seg in p.split('/') if seg])

    dir_depths = [depth(r.src) for r in dirs]
    assert dir_depths == sorted(dir_depths)
    assert dirs[0].src == '/vfs/tmpdata'
