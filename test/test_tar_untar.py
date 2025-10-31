import tarfile
from pathlib import Path

import pytest

from entity.command import Command
from entity.context import CommandContext
from entity.errors import ValidationError
from test.conftest import setup_tree


def _tar_names(archive_path: str) -> set[str]:
    with tarfile.open(archive_path, 'r:gz') as tf:
        return set(tf.getnames())


def test_tar_single_file_creates_archive(tar: Command, fs, ctx: CommandContext):
    setup_tree(fs, ctx)
    out = '/vfs/home/test/pic.tar.gz'
    tar.execute(['/vfs/photos/photo1.png', out], [], ctx)
    assert Path(out).is_file()
    names = _tar_names(out)
    assert 'photo1.png' in names


def test_tar_multiple_files(tar: Command, fs, ctx: CommandContext):
    setup_tree(fs, ctx)
    out = '/vfs/home/test/all.tgz'
    tar.execute(['/vfs/photos/photo1.png', '/vfs/photos/my.png', out], [], ctx)
    assert Path(out).is_file()
    names = _tar_names(out)
    assert 'photo1.png' in names and 'my.png' in names


def test_tar_dir_without_r_is_error(tar: Command, fs, ctx: CommandContext):
    setup_tree(fs, ctx)
    out = '/vfs/home/test/photos.tar.gz'
    with pytest.raises(ValidationError):
        tar.execute(['/vfs/photos', out], [], ctx)


def test_tar_r_directory_includes_nested_with_prefix(
    tar: Command, fs, ctx: CommandContext
):
    setup_tree(fs, ctx)
    fs.create_dir('/vfs/photos/album')
    fs.create_file('/vfs/photos/album/p1.jpg', contents='X')
    out = '/vfs/home/test/photos.tar.gz'
    tar.execute(['/vfs/photos', out], ['-r'], ctx)
    assert Path(out).is_file()
    names = _tar_names(out)
    assert 'photos/photo1.png' in names
    assert 'photos/my.png' in names
    assert 'photos/Azamat.jpg' in names
    assert 'photos/album/p1.jpg' in names


def test_tar_mixed_sources_requires_r_if_any_dir_and_prefix_for_dir(
    tar: Command, fs, ctx: CommandContext
):
    setup_tree(fs, ctx)
    out = '/vfs/home/test/mixed.tar.gz'
    with pytest.raises(ValidationError):
        tar.execute(['/vfs/photos', '/vfs/photos/my.png', out], [], ctx)
    tar.execute(['/vfs/photos', '/vfs/photos/my.png', out], ['-r'], ctx)
    assert Path(out).is_file()
    names = _tar_names(out)
    assert 'photos/my.png' in names


def test_tar_requires_args_and_tar_gz_extension(tar: Command, fs, ctx: CommandContext):
    setup_tree(fs, ctx)
    with pytest.raises(ValidationError):
        tar.execute([], [], ctx)
    with pytest.raises(ValidationError):
        tar.execute(['/vfs/home/test/out.tar.gz'], [], ctx)
    ok1 = '/vfs/home/test/out.tar.gz'
    ok2 = '/vfs/home/test/out.tgz'
    tar.execute(['/vfs/photos/photo1.png', ok1], [], ctx)
    tar.execute(['/vfs/photos/my.png', ok2], [], ctx)
    assert Path(ok1).is_file() and Path(ok2).is_file()


def test_untar_to_pwd_by_default(untar: Command, fs, ctx: CommandContext):
    setup_tree(fs, ctx)
    arc = '/vfs/home/test/p1.tar.gz'
    with tarfile.open(arc, 'w:gz') as tf:
        tmp_dir = '/vfs/home/test/tmp'
        fs.create_dir(tmp_dir)
        fs.create_file(f'{tmp_dir}/a.txt', contents='A')
        fs.create_dir(f'{tmp_dir}/dir')
        fs.create_file(f'{tmp_dir}/dir/b.txt', contents='B')
        tf.add(f'{tmp_dir}/a.txt', arcname='a.txt')
        tf.add(f'{tmp_dir}/dir/b.txt', arcname='dir/b.txt')
    assert Path(arc).is_file()
    untar.execute([arc], [], ctx)
    assert (
        Path('/vfs/home/test/a.txt').is_file()
        and Path('/vfs/home/test/dir/b.txt').is_file()
    )


def test_untar_to_custom_dest(untar: Command, fs, ctx: CommandContext):
    setup_tree(fs, ctx)
    arc = '/vfs/home/test/pics.tgz'
    with tarfile.open(arc, 'w:gz') as tf:
        tmp_dir = '/vfs/home/test/tmp2'
        fs.create_dir(tmp_dir)
        fs.create_file(f'{tmp_dir}/photo1.png', contents='X')
        fs.create_dir(f'{tmp_dir}/sub')
        fs.create_file(f'{tmp_dir}/sub/p2.png', contents='Y')
        tf.add(f'{tmp_dir}/photo1.png', arcname='photo1.png')
        tf.add(f'{tmp_dir}/sub/p2.png', arcname='sub/p2.png')
    dest = '/vfs/etc/exports'
    fs.create_dir(dest)
    untar.execute([arc, dest], [], ctx)
    assert Path(f'{dest}/photo1.png').is_file() and Path(f'{dest}/sub/p2.png').is_file()


def test_untar_nonexistent_archive_is_error(untar: Command, fs, ctx: CommandContext):
    setup_tree(fs, ctx)
    with pytest.raises(ValidationError):
        untar.execute(['/vfs/home/test/no.tar.gz'], [], ctx)
