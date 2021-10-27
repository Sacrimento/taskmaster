#!/usr/bin/env python3

import argparse
from repl import Repl
from tm_socket import PORT, HOST

DEFAULT_LOCK_FILE='/tmp/taskmaster.lock'

parser = argparse.ArgumentParser()
parser.add_argument('-p', '--port', help='port', default=PORT, type=int)

args = parser.parse_args()

Repl(args.port).run()
