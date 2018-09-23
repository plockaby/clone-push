# this is used by invoke
__version__ = '5.0'


# used to make an easy accessor to global data
class AttributeDict(dict):
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            # to conform with __getattr__ spec
            raise AttributeError(key)

    def __setattr__(self, key, value):
        self[key] = value


# modules can import "env" and get a whole bunch of stuff
env = AttributeDict()
