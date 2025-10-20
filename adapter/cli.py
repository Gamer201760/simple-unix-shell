from entity.errors import DomainError
from usecase.shell import Shell


class CLIAdapter:
    def __init__(self, shell: Shell):
        self.shell = shell

    def run(self):
        print('Simple Unix Shell. Для выхода нажми Ctrl-D.')
        while True:
            try:
                line = input(f'{self.shell.user}@{self.shell.pwd}$ ').strip()
                if not line:
                    continue
                parts = line.split()
                name = parts[0]
                args = list(map(str.strip, parts[1:]))
                res = self.shell.run(name, args)
                if res != '':
                    print(res)

            except EOFError:
                print('\nЗавершение shell.')
                break
            except DomainError as e:
                print(e)
            except KeyboardInterrupt:
                print('\nShell завершён по Ctrl-C.')
                break
