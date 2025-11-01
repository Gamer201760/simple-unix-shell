import tarfile
from pathlib import Path

from entity.context import CommandContext
from entity.errors import ValidationError
from repository.command.path_utils import normalize


class Tar:
    @property
    def name(self) -> str:
        return 'tar'

    @property
    def description(self) -> str:
        return 'Архивирует в .tar.gz: tar [-r] <source...> <archive.tar.gz|.tgz>'

    def _validate_args(self, args: list[str]) -> None:
        if len(args) < 2:
            raise ValidationError('tar требует минимум два аргумента: tar -h')

    def _has_recursive(self, flags: list[str]) -> bool:
        return ('-r' in flags) or ('-R' in flags) or ('--recursive' in flags)

    def _check_extension(self, path: Path) -> None:
        # только tar.gz и tgz форматы
        name = path.name.lower()
        if not (name.endswith('.tar.gz') or name.endswith('.tgz')):
            raise ValidationError('Поддерживаются только .tar.gz или .tgz')

    def execute(self, args: list[str], flags: list[str], ctx: CommandContext) -> str:
        self._validate_args(args)

        *srcs, archive_raw = args
        archive_path = normalize(archive_raw, ctx)
        self._check_extension(archive_path)

        # проверка родительской директории
        if not archive_path.parent.exists() or not archive_path.parent.is_dir():
            raise ValidationError(
                f'Родительская директория не существует: {archive_path.parent}'
            )

        if archive_path.exists() and archive_path.is_dir():
            raise ValidationError(
                f'Нельзя перезаписать директорию файлом: {archive_path}'
            )

        recursive = self._has_recursive(flags)
        added_count = 0

        with tarfile.open(str(archive_path), mode='w:gz') as tar:
            for src_arg in srcs:
                src = normalize(src_arg, ctx)

                if not src.exists():
                    raise ValidationError(f'Источник не найден: {src_arg}')

                if src.is_dir() and not recursive:
                    raise ValidationError('Для архивации директории нужен флаг -r')

                tar.add(str(src), arcname=src.name, recursive=recursive)

                # подсчёт добавленных элементов
                if src.is_file():
                    added_count += 1
                else:
                    # для директорий считаем все файлы внутри
                    added_count += sum(1 for _ in src.rglob('*') if _.is_file())

        return f'tar: создан архив {archive_path} с {added_count} файлами'
