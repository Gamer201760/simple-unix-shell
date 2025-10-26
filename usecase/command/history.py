from entity.context import CommandContext
from entity.errors import ValidationError
from usecase.interface import HistoryRepository


class History:
    def __init__(self, history_repo: HistoryRepository) -> None:
        self._history_repo = history_repo

    @property
    def name(self) -> str:
        return 'history'

    @property
    def description(self) -> str:
        return 'Выводит последние n коммнад, history <n>'

    def _validate_args(self, args: list[str]) -> None:
        if len(args) > 1:
            raise ValidationError(
                'history принимает ровно один аргумент, воспользуйтесь history -h'
            )

    def execute(self, args: list[str], flags: list[str], ctx: CommandContext) -> str:
        self._validate_args(args)
        if len(args) == 0:
            return '\n'.join(self._history_repo.all())

        if not args[0].isdigit():
            raise ValidationError('аргумент должен быть числом')
        return '\n'.join(self._history_repo.last(int(args[0])))
