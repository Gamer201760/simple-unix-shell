import os
import zipfile
from pathlib import Path

from entity.context import CommandContext
from entity.errors import ValidationError
from repository.command.path_utils import normalize


class Zip:
    @property
    def name(self) -> str:
        return 'zip'

    @property
    def description(self) -> str:
        return 'Архивирует файлы и директории (директории только с -r): zip [-r] <source...> <archive.zip>'

    def _validate_args(self, args: list[str]) -> None:
        if len(args) < 2:
            raise ValidationError('zip требует минимум два аргумента: zip -h')

    def _is_recursive(self, flags: list[str]) -> bool:
        return ('-r' in flags) or ('-R' in flags) or ('--recursive' in flags)

    def execute(self, args: list[str], flags: list[str], ctx: CommandContext) -> str:
        self._validate_args(args)

        *srcs, archive_raw = args
        archive_path = normalize(archive_raw, ctx)

        parent = archive_path.parent
        if not (parent.exists() and parent.is_dir()):
            raise ValidationError(f'Целевая директория не существует: {parent}')
        if archive_path.exists() and archive_path.is_dir():
            raise ValidationError(
                f'Нельзя перезаписать директорию файлом: {archive_path}'
            )

        recursive = self._is_recursive(flags)
        added = 0

        with zipfile.ZipFile(
            str(archive_path), mode='w', compression=zipfile.ZIP_DEFLATED
        ) as zf:
            for raw in srcs:
                src = normalize(raw, ctx)
                if not src.exists():
                    raise ValidationError(f'Источник не найден: {raw}')
                if src.is_file():
                    zf.write(str(src), arcname=src.name)
                    added += 1
                    continue
                if not recursive:
                    raise ValidationError('Для архивации директории нужен флаг -r')
                # Включаем корневую директорию src.name
                for cur_root, _, files in os.walk(src):
                    cur_root_path = Path(cur_root)
                    rel = os.path.relpath(cur_root_path, src)
                    base = src.name if rel == '.' else f'{src.name}/{rel}'
                    for fname in files:
                        full = cur_root_path / fname
                        zf.write(str(full), arcname=f'{base}/{fname}')
                        added += 1

        return f'zip: создан архив {archive_path} с {added} элементами'
