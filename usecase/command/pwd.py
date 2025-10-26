from entity.context import CommandContext


class Pwd:
    @property
    def name(self) -> str:
        return 'pwd'

    @property
    def description(self) -> str:
        return 'Отображать текущую рабочую директорию'

    def execute(self, args: list[str], flags: list[str], ctx: CommandContext) -> str:
        return ctx.pwd
