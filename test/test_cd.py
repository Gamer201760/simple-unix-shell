import pytest

from entity.command import Command
from entity.errors import ValidationError
from repository.in_memory_fs import InMemoryFileSystemRepository
from usecase.cd import CdCommand


@pytest.fixture
def cd() -> Command:
    return CdCommand(InMemoryFileSystemRepository())


@pytest.mark.parametrize(
    'args',
    (
        ['', ''],
        ['', '', ''],
        ['not-a-dir/'],
    ),
)
def test_validate_args_invalid(args: list[str], cd: Command):
    with pytest.raises(ValidationError):
        cd.validate_args(args)


@pytest.mark.parametrize(
    'args',
    (
        ['.'],
        ['./'],
        ['..'],
        ['../'],
        ['../..'],
        ['../../.'],
        ['../.'],
        ['~'],
        ['/'],
        ['/../../'],
    ),
)
def test_validate_args_valid(args: list[str], cd: Command):
    cd.validate_args(args)
