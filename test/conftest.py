import os
from pathlib import Path

import pytest

from entity.context import CommandContext
from repository.command.cat import Cat
from repository.command.cd import Cd
from repository.command.cp import Cp
from repository.command.ls import Ls
from repository.command.mkdir import Mkdir
from repository.command.mv import Mv
from repository.command.rm import Rm
from repository.in_memory_fs import InMemoryFileSystemRepository
from usecase.interface import FileSystemRepository


@pytest.fixture
def cp() -> Cp:
    return Cp()


@pytest.fixture
def cat() -> Cat:
    return Cat()


@pytest.fixture
def ls() -> Ls:
    return Ls()


@pytest.fixture
def mkdir() -> Mkdir:
    return Mkdir()


@pytest.fixture
def mv() -> Mv:
    return Mv()


@pytest.fixture
def rm() -> Rm:
    return Rm()


@pytest.fixture
def fs_controller() -> FileSystemRepository:
    return InMemoryFileSystemRepository({})


@pytest.fixture
def cd(fs_controller) -> Cd:
    return Cd(fs_controller)


@pytest.fixture
def ctx() -> CommandContext:
    return CommandContext(pwd=os.getcwd(), home=str(Path.home()), user=os.getlogin())
