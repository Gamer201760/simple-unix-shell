from uuid import uuid4


class InMemoryFileSystemRepository:
    def __init__(
        self,
        tree: dict[str, list[str]],  # "директория": ["имя", ...]
        home: str = '/home/test',
        pwd: str = '/home/test',
    ):
        self._tree = tree
        self._pwd = pwd
        self._home = home

    @property
    def current(self) -> str:
        return self._pwd

    def delete(self, source: str) -> str:
        """Удаляет файл source (перемещает в .trash с уникальным именем), возвращает путь в .trash"""
        src_path = self._normalize_path(source)

        parent, name = src_path.rsplit('/', 1)
        if not parent:
            parent = '/'

        # Проверяем, что файл существует
        if parent not in self._tree or name not in self._tree[parent]:
            raise FileNotFoundError(f'File {src_path} not found')

        # Генерируем уникальное имя через uuid4
        trash_dir = '/.trash'
        if trash_dir not in self._tree:
            self._tree[trash_dir] = []

        unique_name = f'{name}.{uuid4().hex}'
        trash_path = f'{trash_dir}/{unique_name}'

        # Удаляем файл из родительской директории
        self._tree[parent].remove(name)
        # Добавляем файл в .trash
        self._tree[trash_dir].append(unique_name)

        # Если это была папка — переносим поддерево
        if src_path in self._tree:
            self._tree[trash_path] = self._tree.pop(src_path)

        return trash_path

    def exists(self, path: str) -> bool:
        """Проверяет наличие файла"""
        norm = self._normalize_path(path)
        parent, name = norm.rsplit('/', 1)
        if not parent:
            parent = '/'
        return (
            parent in self._tree
            and name in self._tree[parent]
            and norm not in self._tree
        )

    # /photos/photo1.png /photos/mv_photo.png
    def move(self, source: str, dest: str) -> None:
        """
        Перемещает файл или папку из source в dest внутри in-memory дерева.
        """
        src_path = self._normalize_path(source)
        dst_path = self._normalize_path(dest)

        src_dir, src_name = src_path.rsplit('/', 1)
        if not src_dir:
            src_dir = '/'

        # Поиск целевой директории (dest)
        if self.is_dir(dst_path):
            # Если dest — директория, перемещаем внутрь, имя сохраняем
            target_dir = dst_path
            dst_name = src_name
        else:
            # Если dest не директоря — это полный путь-имя назначения
            target_dir, dst_name = dst_path.rsplit('/', 1)
            if not target_dir:
                target_dir = '/'

        # Проверки существования
        if src_dir not in self._tree:
            raise FileNotFoundError(f'Source directory {src_dir} does not exist')
        if src_name not in self._tree[src_dir]:
            raise FileNotFoundError(f'Source {src_path} does not exist')
        if target_dir not in self._tree:
            raise FileNotFoundError(f'Target directory {target_dir} does not exist')

        # Формируем финальные абсолютные пути
        src_full = src_dir + '/' + src_name if src_dir != '/' else '/' + src_name
        dst_full = target_dir + '/' + dst_name if target_dir != '/' else '/' + dst_name

        # Если перемещаем папку: делаем вложенность
        if src_full in self._tree:
            # Перемещаем поддерево каталога
            self._tree[dst_full] = self._tree.pop(src_full)  # переносим содержимое
        # Если перемещаем файл: ничего не делаем со структурой дерева

        # Удаляем из старой директории, добавляем в новую
        self._tree[src_dir].remove(src_name)
        if dst_name not in self._tree[target_dir]:
            self._tree[target_dir].append(dst_name)
        print(self._tree)

    def list_dir(self, path: str) -> list[str]:
        """Возвращает список объектов в директории"""
        return self._tree[self._normalize_path(path)]

    def set_current(self, path: str) -> None:
        self._pwd = self._normalize_path(path)

    def is_dir(self, path: str) -> bool:
        return self._normalize_path(path) in self._tree

    def expanduser(self, path: str) -> str:
        if path.startswith('~'):
            return self._home + path[1:]
        return path

    def _normalize_path(self, path: str) -> str:
        path = self.expanduser(path)
        if not path.startswith('/'):
            cur = self._pwd.rstrip('/')
            path = cur + '/' + path

        parts: list[str] = []
        for part in path.split('/'):
            if part in ('.', ''):
                continue
            elif part == '..':
                if parts:
                    parts.pop()
            else:
                parts.append(part)
        return '/' + '/'.join(parts) if parts else '/'
