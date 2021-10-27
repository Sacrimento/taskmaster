import hashlib
import signal
import yaml
import os

def catch_conf_except(func):
    def wrapper(_self):
        if not os.path.isfile(_self.path):
            print('[Taskmaster] %s: file does not exist' % _self.path)
            exit(1)
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
        r = {'start': [], 'stop': [], '_del': []}
        key_changes = set(old) ^ set(new)
        for key in key_changes:
            r['start' if key in new else 'stop'].append(key)
            if key not in new:
                r['_del'].append(key)

        for prog, prog_attr in new.items():
            if prog not in key_changes:
                for k, v in prog_attr.items():
                    if k not in old[prog] or old[prog][k] != v:
                        r['start'].append(prog)
                        r['stop'].append(prog)
                        break
        return r

    def try_cast(self, cast, val, service_errors):
        try:
            return cast(val)
        except Exception as e:
            service_errors.append('Invalid value : value "%s" should be of type %s' % (val, cast.__name__))

    def check_invalid_value(self, program_name, programs, errors):

        if not isinstance(programs, dict):
            return errors.append('%s is not a valid task' % programs)
        service_errors = []
        dic = ["starttime", "stoptime", "startretries"]
        autorestart = ['never', 'always', 'unexpected', None]
        autorestart_with_retry = ['always', 'unexpected']

        if programs.get('cmd') is None:
            errors.append('cmd key missing')
        try:
            getattr(signal, 'SIG' + programs.get('stopsignal', 'TERM').upper())
        except AttributeError:
            service_errors.append('Invalid value for: signal')

        if programs.get("autorestart", None) not in autorestart:
            service_errors.append('autorestart must be: [%]' % autorestart.join(', '))
        startretries = self.try_cast(int, programs.get("startretries", 0), service_errors)
        if startretries is not None:
            if programs.get("startretries", 0) > 0 and programs.get("autorestart", None) not in autorestart_with_retry:
                service_errors.append('autorestart needed when startretries is given')
        numprocs = self.try_cast(int, programs.get("numprocs", 1), service_errors)
        if (numprocs is not None):
            if numprocs <= 0:
                service_errors.append('numprocs must be > 0')
        umask = self.try_cast(int, programs.get("umask", 1), service_errors)
        if (umask is not None):
            if umask < 0:
                    service_errors.append('umask must be > 0')
            if umask > 777:
                    service_errors.append('umask must be <= 777')
        if self.try_cast(dict, programs.get('env', {}), service_errors):
            for key, val in programs.get('env', {}):
                self.try_cast(str, key, service_errors)
                self.try_cast(str, val, service_errors)
        if self.try_cast(list, programs.get('exitcodes', []), service_errors):
            if isinstance(programs.get('exitcodes', []), list):
                for i in programs.get('exitcodes', []):
                    try_cast(int, i, service_errors)
        for index in dic:
            if self.try_cast(int, programs.get(index, 1), service_errors):
                if programs.get(index, 1) < 0:
                    service_errors.append(programs.get(index) + ' must be positive')
        self.try_cast(bool, programs.get('autostart', True), service_errors)
        if (service_errors):
            errors.append('[%s] Invalid properties found:' % program_name)
            errors += service_errors


    def _check_data(self, new):
        errors = []
        if not 'programs' in new:
            errors.append('"programs" root key missing')
        [self.check_invalid_value(k, v, errors) for k, v in new['programs'].items()]

        if errors:
            raise MissingData('\n'.join(errors))

    def __repr__(self):
        return repr(self._dict['programs'])

    def __iter__(self):
        return iter(self._dict['programs'])

    def __getitem__(self, item):
        return self._dict['programs'][item]

    def __delitem__(self, item):
        del self._dict[item]

    def get(self, item, default=None):
        if item in self:
            return self[item]
        return default
