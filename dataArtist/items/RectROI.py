from qtpy import QtCore
import pyqtgraph_karl as pg

from dataArtist.items.QPainterPath import QPainterPath



class RectROI(pg.ROI):

    def __init__(self, *args, **kwargs):
        if 'brush' in kwargs:
            self.brush = kwargs.pop('brush')
        pg.ROI.__init__(self, *args, **kwargs)
        self.addScaleHandle([1, 1], [0, 0])

    def painterPath(self):
        p = self.state['pos']
        s = self.state['size']
        path = QPainterPath()
        path.addRect(QtCore.QRectF(p[0], p[1], s[0], s[1]))
        return path

    def setBrush(self, brush):
        self.brush = brush
        self.update()

    def paint(self, p, opt, widget):
        if self.brush:
            p.setBrush(self.brush)
        return pg.ROI.paint(self, p, opt, widget)



