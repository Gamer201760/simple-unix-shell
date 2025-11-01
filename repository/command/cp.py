import os
import shutil
import tempfile
from pathlib import Path

from entity.context import CommandContext
from entity.errors import ValidationError
from entity.undo import UndoRecord
from repository.command.path_utils import normalize


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
            raise ValidationError('cp требует как минимум два аргумента: cp -h')

    def _create_backup(self, path: Path) -> str:
        # создание временной папки для backup файла
        tmp_dir = Path(tempfile.mkdtemp(prefix='.cp_undo_'))
        backup_path = tmp_dir / path.name
        shutil.copy2(str(path), str(backup_path))
        path.unlink()
        return str(backup_path)

    def _record_undo(self, src: Path, dst: Path, backup: str | None) -> None:
        self._undo_records.append(
            UndoRecord(
                action='cp',
                src=str(src),
                dst=str(dst),
                overwrite=backup is not None,
                overwritten_path=backup,
            )
        )

    def _copy_file(self, src: Path, dst: Path) -> None:
        # проверка родительской директории
        if not dst.parent.exists() or not dst.parent.is_dir():
            raise ValidationError(
                f'Родительская директория не существует: {dst.parent}'
            )

        if dst.exists() and dst.is_dir():
            raise ValidationError(f'Нельзя перезаписать директорию файлом: {dst}')

        # backup если цель существует
        backup = None
        if dst.is_file():
            backup = self._create_backup(dst)

        shutil.copy2(str(src), str(dst))
        self._record_undo(src, dst, backup)

    def _is_recursive(self, flags: list[str]) -> bool:
        return ('-r' in flags) or ('-R' in flags) or ('--recursive' in flags)

    def _copy_dir(self, src: Path, dst: Path, merge_content: bool) -> None:
        # определение корневой директории назначения
        root_dst = dst if merge_content else (dst / src.name)
        root_dst.mkdir(parents=True, exist_ok=True)

        # обход всех файлов в src
        for cur_root, dirs, files in os.walk(src):
            cur_root_path = Path(cur_root)
            rel_path = cur_root_path.relative_to(src)

            # целевая директория для текущего уровня
            target_dir = root_dst if rel_path == Path('.') else root_dst / rel_path
            target_dir.mkdir(parents=True, exist_ok=True)

            # создание поддиректорий
            for dir_name in dirs:
                (target_dir / dir_name).mkdir(parents=True, exist_ok=True)

            # копирование файлов
            for file_name in files:
                src_file = cur_root_path / file_name
                dst_file = target_dir / file_name

                if dst_file.exists() and dst_file.is_dir():
                    raise ValidationError(
                        f'Конфликт типов: в цели директория а копируется файл: {dst_file}'
                    )

                # backup если файл существует
                backup = None
                if dst_file.is_file():
                    backup = self._create_backup(dst_file)

                shutil.copy2(str(src_file), str(dst_file))
                self._record_undo(src_file, dst_file, backup)

    def execute(self, args: list[str], flags: list[str], ctx: CommandContext) -> str:
        self._undo_records.clear()
        self._validate_args(args)

        *srcs, dst = args
        dst_path = normalize(dst, ctx)
        recursive = self._is_recursive(flags)

        # проверка множественного копирования
        if len(srcs) > 1 and not dst_path.is_dir():
            raise ValidationError(
                'Если копируется несколько объектов последний аргумент должен быть директорией'
            )

        for src_arg in srcs:
            # обработка шаблона dir/*
            is_content_mode = Path(src_arg).name == '*'
            src_base = str(Path(src_arg).parent) if is_content_mode else src_arg
            src_path = normalize(src_base, ctx)

            if not src_path.exists():
                raise ValidationError(f'Источник не найден: {src_arg}')

            # копирование файла
            if src_path.is_file():
                target = (
                    (dst_path / src_path.name)
                    if (len(srcs) > 1 or dst_path.is_dir())
                    else dst_path
                )
                self._copy_file(src_path, target)
                continue

            # копирование директории требует флаг -r
            if not recursive:
                raise ValidationError('Для копирования директории нужен флаг -r')

            # нельзя перезаписать файл директорией
            if dst_path.is_file():
                raise ValidationError('Нельзя перезаписать файл директорией')

            if dst_path.is_dir():
                # копирование в существующую директорию
                self._copy_dir(src_path, dst_path, is_content_mode)
            else:
                # создание новой директории
                if len(srcs) > 1:
                    raise ValidationError(
                        'Цель должна существовать при копировании нескольких источников'
                    )
                self._copy_dir(src_path, dst_path, merge_content=True)

        return f'cp: скопировано {len(self._undo_records)} объектов'
