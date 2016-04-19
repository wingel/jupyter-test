#! /usr/bin/python
import time
import numpy
from matcher import Matcher
import re
import math
import cmath
from PIL import Image
from cStringIO import StringIO

print __name__

def u_db(values):
    return 20 * numpy.log10(abs(values))

class Tek11801(object):
    screenres = 552, 704
    touchres = 11,22

    expected_screenshot_size = (screenres[0] * screenres[1]) / 2 + 800

    def __init__(self, f):
        self.f = f
        self.timing = False
        self.mode = None
        self.verbose = 0

        self.failures = 0

        time.sleep(2)

        self.resp_matcher = Matcher(r'''
        ((?P<key>[A-Z0-9/.]+):)?
        (?P<value>
            ("[^"]*")
            |
            ([^,]*)
        )
        ''', re.VERBOSE)

        self.sfr_sma_matcher = Matcher('SFREQUENCY (?P<freq>[-+.0-9E]+),EQ;' +
                                       'SMAGNITUDE (?P<mag>[-+.0-9E]+),EQ')

        self.init()

    def close(self):
        if self.f:
            self.f.close()
        self.f = None

    def junk(self):
        self.f.settimeout(0.1)
        while 1:
            d = self.f.readline()
            if not d:
                break
            if self.verbose >= 2:
                print 'junk', repr(d)

    def cmd(self, cmd):
        self.junk()
        if self.verbose >= 1:
            print 'cmd', repr(cmd)
        if self.timing:
            self.t0 = time.time()
        self.f.write(cmd + '\r')
        self.f.flush()

    def query(self, query, timeout = 1.0):
        self.cmd(query)
        self.f.settimeout(timeout)
        while 1:
            resp = self.f.readline()
            if self.verbose >= 1:
                print 'resp', repr(resp)
            if not resp:
                break

            resp = resp.rstrip()
            if resp and resp != '\xff':
                break

        if self.timing:
            self.t1 = time.time()
            self.elapsed = self.t1 - self.t0
            print 'elapsed', self.elapsed

        return resp

    def init(self):
        self.f.settimeout(1.0)
        while 1:
            d = self.f.read()
            if not d:
                break
            if self.verbose >= 2:
                print 'junk', repr(d)

        self.avg = 0

        self.id = self.query('ID?')
        assert self.id.startswith('ID TEK/11801')
        # self.cmd('BITMAP DATAFORMAT:TIFF,DATACOMPRESS:OFF,DIR:HORIZ,FORMAT:SCREEN')
        self.cmd('BITMAP DATAFORMAT:TIFF,DATACOMPRESS:OFF,DIR:VERT,FORMAT:SCREEN')

    def set_avg(self, avg):
        self.avg = avg
        self.cmd('NAVG %u' % self.avg)

    def copy(self, cb = None):
        self.cmd('COPY')
        if self.timing:
            self.t0 = time.time()
        self.f.settimeout(3.0)
        data = ''
        while 1:
            d = self.f.read(1024)
            if cb:
                cb(d)
            if not d:
                break
            data += d
            if len(data) > 1024:
                self.f.settimeout(1.0)

        if self.timing:
            self.t1 = time.time()
            self.elapsed = self.t1 - self.t0
            print 'elapsed', self.elapsed

        assert data[-5:] == '\r\r\n\r\n'
        data = data[:-5]

        return data

    def copy_pil(self, cb = None):
        data = self.copy(cb)

        f = StringIO(data)
        image = Image.open(f)
        image = image.rotate(90, expand = 1)

        return image

    def vpcurve(self):
        resp = self.query('WFMPRE?;VPCURVE?')

        curves = resp.split(';')

        for curve in curves[:3]:
            print curve

    def init_freq_mag(self, local = True, scope = True):
        self.scope = scope

        self.cmd('REMOVE ALLTRACE')
        if self.scope:
            self.cmd('DISPLAY GRATICULE:DUAL')
        else:
            self.cmd('DISPLAY GRATICULE:SINGLE')

        if 1:
            self.cmd('DISPLAY TYPE:NORMAL')
        else:
            self.cmd('DISPLAY TYPE:VARIABLE')
            self.cmd('DISPLAY PERSISTENCE:0.3')

        if self.avg:
            self.cmd('NAVG %u' % self.avg)
            self.cmd('TRACE1 DESCRIPTION:"AVG(M5)",WFMCALC:FAST')
            if self.scope:
                self.cmd('TRACE2 DESCRIPTION:"FFTMAG(AVG(M5))",WFMCALC:HIPREC')
        else:
            self.cmd('TRACE1 DESCRIPTION:"M5",WFMCALC:FAST')
            if self.scope:
                self.cmd('TRACE2 DESCRIPTION:"FFTMAG(M5)",WFMCALC:HIPREC')

        self.cmd('ADJTRACE1 PANZOOM:OFF,GRLOCATION:UPPER,COLOR:1')
        if self.scope:
            self.cmd('ADJTRACE2 PANZOOM:OFF,GRLOCATION:LOWER,COLOR:2,VPOSITION:-5.0E+1,VSIZE:1.0E+1')

        time.sleep(3)

    def set_tb(self, tb):
        self.cmd('TBMAIN TIME:%.6g' % tb)

    def set_span(self, freq, l = 512):
        span = 1.33 * freq
        t = 25.0 * 500.0 / span * l / 512 / 512
        self.cmd('TBMAIN LENGTH:%u,TIME:%.6g' % (l, t))

    def parse_resp(self, s):
        a = []
        i = 0

        while 1:
            # print i, s[i:]
            j = s.index(' ', i)
            name = s[i:j]
            i = j + 1
            a2 = []
            while 1:
                match = self.resp_matcher.match(s, i)
                if not match:
                    break
                j = self.resp_matcher.end()
                # print i, s[i:j]
                i = j
                if s[i:i+1] != ',':
                    break
                i += 1
                key, value = self.resp_matcher.group('key', 'value')
                if value.startswith('"'):
                    assert value.endswith('"')
                    value = value[1:-1]
                if key:
                    a2.append((key, value))
                else:
                    a2.append(value)

            a.append((name, a2))

            if s[i:i+1] != ';':
                break
            i += 1

        assert i == len(s)
        # if i != len(s):
        #    print left, s[i:]

        return a

    def capture(self):
        if self.avg:
            self.cmd('CONDACQ TYPE:AVG')
        else:
            self.cmd('CONDACQ TYPE:RECORD')
        self.cmd('CONDACQ WAIT')


    def get_waveform(self, trace, *args, **kwargs):
        s = self.query('OUTPUT %s; WAV?' % trace, *args, **kwargs)

        a = self.parse_resp(s)

        assert a[0][0] == 'WFMPRE'
        wfmpre = dict(a[0][1])
        assert wfmpre['WFID'] == trace

        assert a[1][0] == 'CURVE'
        assert a[1][1][0] == ('CRVID', trace)

        samples = numpy.array(a[1][1][1:])
        samples = samples.astype(numpy.float)
        samples = samples * float(wfmpre['YMULT'])
        samples = samples + float(wfmpre['YZERO'])

        sample_start = float(wfmpre['XZERO'])
        sample_spacing = float(wfmpre['XINCR'])

        return samples, sample_start, sample_spacing

    def fft(self, samples, spacing):
        # samples = samples * scipy.signal.blackmanharris(len(samples), False)

        freqs = numpy.fft.rfftfreq(len(samples), spacing)
        fft = numpy.fft.rfft(samples)

        return freqs, fft

    def find_peak(self, freqs, values):
        if 1:
            # Noisy signals have a lot of energy in the lowest
            # and highest frequencies so skip those.
            i = numpy.argmax(abs(values[10:-10])) + 10
        else:
            i = numpy.argmax(abs(values))
        freq = freqs[i]

        # Bin spacing
        spacing = freqs[1] - freqs[0]

        # Two algorithms for improving the frequency estimate for a
        # peak in a FFT from "On Local Interpolation of DFT Outputs"
        # by Eric Jacobsen, EF Data Corporation, EDICS 3.1.1.  Do not
        # apply any windowing on the FFT, it will not work well.
        if 1:
            # Jacobsen
            if self.verbose >= 2:
                print values[i-1:i+1+1]
            fadj = ((values[i-1] - values[i+1]) /
                   (2*values[i] - values[i-1] - values[i+1])).real
        else:
            # Quinn
            if self.verbose >= 2:
                print values[i-1:i+1+1]
            a1 = (values[i-1] / values[i]).real
            A2 = (values[i+1] / values[i]).real

            d1 = a1 / (1 - a1)
            d2 = -a2 / (1 - a2)

            if d1 > 0 and d2 > 0:
                fadj = d2
            else:
                fadj = d1

        freq += fadj * spacing

        # Algorithm for improving magnitude estimate from a FFT
        # https://www.dsprelated.com/showarticle/155.php
        value = values[i]
        value -= 0.94247 * (values[i-1] + values[i+1])
        value += 0.44247 * (values[i-2] + values[i+2])

        return freq, value

    def get_freq_mag(self, trace = None):
        if self.scope:
            return self.get_freq_mag_scope(trace)
        else:
            return self.get_freq_mag_local(trace)

    def get_freq_mag_local(self, trace = None):
        if trace == None:
            trace = 'TRACE1'

        self.samples, self.samples_start, self.samples_spacing = self.get_waveform(trace, timeout = 5.0)
        self.fft_freqs, values = self.fft(self.samples, self.samples_spacing)

        ofs = 10 - u_db(len(values))
        self.fft_mags = u_db(abs(values)) + ofs

        freq, value = self.find_peak(self.fft_freqs, values)

        mag, phase = cmath.polar(value)
        mag = u_db(mag) + ofs

        return freq, mag, phase

    def get_freq_mag_scope(self, trace = None):
        if trace == None:
            trace = 'TRACE2'

        for i in range(5):
            resp = self.query('OUTPUT %s; SFR?;SMA?' % trace, timeout = 3.0)
            if self.sfr_sma_matcher.match(resp):
                break

        else:
            return 0.0, 0.0

        freq = float(self.sfr_sma_matcher.group('freq'))
        mag = float(self.sfr_sma_matcher.group('mag'))

        return freq, mag

    def init_freq_power(self, channel):
        self.channel = channel
        self.trace = 'TRACE1'

        self.cmd('REMOVE ALLTRACE')

        self.cmd('DISPLAY GRATICULE:SINGLE')
        self.cmd('DISPLAY TYPE:NORMAL')

        self.cmd('%s DESCRIPTION:"%s",WFMCALC:FAST' % (
            self.trace, self.channel))
        self.cmd('ADJ%s PANZOOM:OFF,GRLOCATION:UPPER,COLOR:1' % self.trace)

        # TODO should set the vertical scale to something suitable

    def measure_freq_power(self, freq):
        self.set_span(1.0 * freq)
        self.capture()

        samples, sstart, sspacing = self.get_waveform(self.trace, timeout = 5.0)
        fft_freqs, fft_powers = self.fft(samples, sspacing)
        fft_powers *= 10 ** 0.5
        fft_powers /= len(fft_powers)
        mfreq, mpower = self.find_peak(fft_freqs, fft_powers)

        return mfreq, mpower
