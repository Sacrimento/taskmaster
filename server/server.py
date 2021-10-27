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
parser.add_argument('-f', '--file', help='The configuration file to use', default='/tmp/taskmaster.yml', type=check_yml)
parser.add_argument('-l', '--logfile', help='The log file to use', default='taskmaster.log')

args = parser.parse_args()

Taskmaster(Conf(args.file), args.logfile, DEFAULT_LOCK_FILE, args.port).run()
