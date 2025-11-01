import pytest

from entity.command import Command
from entity.context import CommandContext
from entity.errors import ValidationError
from test.conftest import setup_tree


def _setup_fs_for_grep(fs, ctx: CommandContext):
    setup_tree(fs, ctx)

    fs.create_file(
        '/vfs/home/test/file1.txt', contents='Hello World\nhello again\nNothing else'
    )
    fs.create_file(
        '/vfs/home/test/file2.log', contents='Log line 1\nAnother line\nhello world'
    )
    fs.create_file('/vfs/home/test/ignoreme', contents='no match here')
    fs.create_dir('/vfs/home/test/subdir')
    fs.create_file(
        '/vfs/home/test/subdir/subfile.txt', contents='subdir hello\nHELLO WORLD\nbye'
    )


@pytest.mark.parametrize(
    'pattern, args, flags, expected',
    [
        (
            'hello',
            ['/vfs/home/test/file1.txt'],
            [],
            [
                '/vfs/home/test/file1.txt:2:hello again',
            ],
        ),
        ('nomatch', ['/vfs/home/test/file1.txt'], [], []),
        (
            'hello',
            ['/vfs/home/test/file1.txt'],
            ['-i'],
            [
                '/vfs/home/test/file1.txt:1:Hello World',
                '/vfs/home/test/file1.txt:2:hello again',
            ],
        ),
        (
            'bye',
            ['/vfs/home/test'],
            ['-r'],
            [
                '/vfs/home/test/subdir/subfile.txt:3:bye',
            ],
        ),
        (
            'hello',
            ['/vfs/home/test'],
            ['-r', '-i'],
            [
                '/vfs/home/test/file1.txt:1:Hello World',
                '/vfs/home/test/file1.txt:2:hello again',
                '/vfs/home/test/file2.log:3:hello world',
                '/vfs/home/test/subdir/subfile.txt:1:subdir hello',
                '/vfs/home/test/subdir/subfile.txt:2:HELLO WORLD',
            ],
        ),
    ],
)
def test_grep_search(
    pattern, args, flags, expected, grep: Command, fs, ctx: CommandContext
):
    _setup_fs_for_grep(fs, ctx)

    output = grep.execute([pattern] + args, flags, ctx)
    lines = list(filter(None, map(str.strip, output.split('\n'))))
    assert sorted(lines) == sorted(expected)


@pytest.mark.parametrize(
    'invalid_args',
    [
        [],
        ['hello'],
        ['hello', '/nonexistent/path'],
    ],
)
def test_grep_invalid_args(invalid_args, grep: Command, fs, ctx: CommandContext):
    setup_tree(fs, ctx)
    with pytest.raises(ValidationError):
        grep.execute(invalid_args, [], ctx)
