import os
import sys
import signal
import socket
import inspect
import difflib
import readline

import get_tm_info as info

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from tm_socket import send, recv, HOST

class Repl:

    def __init__(self, port):
        self.lock_file='/tmp/taskmaster.lock'
        self._CMDS = {
            'start' : (self._check_send, 'start the PROGNAME program'),
            'stop' : (self._check_send, 'stop the PROGNAME program'),
            'restart' : (self._check_send, 'restart the PROGNAME program'),
            'reread' : (lambda i: self._send('update_conf'), 'update configuration file'),
            'status' : (self._send, 'display status for each program'),
            'help' : (self._help, 'display help'),
            'exit' : (lambda i: [self.socket.close(), os.kill(info.get_tm_pid(self.lock_file), signal.SIGINT), exit(0)], 'exit taskmaster daemon'),
        }

        if not info.is_tm_running(self.lock_file):
            print('[Taskmaster] Fatal : taskmaster daemon not running')
            exit(1)

        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((HOST, port))
        except Exception:
            print('[Taskmaster] Fatal : could not connect to taskmaster daemon')
            exit(1)

        readline.parse_and_bind('tab: complete')
        readline.set_completer(self._completer)
        signal.signal(signal.SIGHUP, lambda _, __: os.kill(info.get_tm_pid(self.lock_file), signal.SIGHUP))
        signal.signal(signal.SIGINT, lambda _, __: (print(), self.cleanup(), exit(0)))

    def __del__(self):
        self.cleanup()

    def cleanup(self):
        if hasattr(self, 'socket'):
            self.socket.close()

    def run(self):
        while True:
            try:
                i = input('Taskmaster > ')
            except EOFError:
                exit()
            if not info.is_tm_running(self.lock_file):
                print('[Taskmaster] Fatal: Connection to taskmaster dameon lost')
                self.cleanup()
                exit(1)
            s = i.split()
            if s:
                self._CMDS.get(s[0], (self._unknown,))[0](i)

    def _send(self, payload):
        os.kill(info.get_tm_pid(self.lock_file), signal.SIGUSR1)
        if not send(self.socket, payload):
            print('[Taskmaster Fatal: Could not send to taskmaster daemon. Exiting...')
            self.cleanup()
            exit(1)
        data = recv(self.socket)
        print('[Taskmaster]: ' + data)

    def _check_send(self, inp):
        if self._has_arg(inp):
            self._send(inp)

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
