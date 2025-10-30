from copy import deepcopy

import pytest

from entity.context import CommandContext
from entity.errors import DomainError, ValidationError
from repository.in_memory_fs import InMemoryFileSystemRepository
from usecase.command.cat import Cat
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
    return InMemoryFileSystemRepository(deepcopy(UNIX_TREE))


@pytest.fixture
def cat(fs: FileSystemRepository) -> Cat:
    return Cat(fs)


def test_cat_single_file_returns_with_trailing_newline(
    cat: Cat, fs: FileSystemRepository, ctx: CommandContext
):
    fs.write('/etc/hosts', 'LINE1')
    out = cat.execute(['/etc/hosts'], [], ctx)
    assert out == 'LINE1\n'


def test_cat_multiple_files_concatenates_in_order(
    cat: Cat, fs: FileSystemRepository, ctx: CommandContext
):
    fs.write('/etc/hosts', 'H1')
    fs.write('/home/test/etc/conf', 'C2')
    out = cat.execute(['/etc/hosts', '/home/test/etc/conf'], [], ctx)
    assert out == 'H1\nC2\n'


def test_cat_keeps_argument_order(
    cat: Cat, fs: FileSystemRepository, ctx: CommandContext
):
    fs.write('/etc/a', 'A')
    fs.write('/etc/b', 'B')
    out = cat.execute(['/etc/b', '/etc/a'], [], ctx)
    assert out == 'B\nA\n'


def test_cat_error_when_no_args(
    cat: Cat, fs: FileSystemRepository, ctx: CommandContext
):
    with pytest.raises(ValidationError):
        cat.execute([], [], ctx)


def test_cat_error_when_path_is_directory(
    cat: Cat, fs: FileSystemRepository, ctx: CommandContext
):
    # '/photos' — каталог в исходном дереве
    with pytest.raises(DomainError):
        cat.execute(['/photos'], [], ctx)


def test_cat_error_when_file_missing(
    cat: Cat, fs: FileSystemRepository, ctx: CommandContext
):
    with pytest.raises(DomainError):
        cat.execute(['/no/such/file'], [], ctx)


def test_cat_raises_on_second_arg_after_first_ok(
    cat: Cat, fs: FileSystemRepository, ctx: CommandContext
):
    fs.write('/etc/one', 'ONE')
    with pytest.raises(DomainError):
        cat.execute(['/etc/one', '/photos'], [], ctx)


def test_cat_properties(cat: Cat):
    assert cat.name == 'cat'
    assert 'Выводит файлы' in cat.description
