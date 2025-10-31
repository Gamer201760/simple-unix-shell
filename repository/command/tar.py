import os
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

    def _is_recursive(self, flags: list[str]) -> bool:
        return ('-r' in flags) or ('-R' in flags) or ('--recursive' in flags)

    def _ensure_targz(self, path: Path) -> None:
        name = path.name.lower()
        if not (name.endswith('.tar.gz') or name.endswith('.tgz')):
            raise ValidationError('Поддерживаются только .tar.gz или .tgz')

    def execute(self, args: list[str], flags: list[str], ctx: CommandContext) -> str:
        self._validate_args(args)

        *srcs, archive_raw = args
        archive_path = normalize(archive_raw, ctx)
        self._ensure_targz(archive_path)

        parent = archive_path.parent
        if not (parent.exists() and parent.is_dir()):
            raise ValidationError(f'Целевая директория не существует: {parent}')

        if archive_path.exists() and archive_path.is_dir():
            raise ValidationError(
                f'Нельзя перезаписать директорию файлом: {archive_path}'
            )

        recursive = self._is_recursive(flags)
        added = 0

        with tarfile.open(str(archive_path), mode='w:gz') as tf:
            for raw in srcs:
                src = normalize(raw, ctx)
                if not src.exists():
                    raise ValidationError(f'Источник не найден: {raw}')
                if src.is_file():
                    tf.add(str(src), arcname=src.name)
                    added += 1
                    continue
                if not recursive:
                    raise ValidationError('Для архивации директории нужен флаг -r')
                for cur_root, _, files in os.walk(src):
                    cur_root_path = Path(cur_root)
                    rel = os.path.relpath(cur_root_path, src)
                    base = src.name if rel == '.' else f'{src.name}/{rel}'
                    if not files:
                        info = tarfile.TarInfo(name=base + '/')
                        info.type = tarfile.DIRTYPE
                        tf.addfile(info)
                    for fname in files:
                        full = cur_root_path / fname
                        tf.add(str(full), arcname=f'{base}/{fname}')
                        added += 1

        return f'tar: создан архив {archive_path} с {added} элементами'
