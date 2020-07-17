import readline
import signal
import difflib
import socket

class Repl:

    HOST = socket.gethostname()
    PORT = 4242

    def __init__(self, tm=None):
        self._tm = tm
        self._CMDS = {
            'start' : (lambda i: self._tm.start(self._get_arg(6, i)), 'start the PROGNAME program'),
            'stop' : (lambda i: self._tm.stop(self._get_arg(5, i)), 'stop the PROGNAME program'),
            'restart' : (self._restart, 'restart the PROGNAME program'),
            'reread' : (lambda i: self._tm.update_conf(), 'update configuration file'),
            'status' : (lambda i: self._tm.status(), 'display status for each program'),
            'help' : (self._help, 'display help'),
            'exit' : (lambda i: exit(0), 'exit taskmaster'),
        }

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.HOST, self.PORT))

        readline.parse_and_bind('tab: complete')
        readline.set_completer(self._completer)
        signal.signal(signal.SIGHUP, lambda _, __: self.tm.update_conf())
        signal.signal(signal.SIGINT, lambda _, __: (print(), exit(0))) # Maybe a bad idea

    def __del__(self):
        self.socket.close()

    def run(self):
        while True:
            i = input('Taskmaster > ')
            self.send(i)
            if i.split():
                self._CMDS.get(i.split()[0], (self._unknown,))[0](i)

    def send(self, payload):
        self.socket.send(payload.encode('utf-8'))
        data = self.socket.recv(1024).decode('utf-8')
        print('Received from server: ' + data)

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

