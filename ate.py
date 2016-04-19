#! /usr/bin/python
from ipywidgets import FloatProgress
from IPython import display
import numpy as np
import math
from PIL import Image
from cStringIO import StringIO
from matplotlib.pyplot import imshow
from io import BytesIO
import matplotlib.pyplot as plt

def to_db(v):
        return 20 * np.log10(np.abs(v))

def display_pil_image(im):
    """Displayhook function for PIL Images, rendered as PNG."""

    b = BytesIO()
    im.save(b, format='png')
    data = b.getvalue()

    ip_img = display.Image(data=data, format='png', embed=True)
    return ip_img._repr_png_()

# register display func with PNG formatter:
png_formatter = get_ipython().display_formatter.formatters['image/png']
dpi = png_formatter.for_type(Image.Image, display_pil_image)

import bg7tbl
import tek11801
import networkanalyzer
import sockwrapper
import time

from bg7tbl import Bg7tbl
from tek11801 import Tek11801
from networkanalyzer import NetworkAnalyzer
from sockwrapper import SockWrapper

def create():
    print "Initializing"

    global source
    global meter
    global na

    if 'source' in globals():
        source.close()
        del source

    if 'meter' in globals():
        meter.close()
        del meter

    if 'na' in globals():
        del na

    reload(bg7tbl)
    reload(tek11801)
    reload(networkanalyzer)
    reload(sockwrapper)

    time.sleep(2)

    source = Bg7tbl(SockWrapper(('localhost', 4715)))
    meter = Tek11801(SockWrapper(('localhost', 4713)))
    meter.init_freq_power('M5')

    na = NetworkAnalyzer(source, meter)

    print "Running"

create()

def set_freq(freq):
    source.set_freq(freq)

def set_tb(t):
    meter.set_tb(t)

def screenshot():
    progress = FloatProgress(min = 0, max = meter.expected_screenshot_size)
    display.display(progress)

    meter.cmd('ABSTOUCH %u,%u' % (0, 0))

    a = [ 0 ]
    def cb(data, a = a, progress = progress):
        if data is None:
            return
        a[0] += len(data)
        progress.value = a[0]

    image = meter.copy_pil(cb)

    progress.close()

    if 0:
        f = open('foo.png', 'wb')
        image.save(f, format = 'png')
        f.close()

    return image

def sweep(start, end, nr_points):
    progress = FloatProgress(min = 0, max = nr_points)
    display.display(progress)

    a = [ 0 ]
    def cb(mfreq, mpower, a = a, progress = progress):
        a[0] += 1
        progress.value = a[0]

    freqs = np.logspace(math.log10(start), math.log10(end), nr_points)
    mfreqs, mpowers = na.sweep(freqs, cb = cb)

    progress.close()
    plt.semilogx()
    plt.grid(True)
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Power (dBm)")
    plt.plot(mfreqs, to_db(mpowers))
    # return mfreqs, mpowers
