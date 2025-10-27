from copy import deepcopy

import pytest

from repository.in_memory_fs import InMemoryFileSystemRepository
from usecase.interface import FileSystemRepository

UNIX_TREE: dict[str, list[str]] = {
    '/': ['home', 'etc', 'photos'],
    '/home': ['test', 'test2'],
    '/home/test': ['etc'],
    '/home/test/etc': [],
    '/home/test2': [],
    '/etc': [],
    '/photos': ['photo1.png', 'my.png', 'Azamat.jpg'],
}


@pytest.fixture
def fs() -> FileSystemRepository:
    """Fixture for InMemoryFileSystemRepository with UNIX_TREE."""
    return InMemoryFileSystemRepository(deepcopy(UNIX_TREE))


@pytest.fixture
def fs_with_files(fs: FileSystemRepository) -> FileSystemRepository:
    """Fixture for fs with some file contents added."""
    fs.write('/photos/photo1.png', 'image data 1')
    fs.write('/photos/my.png', 'image data 2')
    return fs


@pytest.mark.parametrize(
    'path, expected_result',
    [
        (
            '/',
            [
                '/',
                '/home',
                '/etc',
                '/photos',
                '/home/test',
                '/home/test2',
                '/home/test/etc',
                '/photos/photo1.png',
                '/photos/my.png',
                '/photos/Azamat.jpg',
            ],
        ),
        ('/home', ['/home', '/home/test', '/home/test2', '/home/test/etc']),
        (
            '/photos',
            ['/photos', '/photos/photo1.png', '/photos/my.png', '/photos/Azamat.jpg'],
        ),
    ],
)
def test_walk_valid_paths(
    fs: FileSystemRepository, path: str, expected_result: list[str]
):
    """Test walk returns all recursive paths for valid directories."""
    result = fs.walk(path)
    assert sorted(result) == sorted(expected_result)


def test_walk_nonexistent(fs: FileSystemRepository):
    """Test walk on non-existent path returns just the path."""
    result = fs.walk('/nonexistent')
    assert result == ['/nonexistent']


def test_walk_empty_dir(fs: FileSystemRepository):
    """Test walk on empty directory returns just the directory path."""
    result = fs.walk('/home/test/etc')
    assert result == ['/home/test/etc']


@pytest.mark.parametrize('path', ['/home/test/newdir', '/photos/newsubdir'])
def test_mkdir_new_dir(fs: FileSystemRepository, path: str):
    """Test mkdir creates a new directory."""
    fs.mkdir(path)
    assert path in fs._tree
    assert fs._tree[path] == []


def test_mkdir_existing_dir(fs: FileSystemRepository):
    """Test mkdir on existing directory raises FileExistsError."""
    with pytest.raises(FileExistsError):
        fs.mkdir('/home')


@pytest.mark.parametrize('path', ['/nonexistent/new', '/photos/photo1.png/new'])
def test_mkdir_invalid_parent(fs: FileSystemRepository, path: str):
    """Test mkdir raises KeyError for non-existent parent."""
    with pytest.raises(KeyError):
        fs.mkdir(path)


def test_read_existing_file(fs_with_files: FileSystemRepository):
    """Test read returns the content of an existing file."""
    content = fs_with_files.read('/photos/photo1.png')
    assert content == 'image data 1'


@pytest.mark.parametrize('path', ['/photos/nonexistent.txt', '/home/test/nonfile'])
def test_read_nonexistent_file(fs_with_files: FileSystemRepository, path: str):
    """Test read raises FileNotFoundError for non-existent file."""
    with pytest.raises(FileNotFoundError):
        fs_with_files.read(path)


def test_read_empty_file(fs_with_files: FileSystemRepository):
    """Test read returns empty string for file with no content."""
    fs_with_files.write('/home/test/empty.txt', '')
    content = fs_with_files.read('/home/test/empty.txt')
    assert content == ''


@pytest.mark.parametrize('data', ['hello world', '', 'multiline\ncontent'])
def test_write_various_data(fs: FileSystemRepository, data: str):
    """Test write stores different data correctly."""
    path = '/etc/config.txt'
    fs.write(path, data)
    assert path in fs._files
    assert fs.read(path) == data


def test_write_overwrite_file(fs_with_files: FileSystemRepository):
    """Test write overwrites existing file content."""
    path = '/photos/my.png'
    new_data = 'updated image'
    fs_with_files.write(path, new_data)
    assert fs_with_files.read(path) == new_data


