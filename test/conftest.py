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
from repository.command.pwd import Pwd
from repository.command.rm import Rm
from repository.command.whoami import WhoAmI


def _setup_tree(fs, ctx: CommandContext):
    ctx.pwd = '/vfs/home/test'
    ctx.home = '/vfs/home/test'
    ctx.user = 'test'

    fs.create_dir('/vfs')
    fs.create_dir('/vfs/home')
    fs.create_dir('/vfs/etc')
    fs.create_dir('/vfs/photos')

    fs.create_dir('/vfs/home/test')
    fs.create_dir('/vfs/home/test2')

    fs.create_dir('/vfs/home/test/etc')

    fs.create_file('/vfs/photos/photo1.png', contents='IMG1')
    fs.create_file('/vfs/photos/my.png', contents='IMG2')
    fs.create_file('/vfs/photos/Azamat.jpg', contents='IMG3')
    fs.create_file('/vfs/photos/new photo.png', contents='IMG4')


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
    return Rm('/.trash')


@pytest.fixture
def cd() -> Cd:
    return Cd()


@pytest.fixture
def ctx() -> CommandContext:
    return CommandContext(pwd=os.getcwd(), home=str(Path.home()), user=os.getlogin())


@pytest.fixture
def whoami() -> WhoAmI:
    return WhoAmI()


@pytest.fixture
def pwd() -> Pwd:
    return Pwd()
