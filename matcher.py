#! /usr/bin/python
import re

class Matcher(object):
    _cache = {}

    def __init__(self, pattern, *args, **kwargs):
        self._match = None
        self._pattern = pattern
        key = (pattern, args, tuple(kwargs))
        try:
            self._re = self._cache[key]
        except KeyError:
            self._re = re.compile(pattern, *args, **kwargs)

    def match(self, *args, **kwargs):
        self._match = self._re.match(*args, **kwargs)
        return self._match

    def search(self, *args, **kwargs):
        self._match = self._re.search(*args, **kwargs)
        return self._match

    def __getattr__(self, attr):
        return getattr(self._match, attr)

    def __repr__(self):
        return self._pattern
