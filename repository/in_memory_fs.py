import os
from typing import Iterator
from uuid import uuid4


class InMemoryFileSystemRepository:
    def __init__(
        self,
        tree: dict[str, list[str]],
        home: str = '/home/test',
        pwd: str = '/home/test',
    ):
        self._tree = tree
        self._pwd = pwd
        self._home = home
        self._files: dict[str, str] = {}

    @property
    def current(self) -> str:
        return self._pwd

    def walk(self, path: str) -> Iterator[tuple[str, list[str], list[str]]]:
        """Итеративный обход директории, аналогичный os.walk (top-down)."""
        path = self._normalize_path(path)
        if not self.is_dir(path):
            raise FileNotFoundError(f'Directory {path} not found')

        stack = [path]
        while stack:
            root = stack.pop()
            dirnames = []
            filenames = []

            if root in self._tree:
                for name in self._tree[root]:
                    full_child = (
                        root.rstrip('/') + '/' + name if root != '/' else '/' + name
                    )
                    if self.is_dir(full_child):
                        dirnames.append(name)
                    else:
                        filenames.append(name)

            for name in reversed(dirnames):
                full_child = (
                    root.rstrip('/') + '/' + name if root != '/' else '/' + name
                )
                stack.append(full_child)

            yield root, dirnames, filenames

    def mkdir(self, path: str) -> None:
        norm = self._normalize_path(path)
        if norm in self._tree:
            raise FileExistsError(f'Directory {norm} already exists')
        self._tree[norm] = []
        parent, name = norm.rsplit('/', 1)
        if not parent:
            parent = '/'
        if name not in self._tree[parent]:
            self._tree[parent].append(name)

    def read(self, path: str) -> str:
        norm = self._normalize_path(path)
        if not self.is_file(norm):
            raise FileNotFoundError(f'File {norm} not found')
        return self._files.get(norm, '')

    def write(self, path: str, data: str) -> None:
        norm = self._normalize_path(path)
        parent, name = norm.rsplit('/', 1)
        if not parent:
            parent = '/'
        if parent not in self._tree:
            raise FileNotFoundError(f'Directory {parent} does not exist')
        if name not in self._tree[parent]:
            self._tree[parent].append(name)
        self._files[norm] = data

    def basename(self, path: str) -> str:
        norm = self._normalize_path(path)
        return norm.rstrip('/').split('/')[-1]

    def stat(self, path: str) -> dict:
        norm = self._normalize_path(path)
        if self.is_dir(norm):
            return {'type': 'dir', 'items': len(self._tree[norm])}
        if self.is_file(norm):
            return {'type': 'file', 'size': len(self._files.get(norm, ''))}
        raise FileNotFoundError(f'Path {norm} not found')

    def copy(self, source: str, dest: str) -> None:
        src = self._normalize_path(source)
        dst = self._normalize_path(dest)
        if self.is_file(src):
            self.write(dst, self.read(src))
        else:
            raise FileNotFoundError(f'Source file {source} not found')

    def delete(self, path: str) -> str:
        src_path = self._normalize_path(path)
        parent, name = src_path.rsplit('/', 1)
        if not parent:
            parent = '/'
        if parent not in self._tree or name not in self._tree[parent]:
            raise FileNotFoundError(f'File {src_path} not found')
        trash_dir = '/.trash'
        if trash_dir not in self._tree:
            self._tree[trash_dir] = []
        unique_name = f'{name}.{uuid4().hex}'
        trash_path = f'{trash_dir}/{unique_name}'
        self._tree[parent].remove(name)
        self._tree[trash_dir].append(unique_name)
        if src_path in self._files:
            self._files[trash_path] = self._files.pop(src_path)
        return trash_path

    def move(self, source: str, dest: str) -> None:
        src_path = self._normalize_path(source)
        dst_path = self._normalize_path(dest)
        src_dir, src_name = src_path.rsplit('/', 1)
        if not src_dir:
            src_dir = '/'
        if self.is_dir(dst_path):
            target_dir, dst_name = dst_path, src_name
        else:
            target_dir, dst_name = dst_path.rsplit('/', 1)
            if not target_dir:
                target_dir = '/'
        if src_dir not in self._tree:
            raise FileNotFoundError(f'Source directory {src_dir} does not exist')
        if src_name not in self._tree[src_dir]:
            raise FileNotFoundError(f'Source {src_path} does not exist')
        if target_dir not in self._tree:
            raise FileNotFoundError(f'Target directory {target_dir} does not exist')
        src_full = src_dir + '/' + src_name if src_dir != '/' else '/' + src_name
        dst_full = target_dir + '/' + dst_name if target_dir != '/' else '/' + dst_name
        self._tree[src_dir].remove(src_name)
        if dst_name not in self._tree[target_dir]:
            self._tree[target_dir].append(dst_name)
        if src_full in self._files:
            self._files[dst_full] = self._files.pop(src_full)

    def is_file(self, path: str) -> bool:
        norm = self._normalize_path(path)
        parent, name = norm.rsplit('/', 1)
        if not parent:
            parent = '/'
        return (
            parent in self._tree
            and name in self._tree[parent]
            and norm not in self._tree
        )

    def list_dir(self, path: str) -> list[str]:
        return self._tree[self._normalize_path(path)]

    def is_dir(self, path: str) -> bool:
        return self._normalize_path(path) in self._tree

    def set_current(self, path: str) -> None:
        self._pwd = self._normalize_path(path)

    def expanduser(self, path: str) -> str:
        if path.startswith('~'):
            return self._home + path[1:]
        return path

    def _normalize_path(self, path: str) -> str:
        path = self.expanduser(path)
        if not path.startswith('/'):
            cur = self._pwd.rstrip('/')
            path = cur + '/' + path
        parts: list[str] = []
        for part in path.split('/'):
            if part in ('.', ''):
                continue
            elif part == '..':
                if parts:
                    parts.pop()
            else:
                parts.append(part)
        return '/' + '/'.join(parts) if parts else '/'

    def path_join(self, *parts: str) -> str:
        """Аналог os.path.join: интеллектуально соединяет компоненты пути"""
        return os.path.join(*parts)

    def path_dirname(self, path: str) -> str:
        """Аналог os.path.dirname: директория-родитель пути"""
        return os.path.dirname(path)

    def path_relpath(self, path: str, start: str) -> str:
        """Аналог os.path.relpath: относительный путь от start до path"""
        return os.path.relpath(path, start)
