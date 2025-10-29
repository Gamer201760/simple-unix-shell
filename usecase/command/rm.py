from entity.context import CommandContext
from entity.errors import ValidationError
from entity.undo import UndoRecord
from usecase.interface import FileSystemRepository


class Rm:
    def __init__(self, fs: FileSystemRepository) -> None:
        self._fs = fs
        self._undo_records: list[UndoRecord] = []

    @property
    def name(self) -> str:
        return 'rm'

    @property
    def description(self) -> str:
        return 'Удаляет файлы и директории (директории только с -r): rm [-r] <path...>'

    def undo(self) -> list[UndoRecord]:
        return self._undo_records.copy()[::-1]

    def _validate_args(self, args: list[str]) -> None:
        if len(args) < 1:
            raise ValidationError('rm требует как минимум один аргумент, см: rm -h')

    def _is_recursive(self, flags: list[str]) -> bool:
        return ('-r' in flags) or ('-R' in flags) or ('--recursive' in flags)

    def _record_rm(self, path: str, backup: str) -> None:
        self._undo_records.append(
            UndoRecord(
                action='rm',
                src=path,
                dst=backup,
                overwrite=False,
                overwritten_path=None,
            )
        )

    def _rm_file(self, path: str) -> str:
        """Удаляет файл и возвращает путь в .trash"""
        backup = self._fs.delete(path)
        self._record_rm(path, backup)
        return backup

    def _rm_dir(self, path: str) -> None:
        """Удаляет директорию рекурсивно с записью undo на каждый объект"""
        dirs_to_remove: list[str] = []

        for cur_root, dirs, files in self._fs.walk(path):
            for fname in files:
                self._rm_file(self._fs.path_join(cur_root, fname))
            for dname in dirs:
                dirs_to_remove.append(self._fs.path_join(cur_root, dname))

        for d in sorted(dirs_to_remove, key=len, reverse=True):
            self._rm_file(d)

        self._rm_file(path)

    def execute(self, args: list[str], flags: list[str], ctx: CommandContext) -> str:
        self._undo_records.clear()
        self._validate_args(args)
        recursive = self._is_recursive(flags)

        for src in args:
            is_file = self._fs.is_file(src)
            is_dir = self._fs.is_dir(src)

            if not is_file and not is_dir:
                raise ValidationError(f'Путь не существует: {src}')

            if is_file:
                self._rm_file(src)
                continue

            if not recursive:
                raise ValidationError('Для удаления директории нужен флаг -r')

            self._rm_dir(src)

        return f'rm: удалено {len(self._undo_records)} объектов'
