import shutil
import tempfile
from pathlib import Path

from entity.context import CommandContext
from entity.errors import ValidationError
from entity.undo import UndoRecord
from repository.command.path_utils import normalize


class Mv:
    def __init__(self) -> None:
        self._undo_records: list[UndoRecord] = []

    @property
    def name(self) -> str:
        return 'mv'

    @property
    def description(self) -> str:
        return 'Перемещает файл или директорию, mv <source> <dest>'

    def undo(self) -> list[UndoRecord]:
        return self._undo_records.copy()

    def _validate_args(self, args: list[str]) -> None:
        if len(args) < 2:
            raise ValidationError(
                'mv требует как минимум два аргумента: mv <source...> <dest>'
            )

    def _backup_existing_file(self, path: Path) -> str:
        tmp_dir = Path(tempfile.mkdtemp(prefix='.mv_undo_'))
        backup_path = tmp_dir / path.name
        shutil.copy2(str(path), str(backup_path))
        path.unlink()
        return str(backup_path)

    def _ensure_parent(self, target: Path) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)

    def _move_into_dir(self, src: Path, dst_dir: Path) -> str:
        if src.is_dir() and dst_dir.is_relative_to(src):
            raise ValidationError('Нельзя переместить директорию внутрь самой себя')
        return shutil.move(str(src), str(dst_dir))

    def _rename_file(
        self, src_file: Path, dst_path: Path
    ) -> tuple[str, bool, str | None]:
        self._ensure_parent(dst_path)
        overwrite, backup = False, None
        if dst_path.is_file():
            overwrite = True
            backup = self._backup_existing_file(dst_path)
        elif dst_path.exists() and dst_path.is_dir():
            raise ValidationError('Цель является директорией')
        final = shutil.move(str(src_file), str(dst_path))
        return final, overwrite, backup

    def _rename_dir(self, src_dir: Path, dst_path: Path) -> str:
        if dst_path.exists() and dst_path.is_file():
            raise ValidationError('Нельзя перезаписать файл директорией')
        if dst_path.is_relative_to(src_dir):
            raise ValidationError('Нельзя переместить директорию внутрь самой себя')
        self._ensure_parent(dst_path)
        return shutil.move(str(src_dir), str(dst_path))

    def _move_single(
        self, src_path: Path, dst_path: Path, multi: bool
    ) -> tuple[str, bool, str | None]:
        if src_path.is_dir():
            if dst_path.is_dir() or multi:
                final = self._move_into_dir(src_path, dst_path)
                return final, False, None
            if not dst_path.exists():
                parent = dst_path.parent
                if not parent.exists() or not parent.is_dir():
                    raise ValidationError('Родительская директория цели не существует')
                final = self._rename_dir(src_path, dst_path)
                return final, False, None
            if dst_path.is_dir():
                final = self._move_into_dir(src_path, dst_path)
                return final, False, None
            raise ValidationError('Нельзя перезаписать файл директорией')
        else:
            if dst_path.is_dir() or multi:
                final = self._move_into_dir(src_path, dst_path)
                return final, False, None
            parent = dst_path.parent
            if not parent.exists() or not parent.is_dir():
                raise ValidationError('Родительская директория цели не существует')
            return self._rename_file(src_path, dst_path)

    def execute(self, args: list[str], flags: list[str], ctx: CommandContext) -> str:
        self._undo_records.clear()
        self._validate_args(args)

        *srcs, dst = args
        dst_path = normalize(dst, ctx)

        if len(srcs) > 1 and not dst_path.is_dir():
            raise ValidationError(
                'Если перемещается несколько объектов, цель должна быть существующей директорией'
            )

        multi = len(srcs) > 1
        for x in srcs:
            src_path = normalize(x, ctx)
            if not (src_path.is_file() or src_path.is_dir()):
                raise ValidationError(f'Источник не найден: {src_path}')

            final_dst, overwrite, backup = self._move_single(src_path, dst_path, multi)
            self._undo_records.append(
                UndoRecord(
                    action='mv',
                    src=str(src_path),
                    dst=str(final_dst),
                    overwrite=overwrite,
                    overwritten_path=backup,
                )
            )

        return f'Перемещены {" ".join(srcs)} -> {dst}'
