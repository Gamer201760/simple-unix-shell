from entity.context import CommandContext
from entity.errors import ValidationError
from usecase.interface import FileSystemRepository


class LsCommand:
    def __init__(self, fs: FileSystemRepository) -> None:
        self._fs = fs

    @property
    def name(self) -> str:
        """Имя команды"""
        return 'ls'

    @property
    def description(self) -> str:
        """Описание команды"""
        return 'Показывает объекты в директории, ls <path>'

    def _validate_args(self, args: list[str]) -> None:
        """Валидация аргументов, выбрасывает DomainError при ошибке"""
        if len(args) > 1:
            raise ValidationError(
                'Команада cd принимает ровно один аргумент, воспользуйтесь man cd'
            )
        if len(args) == 0:
            args.append('.')
        if not self._fs.is_dir(args[0]):
            raise ValidationError(f'Это не директория {args[0]}')

    def execute(self, args: list[str], ctx: CommandContext) -> str:
        """Выполнение команды, выбрасывает DomainError при ошибке"""
        self._validate_args(args)
        objects = self._fs.list_dir(args[0])
        if len(objects) == 0:
            return ''
        return '\n'.join(objects)
