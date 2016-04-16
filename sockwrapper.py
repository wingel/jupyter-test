#! /usr/bin/python
import socket

class SockWrapper(object):
    def __init__(self, spec):
        self.sock = socket.socket()
        self.sock.connect(spec)
        self.data = ''
        self.sock.settimeout(1.0)

    def settimeout(self, timeout):
        self.sock.settimeout(timeout)

    def fill(self, count):
        try:
            d = self.sock.recv(1024)
            self.data += d
            # print 'd', repr(d)
            # print 'data', repr(self.data)
            return d
        except socket.timeout:
            return None

    def read(self, count = 1024):
        if not self.data:
            if self.fill(count) is None:
                return None

        d = self.data[:count]
        self.data = self.data[count:]
        # print 'r2', repr(d)
        return d

    def readline(self):
        while 1:
            i = self.data.find('\n')
            if i != -1:
                i += 1
                break
            if not self.fill(1024):
                i = len(self.data)
                break

        d = self.data[:i]
        self.data = self.data[i:]
        return d

    def write(self, s):
        self.sock.send(s)

    def flush(self):
        pass
