import os
import shutil
import tempfile
from pathlib import Path

from entity.context import CommandContext
from entity.errors import ValidationError
from entity.undo import UndoRecord


class Cp:
    def __init__(self) -> None:
        self._undo_records: list[UndoRecord] = []

    @property
    def name(self) -> str:
        return 'cp'

    @property
    def description(self) -> str:
        return 'Копирует файлы и директории (директории только с -r): cp [-r] <source...> <dest>'

    def undo(self) -> list[UndoRecord]:
        return self._undo_records.copy()

    def _validate_args(self, args: list[str]) -> None:
        if len(args) < 2:
            raise ValidationError(
                'cp требует как минимум два аргумента: cp <source> <dest>'
            )

    def _normalize(self, raw: str, ctx: CommandContext) -> Path:
        expanded = os.path.expanduser(raw)
        p = Path(expanded)
        if not p.is_absolute():
            p = Path(ctx.pwd) / p
        return p.resolve(strict=False)

    def _ensure_parent_dir_exists(self, path: Path) -> None:
        parent = path.parent
        if not (parent.exists() and parent.is_dir()):
            raise ValidationError(f'Целевая директория не существует: {parent}')

    def _record_cp(self, src: Path, dst: Path, backup: str | None) -> None:
        self._undo_records.append(
            UndoRecord(
                action='cp',
                src=str(src),
                dst=str(dst),
                overwrite=backup is not None,
                overwritten_path=backup,
            )
        )

    def _backup_existing_file(self, path: Path) -> str:
        tmp_dir = Path(tempfile.mkdtemp(prefix='.cp_undo_'))
        backup_path = tmp_dir / path.name
        shutil.copy2(str(path), str(backup_path))
        path.unlink()
        return str(backup_path)

    def _copy_file_with_undo(self, src_file: Path, dst_file: Path) -> None:
        self._ensure_parent_dir_exists(dst_file)

        backup: str | None = None
        if dst_file.is_file():
            backup = self._backup_existing_file(dst_file)

        if dst_file.exists() and dst_file.is_dir():
            raise ValidationError(f'Нельзя перезаписать директорию файлом: {dst_file}')

        shutil.copy2(str(src_file), str(dst_file))
        self._record_cp(src_file, dst_file, backup)

    def _mkdir_if_not_exists(self, path: Path) -> None:
        path.mkdir(parents=True, exist_ok=True)

    def _is_recursive(self, flags: list[str]) -> bool:
        return ('-r' in flags) or ('-R' in flags) or ('--recursive' in flags)

    def _is_dir_content_path(self, path: str) -> tuple[bool, str]:
        if Path(path).name == '*':
            base_dir = str(Path(path).parent)
            return True, base_dir if base_dir else path
        return False, path

    def _copy_dir_recursive(self, src_dir: Path, dst: Path, place_inside: bool) -> None:
        """
        Если place_inside=True: корнем назначения будет dst / basename(src_dir).
        Если place_inside=False: корнем назначения будет dst (слияние содержимого src_dir в dst).
        """
        root_dst = (dst / src_dir.name) if place_inside else dst
        self._mkdir_if_not_exists(root_dst)

        for cur_root, dirs, files in os.walk(src_dir):
            cur_root_path = Path(cur_root)
            rel = os.path.relpath(cur_root_path, src_dir)
            target_dir = root_dst if rel == '.' else root_dst / rel
            self._mkdir_if_not_exists(target_dir)

            for d in dirs:
                self._mkdir_if_not_exists(target_dir / d)

            for fname in files:
                s = cur_root_path / fname
                d = target_dir / fname
                if d.exists() and d.is_dir():
                    raise ValidationError(
                        f'Конфликт типов: в цели директория, а копируется файл: {d}'
                    )
                backup: str | None = None
                if d.is_file():
                    backup = self._backup_existing_file(d)
                shutil.copy2(str(s), str(d))
                self._record_cp(s, d, backup)

    def execute(self, args: list[str], flags: list[str], ctx: CommandContext) -> str:
        self._undo_records.clear()
        self._validate_args(args)
        *srcs, dst = args
        dst_path = self._normalize(dst, ctx)

        if len(srcs) > 1 and not dst_path.is_dir():
            raise ValidationError(
                'Если копируется несколько объектов, последний аргумент должен быть существующей директорией'
            )

        recursive = self._is_recursive(flags)

        for x in srcs:
            content_mode, src_base = self._is_dir_content_path(x)
            src_path = self._normalize(src_base, ctx)

            is_src_file = src_path.is_file()
            is_src_dir = src_path.is_dir()
            if not is_src_file and not is_src_dir:
                raise ValidationError(f'Источник не найден: {x}')

            if is_src_file:
                target = (
                    (dst_path / src_path.name)
                    if (len(srcs) > 1 or dst_path.is_dir())
                    else dst_path
                )
                self._copy_file_with_undo(src_path, target)
                continue

            if not recursive:
                raise ValidationError('Для копирования директории нужен флаг -r')

            if len(srcs) == 1 and dst_path.is_file():
                raise ValidationError('Нельзя перезаписать файл директорией')

            if not dst_path.is_dir():
                if len(srcs) > 1:
                    raise ValidationError(
                        'Целевая директория должна существовать при копировании нескольких источников'
                    )
                self._mkdir_if_not_exists(dst_path)
                self._copy_dir_recursive(src_path, dst_path, place_inside=False)
            else:
                self._copy_dir_recursive(
                    src_path, dst_path, place_inside=not content_mode
                )

        return f'cp: скопировано {len(self._undo_records)} объектов'
