import shutil
import tarfile
from pathlib import Path

from entity.context import CommandContext
from entity.errors import ValidationError
from repository.command.path_utils import normalize


class Untar:
    @property
    def name(self) -> str:
        return 'untar'

    @property
    def description(self) -> str:
        return 'Распаковывает .tar.gz/.tgz: untar <archive.tar.gz|.tgz> [dest_dir]'

    def _validate_args(self, args: list[str]) -> None:
        if len(args) < 1 or len(args) > 2:
            raise ValidationError('untar принимает 1 или 2 аргумента: untar -h')

    def _check_extension(self, path: Path) -> None:
        # только tar.gz и tgz форматы
        name = path.name.lower()
        if not (name.endswith('.tar.gz') or name.endswith('.tgz')):
            raise ValidationError('Поддерживаются только .tar.gz или .tgz')

    def _ensure_dir(self, path: Path) -> None:
        if path.exists() and not path.is_dir():
            raise ValidationError(f'Цель не директория: {path}')
        path.mkdir(parents=True, exist_ok=True)

    def _safe_path(self, root: Path, member_name: str) -> Path:
        # защита от path traversal атак
        root_resolved = root.resolve(strict=False)
        target = (root_resolved / member_name).resolve(strict=False)

        if not target.is_relative_to(root_resolved):
            raise ValidationError(f'Небезопасный путь в архиве: {member_name}')

        return target

    def _is_unsafe_member(self, member: tarfile.TarInfo) -> bool:
        # блокировка опасных типов файлов
        return (
            member.issym()
            or member.islnk()
            or member.ischr()
            or member.isblk()
            or member.isfifo()
            or member.isdev()
        )

    def execute(self, args: list[str], flags: list[str], ctx: CommandContext) -> str:
        self._validate_args(args)

        archive_path = normalize(args[0], ctx)
        self._check_extension(archive_path)

        if not archive_path.is_file():
            raise ValidationError(f'Архив не найден: {args[0]}')

        # определение директории распаковки
        dest_root = normalize(args[1], ctx) if len(args) == 2 else Path(ctx.pwd)
        self._ensure_dir(dest_root)

        extracted_count = 0

        with tarfile.open(str(archive_path), mode='r:gz') as tar:
            for member in tar.getmembers():
                # проверка безопасности типа файла
                if self._is_unsafe_member(member):
                    raise ValidationError(
                        f'Неподдерживаемый или небезопасный тип записи: {member.name}'
                    )

                # проверка path traversal
                target_path = self._safe_path(dest_root, member.name)

                if member.isdir():
                    target_path.mkdir(parents=True, exist_ok=True)
                    continue

                # проверка конфликта типов
                target_path.parent.mkdir(parents=True, exist_ok=True)
                if target_path.exists() and target_path.is_dir():
                    raise ValidationError(
                        f'Конфликт типов: в цели директория а распаковывается файл: {target_path}'
                    )

                # извлечение файла
                file_obj = tar.extractfile(member)
                if file_obj is None:
                    # пустой файл
                    open(target_path, 'wb').close()
                else:
                    with file_obj, open(target_path, 'wb') as dst:
                        shutil.copyfileobj(file_obj, dst)

                extracted_count += 1

        return f'untar: распаковано {extracted_count} файлов в {dest_root}'
