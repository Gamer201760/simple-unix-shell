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
    f = InMemoryFileSystemRepository(deepcopy(UNIX_TREE))
    f.write('/photos/photo1.png', 'image data 1')
    f.write('/photos/my.png', 'image data 2')
    return f


@pytest.mark.parametrize(
    'path, expected_tuples',
    [
        (
            '/',
            [
                ('/', ['etc', 'home', 'photos'], []),  # Корень: директории, без файлов
                ('/etc', [], []),  # Пустая /etc
                ('/home', ['test', 'test2'], []),  # home с поддиректориями
                ('/home/test', ['etc'], []),  # test с etc (предполагаем пустая)
                ('/home/test/etc', [], []),  # Пустая etc в test
                ('/home/test2', [], []),  # Пустая test2
                (
                    '/photos',
                    [],
                    ['Azamat.jpg', 'my.png', 'photo1.png'],
                ),  # photos с файлами (отсортировано)
            ],
        ),
        (
            '/home',
            [
                ('/home', ['test', 'test2'], []),  # home
                ('/home/test', ['etc'], []),  # test
                ('/home/test/etc', [], []),  # etc в test
                ('/home/test2', [], []),  # test2
            ],
        ),
        (
            '/photos',
            [
                ('/photos', [], ['Azamat.jpg', 'my.png', 'photo1.png']),  # Только файлы
            ],
        ),
    ],
)
def test_walk_valid_paths(
    fs: FileSystemRepository,
    path: str,
    expected_tuples: list[tuple[str, list[str], list[str]]],
):
    """Test walk returns correct tuples (root, dirnames, filenames) for valid directories."""
    # Собираем все кортежи из генератора
    result = list(fs.walk(path))
    # Сортируем по root для детерминизма (os.walk сохраняет порядок, но для теста)
    result_sorted = sorted(result, key=lambda x: x[0])
    expected_sorted = sorted(expected_tuples, key=lambda x: x[0])

    # Проверяем каждый кортеж: root, dirnames (сортированные), filenames (сортированные)
    for actual, expected in zip(result_sorted, expected_sorted):
        assert actual[0] == expected[0], f'Root mismatch: {actual[0]} vs {expected[0]}'
        assert sorted(actual[1]) == sorted(
            expected[1]
        ), f'Dirs mismatch for {actual[0]}: {actual[1]} vs {expected[1]}'
        assert sorted(actual[2]) == sorted(
            expected[2]
        ), f'Files mismatch for {actual[0]}: {actual[2]} vs {expected[2]}'


