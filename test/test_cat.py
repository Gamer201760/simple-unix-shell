import pytest

from entity.context import CommandContext
from entity.errors import DomainError, ValidationError
from repository.command.cat import Cat


def test_cat_single_file_returns_with_trailing_newline(
    cat: Cat, fs, ctx: CommandContext
):
    fs.create_dir('/etc')
    fs.create_file('/etc/hosts', contents='LINE1')
    out = cat.execute(['/etc/hosts'], [], ctx)
    assert out == 'LINE1'


def test_cat_multiple_files_concatenates_in_order(cat: Cat, fs, ctx: CommandContext):
    fs.create_dir('/home/test/etc')
    fs.create_file('/etc/hosts', contents='H1')
    fs.create_file('/home/test/etc/conf', contents='C2')
    out = cat.execute(['/etc/hosts', '/home/test/etc/conf'], [], ctx)
    assert out == 'H1\nC2'


def test_cat_keeps_argument_order(cat: Cat, fs, ctx: CommandContext):
    fs.create_dir('/etc')
    fs.create_file('/etc/a', contents='A')
    fs.create_file('/etc/b', contents='B')
    out = cat.execute(['/etc/b', '/etc/a'], [], ctx)
    assert out == 'B\nA'


def test_cat_error_when_no_args(cat: Cat, fs, ctx: CommandContext):
    with pytest.raises(ValidationError):
        cat.execute([], [], ctx)


def test_cat_error_when_path_is_directory(cat: Cat, fs, ctx: CommandContext):
    fs.create_dir('/photos')
    with pytest.raises(DomainError):
        cat.execute(['/photos'], [], ctx)


def test_cat_error_when_file_missing(cat: Cat, fs, ctx: CommandContext):
    with pytest.raises(DomainError):
        cat.execute(['/no/such/file'], [], ctx)


def test_cat_raises_on_second_arg_after_first_ok(cat: Cat, fs, ctx: CommandContext):
    fs.create_dir('/etc')
    fs.create_file('/etc/one', contents='ONE')
    fs.create_dir('/photos')
    with pytest.raises(DomainError):
        cat.execute(['/etc/one', '/photos'], [], ctx)


def test_cat_properties(cat: Cat):
    assert cat.name == 'cat'
    assert 'Выводит файлы' in cat.description
