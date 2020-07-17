import subprocess
import os
import shlex
import sys
import json # ??????????????????????????????????????????
import signal
import socket

class Taskmaster:
    _processes = {}

    HOST = socket.gethostname()
    PORT = 4242

    LOCK = 'taskmaster.lock'

    def __init__(self, conf, autoreload, outfile):
        if not os.path.isfile(self.LOCK):
            with open(self.LOCK, 'w+') as f:
                f.write(str(os.getpid()))
        else:
            exit(1)

        self._conf = conf
        self.update_conf(False)

        self.autoreload = autoreload
        ## TODO logger (outfile)

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.HOST, self.PORT))
        self.socket.listen(1)
        self.conn, _ = self.socket.accept()

        signal.signal(signal.SIGUSR1, lambda _, __: self.listen())
        signal.signal(signal.SIGINT, lambda _, __: self._deinit())
        signal.signal(signal.SIGHUP, lambda _, __: self.update_conf())

    def run(self):
        while True:
            if self.autoreload and self.has_conf_changed():
                self.update_conf()
            # TODO : check_processes() ## Maybe not needed, check SIGCHILD
        self._deinit()

    def _deinit(self):
        if os.path.isfile(self.LOCK):
            os.remove(self.LOCK)
            self.socket.close()
            self.conn.close()
        exit(0)

    def listen(self):
        data = self.conn.recv(1024).decode('utf-8')
        s = data.split()
        if len(s) < 2:
            ret = getattr(self, s[0])()
        else:
            ret = getattr(self, s[0])(*s[1:])
        self.conn.send('OK!'.encode('utf-8'))

    def update_tasks(self, changes):
        for todo in ('start', 'stop'):
            for task in changes[todo]:
                if todo != 'start' or self._conf[task].get('autostart', True):
                    getattr(self, todo)(task)

    def update_conf(self, p=True):
        conf_changes = self._conf.populate()
        if not conf_changes or (not conf_changes['start'] and not conf_changes['stop']):
            return
        if p:
            print('[Taskmaster] Config file updated !', self._conf)
        self.update_tasks(conf_changes)

    def has_conf_changed(self):
        return self._conf.has_changed()

    def initchildproc(self, name):
        os.setpgrp()
        os.umask(int(self._conf[name].get('umask', 777)))
        os.chdir(self._conf[name].get('workingdir', os.getcwd()))

    def start(self, name):
        print('starting:', name) 
        if self._handle_bad_name(name):
            return
        current_state = self._conf[name]
        env = {**os.environ.copy(), **json.loads(json.dumps(current_state.get('env', {})), parse_int=str)}
        with open(current_state.get('stdout', '/dev/stdout'), 'w') as stdout, open(current_state.get('stderr', '/dev/stderr'), 'w') as stderr:
            process = subprocess.Popen(shlex.split(current_state['cmd']),
                    stdout=stdout,
                    stderr=stderr,
                    env=env,
                    preexec_fn=lambda : self.initchildproc(name))
            print(name, 'started')
        self._processes[name] = process

    def stop(self, name):
        print('stoping:', name) 
        if self._handle_bad_name(name):
            return
        try:
            os.kill(self._processes[name].pid, getattr(signal, "SIG" + self._conf[name].get('stopsignal', "TERM")))
        except OSError:
            print('no pid for process', name)
            return
        # os.killpg(os.getpgid(self._processes[name].pid), getattr(signal, self.conf.get('stopsignal', "TERM")))
        print(name, 'stopped')

    def status(self):
        pass

    def _handle_bad_name(self, name):
        if not name:
            return True
        if name not in self._conf:
            print('[Taskmaster] "'+ name +'": unknown process name')
            return True
