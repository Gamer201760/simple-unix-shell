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
        return 'Перемещает файл или директорию, mv <source...> <dest>'

    def undo(self) -> list[UndoRecord]:
        return self._undo_records.copy()

    def _validate_args(self, args: list[str]) -> None:
        if len(args) < 2:
            raise ValidationError('mv требует как минимум два аргумента: mv -h')

    def _create_backup(self, path: Path, is_dir: bool) -> str:
        # создание временной директории для backup
        prefix = '.mv_dir_undo_' if is_dir else '.mv_undo_'
        tmp_dir = Path(tempfile.mkdtemp(prefix=prefix))

        if is_dir:
            # перемещение директории целиком
            backup_path = tmp_dir / path.name
            shutil.move(str(path), str(backup_path))
            return str(backup_path)
        else:
            # копирование файла с метаданными
            backup_path = tmp_dir / path.name
            shutil.copy2(str(path), str(backup_path))
            path.unlink()
            return str(backup_path)

    def _ensure_parent_exists(self, target: Path) -> None:
        # создание родительских директорий если нужно
        target.parent.mkdir(parents=True, exist_ok=True)

    def _check_recursive_move(self, src: Path, dst: Path) -> None:
        # проверка что не перемещаем директорию в саму себя
        if src.is_dir() and dst.is_relative_to(src):
            raise ValidationError('Нельзя переместить директорию внутрь самой себя')

    def _move_file(self, src: Path, dst: Path) -> tuple[str, bool, str | None]:
        self._ensure_parent_exists(dst)

        backup = None
        overwrite = False

        if dst.exists():
            if dst.is_dir():
                raise ValidationError('Цель является директорией')
            # backup существующего файла
            overwrite = True
            backup = self._create_backup(dst, is_dir=False)

        final = shutil.move(str(src), str(dst))
        return final, overwrite, backup

    def _move_dir(self, src: Path, dst: Path) -> tuple[str, bool, str | None]:
        # перемещение директории с обработкой перезаписи
        self._ensure_parent_exists(dst)
        self._check_recursive_move(src, dst)

        backup = None
        overwrite = False

        if dst.exists():
            if dst.is_file():
                raise ValidationError('Нельзя перезаписать файл директорией')
            # backup существующей директории
            overwrite = True
            backup = self._create_backup(dst, is_dir=True)

        final = shutil.move(str(src), str(dst))
        return final, overwrite, backup

    def _move_single(
        self, src: Path, dst: Path, multi: bool
    ) -> tuple[str, bool, str | None]:
        if dst.is_dir() or multi:
            # перемещение внутрь директории
            target = dst / src.name
        else:
            # переименование или перемещение в новый путь
            if not dst.parent.exists() or not dst.parent.is_dir():
                raise ValidationError('Родительская директория цели не существует')
            target = dst

        if not src.exists():
            raise ValidationError(f'Источник не найден: {src}')

        if src.is_dir():
            return self._move_dir(src, target)
        else:
            return self._move_file(src, target)

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

        for src_arg in srcs:
            src_path = normalize(src_arg, ctx)

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
