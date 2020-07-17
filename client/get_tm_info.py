import os

LOCK_PATH = '../server/taskmaster.lock'

def get_tm_pid():
    if os.path.isfile(LOCK_PATH):
        with open(LOCK_PATH, 'r') as f:
            return int(f.read())

def is_tm_running():
    return os.path.isfile(LOCK_PATH)
