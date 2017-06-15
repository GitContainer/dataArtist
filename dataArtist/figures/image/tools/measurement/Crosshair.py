# coding=utf-8
import numpy as np
import pyqtgraph_karl as pg
from qtpy import QtWidgets

# OWN
from dataArtist.widgets.Tool import Tool


class Crosshair(Tool):
    '''
    Set points-of-interest and draw the image coordinated and
    the selected pixel value
    '''
    icon = 'crosshair.svg'

    def __init__(self, display):
        Tool.__init__(self, display)

        self.poiTextList = []
        self.scene = self.view.scene()
        self._first_time = True

        self.actionHide = QtWidgets.QAction('show', self)
        self.actionHide.setCheckable(True)
        self.actionHide.setChecked(True)
        self.actionHide.triggered.connect(self.toggleShow)
        self.addAction(self.actionHide)

        areset = QtWidgets.QAction('reset', self)
        areset.triggered.connect(self.reset)
        self.addAction(areset)

        self.actionShowCoord = QtWidgets.QAction('show coordinates', self)
        self.actionShowCoord.setCheckable(True)
        self.actionShowCoord.setChecked(True)
        self.addAction(self.actionShowCoord)

    def activate(self):
        if self._first_time:
            self.build()
            self._first_time = False
        else:
            self.view.addItem(self.crosshair)
            self.view.addItem(self.vLine)
            self.view.addItem(self.hLine)
        self.scene.sigMouseClicked.connect(self._setPOI)

    def deactivate(self):
        self.view.removeItem(self.crosshair)
        self.view.removeItem(self.vLine)
        self.view.removeItem(self.hLine)
        self.scene.sigMouseClicked.disconnect(self._setPOI)

    def build(self):
        self.poiMarker = pg.ScatterPlotItem(pen='r', brush='r')
        w = self.display.widget
        w.sigTimeChanged.connect(self._updateValues)
        w.imageItem.sigImageChanged.connect(self._updateValues)

        self.view.addItem(self.poiMarker)
        # draw text for crosshair
        self.anchorX, self.anchorY = 0, 1
        self.crosshair = pg.TextItem(
            text='',
            color=(0, 0, 0),
            html=None,
            anchor=(self.anchorX, self.anchorY),
            border=None,
            fill=pg.mkBrush(255, 255, 255, 80),
            angle=0)
        # draw lines
        self.vLine = pg.InfiniteLine(angle=90, movable=False)
        self.hLine = pg.InfiniteLine(angle=0, movable=False)
        # add to viewBox
        self.view.addItem(self.vLine, ignoreBounds=True)
        self.view.addItem(self.hLine, ignoreBounds=True)
        self.view.addItem(self.crosshair)

        def mouseMoved(evt):
            w = self.display.widget
            if self.view.sceneBoundingRect().contains(evt.x(), evt.y()):
                x, y = self.mouseCoord(evt)
                if w.image is None:
                    return

                img = w.image[w.currentIndex]
                s0, s1 = img.shape[:2]
                ix = np.clip(int(x), 0, s1 - 1)
                iy = np.clip(int(y), 0, s0 - 1)
                z = img[iy, ix]

                # set anchor of crosshair
                if evt.y() - 30 > self.crosshair.boundingRect().height():
                    self.anchorY = 1  # at upper corner
                else:
                    self.anchorY = 0
                if (evt.x() + self.crosshair.boundingRect().width() >
                        self.view.sceneBoundingRect().width()):
                    self.anchorX = 1  # at right corner
                else:
                    self.anchorX = 0
                # set relative position of crosshair
                self.crosshair.anchor = pg.Point(
                    (self.anchorX, self.anchorY))
                # set absolute position of crosshair
                self.crosshair.setPos(x, y)
                # move crosshair-lines to mousepos.
                self.vLine.setPos(x)
                self.hLine.setPos(y)
                self.poiText = self._getPOItext(x, y, z)
                self.crosshair.setText(self.poiText)
                # except IndexError:
                #    pass  # out of bounds
        # connect mouse-signals to new methods:
        self.scene.sigMouseMoved.connect(mouseMoved)

    def _getPOItext(self, x, y, z):
        # include axis scaling:
        for a in self.display.axes:
            if a.orientation in ('left', 'right'):
                y *= a.scale
            elif a.orientation in ('top', 'bottom'):
                x *= a.scale
        if self.actionShowCoord.isChecked():
            return "x=%0.5g\ny=%0.5g\nz=%s" % (x, y, z)
        return "%s" % (z)

    def _updateValues(self):
        w = self.display.widget
        img = w.image[w.currentIndex]
        s0, s1 = img.shape[:2]
        try:
            for t, d in zip(self.poiTextList, self.poiMarker.data):
                x, y = d[0], d[1]
                ix = np.clip(int(x), 0, s0 - 1)
                iy = np.clip(int(y), 0, s1 - 1)
                z = img[iy, ix]
                t.setText(self._getPOItext(x, y, z))
        except IndexError:
            # method also called when display closed
            # using try avoids: IndexError: too many indices for array
            pass

    def _setPOI(self, evt):
        mx, my = self.mouseCoord(evt)
        self.poiMarker.addPoints(
            x=[mx],
            y=[my],
            symbol="+",
            size=10)
        textPOI = pg.TextItem(
            text=self.poiText,
            color=(0, 0, 0),
            html=None,
            anchor=(self.anchorX, self.anchorY),
            border=None,
            fill=pg.mkBrush(255, 255, 255, 80),
            angle=0)
        textPOI.setPos(mx, my)
        self.poiTextList.append(textPOI)
        self.view.addItem(textPOI)

    def reset(self):
        self._first_time = True
        for t in self.poiTextList:
            self.view.removeItem(t)
        self.poiTextList = []
        self.poiMarker.clear()

    def toggleShow(self):
        w = self.display.widget
        if self.actionHide.isChecked():
            self.crosshair.show()
            self.poiMarker.show()
            for t in self.poiTextList:
                t.show()
            w.sigTimeChanged.connect(self._updateValues)
            w.imageItem.sigImageChanged.connect(self._updateValues)
        else:
            self.crosshair.hide()
            self.poiMarker.hide()
            for t in self.poiTextList:
                t.hide()
            try:
                # FIXME: sometimes method is not connected any more ...
                w.sigTimeChanged.disconnect(self._updateValues)
                w.imageItem.sigImageChanged.disconnect(self._updateValues)
                print(999)
            except:
                pass

    def transpose(self):
        # TODO
        for text in self.poiTextList:
            p = text.pos()
            text.setPos(p[1], p[0])
        (xVals, yVals) = self.poiMarker.getData()
        self.poiMarker.setData(x=yVals, y=xVals)
