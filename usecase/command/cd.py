from entity.context import CommandContext
from entity.errors import ValidationError
from usecase.interface import FileSystemRepository


class Cd:
    def __init__(self, fs: FileSystemRepository) -> None:
        self._fs = fs

    @property
    def name(self) -> str:
        """Имя команды"""
        return 'cd'

    @property
    def description(self) -> str:
        """Описание команды"""
        return 'Меняет директорию, cd <path>'

    def _validate_args(self, args: list[str]) -> None:
        """Валидация аргументов, выбрасывает DomainError при ошибке"""
        if len(args) > 1:
            raise ValidationError(
                'Команада cd принимает ровно один аргумент, воспользуйтесь cd -h'
            )

    def execute(self, args: list[str], flags: list[str], ctx: CommandContext) -> str:
        """Выполнение команды, выбрасывает DomainError при ошибке"""
        self._validate_args(args)

        if len(args) == 0:
            args.append('~')

        if not self._fs.is_dir(args[0]):
            raise ValidationError(f'Это не директория {args[0]}')

        self._fs.set_current(args[0])
        ctx.pwd = self._fs.current  # мб вынести в shell ?
        return ''
