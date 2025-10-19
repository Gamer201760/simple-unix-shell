import pytest

from entity.command import Command
from entity.context import CommandContext
from entity.pwd import PwdCommand


@pytest.fixture
def pwd() -> Command:
    return PwdCommand()


@pytest.mark.parametrize(
    'args,ctx,expected',
    (
        (['fafdsf'], CommandContext(pwd='123', home='/home/test', user='test'), '123'),
        (['341'], CommandContext(pwd='goose', home='/home/test', user='test'), 'goose'),
        (
            ['ieru', '123123'],
            CommandContext(pwd='palka', home='/home/test', user='test'),
            'palka',
        ),
        (
            [],
            CommandContext(pwd='/home/test/docs', home='/home/test', user='test'),
            '/home/test/docs',
        ),
        ([''], CommandContext(pwd='/etc', home='/home/test', user='test'), '/etc'),
    ),
)
def test_pwd(args: list[str], ctx: CommandContext, expected: str, pwd: Command):
    assert pwd.execute(args, ctx) == expected
