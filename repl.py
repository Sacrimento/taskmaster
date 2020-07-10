import readline
import signal

class Repl:

    _PROMPT = 'Taskmaster > '

    def __init__(self, conf):
        self._conf = conf
        self._CMDS = {
            'test' : (self._printf, 'tests'),
            'help' : (self._help, 'display help'),
            'exit' : (lambda i: exit(0), 'exit taskmaster'),
        }
        readline.parse_and_bind('tab: complete')
        readline.set_completer(self._completer)
        signal.signal(signal.SIGHUP, lambda _, __: self.update_conf())

    def run(self):
        while True:
            i = input(self._PROMPT)
            if self._conf.has_changed():
                self.update_conf()
            self._CMDS.get(i, (self._unknown,))[0](i)

    def update_conf(self):
        self._conf.populate()
        print('[Taskmaster] Config file updated !', self._conf)

    def _printf(self, inp):
        print('helo !')

    def _unknown(self, inp):
        print('[Taskmaster]', inp, ': Unknown command')

    def _help(self, inp):
        for k, v in self._CMDS.items():
            print(k, ':', v[1])

    def _completer(self, text, state):
        opts = [o for o in self._CMDS if o.startswith(text)]
        return opts[state] if state < len(opts) else None
