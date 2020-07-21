import hashlib
import yaml

def catch_conf_except(func):
    def wrapper(_self):
        try:
            r = func(_self)
        except IOError as exc:
            _self.logger.fatal('config file error :\n %s', exc)
            exit(1)
        except (yaml.scanner.ScannerError, MissingData, yaml.parser.ParserError) as exc:
            _self.logger.fatal('config file format error :\n %s', exc)
            if _self._dict:
                _self.logger.info('Last working config file will be used')
            else:
                exit(1)
        else:
            return r
    return wrapper

class MissingData(Exception):
    pass

class Conf:

    _dict = {}
    _file_hash = None

    def __init__(self, path):
        self.path = path

    @catch_conf_except
    def populate(self):
        self._file_hash = self._hash()
        with open(self.path) as file:
            new = yaml.safe_load(file)
            self._check_data(new)
            diff = self._conf_diff(new.get('programs', {}))
        self._dict.update(new)
        return diff

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

    def _conf_diff(self, new):
        old = self._dict.get('programs', {})
        r = {'start': [], 'stop': []}
        key_changes = set(old) ^ set(new)
        for key in key_changes:
            r['start' if key in new else 'stop'].append(key)
        
        for prog, prog_attr in new.items():
            if prog not in key_changes:
                for k, v in prog_attr.items():
                    if k not in old[prog] or old[prog][k] != v:
                        r['start'].append(prog)
                        r['stop'].append(prog)
                        break
        return r

    ## TODO check every *needed* option (such as 'cmd')
    def _check_data(self, new):
        errors = []
        if not 'programs' in new:
            errors.append('"programs" root key missing')
        if errors:
            raise MissingData('\n'.join(errors))

    def __repr__(self):
        return repr(self._dict['programs'])

    def __iter__(self):
        return iter(self._dict['programs'])

    def __getitem__(self, item):
        return self._dict['programs'][item]
