import subprocess
import sys

class Taskmaster:
    _processes = {}

    def __init__(self, conf):
        self._conf = conf
        self.update_conf(False)

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

    def start(self, name):
        print('starting:', name) 
        if self._handle_bad_name(name):
            return
        current_state = self._conf[name]
        with open(current_state['stdout'], 'w') if 'stdout' in current_state else sys.stdout as stdout, open(current_state['stderr'], 'w') if 'stderr' in current_state else sys.stderr as stderr:
            process = subprocess.Popen(current_state['cmd'].split(' '),
                    stdout=stdout,
                    stderr=stderr)
            print(name, 'started')
        self._processes[name] = process

    def stop(self, name):
        print('stoping:', name) 
        if self._handle_bad_name(name):
            return
        stop_signal = self.conf['stopsignal'] if 'stopsignal' in self._conf else "TERM"
        os.killpg(os.getpgid(self._processes[name].pid), getattr(signal, stop_signal))
        print(name, 'stopped')

    def status(self):
        pass

    def _handle_bad_name(self, name):
        if not name:
            return True
        if name not in self._conf:
            print('[Taskmaster] "'+ name +'": unknown process name')
            return True