def test_write_new_file_adds_to_dir(fs: FileSystemRepository):
    """Test write adds file name to parent directory listing."""
    path = '/etc/newfile.txt'
    fs.write(path, 'content')
    assert 'newfile.txt' in fs.list_dir('/etc')


@pytest.mark.parametrize(
    'path, expected_type, expected_detail',
    [
        ('/photos/photo1.png', 'file', {'size': len('image data 1')}),
        ('/home', 'dir', {'items': 2}),
        ('/photos', 'dir', {'items': 3}),
    ],
)
def test_stat_valid_paths(
    fs_with_files: FileSystemRepository,
    path: str,
    expected_type: str,
    expected_detail: dict,
):
    """Test stat returns correct type and details for files and directories."""
    stat_info = fs_with_files.stat(path)
    assert stat_info['type'] == expected_type
    for key, value in expected_detail.items():
        assert stat_info[key] == value


@pytest.mark.parametrize('path', ['/nonexistent', '/home/nonfile'])
def test_stat_nonexistent_raises(fs_with_files: FileSystemRepository, path: str):
    """Test stat raises FileNotFoundError for non-existent path."""
    with pytest.raises(FileNotFoundError):
        fs_with_files.stat(path)


def test_stat_empty_dir(fs: FileSystemRepository):
    """Test stat on empty directory returns items=0."""
    stat_info = fs.stat('/home/test/etc')
    assert stat_info['type'] == 'dir'
    assert stat_info['items'] == 0


def test_copy_file(fs_with_files: FileSystemRepository):
    """Test copy copies a file to new location."""
    fs_with_files.copy('/photos/photo1.png', '/home/test/copied.png')
    assert fs_with_files.read('/home/test/copied.png') == 'image data 1'


def test_copy_overwrite(fs_with_files: FileSystemRepository):
    """Test copy overwrites existing destination file."""
    dest = '/home/test/target.png'
    fs_with_files.write(dest, 'old content')
    fs_with_files.copy('/photos/my.png', dest)
    assert fs_with_files.read(dest) == 'image data 2'


@pytest.mark.parametrize('source', ['/nonexistent.txt', '/home'])
def test_copy_invalid_source(fs_with_files: FileSystemRepository, source: str):
    """Test copy raises FileNotFoundError for invalid source."""
    with pytest.raises(FileNotFoundError):
        fs_with_files.copy(source, '/dest')


@pytest.mark.parametrize('path', ['/photos/photo1.png', '/home/test/newfile.txt'])
def test_delete_file(fs_with_files: FileSystemRepository, path: str):
    """Test delete moves file to trash and removes from original location."""
    if path not in fs_with_files._files:
        fs_with_files.write(path, 'to delete')
    parent, name = path.rsplit('/', 1) if '/' in path else ('/', path)
    result = fs_with_files.delete(path)
    assert result.startswith('/.trash/')
    assert name not in fs_with_files.list_dir(parent)
    assert path not in fs_with_files._files


def test_delete_directory(fs: FileSystemRepository):
    """Test delete moves directory entry to trash."""
    path = '/home/test/etc'
    parent, name = path.rsplit('/', 1)
    result = fs.delete(path)
    assert result.startswith('/.trash/')
    assert name not in fs.list_dir(parent)
    # Note: Directory key remains in _tree (orphan)


@pytest.mark.parametrize('path', ['/nonexistent', '/'])
def test_delete_invalid(fs: FileSystemRepository, path: str):
    """Test delete raises FileNotFoundError for invalid path."""
    with pytest.raises(FileNotFoundError):
        fs.delete(path)


@pytest.mark.parametrize(
    'source, dest',
    [
        ('/photos/my.png', '/home/test/moved.png'),
        ('/etc', '/home/moved_etc'),  # Simple directory move (entry only)
    ],
)
def test_move_valid(fs_with_files: FileSystemRepository, source: str, dest: str):
    """Test move relocates file or directory entry."""
    src_parent, src_name = source.rsplit('/', 1) if '/' in source else ('/', source)
    dst_parent, dst_name = dest.rsplit('/', 1) if '/' in dest else ('/', dest)
    if src_parent == '':
        src_parent = '/'
    if dst_parent == '':
        dst_parent = '/'
    fs_with_files.move(source, dest)
    assert src_name not in fs_with_files.list_dir(src_parent)
    assert dst_name in fs_with_files.list_dir(dst_parent)
    if fs_with_files.is_file(source):
        assert source not in fs_with_files._files
        assert fs_with_files.read(dest) == 'image data 2'


