from entity.context import CommandContext
from entity.errors import ValidationError


class ManCommand:
    @property
    def name(self) -> str:
        return 'man'

    @property
    def description(self) -> str:
        return 'Показывает описание команды, man <command>'

    def _validate_args(self, args: list[str], ctx: CommandContext) -> None:
        if len(args) != 1:
            raise ValidationError(
                'Команада man принимает ровно один аргумент, воспользуйтесь man man'
            )
        if args[0] not in ctx.commands:
            raise ValidationError(f'{args[0]} команада не найдена')

    def execute(self, args: list[str], ctx: CommandContext) -> str:
        self._validate_args(args, ctx)
        return ctx.commands[args[0]].description
