import os
import re
from pathlib import Path
from typing import Iterator

from entity.context import CommandContext
from entity.errors import ValidationError
from repository.command.path_utils import normalize


class Grep:
    @property
    def name(self) -> str:
        return 'grep'

    @property
    def description(self) -> str:
        return 'Поиск строк по шаблону: grep [-r] [-i] <pattern> <path...>'

    def _validate_args(self, args: list[str]) -> None:
        if len(args) < 2:
            raise ValidationError('grep требует минимум два аргумента: grep -h')

    def _is_recursive(self, flags: list[str]) -> bool:
        return ('-r' in flags) or ('-R' in flags) or ('--recursive' in flags)

    def _is_case_insensitive(self, flags: list[str]) -> bool:
        return ('-i' in flags) or ('--ignore-case' in flags)

    def _iter_files(self, paths: list[Path], recursive: bool) -> Iterator[Path]:
        for p in paths:
            if p.is_file():
                yield p
                continue
            if p.is_dir():
                if not recursive:
                    raise ValidationError(f'Для обхода директории нужен флаг -r: {p}')
                for root, _, names in os.walk(p):
                    root_path = Path(root)
                    for n in names:
                        yield root_path / n
                continue
            raise ValidationError(f'Путь не найден: {p}')

    def execute(self, args: list[str], flags: list[str], ctx: CommandContext) -> str:
        self._validate_args(args)

        recursive = self._is_recursive(flags)
        ignore_case = self._is_case_insensitive(flags)

        pattern, *raw_paths = args
        paths = [normalize(x, ctx) for x in raw_paths]

        re_flags = re.IGNORECASE if ignore_case else 0
        regex = re.compile(pattern, re_flags)

        files = self._iter_files(paths, recursive)
        lines_out: list[str] = []

        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    for idx, line in enumerate(f, start=1):
                        if regex.search(line):
                            lines_out.append(f'{file_path}:{idx}:{line.rstrip()}')
            except (OSError, UnicodeError):
                continue

        return '\n'.join(lines_out)
