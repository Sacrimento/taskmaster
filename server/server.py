#!/usr/bin/env python3

import os
import argparse
from conf import Conf
from taskmaster import Taskmaster
from tm_socket import PORT, HOST

DEFAULT_LOCK_FILE='/tmp/taskmaster.lock'

def check_yml(param):
    _, ext = os.path.splitext(param)
    if ext.lower() not in ('.yml', '.yaml'):
        raise argparse.ArgumentTypeError('The configuration file should be a .yml file')
    return param

parser = argparse.ArgumentParser()
parser.add_argument('-p', '--port', help='port', default=PORT, type=int)
parser.add_argument('-f', '--file', help='The configuration file to use (default is "taskmaster.yml")', default='taskmaster.yml', type=check_yml)
parser.add_argument('-o', '--outfile', help='The log file to use', default='taskmaster.log')
parser.add_argument('-l', '--lockfile', help='The lock file to use', default=DEFAULT_LOCK_FILE)
parser.add_argument('-m', '--mail', help='Mail address to send warnings')

args = parser.parse_args()

Taskmaster(Conf(args.file), args.outfile, args.lockfile, args.port, args.mail).run()
