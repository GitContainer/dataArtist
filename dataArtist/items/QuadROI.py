# from qtpy import QtCore
import pyqtgraph_karl as pg
import numpy as np
# from dataArtist.items.QPainterPath import QPainterPath





class QuadROI(pg.PolyLineROI):

    def __init__(self, *args, **kwargs):
        if 'brush' in kwargs:
            self.brush = kwargs.pop('brush')
        else:
            self.brush = None
            
        p = kwargs.pop('pos')
        s = kwargs.pop('size')
        try:
            kwargs.pop('angle')
        except KeyError:
            pass

        pn = np.array([[0,   0],
                       [0,   s[1]],
                       [s[0],s[1]],
                       [s[0],0]]) + p

        kwargs['closed']=True
        kwargs['pen']='r'
        
        pg.PolyLineROI.__init__(self, pn, *args, **kwargs)

        self.translatable = False
        self.mouseHovering = False
        # TODO: just disconnect all signals instead of having lambda
        # PREVENT CREATION OF SUB SEGMENTS:
        for s in self.segments:
            s.mouseClickEvent = lambda x: None


#     def painterPath(self):
#         p = self.state['pos']
#         s = self.state['size']
#         path = QPainterPath()
#         path.addRect(QtCore.QRectF(p[0], p[1], s[0], s[1]))
#         return path
# 

    #TODO: does not work ATM:
    def setBrush(self, brush):
        self.brush = brush
        self.update()
# 
    def paint(self, p, opt, widget):
        if self.brush:
            p.setBrush(self.brush)
        return super().paint(p, opt, widget)



