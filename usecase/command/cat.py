from entity.context import CommandContext
from entity.errors import DomainError, ValidationError
from usecase.interface import FileSystemRepository


class Cat:
    def __init__(self, fs: FileSystemRepository) -> None:
        self._fs = fs

    @property
    def name(self) -> str:
        return 'cat'

    @property
    def description(self) -> str:
        return 'Выводит файлы: cat <path...>'

    def _validate_args(self, args: list[str]) -> None:
        if len(args) < 1:
            raise ValidationError('cat требует как минимум один аргумента: cat -h')

    def execute(self, args: list[str], flags: list[str], ctx: CommandContext) -> str:
        self._validate_args(args)
        res = ''

        for x in args:
            src = self._fs.normalize(x)
            if not self._fs.is_file(src):
                raise DomainError(f'{src} не файл')
            res += self._fs.read(src) + '\n'

        return res
