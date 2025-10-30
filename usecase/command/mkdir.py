from entity.context import CommandContext
from entity.errors import ValidationError
from entity.undo import UndoRecord
from usecase.interface import FileSystemRepository


class Mkdir:
    def __init__(self, fs: FileSystemRepository) -> None:
        self._fs = fs
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

    def _make_parents_if_needed(self, path: str, allow_parents: bool) -> list[str]:
        created: list[str] = []
        parent = self._fs.path_dirname(path) or '/'

        if self._fs.is_dir(parent):
            return created

        if not allow_parents:
            raise ValidationError(f'Родительская директория не существует: {parent}')

        # Собираем директории до существующей
        chain: list[str] = []
        cur = parent
        seen: set[str] = set()
        while not self._fs.is_dir(cur):
            chain.append(cur)
            nxt = self._fs.path_dirname(cur) or '/'
            if nxt == cur or cur in seen:
                break
            seen.add(cur)
            cur = nxt

        for d in reversed(chain):
            if not self._fs.is_dir(d):
                self._fs.mkdir(d)
                created.append(d)

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

        for path in args:
            # Создаём родителей при -p
            created_parents = self._make_parents_if_needed(path, allow_parents)
            self._record_created_dirs(created_parents)
            total_created += len(created_parents)

            if self._fs.is_dir(path):
                # mkdir -p не должен падать, без -p - ошибка
                if not allow_parents:
                    raise ValidationError(f'Директория уже существует: {path}')
                # -p и уже существует -> ничего не делаем и не пишем undo
                continue

            # Создаём саму директорию
            self._fs.mkdir(path)
            self._record_created_dirs([path])
            total_created += 1

        return f'mkdir: создано {total_created} директорий'
