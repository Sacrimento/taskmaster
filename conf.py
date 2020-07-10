import hashlib
import yaml

def catch_conf_except(func):
    def wrapper(_self):
        try:
            r = func(_self)
        except IOError as exc:
            print('[Taskmaster] Fatal: config file error :\n', exc)
            exit(1)
        except yaml.scanner.ScannerError as exc:
            print('[Taskmaster] Critical: config file format error :\n', exc)
            if _self._dict:
                print('[Taskmaster] Info: Last working config file will be used')
            else:
                exit(1)
        else:
            return r
    return wrapper

class Conf:

    _dict = {}
    _file_hash = None

    def __init__(self, path):
        self.path = path
        self.populate()

    @catch_conf_except
    def populate(self):
        self._file_hash = self._hash()
        with open(self.path) as file:
            self._dict.update(yaml.load(file))

    def _hash(self):
        h = hashlib.md5()

        with open(self.path, 'rb') as file:
            while True:
                buf = file.read(h.block_size)
                if not buf:
                    break
                h.update(buf)
        return h.hexdigest()

    def has_changed(self):
        return self._hash() != self._file_hash

    def __repr__(self):
        return repr(self._dict)

    def __iter__(self):
        return iter(self._dict)

    def __getitem__(self, item):
        return self._dict[item]
