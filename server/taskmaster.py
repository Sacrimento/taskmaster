import subprocess
import os
import shlex
import sys
import signal
import socket
import logging
from datetime import datetime, timedelta

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
            print('Taskmaster daemon already running')
            exit(1)

        self._conf = conf
        self.autoreload = autoreload

        self.logger = logging.getLogger('[Taskmaster]')
        logging.basicConfig(
                filename=outfile,
                format='%(name)s %(asctime)s - %(levelname)s: %(message)s',
                datefmt='%d/%m/%Y %H:%M:%S',
                level=logging.DEBUG, ## TODO change this to info
            )
        self._conf.logger = self.logger

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.HOST, self.PORT))
        self.socket.listen(1)
        self.conn = None

        signal.signal(signal.SIGUSR1, lambda _, __: self.listen())
        signal.signal(signal.SIGINT, lambda _, __: exit(0))
        signal.signal(signal.SIGHUP, lambda _, __: self.update_conf())
        
        self.logger.info('taskmaster daemon started')
        self.update_conf(False, True)

    def run(self):
        while True:
            if self.autoreload and self.has_conf_changed():
                self.update_conf()
            self.check_processes()

    def __del__(self):
        if os.path.isfile(self.LOCK):
            os.remove(self.LOCK)
        if hasattr(self, 'socket'):
            self.socket.close()
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
        self.logger.info('taskmaster daemon stopped')

    def listen(self):
        if not self.conn:
            self.conn, _ = self.socket.accept()
        data = self.conn.recv(1024).decode('utf-8')
        s = data.split()
        if len(s) < 2:
            ret = getattr(self, s[0])()
        else:
            ret = getattr(self, s[0])(*s[1:])
        self.conn.send('OK!'.encode('utf-8'))

    def update_tasks(self, changes, first=False):
        for todo in ('start', 'stop'):
            for task in changes[todo]:
                if todo != 'start' or (first and self._conf[task].get('autostart', True)):
                    getattr(self, todo)(task)

    def update_conf(self, p=True, first=False):
        conf_changes = self._conf.populate()
        if not conf_changes or (not conf_changes['start'] and not conf_changes['stop']):
            return
        if p:
            self.logger.info('Config file updated !')
            self.logger.debug(self._conf)
        self.update_tasks(conf_changes, first)

    def check_processes(self):
        ## TODO: WTF is 'stoptime'
        now = datetime.now()

        for proc_name, status in self._processes.items():
            conf = self._conf[proc_name]
            running = not status['process'].poll()
            if not running:
                if timedelta(0, conf.get('starttime', 0)) + status['start_date'] < now: # process is running properly
                    status['status'] = 'running'
            else:
                if status['status'] != 'exited':
                    self.logger.info('%s exited !', proc_name)
                    status['status'] = 'exited' 
                if (status['process'].returncode not in conf.get('exitcodes', [])
                        and conf.get('autorestart', '') == 'unexpected'
                        and status['retries'] < conf.get('startretries', 2147483647)):
                    self.start(proc_name)
                    status['retries'] += 1


    def has_conf_changed(self):
        return self._conf.has_changed()

    def initchildproc(self, name):
        os.setpgrp()
        os.umask(int(self._conf[name].get('umask', 777)))
        os.chdir(self._conf[name].get('workingdir', os.getcwd()))

    def start(self, name):
        # TODO : check if running
        self.logger.debug('Starting %s', name) 
        if self._handle_bad_name(name):
            return
        current_state = self._conf[name]
        env = {**os.environ.copy(), **{str(k): str(v) for k, v in current_state.get('env', {}).items()}}
        ## TODO: What if custom stdout or stderr does not exist ?
        with open(current_state.get('stdout', '/dev/stdout'), 'w') as stdout, open(current_state.get('stderr', '/dev/stderr'), 'w') as stderr:
            process = subprocess.Popen(shlex.split(current_state['cmd']),
                    stdout=stdout,
                    stderr=stderr,
                    env=env,
                    preexec_fn=lambda : self.initchildproc(name))
        self.logger.info('%s started !', name)
        if name not in self._processes:
            self._processes[name] = {
                'retries': 0,
            }
        self._processes[name]['process'] = process
        self._processes[name]['start_date'] = datetime.now()
        self._processes[name]['status'] = 'started'

    def stop(self, name):
        # TODO : check if running
        self.logger.debug('Stopping %s', name)
        if self._handle_bad_name(name):
            return
        try:
            os.kill(self._processes[name].pid, getattr(signal, 'SIG' + self._conf[name].get('stopsignal', 'TERM')))
        except OSError:
            return self.logger.error('No pid for process %s', name)
        # os.killpg(os.getpgid(self._processes[name].pid), getattr(signal, self.conf.get('stopsignal', "TERM")))
        self.logger.info('%s stopped !', name)

    def status(self):
        for proc_name, status in self._processes:
            print(proc_name, status)

    def _handle_bad_name(self, name):
        if not name:
            return True
        if name not in self._conf:
            self.logger.warning('%s: unknown process name', name)
            return True
