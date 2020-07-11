
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
        if self._handle_bad_name(name):
            return
        print(name, 'started')

    def stop(self, name):
        if self._handle_bad_name(name):
            return
        print(name, 'stopped')

    def status(self):
        pass

    def _handle_bad_name(self, name):
        if not name:
            return True
        if name not in self._conf:
            print('[Taskmaster] "'+ name +'": unknown process name')
            return True
