import pyqtgraph_karl as pg
import numpy as np

from imgProcessor.utils.gridLinesFromVertices import gridLinesFromVertices


from .QuadROI import QuadROI
from imgProcessor.array.subCell2D import subCell2DFnArray

from imgProcessor.transform.rmBorder import rmBorder


class PerspectiveGridROI(QuadROI):

    def __init__(self, nCells=(3, 4), **kwargs):
        self.nCells = list(nCells)
        QuadROI.__init__(self, **kwargs)

    def paint(self, p, opt, widget):
        super().paint(p, opt, widget)

        p.setRenderHints(p.Antialiasing, True)
        p.setPen(self.currentPen)

        # generate grid lines:
        h, v = gridLinesFromVertices(self.vertices(), self.nCells)[:2]

        # draw grid lines:
        for lines in (h, v):
            for line in lines:
                h1, h2 = line[0], line[-1]
                p.drawLine(pg.Point(h1[0], h1[1]), pg.Point(h2[0], h2[1]))

    def vertices(self):
        return np.array([h['item'].pos() for h in self.handles])

    def setVertices(self, vertices):
        # show found ROI:
        for h, c in zip(self.handles, vertices):
            pos = c[::-1] - self.pos()
            h['item'].setPos(pos[1], pos[0])
            h['pos'] = h['item'].pos()

    def cellAverages(self, img, fn=np.mean):
        '''
        return an array of shape .ncells
        where every cell contains the average of every grid cell
        '''
        cimg = rmBorder(img, self.vertices())
        return subCell2DFnArray(cimg, fn, self.nCells[::-1])
