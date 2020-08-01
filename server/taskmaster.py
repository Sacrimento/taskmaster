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
            level=logging.DEBUG,  # TODO change this to info
        )
        self._conf.logger = self.logger

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((HOST, PORT))
        self.socket.listen(1)
        self.conn = None

        signal.signal(signal.SIGUSR1, lambda *_: self.listen())
        signal.signal(signal.SIGINT, lambda *_: exit(0))
        signal.signal(signal.SIGHUP, lambda *_: self.update_conf())
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
            exit(1)
            return

        ret = getattr(self, s[0])(' '.join(s[1:]) if len(s) > 1 else [None])
        send(self.conn, ret)

    def update_tasks(self, changes, first=False):
        print(changes)
        for todo in ('stop', '_del', 'start'):
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

    def check_start_retry(self, name, status, conf):
        if status['retries'] > conf.get('startretries', 128):
            return status
        if conf.get('autorestart', '') == 'never':
            return status
        status['retries'] += 1
        return self._start(name, status)

    def _del(self, name):
        if not name or name not in self._processes:
            self.logger.warning('%s: unknown process name', name)
            return

        for i in range(len(self._processes[name])):
            if self._processes[name][i]['status'] in ('started', 'running'):
                self.kill(self._processes[name][i], signal.SIGKILL)

        del self._processes[name]

    def check_processes(self):
        now = datetime.now()
        processes_copy = {**self._processes}
        for proc_name, stat in processes_copy.items():
            for i, status in enumerate(stat):
                conf = self._conf.get(proc_name, None)
                if not conf:
                    continue
                running = status['process'].poll() is None
                if (status['status'] == 'stopped'
                     and status['stop_time'] - now > timedelta(0, conf.get('stop_time', 0))
                     and running):
                        status = self.kill(status, signal.SIGKILL)

                if running:
                    if timedelta(0, conf.get('starttime', 0)) + status['start_date'] < now: # process is running properly
                        status['status'] = 'running'
                else:
                    if status['status'] not in ('exited', 'stopped'):
                        self.logger.info('%s exited !', proc_name)
                        status['status'] = 'exited'
                    if (conf.get('autorestart', '') == 'unexpected'
                        and status['status'] == 'exited'
                        and status['process'].returncode not in conf.get('exitcodes', [])):
                        status = self.check_start_retry(proc_name, status, conf)
                    if (conf.get('autorestart', '') == 'always'
                        and status['status'] in ('exited', 'stopped')):
                        status = self.check_start_retry(proc_name, status, conf)

    def has_conf_changed(self):
        return self._conf.has_changed()

    def initchildproc(self, name):
        os.setpgrp()
        umask = int(self._conf[name].get('umask', 777))

        os.umask(umask)
        os.chdir(self._conf[name].get('workingdir', os.getcwd()))

    def _get_io(self, io_name, current_state):
        selected_io = current_state.get(io_name, '/dev/' + io_name)
        if selected_io == "-":
            return open("/dev/null", 'w')
        return open(selected_io, 'w')

    def _start(self, name, status):
        current_state = self._conf[name]
        env = {**os.environ.copy(), **{str(k): str(v) for k, v in current_state.get('env', {}).items()}}

        with self._get_io("stdout", current_state) as stdout, self._get_io("stderr", current_state) as stderr:
            process = subprocess.Popen(
                shlex.split(current_state['cmd']),
                stdout=stdout,
                stderr=stderr,
                env=env,
                preexec_fn=lambda: self.initchildproc(name)
            )

        self.logger.info('%s started !', name)
        return {
            'retries': status.get('retries', 0),
            'process': process,
            'start_date': datetime.now(),
            'status': 'started'
        }

    def start(self, name):
        if self._handle_bad_name(name):
            return '%s: unknown process name' % name
        ret = ""
        status = self._processes.get(name, [])

        for i in range(self._conf[name].get('numprocs', 1)):
            if len(status) > i and status[i].get('status', '') in ('started', 'running'):
                ret += '%s numproc[%d]: process alreay running' % (name, i)
                continue
            elem = status[i] if len(status) > i else {}
            try:
                status.insert(i, self._start(name, elem))
            except (IOError, subprocess.SubprocessError): # bad stderr stdout or umask
                self.logger.info('Invalid Value for uname in: %s', name)

        self._processes[name] = status
        return ret + '%s successfully started' % name

    def kill(self, status, signal):
        os.kill(status['process'].pid, signal)
        status['stop_time'] = datetime.now()
        status['status'] = 'stopped'
        return status

    def stop(self, name):
        if self._handle_bad_name(name):
            return '%s: unknown process name' % name
        if name not in self._processes:
            return '%s already stopped' % name

        ret = ""
        sign = getattr(signal, 'SIG' + self._conf[name].get('stopsignal', 'TERM').upper(), "SIGTERM")
        for i, proc in enumerate(self._processes[name]):
            if proc.get('status', '') in ('started', 'running'):
                ret += '%s numproc[%d]: process alreay stopped' % (name, i)
            try:
                self._processes[name][i] = self.kill(proc, sign)
            except OSError:
                self.logger.warning('Process %s already exited', name)
                return ret + 'process %s already exited' % name

        self.logger.info('%s stopped !', name)
        return ret + '%s successfully stopped' % name

    def restart(self, name):
        self.stop(name)
        return self.start(name)

    def status(self, _):
        out = ''
        for proc_name, status in self._processes.items():
            out += '\n%s (%s):\n' % (proc_name, self._conf[proc_name]['cmd'])
            for proc in status:
                out += '  status: %s' % proc['status']
                if proc['status'] in ('exited', 'stopped'):
                    out += ' (%d)' % proc['process'].returncode
                else:
                    out += '\n  started at: %s' % proc['start_date'].strftime('%d/%m/%Y, %H:%M:%S')
        return out

    def _handle_bad_name(self, name):
        if not name:
            return True
        if name not in self._conf:
            self.logger.warning('%s: unknown process name', name)
            return True
