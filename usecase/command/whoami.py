from entity.context import CommandContext


class WhoAmICommand:
    @property
    def name(self) -> str:
        return 'whoami'

    @property
    def description(self) -> str:
        return 'Отображать действующий идентификатор пользователя'

    def validate_args(self, args: list[str]) -> None:
        return None

    def execute(self, args: list[str], ctx: CommandContext) -> str:
        return ctx.user
