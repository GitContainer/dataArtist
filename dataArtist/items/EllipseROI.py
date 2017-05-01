from qtpy import QtCore
import pyqtgraph_karl as pg

from dataArtist.items.QPainterPath import QPainterPath



class EllipseROI(pg.EllipseROI):

    def __init__(self, *args, **kwargs):
        if 'brush' in kwargs:
            self.brush = kwargs.pop('brush')
        pg.EllipseROI.__init__(self, *args, **kwargs)

    def painterPath(self):
        p = self.state['pos']
        s = self.state['size']
        path = QPainterPath()
        path.addEllipse(QtCore.QRectF(p[0], p[1], s[0], s[1]))
        return path

    def setBrush(self, brush):
        self.brush = brush
        self.update()

    def paint(self, p, opt, widget):
        if self.brush:
            p.setBrush(self.brush)
        return pg.EllipseROI.paint(self, p, opt, widget)