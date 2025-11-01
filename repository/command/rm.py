import shutil
import uuid
from pathlib import Path

from entity.context import CommandContext
from entity.errors import ValidationError
from entity.undo import UndoRecord
from repository.command.path_utils import normalize


class Rm:
    def __init__(self, trash_dir: Path | str) -> None:
        self._undo_records: list[UndoRecord] = []
        self._trash_dir = Path(trash_dir)

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
            raise ValidationError('rm требует как минимум один аргумент: rm -h')

    def _check_protection(self, target: Path, ctx: CommandContext) -> None:
        # запрет удаления корня
        root = Path(target.anchor or '/').resolve(strict=False)
        if target.resolve(strict=False) == root:
            raise ValidationError(f'Нельзя удалять корневой каталог: {target}')

        # запрет удаления родителя текущей директории
        cwd_parent = Path(ctx.pwd).resolve(strict=False).parent
        if target.resolve(strict=False) == cwd_parent:
            raise ValidationError(
                f'Нельзя удалять родительский каталог текущего: {target}'
            )

    def _is_recursive(self, flags: list[str]) -> bool:
        return ('-r' in flags) or ('-R' in flags) or ('--recursive' in flags)

    def _ensure_trash(self) -> None:
        self._trash_dir.mkdir(parents=True, exist_ok=True)

    def _move_to_trash(self, path: Path) -> Path:
        # уникальное имя в trash
        suffix = f'.{uuid.uuid4().hex}'
        target = self._trash_dir / f'{path.name}{suffix}'
        final = shutil.move(str(path), str(target))
        return Path(final)

    def _record_undo(self, original: Path, backup: Path) -> None:
        self._undo_records.append(
            UndoRecord(
                action='rm',
                src=str(original),
                dst=str(backup),
                overwrite=False,
                overwritten_path=None,
            )
        )

    def _remove(self, path: Path) -> None:
        # перемещение в trash вместо удаления
        backup = self._move_to_trash(path)
        self._record_undo(path, backup)

    def _confirm(self, path: Path) -> bool:
        ans = input(f'Удалить {path}? [y/N]: ').strip().lower()
        return ans in ('y', 'yes', 'д', 'да')

    def execute(self, args: list[str], flags: list[str], ctx: CommandContext) -> str:
        self._undo_records.clear()
        self._validate_args(args)

        recursive = self._is_recursive(flags)
        skip_confirm = '-y' in flags
        self._ensure_trash()

        for arg in args:
            src = normalize(arg, ctx)
            self._check_protection(src, ctx)

            if not src.exists():
                raise ValidationError(f'Путь не существует: {src}')

            # проверка флага -r для директорий
            if src.is_dir() and not recursive:
                raise ValidationError('Для удаления директории нужен флаг -r')

            # подтверждение перед удалением
            if not skip_confirm and not self._confirm(src):
                continue

            # удаление файла или директории целиком
            self._remove(src)

        return f'rm: удалено {len(self._undo_records)} объектов'
