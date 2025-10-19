from pathlib import Path

from entity.errors import ValidationError
from usecase.interface import FileSystemRepository


class CdCommand:
    def __init__(self, fs: FileSystemRepository) -> None:
        self._fs = fs

    @property
    def name(self) -> str:
        """Имя команды"""
        return 'cd'

    @property
    def description(self) -> str:
        """Описание команды"""
        return 'Меняет директорию, cd <path>'

    def validate_args(self, args: list[str]) -> None:
        """Валидация аргументов, выбрасывает DomainError при ошибке"""
        if len(args) > 1:
            raise ValidationError(
                'Команада cd принимает ровно один аргумент, воспользуйтесь man cd'
            )
        path = Path(args[0].strip()).expanduser()
        if not path.is_dir():
            raise ValidationError(f'Это не дирректория {path}')

    def execute(self, args: list[str]) -> str:
        """Выполнение команды, выбрасывает DomainError при ошибке"""
        self._fs.set_current(Path(args[0]))
        return ''
