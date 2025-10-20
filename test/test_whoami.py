import pytest

from entity.command import Command
from entity.context import CommandContext
from usecase.command.whoami import WhoAmICommand


@pytest.fixture
def whoami() -> Command:
    return WhoAmICommand()


@pytest.mark.parametrize(
    'args,ctx,expected',
    (
        (['fafdsf'], CommandContext(pwd='123', home='/home/test', user='test'), 'test'),
        (
            ['341'],
            CommandContext(pwd='goose', home='/home/test', user='azamat'),
            'azamat',
        ),
        (
            ['ieru', '123123'],
            CommandContext(pwd='palka', home='/home/test', user='web'),
            'web',
        ),
        (
            [],
            CommandContext(pwd='/home/test/docs', home='/home/test', user='www'),
            'www',
        ),
        ([''], CommandContext(pwd='/etc', home='/home/test', user='root'), 'root'),
    ),
)
def test_whoami(args: list[str], ctx: CommandContext, expected: str, whoami: Command):
    assert whoami.execute(args, [], ctx) == expected
