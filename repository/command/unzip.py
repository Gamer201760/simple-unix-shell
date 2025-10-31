import shutil
import zipfile
from pathlib import Path

from entity.context import CommandContext
from entity.errors import ValidationError
from repository.command.path_utils import normalize


class Unzip:
    @property
    def name(self) -> str:
        return 'unzip'

    @property
    def description(self) -> str:
        return 'Распаковывает архив: unzip <archive.zip> [dest_dir]'

    def _validate_args(self, args: list[str]) -> None:
        if len(args) < 1 or len(args) > 2:
            raise ValidationError('unzip принимает 1 или 2 аргумента: unzip -h')

    def _mkdir_if_not_exist(self, d: Path) -> None:
        if d.exists() and not d.is_dir():
            raise ValidationError(f'Цель не директория: {d}')
        d.mkdir(parents=True, exist_ok=True)

    def _safe_join(self, root: Path, member: str) -> Path:
        target = (root / member).resolve(strict=False)
        if not target.is_relative_to(root.resolve(strict=False)):
            raise ValidationError(f'Небезопасный путь в архиве: {member}')
        return target

    def execute(self, args: list[str], flags: list[str], ctx: CommandContext) -> str:
        self._validate_args(args)

        archive_path = normalize(args[0], ctx)
        if not (archive_path.exists() and archive_path.is_file()):
            raise ValidationError(f'Архив не найден: {args[0]}')

        dest_root = normalize(args[1], ctx) if len(args) == 2 else Path(ctx.pwd)
        self._mkdir_if_not_exist(dest_root)

        extracted = 0
        with zipfile.ZipFile(str(archive_path), mode='r') as zf:
            for info in zf.infolist():
                name = info.filename
                if name.endswith('/'):
                    self._safe_join(dest_root, name).mkdir(parents=True, exist_ok=True)
                    continue

                target_file = self._safe_join(dest_root, name)
                target_file.parent.mkdir(parents=True, exist_ok=True)

                if target_file.exists() and target_file.is_dir():
                    raise ValidationError(
                        f'Конфликт типов: в цели директория, а распаковывается файл: {target_file}'
                    )

                with zf.open(info, 'r') as src, open(target_file, 'wb') as dst:
                    shutil.copyfileobj(src, dst)
                extracted += 1

        return f'unzip: распаковано {extracted} файлов в {dest_root}'
