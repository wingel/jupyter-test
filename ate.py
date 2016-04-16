#! /usr/bin/python
from ipywidgets import FloatProgress
from IPython import display
import numpy as np
import math

import bg7tbl
import tek11803
import networkanalyzer
import sockwrapper
import time

from bg7tbl import Bg7tbl
from tek11803 import Tek11803
from networkanalyzer import NetworkAnalyzer
from sockwrapper import SockWrapper

print __name__

def create():
    global source
    global meter
    global na

    if 'source' in globals():
        source.close()
        del source

    if 'meter' in globals():
        meter.close()
        del meter

    reload(bg7tbl)
    reload(tek11803)
    reload(networkanalyzer)
    reload(sockwrapper)

    time.sleep(2)

    print "Initializing"

    source = Bg7tbl(SockWrapper(('localhost', 4715)))
    meter = Tek11803(SockWrapper(('localhost', 4713)))
    meter.init_freq_power('M5')

    na = NetworkAnalyzer(source, meter)

    print "Running"

def sweep(start, end, nr_points):
    f = FloatProgress(min = 0, max = nr_points)
    display.display(f)

    a = []

    def cb(mfreq, mpower, a = a, f = f):
        a.append((mfreq, mpower))
        f.value = len(a)

    freqs = np.logspace(math.log10(start), math.log10(end), nr_points)
    mfreqs, mpowers = na.sweep(freqs, cb = cb)

    f.close()

    return mfreqs, mpowers
