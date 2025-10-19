from entity.context import CommandContext


class InMemoryFileSystemRepository:
    def __init__(
        self,
        ctx: CommandContext,
        tree: dict[str, list[str]],  # "директория": ["имя", ...]
    ):
        self._ctx = ctx
        self._tree = tree

    @property
    def current(self) -> str:
        return self._ctx.pwd

    def set_current(self, path: str) -> None:
        self._ctx.pwd = self._normalize_path(path)

    def is_dir(self, path: str) -> bool:
        return self._normalize_path(path) in self._tree

    def expanduser(self, path: str) -> str:
        if path.startswith('~'):
            return self._ctx.home + path[1:]
        return path

    def _normalize_path(self, path: str) -> str:
        path = self.expanduser(path)
        if not path.startswith('/'):
            cur = self._ctx.pwd.rstrip('/')
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
