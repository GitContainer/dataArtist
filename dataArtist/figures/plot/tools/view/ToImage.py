# coding=utf-8
import numpy as np
from dataArtist.widgets.Tool import Tool
from fancytools.math.avgMultiplePlots import bringPlotOverSameX


class ToImage(Tool):
    '''
    Show the content of all plots as image
    '''
    icon = 'toImage.svg'
    reinit = True

    def __init__(self, imageDisplay):
        Tool.__init__(self, imageDisplay)

    def activate(self):
        d = self.display
        data = d.widget.data

        # check whether all x values are the same:
        same_x = True
        x0 = data[0].x
        for plot in data[1:]:
            if not np.allclose(plot.x, x0):
                same_x = False
                break

        if not same_x:
            x0, img = bringPlotOverSameX(data)
        else:
            img = np.empty(shape=(len(data), len(x0)),
                           dtype=data[0].y.dtype)
            for n, dd in enumerate(data):
                img[n] = dd.y

        self.display.workspace.addDisplay(
            axes=3,
            data=[img],
            title='Image view of display (%s)' % d.number)
