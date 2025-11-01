from entity.context import CommandContext
from entity.errors import ValidationError
from repository.command.path_utils import normalize


class Cd:
    @property
    def name(self) -> str:
        return 'cd'

    @property
    def description(self) -> str:
        return 'Меняет директорию, cd <path>'

    def _validate_args(self, args: list[str]) -> None:
        if len(args) > 1:
            raise ValidationError('Команада cd принимает ровно один аргумент: cd -h')

    def execute(self, args: list[str], flags: list[str], ctx: CommandContext) -> str:
        self._validate_args(args)
        target = args[0] if args else '~'
        path = normalize(target, ctx)
        if not path.is_dir():
            raise ValidationError(f'Это не директория {target}')
        ctx.pwd = str(path)
        return ''
