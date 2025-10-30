from entity.context import CommandContext
from entity.errors import ValidationError
from usecase.interface import FileSystemRepository


class Ls:
    def __init__(self, fs: FileSystemRepository) -> None:
        self._fs = fs

    @property
    def name(self) -> str:
        return 'ls'

    @property
    def description(self) -> str:
        return 'Показывает объекты в директории, ls <path>'

    def _validate_args(self, args: list[str]) -> None:
        if len(args) > 1:
            raise ValidationError(
                'Команада ls принимает ровно один аргумент, воспользуйтесь man ls'
            )

    def execute(self, args: list[str], flags: list[str], ctx: CommandContext) -> str:
        self._validate_args(args)

        if len(args) == 0:
            args.append('.')
        if not self._fs.is_dir(args[0]):
            raise ValidationError(f'Это не директория {args[0]}')

        objects = self._fs.list_dir(args[0])
        if len(objects) == 0:
            return ''
        return '\n'.join(objects)
