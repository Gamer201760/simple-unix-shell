import os
from pathlib import Path

from entity.context import CommandContext
from entity.errors import ValidationError
from usecase.interface import FileSystemRepository


class Cd:
    def __init__(self, fs: FileSystemRepository) -> None:
        self._fs = fs

    @property
    def name(self) -> str:
        return 'cd'

    @property
    def description(self) -> str:
        return 'Меняет директорию, cd <path>'

    def _validate_args(self, args: list[str]) -> None:
        if len(args) > 1:
            raise ValidationError(
                'Команада cd принимает ровно один аргумент, воспользуйтесь cd -h'
            )

    def _normalize(self, raw: str, ctx: CommandContext) -> Path:
        expanded = os.path.expanduser(raw)
        p = Path(expanded)
        if not p.is_absolute():
            p = Path(ctx.pwd) / p
        return p.resolve(strict=False)

    def execute(self, args: list[str], flags: list[str], ctx: CommandContext) -> str:
        self._validate_args(args)

        if len(args) == 0:
            args.append('~')

        if not self._fs.is_dir(args[0]):
            raise ValidationError(f'Это не директория {args[0]}')

        self._fs.set_current(str(self._normalize(args[0], ctx)))
        ctx.pwd = self._fs.current
        return ''
