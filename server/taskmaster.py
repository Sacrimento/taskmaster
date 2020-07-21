import os
import sys
import shlex
import signal
import socket
import logging
import inspect
import subprocess
from datetime import datetime, timedelta

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from tm_socket import send, recv, HOST, PORT

class Taskmaster:
    _processes = {}

    def __init__(self, conf, autoreload, outfile, lock_file):
        self.lock_file = lock_file
        self.logger = logging.getLogger('[Taskmaster]')

        if not os.path.isfile(lock_file):
            with open(lock_file, 'w+') as f:
                f.write(str(os.getpid()))
        else:
            print('Taskmaster daemon already running')
            exit(1)

        self._conf = conf
        self.autoreload = autoreload

        logging.basicConfig(
                filename=outfile,
                format='%(name)s %(asctime)s - %(levelname)s: %(message)s',
                datefmt='%d/%m/%Y %H:%M:%S',
                level=logging.DEBUG, ## TODO change this to info
            )
        self._conf.logger = self.logger

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((HOST, PORT))
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
        if os.path.isfile(self.lock_file):
            os.remove(self.lock_file)
        if hasattr(self, 'socket'):
            self.socket.close()
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
        self.logger.info('taskmaster daemon stopped')

    def listen(self):
        if not self.conn:
            self.conn, _ = self.socket.accept()
        data = recv(self.conn)
        s = data.split()
        if len(s) == 0:
            self.logger.info('invalid commmand received')
            exit(1) # if we received an invalid command that mean it doesnt come from our client
            return

        ret = getattr(self, s[0])(*s[1:] if len(s) > 1 else [None])
        send(self.conn, ret)

    def update_tasks(self, changes, first=False):
        for todo in ('start', 'stop'):
            for task in changes[todo]:
                if todo != 'start' or (first and self._conf[task].get('autostart', True)):
                    getattr(self, todo)(task)

    def update_conf(self, p=True, first=False):
        conf_changes = self._conf.populate()
        if not conf_changes:
            return 'error occurred while updating the config file'
        if not conf_changes['start'] and not conf_changes['stop']:
            return 'config file updated'
        if p:
            self.logger.info('Config file updated !')
            self.logger.debug(self._conf)
        self.update_tasks(conf_changes, first)
        return 'config file updated'

    def kill(self, name, signal):
        try:
            os.kill(self._processes[name]['process'].pid, signal)
        except OSError:
            self.logger.warning('Process %s already exited', name)
            return 'process %s already exited' % name

    def check_processes(self):
        now = datetime.now()

        for proc_name, status in self._processes.items():
            conf = self._conf[proc_name]
            running = status['process'].poll() is None
            if (status['status'] == 'stopped'
                 and status['stop_time'] - now > timedelta(0, conf.get('stop_time', 0))
                 and running):
                    self.kill(proc_name, signal.SIGKILL)

            if running:
                if timedelta(0, conf.get('starttime', 0)) + status['start_date'] < now: # process is running properly
                    status['status'] = 'running'
            else:
                if status['status'] not in ('exited', 'stopped'):
                    self.logger.info('%s exited !', proc_name)
                    status['status'] = 'exited'
                if (status['status'] == 'exited'
                        and status['process'].returncode not in conf.get('exitcodes', [])
                        and conf.get('autorestart', '') == 'unexpected'
                        and status['retries'] < conf.get('startretries', 128)):
                    self.start(proc_name)
                    status['retries'] += 1

    def has_conf_changed(self):
        return self._conf.has_changed()

    def initchildproc(self, name):
        os.setpgrp()
        os.umask(int(self._conf[name].get('umask', 777)))
        os.chdir(self._conf[name].get('workingdir', os.getcwd()))

    def start(self, name):
        self.logger.debug('Starting %s', name) 
        if self._handle_bad_name(name):
            return '%s: unknown process name' % name
        if name in self._processes and self._processes[name]['status'] in ('started', 'running'):
            return '%s is already running' % name
        current_state = self._conf[name]
        env = {**os.environ.copy(), **{str(k): str(v) for k, v in current_state.get('env', {}).items()}}
        try:
            with open(current_state.get('stdout', '/dev/stdout'), 'w') as stdout, open(current_state.get('stderr', '/dev/stderr'), 'w') as stderr:
                process = subprocess.Popen(shlex.split(current_state['cmd']),
                        stdout=stdout,
                        stderr=stderr,
                        env=env,
                        preexec_fn=lambda : self.initchildproc(name))
        except IOError as e:
            print(e)
            exit("un petit log au moins") # TODO: exit properly

        self.logger.info('%s started !', name)
        if name not in self._processes:
            self._processes[name] = {
                'retries': 0,
            }
        self._processes[name]['process'] = process
        self._processes[name]['start_date'] = datetime.now()
        self._processes[name]['status'] = 'started'
        return '%s successfully started' % name

    def stop(self, name):
        self.logger.debug('Stopping %s', name)

        if self._handle_bad_name(name):
            return '%s: unknown process name' % name

        self.kill(name, getattr(signal, 'SIG' + self._conf[name].get('stopsignal', 'TERM')))
        self._processes[name]['stop_time'] = datetime.now()
        self._processes[name]['status'] = 'stopped'
        self.logger.info('%s stopped !', name)
        return '%s successfully stopped' % name

    def restart(self, name):
        self.stop(name)
        return self.start(name)

    def status(self, _):
        out = ''
        for proc_name, status in self._processes.items():
            out += '%s:\n' % proc_name
            out += '  status: %s' % status['status']
            if status['status'] in ('exited', 'stopped'):
                out += ' (%d)' % status['process'].returncode
            else:
                out += '\n  started at: %s' % status['start_date'].strftime('%d/%m/%Y, %H:%M:%S')
        return out

    def _handle_bad_name(self, name):
        if not name:
            return True
        if name not in self._conf:
            self.logger.warning('%s: unknown process name', name)
            return True
