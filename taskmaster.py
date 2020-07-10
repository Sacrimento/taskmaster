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
        print('changes: ', changes)

    def update_conf(self, p=True):
        self.update_tasks(self._conf.populate())
        if p:
            print('[Taskmaster] Config file updated !', self._conf)

    def has_conf_changed(self):
        return self._conf.has_changed()

    def start(self, name):
        print(name)
        pass

    def stop(self, name):
        print(name)
        pass

    def status(self):
        pass

Repl(Taskmaster(conf)).run()