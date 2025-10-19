from dataclasses import dataclass


@dataclass
class CommandContext:
    pwd: str
    home: str
    user: str
    commands: dict[str, 'Command']
