import shlex
from logging import getLogger

from entity.errors import DomainError, ValidationError
from usecase.shell import Shell

logger = getLogger(__name__)


class CLIAdapter:
    def __init__(self, shell: Shell):
        self.shell = shell

    def run(self):
        print('Simple Unix Shell. Для выхода нажми Ctrl-D')
        while True:
            try:
                line = input(f'{self.shell.user}@{self.shell.pwd}$ ').strip()
                if not line:
                    continue
                parts = shlex.split(line)
                name = parts[0]
                args = []
                flags = []
                for arg in parts[1:]:
                    if arg.startswith('-'):
                        flags.append(arg)
                    else:
                        args.append(arg)
                logger.info(line)
                res = self.shell.run(name, args, flags)
                if res != '':
                    print(res)
            except EOFError:
                print('\nЗавершение shell')
                break
            except PermissionError as e:
                logger.error(e)
                print('Недостаточно прав')
            except ValidationError as e:
                logger.warning(e)
                print(e)
            except DomainError as e:
                logger.error(e)
                print(e)
            except KeyboardInterrupt:
                print('\nShell завершён по Ctrl-C. Лучше через Ctrl-D')
                break
            except Exception as e:
                logger.critical(e, exc_info=e)
                break
