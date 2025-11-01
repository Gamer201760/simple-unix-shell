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

    def _ensure_dir(self, path: Path) -> None:
        if path.exists() and not path.is_dir():
            raise ValidationError(f'Цель не директория: {path}')
        path.mkdir(parents=True, exist_ok=True)

    def _safe_path(self, root: Path, member: str) -> Path:
        # защита от path traversal атак
        target = (root / member).resolve(strict=False)
        if not target.is_relative_to(root.resolve(strict=False)):
            raise ValidationError(f'Небезопасный путь в архиве: {member}')
        return target

    def execute(self, args: list[str], flags: list[str], ctx: CommandContext) -> str:
        self._validate_args(args)

        archive_path = normalize(args[0], ctx)
        if not archive_path.is_file():
            raise ValidationError(f'Архив не найден: {args[0]}')

        # определение директории распаковки
        dest_root = normalize(args[1], ctx) if len(args) == 2 else Path(ctx.pwd)
        self._ensure_dir(dest_root)

        extracted_count = 0

        with zipfile.ZipFile(str(archive_path), mode='r') as zip_file:
            for info in zip_file.infolist():
                name = info.filename

                if name.endswith('/'):
                    self._safe_path(dest_root, name).mkdir(parents=True, exist_ok=True)
                    continue

                # проверка path traversal
                target_file = self._safe_path(dest_root, name)
                target_file.parent.mkdir(parents=True, exist_ok=True)

                if target_file.exists() and target_file.is_dir():
                    raise ValidationError(
                        f'Конфликт типов: в цели директория а распаковывается файл: {target_file}'
                    )

                with zip_file.open(info, 'r') as src, open(target_file, 'wb') as dst:
                    shutil.copyfileobj(src, dst)

                extracted_count += 1

        return f'unzip: распаковано {extracted_count} файлов в {dest_root}'
