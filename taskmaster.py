#!/usr/bin/python3

import sys

from conf import Conf
from repl import Repl

conf = Conf('conf.yml')

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
        if p:
            print('[Taskmaster] Config file updated !', self._conf)
        self.update_tasks(self._conf.populate())

    def has_conf_changed(self):
        return self._conf.has_changed()

    def start(self, name):
        if not name:
            return
        print(name, 'started')

    def stop(self, name):
        if not name:
            return
        print(name, 'stopped')

    def status(self):
        pass

Repl(Taskmaster(conf)).run()