import readline
import signal

class Repl:

    def __init__(self, tm):
        self._tm = tm
        self._CMDS = {
            'start' : (lambda i: self._tm.start(self._get_arg(6, i)), 'start the PROGNAME program'),
            'stop' : (lambda i: self._tm.start(self._get_arg(5, i)), 'stop the PROGNAME program'),
            'restart' : (self._restart, 'restart the PROGNAME program'),
            'reread' : (lambda i: self._tm.update_conf(), 'update configuration file'),
            'status' : (lambda i: self._tm.status(), 'display status for each program'),
            'help' : (self._help, 'display help'),
            'exit' : (lambda i: exit(0), 'exit taskmaster'),
        }
        readline.parse_and_bind('tab: complete')
        readline.set_completer(self._completer)
        signal.signal(signal.SIGHUP, lambda _, __: self.tm.update_conf())
        signal.signal(signal.SIGINT, lambda _, __: (print(), exit(0))) # Maybe a bad idea

    def run(self):
        while True:
            i = input('Taskmaster > ')
            if self._tm.has_conf_changed():
                self._tm.update_conf()
            self._CMDS.get(i.split()[0], (self._unknown,))[0](i)

    def _restart(self, inp):
        arg = self.get_arg(7, inp)

        self._tm.stop(arg)
        self._tm.start(arg)

    def _unknown(self, inp):
        print('[Taskmaster]', inp, ': Unknown command')

    def _help(self, inp):
        for k, v in self._CMDS.items():
            print(k, ':', v[1])

    def _completer(self, text, state):
        opts = [o for o in self._CMDS if o.startswith(text)]
        return opts[state] if state < len(opts) else None

    def _get_arg(self, index, inp):
        if len(inp.split()) > 1:
            return inp[index:]
        print('[Taskmaster]', inp, 'expects a PROGNAME argument')

