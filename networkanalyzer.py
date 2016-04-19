#! /usr/bin/python
import numpy as np
import math

print __name__

class NetworkAnalyzer(object):
    _default = None

    def __init__(self, source, meter):
        self.source = source
        self.meter = meter
        self.mismatches = 0

    def measure(self, freq):
        self.source.set_freq(freq)
        for i in range(5):
            mfreq, mpower = self.meter.measure_freq_power(freq)
            if mfreq == np.nan:
                break

            ratio = mfreq / freq
            if ratio > 0.99 and ratio < 1.01:
                return mfreq, mpower

            print "Measured frequency %.3g is too far off from generated frequency %.3g, retrying" % (freq, mfreq)
            self.mismatches += 1

        return np.nan, np.nan

    def sweep(self, freqs, cb = None):
        mfreqs = np.zeros(len(freqs))
        mpowers = np.zeros(len(freqs), np.complex)
        for i in range(len(freqs)):
            mfreqs[i], mpowers[i] = self.measure(freqs[i])
            if cb:
                cb(mfreqs[i], mpowers[i])
        return mfreqs, mpowers

    @staticmethod
    def create_default():
        global NetworkAnalyzer
        if NetworkAnalyzer._default:
            return NetworkAnalyzer._default

        from bg7tbl import Bg7tbl
        from tek11801 import Tek11801
        from networkanalyzer import NetworkAnalyzer
        from sockwrapper import SockWrapper

        source = Bg7tbl(SockWrapper(('localhost', 4715)))
        meter = Tek11801(SockWrapper(('localhost', 4713)))
        meter.init_freq_power('M5')

        na = NetworkAnalyzer(source, meter)

        NetworkAnalyzer._default = na

        return na

if __name__ == '__main__':
    na = NetworkAnalyzer.create_default()
    freqs = np.logspace(math.log10(200E6), math.log10(4E9), 101)
    mfreqs, mpowers = na.sweep(freqs)
    print mfreqs, mpowers
