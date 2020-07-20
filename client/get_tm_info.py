import os

def get_tm_pid(lock_file):
    if os.path.isfile(lock_file):
        with open(lock_file, 'r') as f:
            return int(f.read())

def is_tm_running(lock_file):
    return os.path.isfile(lock_file)
