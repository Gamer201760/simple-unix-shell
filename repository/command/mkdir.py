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
            raise ValidationError(
                'mkdir требует как минимум один аргумент, см: mkdir -h'
            )

    def _with_parents(self, flags: list[str]) -> bool:
        return ('-p' in flags) or ('--parents' in flags)

    def _make_parents_if_needed(self, path: Path, allow_parents: bool) -> list[str]:
        created: list[str] = []
        parent = path.parent
        if parent.exists() and parent.is_dir():
            return created

        if not allow_parents:
            raise ValidationError(f'Родительская директория не существует: {parent}')

        chain: list[Path] = []
        cur = parent
        seen: set[Path] = set()
        while not (cur.exists() and cur.is_dir()):
            chain.append(cur)
            nxt = cur.parent
            if nxt == cur or cur in seen:
                break
            seen.add(cur)
            cur = nxt

        for d in reversed(chain):
            if not d.exists():
                d.mkdir()
                created.append(str(d))

        return created

    def _record_created_dirs(self, created: list[str]) -> None:
        for d in created:
            self._undo_records.append(
                UndoRecord(
                    action='cp',
                    src=d,
                    dst=d,
                    overwrite=False,
                    overwritten_path=None,
                )
            )

    def execute(self, args: list[str], flags: list[str], ctx: CommandContext) -> str:
        self._undo_records.clear()
        self._validate_args(args)

        allow_parents = self._with_parents(flags)
        total_created = 0

        for x in args:
            path = normalize(x, ctx)

            created_parents = self._make_parents_if_needed(path, allow_parents)
            self._record_created_dirs(created_parents)
            total_created += len(created_parents)

            if path.exists():
                if path.is_dir():
                    if not allow_parents:
                        raise ValidationError(f'Директория уже существует: {path}')
                    continue
                raise ValidationError(f'Путь уже существует и является файлом: {path}')

            path.mkdir()
            self._record_created_dirs([str(path)])
            total_created += 1

        return f'mkdir: создано {total_created} директорий'
