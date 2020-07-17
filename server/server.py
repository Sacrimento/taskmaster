import os
import argparse
from conf import Conf
from taskmaster import Taskmaster


def check_yml(param):
    _, ext = os.path.splitext(param)
    if ext.lower() not in ('.yml', '.yaml'):
        raise argparse.ArgumentTypeError('The configuration file should be a .yml file')
    return param

parser = argparse.ArgumentParser()
parser.add_argument('-r', '--auto-reload', help='Automatically reload the configuration file', action='store_true')
parser.add_argument('-f', '--file', help='The configuration file to use (default is "taskmaster.yml")', default='taskmaster.yml', type=check_yml)
parser.add_argument('-o', '--output', help='', default='taskmaster.log')

args = parser.parse_args()

Taskmaster(Conf(args.file)).run()
