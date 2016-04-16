#! /usr/bin/python

print __name__

class Bg7tbl(object):
    def __init__(self, f):
        self.f = f
        self.verbose = 0

    def set_freq(self, freq):
        cmd = '\x8f' + 'f%09u' % (int(round(freq / 10.0)))
        if self.verbose:
            print "bg7tbl %.0f %.3g %s" % (freq, freq, repr(cmd))
        self.f.write(cmd)
        #resp = self.f.read()
        #print resp.encode('hex')

    def close(self):
        if self.f:
            self.f.close()
        self.f = None

if __name__ == '__main__':
    import socket
    import sys
    from sockwrapper import SockWrapper

    freq = float(sys.argv[1])

    sock = socket.socket()
    sock.connect(('localhost', 4715))
    bg7tbl = Bg7tbl(SockWrapper(sock))

    bg7tbl.set_freq(freq)
