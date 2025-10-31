from entity.context import CommandContext


class Exit:
    @property
    def name(self) -> str:
        return 'exit'

    @property
    def description(self) -> str:
        return 'Выйти из simple-unix-shell'

    def execute(self, args: list[str], flags: list[str], ctx: CommandContext) -> str:
        raise EOFError
