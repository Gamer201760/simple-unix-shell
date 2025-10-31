import os
from pathlib import Path

from entity.context import CommandContext
from entity.errors import DomainError, ValidationError


class Cat:
    @property
    def name(self) -> str:
        return 'cat'

    @property
    def description(self) -> str:
        return 'Выводит файлы: cat <path...>'

    def _validate_args(self, args: list[str]) -> None:
        if len(args) < 1:
            raise ValidationError('cat требует как минимум один аргумента: cat -h')

    def _normalize(self, raw: str, ctx: CommandContext) -> Path:
        expanded = os.path.expanduser(raw)
        p = Path(expanded)
        if not p.is_absolute():
            p = Path(ctx.pwd) / p
        return p.resolve(strict=False)

    def execute(self, args: list[str], flags: list[str], ctx: CommandContext) -> str:
        self._validate_args(args)

        parts: list[str] = []
        for x in args:
            src = self._normalize(x, ctx)
            if not src.is_file():
                raise DomainError(f'{src} не файл')
            parts.append(src.read_text(encoding='utf-8'))
        return '\n'.join(parts) + '\n'
