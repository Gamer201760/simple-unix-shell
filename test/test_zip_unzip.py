import zipfile
from pathlib import Path

import pytest

from entity.command import Command
from entity.context import CommandContext
from entity.errors import ValidationError
from test.conftest import setup_tree


def _zip_namelist(archive_path: str) -> list[str]:
    with zipfile.ZipFile(archive_path, 'r') as zf:
        return zf.namelist()


def _zip_has(archive_path: str, member: str) -> bool:
    return member in _zip_namelist(archive_path)


def test_zip_single_file_creates_archive(zip: Command, fs, ctx: CommandContext):
    setup_tree(fs, ctx)
    out = '/vfs/home/test/pics.zip'
    zip.execute(['/vfs/photos/photo1.png', out], [], ctx)
    assert Path(out).is_file()
    assert _zip_has(out, 'photo1.png')


def test_zip_multiple_files(zip: Command, fs, ctx: CommandContext):
    setup_tree(fs, ctx)
    out = '/vfs/home/test/all.zip'
    zip.execute(['/vfs/photos/photo1.png', '/vfs/photos/my.png', out], [], ctx)
    assert Path(out).is_file()
    names = set(_zip_namelist(out))
    assert 'photo1.png' in names and 'my.png' in names


def test_zip_dir_without_r_is_error(zip: Command, fs, ctx: CommandContext):
    setup_tree(fs, ctx)
    out = '/vfs/home/test/photos.zip'
    with pytest.raises(ValidationError):
        zip.execute(['/vfs/photos', out], [], ctx)


def test_zip_r_directory_includes_nested(zip: Command, fs, ctx: CommandContext):
    setup_tree(fs, ctx)
    fs.create_dir('/vfs/photos/album')
    fs.create_file('/vfs/photos/album/p1.jpg', contents='X')
    out = '/vfs/home/test/photos.zip'
    zip.execute(['/vfs/photos', out], ['-r'], ctx)
    assert Path(out).is_file()
    names = set(_zip_namelist(out))
    assert 'photos/photo1.png' in names
    assert 'photos/Azamat.jpg' in names
    assert 'photos/my.png' in names
    assert 'photos/album/p1.jpg' in names


def test_zip_mixed_sources_requires_r_if_any_dir(zip: Command, fs, ctx: CommandContext):
    setup_tree(fs, ctx)
    out = '/vfs/home/test/mixed.zip'
    with pytest.raises(ValidationError):
        zip.execute(['/vfs/photos', '/vfs/photos/my.png', out], [], ctx)
    zip.execute(['/vfs/photos', '/vfs/photos/my.png', out], ['-r'], ctx)
    assert Path(out).is_file()
    names = set(_zip_namelist(out))
    assert 'my.png' in names


def test_unzip_to_pwd_by_default(unzip: Command, fs, ctx: CommandContext):
    setup_tree(fs, ctx)
    arc = '/vfs/home/test/p1.zip'
    with zipfile.ZipFile(arc, 'w') as zf:
        zf.writestr('a.txt', 'A')
        zf.writestr('dir/b.txt', 'B')
    assert Path(arc).is_file()
    unzip.execute([arc], [], ctx)
    assert Path('/vfs/home/test/a.txt').is_file()
    assert Path('/vfs/home/test/dir/b.txt').is_file()


def test_unzip_to_custom_dest(unzip: Command, fs, ctx: CommandContext):
    setup_tree(fs, ctx)
    arc = '/vfs/home/test/pics.zip'
    with zipfile.ZipFile(arc, 'w') as zf:
        zf.writestr('photo1.png', 'X')
        zf.writestr('sub/p2.png', 'Y')
    dest = '/vfs/etc/exports'
    fs.create_dir(dest)
    unzip.execute([arc, dest], [], ctx)
    assert Path(f'{dest}/photo1.png').is_file()
    assert Path(f'{dest}/sub/p2.png').is_file()


def test_unzip_nonexistent_archive_is_error(unzip: Command, fs, ctx: CommandContext):
    setup_tree(fs, ctx)
    with pytest.raises(ValidationError):
        unzip.execute(['/vfs/home/test/no.zip'], [], ctx)


def test_zip_requires_args_and_ends_with_zip(zip: Command, fs, ctx: CommandContext):
    setup_tree(fs, ctx)
    with pytest.raises(ValidationError):
        zip.execute([], [], ctx)
    with pytest.raises(ValidationError):
        zip.execute(['/vfs/home/test/out.zip'], [], ctx)