def test_move_overwrite(fs_with_files: FileSystemRepository):
    """Test move overwrites destination if it exists."""
    dest = '/photos/overwritten.png'
    fs_with_files.write(dest, 'old')
    fs_with_files.move('/photos/my.png', dest)
    assert fs_with_files.read(dest) == 'image data 2'


@pytest.mark.parametrize(
    'source,dest',
    [
        ('/nonexistent', '/dest'),
    ],
)
def test_move_invalid(fs_with_files: FileSystemRepository, source: str, dest: str):
    """Test move raises FileNotFoundError for invalid source or destination."""
    with pytest.raises(FileNotFoundError):
        fs_with_files.move(source, dest)


@pytest.mark.parametrize(
    'path, expected',
    [
        ('/photos/photo1.png', True),
        ('/home/test/etc', False),
        ('/nonexistent.txt', False),
    ],
)
def test_is_file(fs_with_files: FileSystemRepository, path: str, expected: bool):
    """Test is_file returns correct result for files and non-files."""
    if expected and path not in fs_with_files._files:
        fs_with_files.write(path, 'content')
    assert fs_with_files.is_file(path) == expected


def test_is_file_directory(fs: FileSystemRepository):
    """Test is_file returns False for directories."""
    assert not fs.is_file('/home')


def test_is_file_nonexistent_parent(fs: FileSystemRepository):
    """Test is_file returns False if parent does not exist."""
    assert not fs.is_file('/nonexistent/file.txt')


@pytest.mark.parametrize(
    'path, expected',
    [
        ('/', True),
        ('/photos', True),
        ('/photos/photo1.png', False),
        ('/nonexistent', False),
    ],
)
def test_is_dir(fs: FileSystemRepository, path: str, expected: bool):
    """Test is_dir returns correct result for directories and non-directories."""
    assert fs.is_dir(path) == expected


def test_is_dir_file(fs_with_files: FileSystemRepository):
    """Test is_dir returns False for files."""
    assert not fs_with_files.is_dir('/photos/photo1.png')


def test_is_dir_after_write(fs: FileSystemRepository):
    """Test is_dir remains False after writing a file (no conversion to dir)."""
    fs.write('/home/test/file.txt', 'content')
    assert not fs.is_dir('/home/test/file.txt')


@pytest.mark.parametrize(
    'path, expected',
    [
        ('/photos', ['photo1.png', 'my.png', 'Azamat.jpg']),
        ('/home', ['test', 'test2']),
        ('/home/test/etc', []),
    ],
)
def test_list_dir_valid(fs: FileSystemRepository, path: str, expected: list[str]):
    """Test list_dir returns the contents of a directory."""
    result = fs.list_dir(path)
    assert sorted(result) == sorted(expected)


@pytest.mark.parametrize('path', ['/nonexistent', '/photos/non'])
def test_list_dir_invalid(fs: FileSystemRepository, path: str):
    """Test list_dir raises KeyError for non-existent directory."""
    with pytest.raises(KeyError):
        fs.list_dir(path)


def test_list_dir_empty(fs: FileSystemRepository):
    """Test list_dir returns empty list for empty directory."""
    assert fs.list_dir('/home/test/etc') == []


@pytest.mark.parametrize(
    'path, expected',
    [
        ('/photos/photo1.png', 'photo1.png'),
        ('/home/test/etc', 'etc'),
        ('/', ''),
        ('/home/test/../test', 'test'),
    ],
)
def test_basename_valid(fs: FileSystemRepository, path: str, expected: str):
    """Test basename extracts the base name correctly."""
    assert fs.basename(path) == expected


def test_basename_with_trailing_slash(fs: FileSystemRepository):
    """Test basename handles trailing slash."""
    assert fs.basename('/photos/') == 'photos'


def test_basename_relative(fs: FileSystemRepository):
    """Test basename on relative path after normalization."""
    assert fs.basename('etc') == 'etc'


def test_current_property(fs: FileSystemRepository):
    """Test current property returns the current working directory."""
    assert fs.current == '/home/test'


@pytest.mark.parametrize('path', ['/home', '/photos', '/home/test/etc'])
def test_set_current_valid(fs: FileSystemRepository, path: str):
    """Test set_current updates the current directory to valid paths."""
    fs.set_current(path)
    assert fs.current == path


def test_set_current_relative(fs: FileSystemRepository):
    """Test set_current handles relative paths."""
    fs.set_current('etc')
    assert fs.current == '/home/test/etc'


def test_set_current_nonexistent(fs: FileSystemRepository):
    """Test set_current sets even non-existent paths."""
    fs.set_current('/nonexistent')
    assert fs.current == '/nonexistent'
