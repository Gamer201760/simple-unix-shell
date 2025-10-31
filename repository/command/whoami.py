from entity.context import CommandContext


class WhoAmI:
    @property
    def name(self) -> str:
        return 'whoami'

    @property
    def description(self) -> str:
        return 'Отображать действующий идентификатор пользователя'

    def execute(self, args: list[str], flags: list[str], ctx: CommandContext) -> str:
        return ctx.user
