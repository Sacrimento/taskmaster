import readline

class Repl:

    PROMPT = 'Taskmaster > '

    def __init__(self):
        self.CMDS = {
            'test' : self._printf,
            'exit' : lambda i: exit(0)
        }
        readline.parse_and_bind('tab: complete')
        readline.set_completer(self._completer)

    def run(self):
        while True:
            i = input(self.PROMPT)
            self.CMDS.get(i, self._unknown)(i)
                

    def _printf(self, inp):
        print('helo !')

    def _unknown(self, inp):
        print('[Taskmaster]', inp, ': Unknown command')

    def _completer(self, text, state):
        opts = [o for o in self.CMDS if o.startswith(text)]
        return opts[state] if state < len(opts) else None
