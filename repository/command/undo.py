import shutil
from pathlib import Path

from entity.context import CommandContext
from entity.errors import DomainError
from usecase.interface import UndoRepository


class Undo:
    def __init__(self, undo_repo: UndoRepository) -> None:
        self._undo_repo = undo_repo

    @property
    def name(self) -> str:
        return 'undo'

    @property
    def description(self) -> str:
        return 'Отменяет последнюю изменяющую команду (mv, cp, rm)'

    def _ensure_parent(self, target: Path) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)

    def _delete_path(self, p: Path) -> None:
        if p.is_dir():
            shutil.rmtree(p)
        elif p.exists():
            p.unlink()

    def execute(self, args: list[str], flags: list[str], ctx: CommandContext) -> str:
        records = self._undo_repo.pop()
        if records is None:
            raise DomainError('Нет отменяемых команд в истории')

        res_parts: list[str] = []
        for record in records:
            action = record.action
            if action == 'rm':
                src = Path(record.src)
                dst = Path(record.dst)
                self._ensure_parent(src)
                shutil.move(str(dst), str(src))
                res_parts.append(f'Восстановлен {record.src} из корзины')
                continue

            if action == 'mv':
                src = Path(record.src)
                dst = Path(record.dst)
                self._ensure_parent(src)
                shutil.move(str(dst), str(src))
                if record.overwrite and record.overwritten_path is not None:
                    overwritten = Path(record.overwritten_path)
                    self._ensure_parent(dst)
                    shutil.move(str(overwritten), str(dst))
                    res_parts.append(
                        f'Откат: {record.dst} -> {record.src},\nвосстановлен оригинал по {record.dst}'
                    )
                    continue
                res_parts.append(f'Откат: {record.dst} -> {record.src}')
                continue

            if action == 'cp':
                dst = Path(record.dst)
                if record.overwrite and record.overwritten_path is not None:
                    overwritten = Path(record.overwritten_path)
                    self._ensure_parent(dst)
                    shutil.move(str(overwritten), str(dst))
                    res_parts.append(
                        'Откат: восстановлен старый {0}; копия удалена'.format(
                            record.dst
                        )
                    )
                    continue
                self._delete_path(dst)
                res_parts.append(f'Откат: удалена скопированная копия {record.dst}')
                continue

        return '\n'.join(res_parts)
