from pathlib import Path

import pytest

from entity.command import Command
from entity.context import CommandContext
from entity.errors import ValidationError
from test.conftest import setup_tree


def test_mkdir_creates_single_dir_in_pwd(mkdir: Command, fs, ctx: CommandContext):
    setup_tree(fs, ctx)
    mkdir.execute(['newdir'], [], ctx)
    assert Path('/vfs/home/test/newdir').is_dir()


def test_mkdir_creates_multiple_dirs(mkdir: Command, fs, ctx: CommandContext):
    setup_tree(fs, ctx)
    mkdir.execute(['a', 'b'], [], ctx)
    assert Path('/vfs/home/test/a').is_dir()
    assert Path('/vfs/home/test/b').is_dir()


def test_mkdir_nested_without_p_is_error(mkdir: Command, fs, ctx: CommandContext):
    setup_tree(fs, ctx)
    with pytest.raises(ValidationError):
        mkdir.execute(['nested/x/y'], [], ctx)


def test_mkdir_p_nested_creates_all(mkdir: Command, fs, ctx: CommandContext):
    setup_tree(fs, ctx)
    mkdir.execute(['nested/x/y'], ['-p'], ctx)
    assert Path('/vfs/home/test/nested/x/y').is_dir()


def test_mkdir_existing_dir_without_p_is_error(mkdir: Command, fs, ctx: CommandContext):
    setup_tree(fs, ctx)
    Path('/vfs/home/test/exist').mkdir(parents=True, exist_ok=True)
    with pytest.raises(ValidationError):
        mkdir.execute(['exist'], [], ctx)


def test_mkdir_existing_dir_with_p_is_ok(mkdir: Command, fs, ctx: CommandContext):
    setup_tree(fs, ctx)
    Path('/vfs/home/test/exist').mkdir(parents=True, exist_ok=True)
    mkdir.execute(['exist'], ['-p'], ctx)
    assert Path('/vfs/home/test/exist').is_dir()


def test_mkdir_path_collides_with_file_is_error(
    mkdir: Command, fs, ctx: CommandContext
):
    setup_tree(fs, ctx)
    assert Path('/vfs/photos/photo1.png').is_file()
    with pytest.raises(ValidationError):
        mkdir.execute(['/vfs/photos/photo1.png'], [], ctx)


def test_mkdir_absolute_path(mkdir: Command, fs, ctx: CommandContext):
    setup_tree(fs, ctx)
    mkdir.execute(['/vfs/etc/newplace'], [], ctx)
    assert Path('/vfs/etc/newplace').is_dir()


def test_mkdir_tilde_home_expansion(mkdir: Command, fs, ctx: CommandContext):
    setup_tree(fs, ctx)
    mkdir.execute(['~/work'], [], ctx)
    assert Path('/vfs/home/test/work').is_dir()
