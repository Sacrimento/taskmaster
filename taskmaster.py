#!/usr/bin/python3

import sys

from conf import Conf
from repl import Repl

conf = Conf('conf.yml')

Repl(conf).run()