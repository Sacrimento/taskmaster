#!/usr/bin/env python3

import argparse
from repl import Repl

DEFAULT_LOCK_FILE='/tmp/taskmaster.lock'

parser = argparse.ArgumentParser()
parser.add_argument('-l', '--lockfile', help='The lock file to use', default=DEFAULT_LOCK_FILE)

args = parser.parse_args()

Repl(args.lockfile).run()
