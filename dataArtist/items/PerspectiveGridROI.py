from qtpy import QtGui, QtCore
import pyqtgraph_karl as pg
import numpy as np
# from dataArtist.items.QPainterPath import QPainterPath

from imgProcessor.utils.gridLinesFromVertices import gridLinesFromVertices


from .QuadROI import QuadROI



class PerspectiveGridROI(QuadROI):

    def __init__(self, nCells=(3,4), **kwargs):
        self.nCells = nCells
        QuadROI.__init__(self, **kwargs)


    def paint(self, p, opt, widget):
        super().paint(p, opt, widget)

        p.setRenderHints(p.Antialiasing, True)
        p.setPen(self.currentPen)
        
        #generate grid lines:
        h, v = gridLinesFromVertices(self.edges(), self.nCells)[:2]
        
        #draw grid lines:
        for lines in (h, v):
            for line in lines:
                h1,h2 = line[0],line[-1]
                p.drawLine(pg.Point(h1[0],h1[1]), pg.Point(h2[0],h2[1]))


    def edges(self):
        return np.array([h['item'].pos() for h in self.handles])