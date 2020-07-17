import readline
import signal
import difflib
import socket
import os

import get_tm_info as info

class Repl:

    HOST = socket.gethostname()
    PORT = 4242

    def __init__(self, tm=None):
        self._tm = tm
        self._CMDS = {
            'start' : (lambda i: self.send(i) if self._has_arg(i) else None, 'start the PROGNAME program'),
            'stop' : (lambda i: self.send(i) if self._has_arg(i) else None, 'stop the PROGNAME program'),
            'restart' : (self._restart, 'restart the PROGNAME program'),
            'reread' : (lambda i: self.send('update_conf'), 'update configuration file'),
            'status' : (self.send, 'display status for each program'),
            'help' : (self._help, 'display help'),
            'exit' : (lambda i: exit(0), 'exit taskmaster'),
        }

        if not info.is_tm_running():
            print('[Taskmaster] Fatal : taskmaster daemon not running')
            exit(1)

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.HOST, self.PORT))

        readline.parse_and_bind('tab: complete')
        readline.set_completer(self._completer)
        signal.signal(signal.SIGHUP, lambda _, __: os.kill(info.get_tm_pid(), signal.SIGHUP))
        signal.signal(signal.SIGINT, lambda _, __: (print(), exit(0))) # Maybe a bad idea

    def __del__(self):
        if hasattr(self, 'socket'):
            self.socket.close()

    def run(self):
        while True:
            i = input('Taskmaster > ')
            if i.split():
                self._CMDS.get(i.split()[0], (self._unknown,))[0](i)

    def send(self, payload):
        os.kill(info.get_tm_pid(), signal.SIGUSR1)
        self.socket.send(payload.encode('utf-8'))
        data = self.socket.recv(1024).decode('utf-8')
        print('Received from server: ' + data)

    def _restart(self, inp):
        if self._has_arg(inp):
            arg = ' '.join(inp.split()[1:])
            self.send('stop ' + arg)
            self.send('start ' + arg)

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

    def _has_arg(self, inp):
        if len(inp.split()) > 1:
            return True
        print('[Taskmaster]', inp, 'expects a PROGNAME argument')
