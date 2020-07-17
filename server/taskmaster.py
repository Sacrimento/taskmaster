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

    def __init__(self, conf):
        self._conf = conf
        self.update_conf(False)
        
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.HOST, self.PORT))
        self.socket.listen(2)

    def __del__(self):
        self.socket.close()

    def run(self):
        while True:
            self.listen()
            # TODO : check_processes()
            pass

    def listen(self):
        conn, _ = self.socket.accept()
        data = conn.recv(1024).decode('utf-8')
        print('From online user: ' + data)

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
