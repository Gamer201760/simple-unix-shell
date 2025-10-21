from entity.context import CommandContext
from entity.errors import ValidationError
from usecase.interface import FileSystemRepository


class MvCommand:
    def __init__(self, fs: FileSystemRepository) -> None:
        self._fs = fs
        self._undo_state = None  # Храним состояние для возможности undo

    @property
    def name(self) -> str:
        return 'mv'

    @property
    def description(self) -> str:
        return 'Перемещает файл или директорию, mv <source> <dest>'

    def undo(self) -> None:
        """Отменяет команду перемещения, восстанавливая предыдущее состояние"""
        if self._undo_state is None:
            return
        src, dst = self._undo_state['src'], self._undo_state['dst']
        # Переместить обратно (меняем местами src и dst)
        self._fs.move(dst, src)
        self._undo_state = None

    def _validate_args(self, args: list[str]) -> None:
        """Валидация аргументов"""
        if len(args) != 2:
            raise ValidationError('mv требует два аргумента: mv <source> <dest>')
        src = self._fs._normalize_path(args[0])
        if not self._fs.is_dir(src) and src not in self._flatten_fs_files():
            raise ValidationError(f'Источник не найден: {args[0]}')

    def _flatten_fs_files(self):
        result = []
        for dir_path, items in self._fs._tree.items():
            for item in items:
                item_path = f"{dir_path.rstrip('/')}/{item}"
                result.append(item_path)
        return set(result)

    def execute(self, args: list[str], flags: list[str], ctx: CommandContext) -> str:
        self._validate_args(args)
        src, dst = args
        # Сохраняем для undo
        self._undo_state = {
            'src': self._fs._normalize_path(src),
            'dst': self._fs._normalize_path(dst),
        }
        self._fs.move(src, dst)
        return f'Moved {src} → {dst}'
