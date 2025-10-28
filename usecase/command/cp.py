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

    def _is_recursive(self, flags: list[str]) -> bool:
        return ('-r' in flags) or ('-R' in flags) or ('--recursive' in flags)

    def _is_dir_content_path(self, path: str) -> tuple[bool, str]:
        """
        Возвращает (is_content_mode, base_dir_path).
        content_mode=True для путей вида "<dir>/." — копировать содержимое dir внутрь назначения.
        """
        if self._fs.basename(path) == '.':
            base_dir = self._fs.path_dirname(path)
            return True, base_dir if base_dir else path
        return False, path

    def _copy_dir_recursive(self, src_dir: str, dst: str, place_inside: bool) -> None:
        """
        Если place_inside=True: корнем назначения будет join(dst, basename(src_dir)).
        Если place_inside=False: корнем назначения будет dst (слияние содержимого src_dir в dst).
        """
        root_dst = (
            self._fs.path_join(dst, self._fs.basename(src_dir)) if place_inside else dst
        )
        self._mkdir_if_not_exists(root_dst)

        for cur_root, dirs, files in self._fs.walk(src_dir):
            rel = self._fs.path_relpath(cur_root, src_dir)
            target_dir = root_dst if rel == '.' else self._fs.path_join(root_dst, rel)
            self._mkdir_if_not_exists(target_dir)

            for d in dirs:
                self._mkdir_if_not_exists(self._fs.path_join(target_dir, d))

            for fname in files:
                s = self._fs.path_join(cur_root, fname)
                d = self._fs.path_join(target_dir, fname)
                if self._fs.is_dir(d):
                    raise ValidationError(
                        f'Конфликт типов: в цели директория, а копируется файл: {d}'
                    )
                backup: str | None = None
                if self._fs.is_file(d):
                    backup = self._fs.delete(d)
                self._fs.copy(s, d)
                self._record_cp(s, d, backup)

    def execute(self, args: list[str], flags: list[str], ctx: CommandContext) -> str:
        self._undo_records.clear()
        self._validate_args(args)
        *srcs, dst = args

        if len(srcs) > 1 and not self._fs.is_dir(dst):
            raise ValidationError(
                'Если копируется несколько объектов, последний аргумент должен быть существующей директорией'
            )

        recursive = self._is_recursive(flags)

        for raw_src in srcs:
            content_mode, src = self._is_dir_content_path(raw_src)
            is_src_file = self._fs.is_file(src)
            is_src_dir = self._fs.is_dir(src)
            if not is_src_file and not is_src_dir:
                raise ValidationError(f'Источник не найден: {raw_src}')

            if is_src_file:
                target = (
                    self._fs.path_join(dst, self._fs.basename(src))
                    if (len(srcs) > 1 or self._fs.is_dir(dst))
                    else dst
                )
                self._copy_file_with_undo(src, target)
                continue

            if not recursive:
                raise ValidationError('Для копирования директории нужен флаг -r')

            if len(srcs) == 1 and self._fs.is_file(dst):
                raise ValidationError('Нельзя перезаписать файл директорией')

            if not self._fs.is_dir(dst):
                if len(srcs) > 1:
                    raise ValidationError(
                        'Целевая директория должна существовать при копировании нескольких источников'
                    )
                # cp -r src dst (dst не существует): создаём dst и вливаем СОДЕРЖИМОЕ src в dst
                self._mkdir_if_not_exists(dst)
                self._copy_dir_recursive(src, dst, place_inside=False)
            else:
                # dst — существующая директория:
                # по умолчанию place-inside (dst/basename(src)), а для "<src>/." — слияние содержимого в dst
                self._copy_dir_recursive(src, dst, place_inside=not content_mode)

        return f'cp: скопировано {len(self._undo_records)} объектов'
