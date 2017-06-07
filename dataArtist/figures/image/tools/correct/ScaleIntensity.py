# coding=utf-8
import numpy as np


from dataArtist.widgets.Tool import Tool


def equalizeImage(img):
    # i am not sure whether i should keep that function in here...
    # to speed up import keep this fn extra.
    from imgProcessor.transform.equalizeImage import equalizeImage as E
    return E(img)


class ScaleIntensity(Tool):
    '''
    Equalize the histogram (contrast) of all given images
    '''
    icon = 'equalize.svg'

    def __init__(self, imageDisplay):
        from imgProcessor.imgSignal import scaleSignal, scaleSignalCut

        Tool.__init__(self, imageDisplay)

        self._refImg = None

        pa = self.setParameterMenu()

        self._methods = {
            # NAME: (FUNCTION, HISTOGRAM LEVELS)
            'Reference image':
            (lambda x: scaleSignal(x, reference=self._refImg), None),
            '% CDF':
            (lambda x: scaleSignalCut(x, self.pRatio.value() / 100), [0, 1]),
            'Equalize histogram':
                (equalizeImage, None),
            'Scale Hist. Background-Signal: 0-1':
                (lambda x: scaleSignal(x, backgroundToZero=True), [0, 1]),
            'Scale Hist. signal +/-3std':
                (scaleSignal, [0, 1]),
            'Maximum=1':
                (lambda img: img / np.nanmax(img), [0, 1]),
            'Average=1':
                (lambda img: img / np.nanmean(img), [-1, 2]),
            'Minimum=0, Maximum=1':
                (self._scaleMinMax, [0, 1]),
        }

        self.pMethod = pa.addChild({
            'name': 'Method',
            'type': 'list',
            'value': 'Average=1',
            'limits': list(self._methods.keys())})

        self.pRefImgChoose = self.pMethod.addChild({
            'name': 'Reference image',
            'value': 'From display',
            'type': 'menu',
            'visible': False})
        self.pRefImg = self.pRefImgChoose.addChild({
            'name': 'Chosen',
            'value': '-',
            'type': 'str',
            'readonly': True})

        self.pRefImgChoose.aboutToShow.connect(lambda menu:
                                               self.buildOtherDisplayLayersMenu(menu, self._setRefImg))

        self.pMethod.sigValueChanged.connect(
            lambda p, v: self.pRefImgChoose.show(v == 'Reference image'))

        self.pRatio = self.pMethod.addChild({
            'name': 'Percentage',
            'value': 2,
            'type': 'float',
            'limits': [0.05, 100],
            'visible': False})

        self.pMethod.sigValueChanged.connect(
            lambda p, v: self.pRatio.show(v == '% CDF'))

    def _setRefImg(self, display, layernumber, layername):
        '''
        extract the reference image and -name from a
        given display and layer number
        '''
        im = display.widget.image
        self._refImg = im[layernumber]
        self.pRefImg.setValue(layername)

    @staticmethod
    def _scaleMinMax(img):
        mn, mx = img.min(), img.max()
        return (img - mn) / (mx - mn)

    def activate(self):
        img = self.display.widget.image

        fn, levels = self._methods[self.pMethod.value()]
        # APPLY FOR EACH LAYER:
        for n, i in enumerate(img):
            try:
                out = fn(i)
                if isinstance(out, np.ndarray):
                    img[n] = out
            except Exception as err:
                print("couldn't scale image: %s" % err)
        self.display.changeLayer(img, 'Normalized', levels=levels)
