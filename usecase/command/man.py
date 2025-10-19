from entity.context import CommandContext
from entity.errors import ValidationError


class ManCommand:
    @property
    def name(self) -> str:
        return 'man'

    @property
    def description(self) -> str:
        return 'Показывает описание команды, man <command>'

    def validate_args(self, args: list[str]) -> None:
        if len(args) != 1:
            raise ValidationError(
                'Команада man принимает ровно один аргумент, воспользуйтесь man man'
            )
        # TODO: добавить проверку на существование такой команды

    def execute(self, args: list[str], ctx: CommandContext) -> str:
        if args[0] not in ctx.commands:
            raise ValidationError(f'{args[0]} команада не найдена')
        return ctx.commands[args[0]].description
