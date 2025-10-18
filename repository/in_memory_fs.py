from pathlib import Path


class InMemoryFileSystemRepository:
    def __init__(self) -> None:
        self.pwd = Path.home()

    def get_current(self) -> Path:
        return self.pwd

    def set_current(self, path: Path) -> None:
        self.pwd = path
