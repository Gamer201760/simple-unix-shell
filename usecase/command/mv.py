from entity.context import CommandContext
from entity.errors import ValidationError
from entity.undo import UndoRecord
from usecase.interface import FileSystemRepository


class Mv:
    def __init__(self, fs: FileSystemRepository) -> None:
        self._fs = fs
        self._undo_records: list[UndoRecord] = []

    @property
    def name(self) -> str:
        return 'mv'

    @property
    def description(self) -> str:
        return 'Перемещает файл или директорию, mv <source> <dest>'

    def undo(self) -> list[UndoRecord]:
        """Возвращает объект/объекты для отмены этой команды"""
        return self._undo_records.copy()

    def _validate_args(self, args: list[str]) -> None:
        """Валидация аргументов"""
        if len(args) < 2:
            raise ValidationError(
                'mv требует как минимум два аргумента: mv <source> <dest>'
            )

    def execute(self, args: list[str], flags: list[str], ctx: CommandContext) -> str:
        self._undo_records.clear()
        self._validate_args(args)
        *srcs, dst = args
        for src in srcs:
            if not (self._fs.exists(src) or self._fs.is_dir(src)):
                raise ValidationError(f'Источник не найден: {src}')

            overwrite = self._fs.exists(dst)
            overwrite_path = None
            if overwrite:
                overwrite_path = self._fs.delete(dst)
            self._fs.move(src, dst)
            record = UndoRecord(
                action='mv',
                src=src,
                dst=dst,
                overwrite=overwrite,
                overwritten_path=overwrite_path,
            )
            self._undo_records.append(record)
        return f'Перемещены {' '.join(srcs)} -> {dst}'
