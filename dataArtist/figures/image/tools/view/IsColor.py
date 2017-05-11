# coding=utf-8
import numpy as np

from dataArtist.widgets.Tool import Tool

from imgProcessor.transformations import isColor, toColor, toGray,\
    rgChromaticity, monochromaticWavelength


class IsColor(Tool):
    '''
    Indicate whether image is color
    activate: transform image to color image
    deactivate: transform image to grayscale image
    '''
    icon = 'isColor.svg'

    def __init__(self, display):
        Tool.__init__(self, display)

        display.sigLayerChanged.connect(self._check)
        display.sigNewLayer.connect(self._check)

        pa = self.setParameterMenu()

        pa.addChild({
            'name': 'Separate color channels',
            'type': 'action'}).sigActivated.connect(self.separate)

        pa.addChild({
            'name': 'RG chromaticity',
            'type': 'action',
            'tip': rgChromaticity.__doc__}).sigActivated.connect(
                self._chromaticity)

        pa.addChild({
            'name': 'Monochromatic wavelength',
            'type': 'action',
            'tip': monochromaticWavelength.__doc__}).sigActivated.connect(
                self._monochromaticWavelength)

        self.createResultInDisplayParam(pa, value='[ALLWAYS NEW]')

        self._check()

    def _check(self):
        i = self.display.widget.image
        if i is not None:
            self.setChecked(isColor(i))

    def separate(self):
        i = self.display.widget.image
        assert isColor(i), 'Only works on color images'
        out = np.transpose(i, axes=(3, 0, 1, 2))
        self.handleOutput(out, title='Color channels separated',
                          names=['red', 'green', 'blue'])

    def _chromaticity(self):
        i = self.display.widget.image
        assert isColor(i), 'Only works on color images'
        out = np.empty_like(i)
        for n, im in enumerate(i):
            out[n] = rgChromaticity(im)
        self.handleOutput(out, title='RG chromacity')

    def _monochromaticWavelength(self):
        i = self.display.widget.image
        assert isColor(i), 'Only works on color images'
        out = np.empty(shape=i.shape[:-1])
        for n, im in enumerate(i):
            out[n] = monochromaticWavelength(im)
        self.handleOutput(out, title='monochromatic wavelength',
                          axes=('x', 'y', 'wavelength [nm]'))

    def activate(self):
        w = self.display.widget
        w.setImage(toColor(w.image))

    def deactivate(self):
        w = self.display.widget
        w.setImage(toGray(w.image))
