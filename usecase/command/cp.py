from entity.context import CommandContext
from entity.errors import ValidationError
from entity.undo import UndoRecord
from usecase.interface import FileSystemRepository


class Cp:
    def __init__(self, fs: FileSystemRepository) -> None:
        self._fs = fs
        self._undo_records: list[UndoRecord] = []

    @property
    def name(self) -> str:
        return 'cp'

    @property
    def description(self) -> str:
        return 'Копирует файл(ы): cp <source>... <dest>'

    def undo(self) -> list[UndoRecord]:
        return self._undo_records.copy()

    def _validate_args(self, args: list[str]) -> None:
        if len(args) < 2:
            raise ValidationError(
                'cp требует как минимум два аргумента: cp <source> <dest>'
            )

    def execute(self, args: list[str], flags: list[str], ctx: CommandContext) -> str:
        self._undo_records.clear()
        self._validate_args(args)
        *srcs, dst = args

        # Если несколько исходников — dst должен быть директорией!
        if len(srcs) > 1 and not self._fs.is_dir(dst):
            raise ValidationError(
                'Если копируется несколько файлов, последний аргумент должен быть директорией!'
            )

        for src in srcs:
            if not self._fs.is_file(src):
                raise ValidationError(f'Источник не найден или не файл: {src}')

            if self._fs.is_dir(dst):
                target = (
                    dst.rstrip('/') + '/' + self._fs.basename(src)
                    if dst != '/'
                    else '/' + self._fs.basename(src)
                )
            else:
                target = dst

            overwrite = self._fs.is_file(target)
            overwritten_path = None
            if overwrite:
                overwritten_path = self._fs.delete(target)

            self._fs.copy(src, target)
            rec = UndoRecord(
                action='cp',
                src=src,
                dst=target,
                overwrite=overwrite,
                overwritten_path=overwritten_path,
            )
            self._undo_records.append(rec)

        return f'Скопированы {" ".join(srcs)} -> {dst}'
