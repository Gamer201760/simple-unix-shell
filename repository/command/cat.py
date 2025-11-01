from entity.context import CommandContext
from entity.errors import DomainError, ValidationError
from repository.command.path_utils import normalize


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

    def execute(self, args: list[str], flags: list[str], ctx: CommandContext) -> str:
        self._validate_args(args)

        parts: list[str] = []
        for x in args:
            src = normalize(x, ctx)
            if not src.is_file():
                raise DomainError(f'{src} не файл')
            try:
                parts.append(src.read_text(encoding='utf-8').strip())
            except UnicodeDecodeError:
                raise DomainError(f'{src} файл не в кодировке utf-8')
        return '\n'.join(parts)
