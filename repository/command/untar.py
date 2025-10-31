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
            raise ValidationError(
                'untar.gz принимает 1 или 2 аргумента: untar.gz <archive.tar.gz|.tgz> [dest_dir]'
            )

    def _ensure_targz(self, path: Path) -> None:
        name = path.name.lower()
        if not (name.endswith('.tar.gz') or name.endswith('.tgz')):
            raise ValidationError('Поддерживаются только .tar.gz или .tgz')

    def _ensure_dir(self, d: Path) -> None:
        if d.exists() and not d.is_dir():
            raise ValidationError(f'Цель не директория: {d}')
        d.mkdir(parents=True, exist_ok=True)

    def _safe_join(self, root: Path, member_name: str) -> Path:
        root_res = root.resolve(strict=False)
        target = (root_res / member_name).resolve(strict=False)
        if not target.is_relative_to(root_res):
            raise ValidationError(f'Небезопасный путь в архиве: {member_name}')
        return target

    def execute(self, args: list[str], flags: list[str], ctx: CommandContext) -> str:
        self._validate_args(args)

        archive_path = normalize(args[0], ctx)
        self._ensure_targz(archive_path)

        if not (archive_path.exists() and archive_path.is_file()):
            raise ValidationError(f'Архив не найден: {args[0]}')

        dest_root = normalize(args[1], ctx) if len(args) == 2 else Path(ctx.pwd)
        self._ensure_dir(dest_root)

        extracted_files = 0

        with tarfile.open(str(archive_path), mode='r:gz') as tf:
            for member in tf.getmembers():
                name = member.name
                if (
                    member.issym()
                    or member.islnk()
                    or member.ischr()
                    or member.isblk()
                    or member.isfifo()
                    or member.isdev()
                ):
                    raise ValidationError(
                        f'Неподдерживаемый или небезопасный тип записи: {name}'
                    )

                target_path = self._safe_join(dest_root, name)

                if member.isdir():
                    target_path.mkdir(parents=True, exist_ok=True)
                    continue

                target_path.parent.mkdir(parents=True, exist_ok=True)
                if target_path.exists() and target_path.is_dir():
                    raise ValidationError(
                        f'Конфликт типов: в цели директория, а распаковывается файл: {target_path}'
                    )

                src_f = tf.extractfile(member)
                if src_f is None:
                    open(target_path, 'wb').close()
                else:
                    with src_f, open(target_path, 'wb') as dst:
                        shutil.copyfileobj(src_f, dst)
                extracted_files += 1

        return (
            f'untar.gz: распаковано {extracted_files} файлов в {dest_root}'  # [web:167]
        )
