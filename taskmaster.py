#!/usr/bin/python3

import sys

from conf import Conf
from repl import Repl

def load_conf():
    conf = Conf(sys.argv[1])
    print(conf['programs'])

load_conf()
Repl().run()