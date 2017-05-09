from dataArtist.widgets.Tool import Tool
from imgProcessor.measure.SNR.SNR import SNR
from imgProcessor.measure.SNR.SNRaverage import SNRaverage
from imgProcessor.transformations import toGray, isColor


class MinimumExposureTime(Tool):
    '''
    Determine shortest exposure time [s]
    to ensure image quality is above quality standard 
    as defined by IEC TS 60904-13
    ##
    Conduct averaged signal-to-noise ratio (SNR) measurement
    using one EL image
    '''
    icon = 'bestExposureTime.svg'

    def __init__(self, display):
        Tool.__init__(self, display)

        self.SNR_LIMITS = (('Lab', 45),
                           ('Industrial', 15),
                           ('Outdoor', 5)
                           )

        pa = self.setParameterMenu()

        self.pTime = pa.addChild({
            'name': 'Current exposure time [s]',
            'type': 'float',
            'value': 0})

        l = []
        for s, li in self.SNR_LIMITS:
            l.append('%s  (SNR>=%s)' % (s, li))

        self.pOpt = pa.addChild({
            'name': 'Image quality',
            'type': 'list',
            'value': l[0],
            'limits': l})

    def activate(self):
        self.startThread(self._process, self._done)

    def _process(self):
        img = self.display.widget.image[-1]
        if isColor(img):
            img = toGray(img)
        avg = SNRaverage(SNR(img))
        i = self.pOpt.opts['limits'].index(self.pOpt.value())
        limit = self.SNR_LIMITS[i][1]
        fac = limit / avg
        return fac

    def _done(self, fac):
        time = self.pTime.value()
        if time == 0:
            print('Exposure time should be %.3f times longer' % fac)
        else:
            print('Minimum exposure time = %.3f s' % (time * fac))
