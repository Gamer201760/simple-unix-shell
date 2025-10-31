import os
import shutil
import tempfile
from pathlib import Path

from entity.context import CommandContext
from entity.errors import ValidationError
from entity.undo import UndoRecord


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
                'mv требует как минимум два аргумента: mv <source> <dest>'
            )

    def _normalize(self, raw: str, ctx: CommandContext) -> Path:
        expanded = os.path.expanduser(raw)
        p = Path(expanded)
        if not p.is_absolute():
            p = Path(ctx.pwd) / p
        return p.resolve(strict=False)

    def _backup_existing_file(self, path: Path) -> str:
        tmp_dir = Path(tempfile.mkdtemp(prefix='.mv_undo_'))
        backup_path = tmp_dir / path.name
        shutil.copy2(str(path), str(backup_path))
        path.unlink()
        return str(backup_path)

    def execute(self, args: list[str], flags: list[str], ctx: CommandContext) -> str:
        self._undo_records.clear()
        self._validate_args(args)

        *srcs, dst = args
        dst_path = self._normalize(dst, ctx)

        for x in srcs:
            src_path = self._normalize(x, ctx)
            if not (src_path.is_file() or src_path.is_dir()):
                raise ValidationError(f'Источник не найден: {src_path}')

            overwrite = False
            backup: str | None = None

            if not dst_path.is_dir():
                if dst_path.is_file():
                    overwrite = True
                    backup = self._backup_existing_file(dst_path)
                final_dst = shutil.move(str(src_path), str(dst_path))
            else:
                final_dst = shutil.move(str(src_path), str(dst_path))

            record = UndoRecord(
                action='mv',
                src=str(src_path),
                dst=str(final_dst),
                overwrite=overwrite,
                overwritten_path=backup,
            )
            self._undo_records.append(record)

        return f'Перемещены {" ".join(srcs)} -> {dst}'
