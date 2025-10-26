from entity.context import CommandContext
from entity.errors import DomainError
from usecase.interface import FileSystemRepository, UndoRepository


class Undo:
    def __init__(
        self,
        undo_repo: UndoRepository,
        fs: FileSystemRepository,
    ) -> None:
        self._undo_repo = undo_repo
        self._fs = fs

    @property
    def name(self) -> str:
        return 'undo'

    @property
    def description(self) -> str:
        return 'Отменяет последнюю изменяющую команду (mv, cp, rm)'

    def execute(self, args: list[str], flags: list[str], ctx: CommandContext) -> str:
        records = self._undo_repo.pop()
        if records is None:
            raise DomainError('Нет отменяемых команд в истории')

        res = ''
        for record in records:
            match record.action:
                case 'rm':
                    # rm: src - был удален (откуда), dst - находится в .trash
                    self._fs.move(record.dst, record.src)
                    res += f'Восстановлен {record.src} из корзины\n'
                    break
                case 'mv':
                    # mv: src - откуда был перемещён, dst - куда был перемещён
                    self._fs.move(record.dst, record.src)
                    if record.overwrite and record.overwritten_path is not None:
                        self._fs.move(record.overwritten_path, record.dst)
                        res += (
                            f'Откат: {record.dst} -> {record.src},\n'
                            f'восстановлен оригинал по {record.dst}\n'
                        )
                        break
                    res += f'Откат: {record.dst} -> {record.src}'
                    break
                case 'cp':
                    # cp: src - исходный файл, dst - путь куда скопировали
                    if (
                        record.overwrite is not None
                        and record.overwrite
                        and record.overwritten_path is not None
                    ):
                        self._fs.move(record.overwritten_path, record.dst)
                        res += f'Откат: восстановлен старый {record.dst}; копия удалена'
                        break
                    self._fs.delete(record.dst)
                    res += f'Откат: удалена скопированная копия {record.dst}'
                    break
        return res
