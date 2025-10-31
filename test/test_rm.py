import builtins
from pathlib import Path

import pytest

from entity.command import Command
from entity.context import CommandContext
from entity.errors import ValidationError
from test.conftest import setup_tree


def test_rm_file_deletes_and_moves_to_trash(rm: Command, fs, ctx: CommandContext):
    setup_tree(fs, ctx)
    assert Path('/vfs/photos/photo1.png').is_file()
    rm.execute(['/vfs/photos/photo1.png'], ['-y'], ctx)
    assert not Path('/vfs/photos/photo1.png').exists()
    trash = Path('/.trash')
    assert trash.is_dir()
    trashed = [p.name for p in trash.iterdir()]
    assert any(name.startswith('photo1.png.') for name in trashed)
    undo = getattr(rm, 'undo')()
    assert len(undo) == 1
    assert undo[0].action == 'rm'
    assert undo[0].src == '/vfs/photos/photo1.png'
    assert undo[0].dst.startswith('/.trash/')


def test_rm_dir_without_r_is_error(rm: Command, fs, ctx: CommandContext, monkeypatch):
    setup_tree(fs, ctx)

    def fail_input(*a, **k):
        raise AssertionError('input() must not be called without -r')

    monkeypatch.setattr(builtins, 'input', fail_input)
    with pytest.raises(ValidationError):
        rm.execute(['/vfs/photos'], [], ctx)


def test_rm_r_dir_deletes_recursively(rm: Command, fs, ctx: CommandContext):
    setup_tree(fs, ctx)
    fs.create_dir('/vfs/photos/album')
    fs.create_file('/vfs/photos/album/p1.jpg', contents='X')
    fs.create_file('/vfs/photos/album/p2.jpg', contents='Y')

    assert Path('/vfs/photos').is_dir()
    assert Path('/vfs/photos/photo1.png').is_file()
    assert Path('/vfs/photos/my.png').is_file()
    assert Path('/vfs/photos/Azamat.jpg').is_file()
    assert Path('/vfs/photos/album').is_dir()
    assert Path('/vfs/photos/album/p1.jpg').is_file()

    rm.execute(['/vfs/photos'], ['-r', '-y'], ctx)
    assert not Path('/vfs/photos').exists()
    undo = getattr(rm, 'undo')()
    assert len(undo) >= 4
    assert all(u.action == 'rm' and u.dst.startswith('/.trash/') for u in undo)


def test_rm_multiple_files(rm: Command, fs, ctx: CommandContext):
    setup_tree(fs, ctx)
    assert Path('/vfs/photos/photo1.png').is_file()
    assert Path('/vfs/photos/my.png').is_file()
    rm.execute(['/vfs/photos/photo1.png', '/vfs/photos/my.png'], ['-y'], ctx)
    assert not Path('/vfs/photos/photo1.png').exists()
    assert not Path('/vfs/photos/my.png').exists()
    undo = getattr(rm, 'undo')()
    dsts = {u.dst for u in undo}
    assert any(d.startswith('/.trash/photo1.png.') for d in dsts)
    assert any(d.startswith('/.trash/my.png.') for d in dsts)


def test_rm_r_mixed_file_and_dir(rm: Command, fs, ctx: CommandContext, monkeypatch):
    setup_tree(fs, ctx)
    fs.create_dir('/vfs/etc/conf')
    fs.create_file('/vfs/etc/conf/app.ini', contents='CFG')

    def fail_input(*a, **k):
        raise AssertionError('input() must not be called before -r validation')

    monkeypatch.setattr(builtins, 'input', fail_input)
    with pytest.raises(ValidationError):
        rm.execute(['/vfs/etc/conf', '/vfs/photos/my.png'], [], ctx)

    rm.execute(['/vfs/etc/conf', '/vfs/photos/my.png'], ['-r', '-y'], ctx)
    assert not Path('/vfs/etc/conf').exists()
    assert not Path('/vfs/photos/my.png').exists()
    undo = getattr(rm, 'undo')()
    assert len(undo) >= 2
    assert all(u.action == 'rm' for u in undo)


def test_rm_nonexistent_path_is_error(
    rm: Command, fs, ctx: CommandContext, monkeypatch
):
    setup_tree(fs, ctx)

    def fail_input(*a, **k):
        raise AssertionError('input() must not be called for nonexistent path')

    monkeypatch.setattr(builtins, 'input', fail_input)
    with pytest.raises(ValidationError):
        rm.execute(['/no/such/file'], [], ctx)


def test_rm_prompts_and_respects_answer(
    rm: Command, fs, ctx: CommandContext, monkeypatch
):
    setup_tree(fs, ctx)
    fs.create_file('/vfs/etc/hosts', contents='H')

    monkeypatch.setattr(builtins, 'input', lambda *_: 'n')
    msg = rm.execute(['/vfs/etc/hosts'], [], ctx)
    assert msg.endswith('0 объектов')
    assert Path('/vfs/etc/hosts').is_file()

    monkeypatch.setattr(builtins, 'input', lambda *_: 'да')
    msg = rm.execute(['/vfs/etc/hosts'], [], ctx)
    assert msg.endswith('1 объектов')
    assert not Path('/vfs/etc/hosts').exists()
    undo = getattr(rm, 'undo')()
    assert len(undo) == 1
