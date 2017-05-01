from qtpy import QtCore
import pyqtgraph_karl as pg

from dataArtist.items.QPainterPath import QPainterPath

class IsoCurveROI(pg.IsocurveItem):

    def __init__(self, *args, **kwargs):
        self.brush = kwargs.pop('brush', None)
        elements = None
        if 'elements' in kwargs:
            elements = kwargs.pop('elements')

        pg.IsocurveItem.__init__(self, *args, **kwargs)

        self.setElements(elements)

    def setData(self, data, level=None):
        if data is not None:
            if data.ndim > 2:
                raise Exception(
                    'cannot create iso lines on color image at the moment')
            pg.IsocurveItem.setData(self, data, level)

    def setElements(self, elem):
        self.path = QPainterPath()
        if elem:
            self.path.moveTo(*elem[0])
            for e in elem[1:]:
                self.path.lineTo(*e)
            self.update()

    def elements(self):
        elem = []
        for i in range(self.path.elementCount() - 1):
            e = self.path.elementAt(i)
            elem.append((e.x, e.y))
        return elem

    def painterPath(self):
        return QPainterPath(self.path)

    def paint(self, p, *args):
        if self.data is None:
            return
        if self.path is None:
            self.generatePath()
        p.setPen(self.pen)
        if self.brush:
            p.setBrush(self.brush)
        p.drawPath(self.path)

    def saveState(self):
        return {'elements': self.elements()}