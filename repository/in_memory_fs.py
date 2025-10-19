class InMemoryFileSystemRepository:
    def __init__(
        self,
        tree: dict[str, list[str]],  # "директория": ["имя", ...]
        home: str = '/home/test',
        pwd: str = '/home/test',
    ):
        self._tree = tree
        self._pwd = pwd
        self._home = home

    def get_current(self) -> str:
        return self._pwd

    def set_current(self, path: str) -> None:
        self._pwd = self._normalize_path(path)

    def is_dir(self, path: str) -> bool:
        return self._normalize_path(path) in self._tree

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
