import os
import stat
from datetime import datetime
from pathlib import Path

from entity.context import CommandContext
from entity.errors import DomainError
from repository.command.path_utils import normalize


class Ls:
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
            path = normalize(x, ctx)
            if not (path.is_dir() or path.is_file()):
                raise DomainError(f'{path} не существует')

            if path.is_dir():
                for name in os.listdir(path):
                    full = path / name
                    lines.append(self._format_entry(full, long))
                if len(args) > 1:
                    lines.append('')
                continue

            if path.is_file():
                lines.append(self._format_entry(path, long))
                continue

        if len(lines) > 0 and lines[-1] == '':
            lines.pop()

        return '\n'.join(lines)

    def _format_entry(self, path: Path, long: bool) -> str:
        name = path.name
        if not long:
            return name

        st = path.stat()
        perm = stat.filemode(st.st_mode)
        size = st.st_size
        when = datetime.fromtimestamp(st.st_mtime).strftime('%Y-%m-%d %H:%M')

        return f'{perm} {size:>10} {when} {name}'
