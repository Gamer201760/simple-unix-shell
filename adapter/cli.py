import sys

from usecase.shell import Shell


class CLIAdapter:
    def __init__(self, shell: Shell):
        self.shell = shell

    def run(self):
        print('Мой shell. Для выхода нажми Ctrl-D.')
        try:
            while True:
                try:
                    line = input(
                        f'{self.shell._context.user}@{self.shell._context.pwd}$ '
                    ).strip()
                except EOFError:
                    print('\nЗавершение shell.')
                    break
                if not line:
                    continue  # пустая строка — не команда
                parts = line.split()
                name = parts[0]
                args = list(map(str.strip, parts[1:]))
                print(self.shell.run(name, args))
        except KeyboardInterrupt:
            print('\nShell завершён по Ctrl-C.')
            sys.exit(0)