def test_walk_nonexistent(fs: FileSystemRepository):
    """Test walk on non-existent path raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError, match='Directory /nonexistent not found'):
        list(
            fs.walk('/nonexistent')
        )  # Генератор не стартует, если директория не существует


def test_walk_empty_dir(fs: FileSystemRepository):
    """Test walk on empty directory yields single tuple with empty lists."""
    result = list(fs.walk('/home/test/etc'))
    assert len(result) == 1
    root, dirnames, filenames = result[0]
    assert root == '/home/test/etc'
    assert dirnames == []
    assert filenames == []


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


def test_read_existing_file(fs: FileSystemRepository):
    """Test read returns the content of an existing file."""
    content = fs.read('/photos/photo1.png')
    assert content == 'image data 1'


@pytest.mark.parametrize('path', ['/photos/nonexistent.txt', '/home/test/nonfile'])
def test_read_nonexistent_file(fs: FileSystemRepository, path: str):
    """Test read raises FileNotFoundError for non-existent file."""
    with pytest.raises(FileNotFoundError):
        fs.read(path)


def test_read_empty_file(fs: FileSystemRepository):
    """Test read returns empty string for file with no content."""
    fs.write('/home/test/empty.txt', '')
    content = fs.read('/home/test/empty.txt')
    assert content == ''


@pytest.mark.parametrize('data', ['hello world', '', 'multiline\ncontent'])
def test_write_various_data(fs: FileSystemRepository, data: str):
    """Test write stores different data correctly."""
    path = '/etc/config.txt'
    fs.write(path, data)
    assert path in fs._files
    assert fs.read(path) == data


def test_write_overwrite_file(fs: FileSystemRepository):
    """Test write overwrites existing file content."""
    path = '/photos/my.png'
    new_data = 'updated image'
    fs.write(path, new_data)
    assert fs.read(path) == new_data


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
    fs: FileSystemRepository,
    path: str,
    expected_type: str,
    expected_detail: dict,
):
    """Test stat returns correct type and details for files and directories."""
    stat_info = fs.stat(path)
    assert stat_info['type'] == expected_type
    for key, value in expected_detail.items():
        assert stat_info[key] == value


@pytest.mark.parametrize('path', ['/nonexistent', '/home/nonfile'])
def test_stat_nonexistent_raises(fs: FileSystemRepository, path: str):
    """Test stat raises FileNotFoundError for non-existent path."""
    with pytest.raises(FileNotFoundError):
        fs.stat(path)


def test_stat_empty_dir(fs: FileSystemRepository):
    """Test stat on empty directory returns items=0."""
    stat_info = fs.stat('/home/test/etc')
    assert stat_info['type'] == 'dir'
    assert stat_info['items'] == 0


def test_copy_file(fs: FileSystemRepository):
    """Test copy copies a file to new location."""
    fs.copy('/photos/photo1.png', '/home/test/copied.png')
    assert fs.read('/home/test/copied.png') == 'image data 1'


def test_copy_overwrite(fs: FileSystemRepository):
    """Test copy overwrites existing destination file."""
    dest = '/home/test/target.png'
    fs.write(dest, 'old content')
    fs.copy('/photos/my.png', dest)
    assert fs.read(dest) == 'image data 2'


@pytest.mark.parametrize('source', ['/nonexistent.txt', '/home'])
def test_copy_invalid_source(fs: FileSystemRepository, source: str):
    """Test copy raises FileNotFoundError for invalid source."""
    with pytest.raises(FileNotFoundError):
        fs.copy(source, '/dest')


@pytest.mark.parametrize('path', ['/photos/photo1.png', '/home/test/newfile.txt'])
def test_delete_file(fs: FileSystemRepository, path: str):
    """Test delete moves file to trash and removes from original location."""
    if path not in fs._files:
        fs.write(path, 'to delete')
    parent, name = path.rsplit('/', 1) if '/' in path else ('/', path)
    result = fs.delete(path)
    assert result.startswith('/.trash/')
    assert name not in fs.list_dir(parent)
    assert path not in fs._files


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
def test_move_valid(fs: FileSystemRepository, source: str, dest: str):
    """Test move relocates file or directory entry."""
    src_parent, src_name = source.rsplit('/', 1) if '/' in source else ('/', source)
    dst_parent, dst_name = dest.rsplit('/', 1) if '/' in dest else ('/', dest)
    if src_parent == '':
        src_parent = '/'
    if dst_parent == '':
        dst_parent = '/'
    fs.move(source, dest)
    assert src_name not in fs.list_dir(src_parent)
    assert dst_name in fs.list_dir(dst_parent)
    if fs.is_file(source):
        assert source not in fs._files
        assert fs.read(dest) == 'image data 2'


def test_move_overwrite(fs: FileSystemRepository):
    """Test move overwrites destination if it exists."""
    dest = '/photos/overwritten.png'
    fs.write(dest, 'old')
    fs.move('/photos/my.png', dest)
    assert fs.read(dest) == 'image data 2'


@pytest.mark.parametrize(
    'source,dest',
    [
        ('/nonexistent', '/dest'),
    ],
)
def test_move_invalid(fs: FileSystemRepository, source: str, dest: str):
    """Test move raises FileNotFoundError for invalid source or destination."""
    with pytest.raises(FileNotFoundError):
        fs.move(source, dest)


@pytest.mark.parametrize(
    'path, expected',
    [
        ('/photos/photo1.png', True),
        ('/home/test/etc', False),
        ('/nonexistent.txt', False),
    ],
)
def test_is_file(fs: FileSystemRepository, path: str, expected: bool):
    """Test is_file returns correct result for files and non-files."""
    if expected and path not in fs._files:
        fs.write(path, 'content')
    assert fs.is_file(path) == expected


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


def test_is_dir_file(fs: FileSystemRepository):
    """Test is_dir returns False for files."""
    assert not fs.is_dir('/photos/photo1.png')


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
