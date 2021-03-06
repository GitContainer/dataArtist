# coding=utf-8
from builtins import str
from builtins import range
import numpy as np
from dataArtist.widgets.Tool import Tool


class ToPlot(Tool):
    '''
    Show the content of this image as mutliple plots
    '''
    icon = 'toPlot.svg'
    reinit = True

    def __init__(self, imageDisplay):
        Tool.__init__(self, imageDisplay)

        pa = self.setParameterMenu()

        self.pMax = pa.addChild({
            'name': 'Max plots',
                    'value': 20,
                    'type': 'int',
                    'min': 0})

    def activate(self):
        d = self.display
        _, s1, s2 = d.widget.image.shape

        x = np.arange(s2)
        if self.pMax.value() < s1:
            y = np.linspace(0, s1 - 1, self.pMax.value(), dtype=int)
        else:
            y = range(s1)

        names = [str(val) for val in y]

        for n, im in enumerate(d.widget.image):
            vals = [(x, im[i]) for i in y]

            d = self.display.workspace.addDisplay(
                axes=2,
                names=names,
                data=vals,
                title='Plot view of image %s for display (%s)' % (n, d.number))
