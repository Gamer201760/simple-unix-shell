from pathlib import Path

from entity.context import CommandContext
from entity.errors import ValidationError
from entity.undo import UndoRecord
from repository.command.path_utils import normalize


class Mkdir:
    def __init__(self) -> None:
        self._undo_records: list[UndoRecord] = []

    @property
    def name(self) -> str:
        return 'mkdir'

    @property
    def description(self) -> str:
        return 'Создаёт директорию: mkdir [-p] <path...>'

    def undo(self) -> list[UndoRecord]:
        return self._undo_records.copy()

    def _validate_args(self, args: list[str]) -> None:
        if len(args) < 1:
            raise ValidationError('mkdir требует как минимум один аргумент: mkdir -h')

    def _has_parents_flag(self, flags: list[str]) -> bool:
        return ('-p' in flags) or ('--parents' in flags)

    def _collect_missing_parents(self, path: Path) -> list[Path]:
        missing = []
        current = path

        while not current.exists():
            missing.append(current)
            parent = current.parent
            if parent == current:
                break
            current = parent

        return list(reversed(missing))

    def _record_undo(self, path: Path) -> None:
        self._undo_records.append(
            UndoRecord(
                action='cp',
                src=str(path),
                dst=str(path),
                overwrite=False,
                overwritten_path=None,
            )
        )

    def execute(self, args: list[str], flags: list[str], ctx: CommandContext) -> str:
        self._undo_records.clear()
        self._validate_args(args)

        allow_parents = self._has_parents_flag(flags)
        created_count = 0

        for arg in args:
            path = normalize(arg, ctx)

            if path.exists() and not path.is_dir():
                raise ValidationError(f'Путь уже существует и является файлом: {path}')

            if path.exists():
                if not allow_parents:
                    raise ValidationError(f'Директория уже существует: {path}')
                continue

            if not allow_parents and (
                not path.parent.exists() or not path.parent.is_dir()
            ):
                raise ValidationError(
                    f'Родительская директория не существует: {path.parent}'
                )

            missing = self._collect_missing_parents(path)

            path.mkdir(parents=allow_parents, exist_ok=False)

            for created_path in missing:
                self._record_undo(created_path)
                created_count += 1

        return f'mkdir: создано {created_count} директорий'
