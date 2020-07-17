import readline
import signal
import difflib

class Repl:

    def __init__(self, tm, auto_reload):
        self._tm = tm
        self.auto_reload = auto_reload
        self._CMDS = {
            'start' : (lambda i: self._tm.start(self._get_arg(6, i)), 'start the PROGNAME program'),
            'stop' : (lambda i: self._tm.stop(self._get_arg(5, i)), 'stop the PROGNAME program'),
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
            try:
                i = input('Taskmaster > ')
            except:
                exit()
            if self.auto_reload and self._tm.has_conf_changed():
                self._tm.update_conf()
            if i.split():
                self._CMDS.get(i.split()[0], (self._unknown,))[0](i)

    def _restart(self, inp):
        arg = self.get_arg(7, inp)

        self._tm.stop(arg)
        self._tm.start(arg)

    def _unknown(self, inp):
        closest = difflib.get_close_matches(inp, list(self._CMDS.keys()), 1, 0.5)
        print('[Taskmaster]', inp, ': Unknown command', end='')
        print(f'. Did you mean "{closest[0]}" ?\n' if closest else '\n', end='')

    def _help(self, inp):
        for k, v in self._CMDS.items():
            print(k, ':', v[1])

    def _completer(self, text, state):
        opts = [o for o in self._CMDS if o.startswith(text)]
        return opts[state] if state < len(opts) else None

    def _get_arg(self, index, inp):
        if len(inp.split()) > 1:
            return inp[index:].lstrip()
        print('[Taskmaster]', inp, 'expects a PROGNAME argument')

