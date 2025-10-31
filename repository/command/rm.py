import os
import shutil
import uuid
from pathlib import Path

from entity.context import CommandContext
from entity.errors import ValidationError
from entity.undo import UndoRecord
from repository.command.path_utils import normalize


class Rm:
    def __init__(self, trash_dir: str) -> None:
        self._undo_records: list[UndoRecord] = []
        self._trash_dir = trash_dir

    @property
    def name(self) -> str:
        return 'rm'

    @property
    def description(self) -> str:
        return 'Удаляет файлы и директории (директории только с -r): rm [-r] [-y] <path...>'

    def undo(self) -> list[UndoRecord]:
        return self._undo_records.copy()[::-1]

    def _validate_args(self, args: list[str]) -> None:
        if len(args) < 1:
            raise ValidationError('rm требует как минимум один аргумент, см: rm -h')

    def _is_recursive(self, flags: list[str]) -> bool:
        return ('-r' in flags) or ('-R' in flags) or ('--recursive' in flags)

    def _ensure_trash(self, ctx: CommandContext) -> Path:
        trash = Path(self._trash_dir)
        trash.mkdir(parents=True, exist_ok=True)
        return trash

    def _record_rm(self, path: Path, backup: Path) -> None:
        self._undo_records.append(
            UndoRecord(
                action='rm',
                src=str(path),
                dst=str(backup),
                overwrite=False,
                overwritten_path=None,
            )
        )

    def _delete_to_trash(self, path: Path, trash_root: Path) -> Path:
        # Делает уникальное имя в .trash и перемещает туда объект
        suffix = f'.{uuid.uuid4().hex}'
        target = trash_root / f'{path.name}{suffix}'
        final = shutil.move(str(path), str(target))
        return Path(final)

    def _rm_file(self, path: Path, trash_root: Path) -> Path:
        backup = self._delete_to_trash(path, trash_root)
        self._record_rm(path, backup)
        return backup

    def _rm_dir(self, path: Path, trash_root: Path) -> None:
        dirs_to_remove: list[Path] = []
        for cur_root, dirs, files in os.walk(path):
            cur_root_path = Path(cur_root)
            for fname in files:
                self._rm_file(cur_root_path / fname, trash_root)
            for dname in dirs:
                dirs_to_remove.append(cur_root_path / dname)

        for d in sorted(dirs_to_remove, key=lambda p: len(str(p)), reverse=True):
            self._rm_file(d, trash_root)

        self._rm_file(path, trash_root)

    def _confirm(self, src: Path) -> bool:
        ans = input(f'Удалить {src}? [y/N]: ').strip().lower()
        return ans in ('y', 'yes', 'д', 'да')

    def execute(self, args: list[str], flags: list[str], ctx: CommandContext) -> str:
        self._undo_records.clear()
        self._validate_args(args)

        recursive = self._is_recursive(flags)
        yes = '-y' in flags
        trash_root = self._ensure_trash(ctx)

        for x in args:
            src = normalize(x, ctx)
            is_file = src.is_file()
            is_dir = src.is_dir()

            if not is_file and not is_dir:
                raise ValidationError(f'Путь не существует: {src}')

            if is_dir and not recursive:
                raise ValidationError('Для удаления директории нужен флаг -r')

            if not (yes or self._confirm(src)):
                continue

            if is_file:
                self._rm_file(src, trash_root)
            else:
                self._rm_dir(src, trash_root)

        return f'rm: удалено {len(self._undo_records)} объектов'
