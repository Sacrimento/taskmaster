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

from tm_socket import send, recv, HOST

class Taskmaster:
    _processes = {}

    def __init__(self, conf, autoreload, outfile, lock_file, port):
        self.lock_file = lock_file
        self.logger = logging.getLogger('[Taskmaster]')

        if not os.path.isfile(lock_file):
            with open(lock_file, 'w+') as f:
                f.write(str(os.getpid()))
        else:
            print('Taskmaster daemon already running')
            exit(1)

        self._conf = conf
        self.current_conf = {}
        self.current_status = {}
        self.autoreload = autoreload

        logging.basicConfig(
                filename=outfile,
                format='%(name)s %(asctime)s - %(levelname)s: %(message)s',
                datefmt='%d/%m/%Y %H:%M:%S',
                level=logging.DEBUG,  # TODO change this to info
                )
        self._conf.logger = self.logger

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((HOST, port))
        self.socket.listen(1)
        self.conn = None

        signal.signal(signal.SIGUSR1, lambda *_: self.listen())
        signal.signal(signal.SIGINT, lambda *_: exit(0))
        signal.signal(signal.SIGHUP, lambda *_: self.update_conf())
        self.logger.info('taskmaster daemon started')
        self.update_conf(False, True)

    def run(self):
        while True:
            if self.autoreload and self._conf.has_changed():
                self.update_conf()
            self.check_processes()

    def __del__(self):
        if os.path.isfile(self.lock_file):
            os.remove(self.lock_file)
        if hasattr(self, 'socket'):
            self.socket.close()
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
        processes_copy = {**self._processes}
        for proc_name, stat in processes_copy.items():
            for i, status in enumerate(stat):
                try:
                    os.kill(status['process'].pid, signal.SIGKILL)
                except:
                    continue
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

        if len(s) > 0 and s[0] == 'exit':
            send(self.conn, 'exit done')
            self.__del__()
            return

        ret = getattr(self, s[0])(' '.join(s[1:]) if len(s) > 1 else [None])
        send(self.conn, ret)

    def update_tasks(self, changes, first=False):
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
        if status['retries'] >= conf.get('startretries', 128):
            return status
        if conf.get('autorestart', '') == 'never':
            return status
        self.logger.info('Restarting %s (%s)', name, status['retries'])
        status['retries'] += 1
        return self._start(name, status)

    def _del(self, name):
        if not name or name not in self._processes:
            self.logger.warning('%s: unknown process name', name)
            return

        for elem in self._processes[name]:
            print(elem)
        exit(1)
        for i in range(len(self._processes[name])):
            if self._processes[name][i]['status'] in ('started', 'running'):
                self.kill(self._processes[name][i], signal.SIGKILL)

        del self._processes[name]

    def is_process_allowed_to_run(self, current_status, running):
        return current_status == 'stopped' and running

    def is_stop_time(self, stoptime):
        now = datetime.now()
        conf_stop_time = self.current_conf.get('stoptime', 0)
        return (now - stoptime) > timedelta(0, conf_stop_time)

    def start_date_is_done(self, start_date):
        now = datetime.now()
        conf_start_time = self.current_conf.get('starttime', 0)
        return (now - start_date) < timedelta(0, conf_start_time)

    def process_should_not_run(self, running):
        current_status = self.current_status['status']
        stoptime = self.current_status.get('stoptime', 0)
        return self.is_process_allowed_to_run(current_status, running) and self.is_stop_time(stoptime)

    def process_is_running(self, status):
        return status in ('started', 'running')

    def process_should_run(self, running):
        start_time = self.current_conf.get('starttime', 0)
        return start_time > 0 and self.process_is_running(self.current_status['status']) and not running

    def is_exit_code_known(self):
        known_codes = self.current_conf.get('exitcodes', [])
        return_code = self.current_status['process'].returncode
        # print(return_code)
        return return_code not in known_codes

    def return_code_unexpected(self):
        restart_when_unexpected = self.current_conf.get('autorestart', '') == 'unexpected'
        return restart_when_unexpected and self.current_status['status'] == 'exited' and self.is_exit_code_known()

    def process_should_never_stop_but_did(self):
        autorestart = self.current_conf.get('autorestart', '')
        return autorestart =='always' and self.current_status['status'] in ('exited')

    def check_processes(self):
        processes_copy = {**self._processes}
        for proc_name, stat in processes_copy.items():
            for i, status in enumerate(stat):
                self.current_status = status
                self.current_conf = self._conf.get(proc_name, None)

                if not self.current_conf:
                    continue
                conf = self.current_conf
                running = status['process'].poll() is None

                if self.process_should_not_run(running):
                    status = self.kill(status, signal.SIGKILL)
                    self.logger.info('%s was killed', proc_name)

                if running: continue

                if self.process_should_run(running):
                    if self.start_date_is_done(status['start_date']):
                        status = self.check_start_retry(proc_name, status, conf)
                else:
                    if status['status'] not in ('exited', 'stopped'):
                        self.logger.info('%s exited !', proc_name)
                        status['status'] = 'exited'
                    if self.return_code_unexpected() or self.process_should_never_stop_but_did():
                        if (proc_name == 'ginx'):
                            print(self.return_code_unexpected())
                        status = self.check_start_retry(proc_name, status, conf)

                self._processes[proc_name][i] = status

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
        new_process = {
                'retries': status.get('retries', 0),
                'process': process,
                'start_date': datetime.now(),
                'status': 'started'
                }
        return new_process

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
            except (IOError, subprocess.SubprocessError) as e: # bad stderr stdout or umask
                self.logger.info(e)
                self.logger.info('Command was not executed by shell for: %s', name)

        self._processes[name] = status
        return ret + '%s successfully started' % name

    def kill(self, status, signal):
        status['process'].send_signal(signal)
        status['stoptime'] = datetime.now()
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
            if proc.get('status', '') in ('exited', 'stopped'):
                ret += '%s numproc[%d]: process alreay stopped' % (name, i)
            try:
                self._processes[name][i] = self.kill(proc, sign)
            except OSError:
                self.logger.warning('Process %s already exited', name) # TODO: it crash for some obscur Reason
                return ret + 'process %s already exited' % name

        self.logger.info('%s was sent to %s ', sign, name)
        return ret + '%s was sent to %s ' % (sign, name)

    def restart(self, name):
        self.stop(name)
        return self.start(name)

    def status(self, _):
        out = ''
        for proc_name, status in self._processes.items():
            out += '\n%s (%s):\n' % (proc_name, self._conf[proc_name]['cmd'])
            for proc in status:
                out += '  status: %s' % proc['status']
                out += '\n  running: %s' % ('Yes' if proc['process'].poll() is None else 'No')
                if proc['status'] in ('started', 'running'):
                    out += '\n  started at: %s' % proc['start_date'].strftime('%d/%m/%Y, %H:%M:%S')
                elif proc['process'].returncode:
                    out += ' (%d)' % proc['process'].returncode
        return out

    def _handle_bad_name(self, name):
        if not name:
            return True
        if name not in self._conf:
            self.logger.warning('%s: unknown process name', name)
            return True
