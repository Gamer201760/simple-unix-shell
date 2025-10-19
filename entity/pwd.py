from entity.context import CommandContext


class PwdCommand:
    @property
    def name(self) -> str:
        return 'pwd'

    @property
    def description(self) -> str:
        return 'Отображать текущую рабочую директорию'

    def validate_args(self, args: list[str]) -> None:
        return None

    def execute(self, args: list[str], ctx: CommandContext) -> str:
        return ctx.pwd
