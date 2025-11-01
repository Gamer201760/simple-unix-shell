import os
from pathlib import Path


class HistoryFileRepository:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def add(self, name: str, args: list[str], flags: list[str]) -> None:
        cmd = ' '.join([name, *flags, *args]).strip()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        last_lines = self._read_last_lines(1)
        last_no = self._parse_leading_number(last_lines[0]) if last_lines else 0
        with self.path.open('a', encoding='utf-8') as f:
            f.write(f'{last_no + 1} {cmd}\n')

    def last(self, n: int) -> list[str]:
        if n <= 0:
            return []
        return self._read_last_lines(n)

    def all(self) -> list[str]:
        if not self.path.exists():
            return []
        with self.path.open('r', encoding='utf-8') as f:
            return [line.rstrip('\r\n') for line in f]

    def clear(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open('w', encoding='utf-8'):
            pass

    def _read_last_lines(self, n: int, chunk_size: int = 8192) -> list[str]:
        """Читает последние n строк, двигаясь с конца файла"""
        if n <= 0 or not self.path.exists():
            return []
        buf = b''
        with self.path.open('rb') as f:
            f.seek(0, os.SEEK_END)
            file_end = f.tell()
            pos = file_end
            newlines = 0

            while pos > 0 and newlines <= n:
                read_size = min(chunk_size, pos)
                pos -= read_size
                f.seek(pos, os.SEEK_SET)
                chunk = f.read(read_size)
                buf = chunk + buf
                newlines += chunk.count(b'\n')

        text = buf.decode('utf-8', errors='replace')
        lines = text.splitlines()
        return lines[-n:]

    @staticmethod
    def _parse_leading_number(line: str) -> int:
        obj = line.strip().split()
        if len(obj) == 0:
            return 0
        n = obj[0]
        if n.isdigit():
            return int(n)
        return 0
