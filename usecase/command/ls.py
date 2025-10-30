import stat
from datetime import datetime

from entity.context import CommandContext
from usecase.interface import FileSystemRepository


class Ls:
    def __init__(self, fs: FileSystemRepository) -> None:
        self._fs = fs

    @property
    def name(self) -> str:
        return 'ls'

    @property
    def description(self) -> str:
        return 'Показывает объекты в директории, ls [-l] <path...>'

    def execute(self, args: list[str], flags: list[str], ctx: CommandContext) -> str:
        if not args:
            args = ['.']

        long = '-l' in flags
        lines: list[str] = []

        for x in args:
            path = self._fs.normalize(x)

            if self._fs.is_dir(path):
                for name in self._fs.list_dir(path):
                    full = self._fs.path_join(path, name)
                    lines.append(self._format_entry(full, long))
                if len(args) > 1:
                    lines.append('')
                continue

            if self._fs.is_file(path):
                lines.append(self._format_entry(path, long))
                continue
        if lines[-1] == '':
            lines.pop()

        return '\n'.join(lines)

    def _format_entry(self, path: str, long: bool) -> str:
        name = self._fs.basename(path)
        if not long:
            return name

        st = self._fs.stat(path)
        mode = st.get('mode')
        size = st.get('size')
        mtime = st.get('mtime')

        perm = (
            stat.filemode(mode)
            if isinstance(mode, int)
            else st.get('permissions', '???????????')
        )
        when = (
            datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')
            if isinstance(mtime, (int, float))
            else ''
        )

        return f'{perm} {size:>10} {when} {name}'
