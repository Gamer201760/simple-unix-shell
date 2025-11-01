from pathlib import Path

import pytest

from entity.command import Command
from entity.context import CommandContext
from entity.errors import ValidationError


def test_cp_r_dir_to_new_path_creates_root(cp: Command, fs, ctx: CommandContext):
    fs.create_dir('/photos')
    fs.create_file('/photos/photo1.png', contents='SRC1')
    fs.create_file('/photos/my.png', contents='SRC2')
    fs.create_file('/photos/Azamat.jpg', contents='SRC3')

    cp.execute(['/photos', '/backup'], ['-r'], ctx)

    assert Path('/backup').is_dir()
    assert Path('/backup/photo1.png').is_file()
    assert Path('/backup/photo1.png').read_text() == 'SRC1'
    assert Path('/backup/my.png').is_file()
    assert Path('/backup/my.png').read_text() == 'SRC2'
    assert Path('/backup/Azamat.jpg').is_file()
    assert Path('/backup/Azamat.jpg').read_text() == 'SRC3'


def test_cp_r_dir_into_existing_dir_places_inside(cp: Command, fs, ctx: CommandContext):
    fs.create_dir('/photos')
    fs.create_file('/photos/photo1.png', contents='SRC1')
    fs.create_file('/photos/my.png', contents='SRC2')
    fs.create_file('/photos/Azamat.jpg', contents='SRC3')

    fs.create_dir('/home')

    cp.execute(['/photos', '/home'], ['-r'], ctx)

    assert Path('/home/photos').is_dir()
    assert Path('/home/photos/photo1.png').is_file()
    assert Path('/home/photos/my.png').is_file()
    assert Path('/home/photos/Azamat.jpg').is_file()


def test_cp_dir_without_r_is_error(cp: Command, fs, ctx: CommandContext):
    fs.create_dir('/photos')
    with pytest.raises(ValidationError):
        cp.execute(['/photos', '/home/new_photos'], [], ctx)


def test_cp_r_dir_over_file_is_error(cp: Command, fs, ctx: CommandContext):
    fs.create_dir('/photos')
    fs.create_file('/photos/my.png', contents='OLD_FILE')

    with pytest.raises(ValidationError):
        cp.execute(['/home'], ['-r'], ctx)

    fs.create_dir('/home')
    with pytest.raises(ValidationError):
        cp.execute(['/home', '/photos/my.png'], ['-r'], ctx)


def test_cp_r_overwrite_with_undo_records(cp: Command, fs, ctx: CommandContext):
    fs.create_dir('/photos')
    fs.create_file('/photos/photo1.png', contents='SRC1')
    fs.create_file('/photos/my.png', contents='SRC2')
    fs.create_file('/photos/Azamat.jpg', contents='SRC3')

    fs.create_dir('/backup')
    fs.create_dir('/backup/photos')
    fs.create_file('/backup/photos/photo1.png', contents='OLD1')

    cp.execute(['/photos', '/backup'], ['-r'], ctx)

    assert Path('/backup/photos/photo1.png').read_text() == 'SRC1'
    assert Path('/backup/photos/my.png').read_text() == 'SRC2'

    undo = getattr(cp, 'undo')()
    copied_targets = {u.dst for u in undo}
    assert '/backup/photos/photo1.png' in copied_targets
    assert '/backup/photos/my.png' in copied_targets
    assert '/backup/photos/Azamat.jpg' in copied_targets

    over = [u for u in undo if u.dst == '/backup/photos/photo1.png']
    for x in over:
        assert x and x.overwrite is True and x.overwritten_path


def test_cp_r_conflict_file_vs_dir_in_tree(cp: Command, fs, ctx: CommandContext):
    fs.create_dir('/src')
    fs.create_dir('/src/docs')
    fs.create_file('/src/docs/readme', contents='TEXT')

    fs.create_dir('/dst')
    fs.create_dir('/dst/docs')
    fs.create_dir('/dst/docs/readme')

    with pytest.raises(ValidationError):
        cp.execute(['/src/*', '/dst'], ['-r'], ctx)


def test_cp_r_multiple_sources_into_existing_dir(cp: Command, fs, ctx: CommandContext):
    fs.create_dir('/etc')
    fs.create_dir('/photos')
    fs.create_file('/photos/photo1.png', contents='IMG')

    fs.create_dir('/mnt')

    cp.execute(['/etc', '/photos', '/mnt'], ['-r'], ctx)
    assert Path('/mnt/etc').is_dir()
    assert Path('/mnt/photos').is_dir()
    assert Path('/mnt/photos/photo1.png').is_file()

    with pytest.raises(ValidationError):
        cp.execute(['/etc', '/photos', '/mnt/new_place'], ['-r'], ctx)
