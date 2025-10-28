from entity.context import CommandContext
from entity.errors import ValidationError
from entity.undo import UndoRecord
from usecase.interface import FileSystemRepository


class Cp:
    def __init__(self, fs: FileSystemRepository) -> None:
        self._fs = fs
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

    def _is_recursive(self, flags: list[str]) -> bool:
        return ('-r' in flags) or ('-R' in flags) or ('--recursive' in flags)

    def _ensure_parent_dir_exists(self, path: str) -> None:
        parent = self._fs.path_dirname(path) or '.'
        if not self._fs.is_dir(parent):
            raise ValidationError(f'Целевая директория не существует: {parent}')

    def _record_cp(self, src: str, dst: str, backup: str | None) -> None:
        self._undo_records.append(
            UndoRecord(
                action='cp',
                src=src,
                dst=dst,
                overwrite=backup is not None,
                overwritten_path=backup,
            )
        )

    def _copy_file_with_undo(self, src_file: str, dst_file: str) -> None:
        # Поддержка перезаписи с undo:
        # - если dst_file существует как файл — удалить (получить backup) и потом копировать
        # - если dst_file — директория, это ошибка
        self._ensure_parent_dir_exists(dst_file)

        backup: str | None = None
        if self._fs.is_file(dst_file):
            backup = self._fs.delete(dst_file)

        if self._fs.is_dir(dst_file):
            raise ValidationError(f'Нельзя перезаписать директорию файлом: {dst_file}')

        self._fs.copy(src_file, dst_file)
        self._record_cp(src_file, dst_file, backup)

    def _mkdir_if_not_exists(self, path: str) -> None:
        if not self._fs.is_dir(path):
            self._fs.mkdir(path)

    def _copy_dir_recursive(self, src_dir: str, dst: str, place_inside: bool) -> None:
        """
        Рекурсивно копирует директорию:
        - place_inside=True: корень назначения = join(dst, basename(src_dir))
        - place_inside=False: корень назначения = dst
        Перезапись файлов в существующих директориях с поддержкой undo.
        """
        root_dst = (
            self._fs.path_join(dst, self._fs.basename(src_dir)) if place_inside else dst
        )
        self._mkdir_if_not_exists(root_dst)

        for cur_root, dirs, files in self._fs.walk(src_dir):
            rel = self._fs.path_relpath(cur_root, src_dir)
            target_dir = root_dst if rel == '.' else self._fs.path_join(root_dst, rel)
            self._mkdir_if_not_exists(target_dir)

            # Поддиректории (создание, без удаления существующих)
            for d in dirs:
                subdir = self._fs.path_join(target_dir, d)
                self._mkdir_if_not_exists(subdir)

            for fname in files:
                s = self._fs.path_join(cur_root, fname)
                d = self._fs.path_join(target_dir, fname)

                backup: str | None = None
                if self._fs.is_file(d):
                    backup = self._fs.delete(d)
                if self._fs.is_dir(d):
                    raise ValidationError(
                        f'Конфликт типов: в цели директория, а копируется файл: {d}'
                    )

                self._fs.copy(s, d)
                self._record_cp(s, d, backup)

    def execute(self, args: list[str], flags: list[str], ctx: 'CommandContext') -> str:
        self._undo_records.clear()
        self._validate_args(args)
        *srcs, dst = args

        # Если источников несколько, dst должен быть существующей директорией
        if len(srcs) > 1 and not self._fs.is_dir(dst):
            raise ValidationError(
                'Если копируется несколько объектов, последний аргумент должен быть существующей директорией'
            )

        recursive = self._is_recursive(flags)

        for src in srcs:
            is_src_file = self._fs.is_file(src)
            is_src_dir = self._fs.is_dir(src)
            if not is_src_file and not is_src_dir:
                raise ValidationError(f'Источник не найден: {src}')

            # Калькуляция целевого пути
            if len(srcs) > 1:
                # Несколько источников: внутрь dst/<basename(src)>
                if not self._fs.is_dir(dst):
                    raise ValidationError(
                        'Целевая директория должна существовать при копировании нескольких источников'
                    )
                target = self._fs.path_join(dst, self._fs.basename(src))
            # Один источник
            elif self._fs.is_dir(dst):
                target = self._fs.path_join(dst, self._fs.basename(src))
            else:
                target = dst

            if is_src_file:
                self._copy_file_with_undo(src, target)
                continue

            # Директория
            if not recursive:
                raise ValidationError('Для копирования директории нужен флаг -r')

            if self._fs.is_file(target):
                raise ValidationError('Нельзя перезаписать файл директорией')

            # Размещение директории:
            # - dst — существующая директория: src помещается внутрь (dst/basename(src))
            # - dst — не существует и src один: создаётся dst как корень копии src
            place_inside = self._fs.is_dir(dst)
            base_dst = dst if not place_inside else dst
            self._copy_dir_recursive(src, base_dst, place_inside)

        return f'cp: скопировано {len(self._undo_records)} объектов'
