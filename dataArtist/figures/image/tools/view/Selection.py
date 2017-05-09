# coding=utf-8
from __future__ import division
from __future__ import print_function

import numpy as np

from pyqtgraph_karl.functions import mkPen, mkBrush
from qtpy import QtCore, QtGui
import pyqtgraph_karl as pg
import cv2


# OWN
from dataArtist.widgets.Tool import Tool
from dataArtist.items.FreehandItem import FreehandItem
from dataArtist.items.QPainterPath import QPainterPath

from dataArtist.items.GridROI import GridROI
from dataArtist.items.RectROI import RectROI
from dataArtist.items.EllipseROI import EllipseROI
from dataArtist.items.IsoCurveROI import IsoCurveROI
from dataArtist.items.QuadROI import QuadROI
from dataArtist.items.PerspectiveGridROI import PerspectiveGridROI


ITEMS = {FreehandItem: 'Freehand',
         RectROI: 'Rectangle',
         GridROI: 'Grid',
         IsoCurveROI: 'Isolines',
         EllipseROI: 'Ellipse',
         QuadROI: 'Quad',
         PerspectiveGridROI: 'PerspectiveGrid',
         }


class Selection(Tool):
    '''
    Mark and measure image features using various selection types, like
        freehand and rectangle
    '''
    icon = 'selection.svg'

    def __init__(self, display):
        Tool.__init__(self, display)

        self.paths = []
        # min time difference to add a line to qpainterpath
        # when drawing in [ms]:
        self.MIN_DT = 25
        self._timer = QtCore.QTime()

        self.pa = self.setParameterMenu()
        self.pa.sigChildRemoved.connect(self._removePath)

        self.pType = self.pa.addChild({
            'name': 'Type',
            'type': 'list',
            'value': 'Freehand',
            'limits': list(ITEMS.values())})

        self.pNew = self.pa.addChild({
            'name': 'New',
            'type': 'action',
            'value': True})
        self.pNew.sigActivated.connect(self.new)
        self.pNew.sigActivated.connect(self._menu.resizeToContent)

        pMask = self.pa.addChild({
            'name': 'Create Mask',
            'type': 'action'})
        pMask.sigActivated.connect(self._createMaskFromSelection)

        pArea = self.pa.addChild({
            'name': 'Measure areas',
            'type': 'action'})
        pArea.sigActivated.connect(self._measurePath)

        self.pMask = pArea.addChild({
            'name': 'Relative to selection',
            'type': 'list',
            'value': '-',
            'limits': ['-']})
        list(self.pMask.items.keys())[0].widget.showPopup = self._updatePMask

    def findPath(self, cls):
        def check(roi):
            return isinstance(roi, cls)
        return next((roi for roi in self.paths if check(roi)), None)

    def _updatePMask(self):
        l = ['-']
        l.extend([p.name() for p in self.pa.childs[3:]])
        self.pMask.setLimits(l)
        i = list(self.pMask.items.keys())[0].widget
        i.__class__.showPopup(i)

    def new(self):
        pen = mkPen(10, len(self.paths) + 2)
        name = typ = self.pType.value()
        return self._add(typ, name, {'pen': pen})

    def _add(self, typ, name, state):
        self.curIndex = -1

        p = self.pa.addChild({
            'name': '[%i] %s' % (len(self.paths) + 1, name),
            'type': 'empty',
            'highlight': True,
            'removable': True,
            'renamable': True,
            'autoIncrementName': True})

        if typ == 'Freehand':
            path = self._addFreehand(p, state)
            if path.isEmpty():
                self._initFreehand()
        elif typ == 'Grid':
            path = self._addGrid(p, state)
        elif typ == 'Isolines':
            path = self._addIso(p, state)
        elif typ == 'PerspectiveGrid':
            path = self._addPerspectiveGrid(p, state)
        else:
            cls = [k for k, v in ITEMS.items() if v == typ][0]
            path = self._addROI(cls, state)

        self.paths.append(path)

        color = state['pen'].color()

        pLineColor = p.addChild({
            'name': 'Line color',
            'type': 'color',
            'value': color,
            'path': path})
        pLineColor.sigValueChanged.connect(self._changeLineColor)

        if 'brush' in state:
            br = state['brush'].color()
        else:
            br = QtGui.QColor(color)
            br.setAlpha(25)
            path.setBrush(br)

        pFillColor = p.addChild({
            'name': 'Fill color',
            'type': 'color',
            'value': br,
            'path': path})
        pFillColor.sigValueChanged.connect(self._changeFillColor)

        self.setChecked(True)
        return path

    def _initFreehand(self):
        w = self.display.widget
        self._mouseDragEvent = w.view.vb.mouseDragEvent
        w.view.vb.mouseDragEvent = self._drawFreehand
        self._timer.start()

    def _changeLineColor(self, param, val):
        p = param.opts['path']
        p.setPen(val)

    def _changeFillColor(self, param, val):
        c = param.opts['path']
        c.setBrush(val)

    def _getPathIndex(self, param):
        i = param.parent().childs.index(param)
        return i - 4

    def _modifyFreehand(self, param):
        path = self.paths[self._getPathIndex(param.parent())]
        if path.isModify:
            param.setName('Modify')
            path.setModify(False)
        else:
            param.setName('Done Modify')
            path.setModify(True)

    def _setFreehandIsArea(self, param, value):
        path = self.paths[self._getPathIndex(param.parent())]
        path.is_area = value

    def _addOrStopFreehand(self, param, forceStop=False):
        self.curIndex = self._getPathIndex(param.parent())
        if not forceStop and param.name() == 'Add':
            param.setName('Done Add')
            self.pNew.hide()
            self._initFreehand()
        else:
            param.setName('Add')
            self.pNew.show()
            self._endFreehand()

    def _endFreehand(self):
        w = self.display.widget
        p = self.paths[self.curIndex]
        p.closePath()
        w.view.vb.mouseDragEvent = self._mouseDragEvent

    def _drawFreehand(self, ev, axis=None):
        ev.accept()

        # Scale or translate based on mouse button
        if ev.button() & QtCore.Qt.MidButton:
            return self._mouseDragEvent(ev, axis)
        if ev.button() & QtCore.Qt.LeftButton:
            pos = self.mouseCoord(ev)
            p = self.paths[self.curIndex]

            if self._timer.elapsed() > self.MIN_DT:
                self._timer.restart()

                if ev.isStart():
                    p.startPath(pos)
                    # when viewbox view changed before (mouse drag)
                    # path wont be visible -> force update:
                    self.display.widget.view.vb.update()
                else:
                    p.continuePath(pos)

    def _removePath(self, _parent, _child, index):
        w = self.display.widget
        path = self.paths.pop(index - 3)
        if isinstance(path, IsoCurveROI):
            try:
                w.ui.histogram.vb.removeItem(path.isoLine)
            except ValueError:
                # TODO:
                pass  # this method is called twice for some reason
        try:
            path.close()
        except AttributeError:
            w.view.vb.removeItem(path)

    def activate(self):
        for c in self.paths:
            c.show()

    def deactivate(self):
        for c in self.paths:
            c.hide()
        try:
            # reset draw event // in case freehand tool still activated
            self.display.widget.view.vb.mouseDragEvent = self._mouseDragEvent
        except AttributeError:
            pass

    def _savePaths(self):
        l = []
        for p, path in zip(self.pa.childs[4:], self.paths):
            name = p.name()
            state = path.saveState()
            typ = ITEMS[path.__class__]
            state['pen'] = p.param('Line color').value().getRgb()
            state['brush'] = p.param('Fill color').value().getRgb()
            l.append((typ, name, state))
        return l

    # TODO: default argument is mutable: Default argument values are evaluated
    # only once at function definition time,
    # which means that modifying the default value of the argument will affect
    # all subsequent calls of the function.
    def saveState(self, state={}):
        state['activated'] = self.isChecked()
        state['paths'] = self._savePaths()
        return state

    def restoreState(self, state):
        for typ, name, s in state['paths']:
            s['pen'] = mkPen(state['pen'])
            s['brush'] = mkBrush(state['brush'])
            self._add(typ, name, s)
        self.setChecked(state['activated'])


#     def save(self, session, path):
#         l = {}
#         l['activated'] = self.isChecked()
#         l['paths'] = self._savePaths()
#         session.addContentToSave(l, *path+('general.txt',))
#
#
#     def restore(self, session, path):
#         l =  eval(session.getSavedContent(*path +('general.txt',) ))
#         for typ,name,state in l['paths']:
#             state['pen'] = mkPen(state['pen'])
#             state['brush'] = mkBrush(state['brush'])
#             self._add(typ, name, state)
#         self.setChecked(l['activated'])

    def _createMaskFromSelection(self):
        img = self.display.widget.image
        assert img is not None, 'need image defined'

        out = np.zeros(img.shape[1:3], dtype=np.uint8)
        for n, p in enumerate(self.paths):
            assert isinstance(
                p, FreehandItem), 'TODO: make work for other items as well'
            cv2.fillPoly(out, np.array([p.elements()], dtype=np.int32), n + 1)

        self.handleOutput([out.T], title='selection')

    def _measurePath(self):
        mask = None
        v = self.pMask.value()
        if v != '-':
            for i, ch in enumerate(self.pa.childs[3:]):
                if ch.name() == v:
                    break
            mask = self.paths[i].painterPath()
        # TODO: mean + ...
            # mask area:
            ma = mask.calcArea()

        for n, p in enumerate(self.paths):
            a = p.painterPath()
            name = self.pa.childs[n + 3].name()
            if mask is None or i == n:
                print('%s. %s - Area:%s | Length: %s' % (
                    n + 1, name, a.calcArea(), a.length()))
            else:
                ia = QPainterPath(mask.intersected(a)).calcArea()
                print('%s. %s - Area:(%s, area intersection: %s, relative %s) \
| Length:%s' % (n + 1, name, a.calcArea(), ia, ia / ma, a.length()))

    def _addIso(self, p, state):
        w = self.display.widget

        pGauss = p.addChild({
            'name': 'Smooth kernel size',
            'type': 'float',
            'value': 0})

        hist = w.ui.histogram
        mn, mx = hist.getLevels()
        lev = (mn + mx) / 2

        # Isocurve drawing
        iso = IsoCurveROI(level=lev, **state)

        iso.setParentItem(w.imageItem)
        iso.setZValue(5)  # todo
        # build isocurves from smoothed data
        # connect
        pGauss.sigValueChanged.connect(self._isolinePGaussChanged)

        def fn():
            self._isolinePGaussChanged(pGauss, pGauss.value())
        w.imageItem.sigImageChanged.connect(fn)
        w.sigTimeChanged.connect(fn)

        # Draggable line for setting isocurve level
        isoLine = pg.InfiniteLine(angle=0, movable=True, pen=state['pen'])
        iso.isoLine = isoLine
        hist.vb.addItem(isoLine)
        isoLine.setValue(lev)
        isoLine.setZValue(1000)  # bring iso line above contrast controls
        # connect
        isoLine.sigDragged.connect(lambda isoLine, iso=iso:
                                   iso.setLevel(isoLine.value()))
        p.opts['iso'] = iso
        fn()
        return iso

    def _isolinePGaussChanged(self, p, v):
        w = self.display.widget
        if v > 0:
            d = pg.gaussianFilter(w.image[w.currentIndex], (v, v))
        else:
            d = w.image[w.currentIndex]
        p.parent().opts['iso'].setData(d)

    def _addROI(self, cls, state):
        w = self.display.widget
        r = w.view.vb.viewRange()
        if 'pos' not in state:
            state['pos'] = ((r[0][0] + r[0][1]) / 2,
                            (r[1][0] + r[1][1]) / 2)
            state['size'] = [
                (r[0][1] - r[0][0]) * 0.2,
                (r[1][1] - r[1][0]) * 0.2]
            state['angle'] = 0.0
        path = cls(**state)
        w.view.vb.addItem(path)
        return path

    def _addPerspectiveGrid(self, param, state):
        nCells = (10, 6)
        state['nCells'] = nCells

        path = self._addROI(PerspectiveGridROI, state)
        path.p = param
        pX = param.addChild({
            'name': 'X',
            'type': 'int',
            'value': nCells[0],
            'limits': (1, 200)})
        pY = param.addChild({
            'name': 'Y',
            'type': 'int',
            'value': nCells[1],
            'limits': (1, 200)})

        def updateY(_p, v, path=path):
            path.nCells[0] = v
            path.update()

        def updateX(_p, v, path=path):
            path.nCells[1] = v
            path.update()
        pX.sigValueChanged.connect(updateY)
        pY.sigValueChanged.connect(updateX)

        pAvg = param.addChild({
            'name': 'Create cell averages',
            'type': 'action'})
        pAvType = pAvg.addChild({
            'name': 'Type',
            'type': 'list',
            'value': 'mean',
            'limits': ['mean', 'standard deviation']})

        pAvg.sigActivated.connect(lambda _p, path=path, param=pAvType:
                                  self._showCellAverage_Pgrid(path,
                                                              param.value()))
        return path

    def _addFreehand(self, param, state):
        w = self.display.widget
        path = FreehandItem(w.imageItem, **state)

        pAdd = param.addChild({
            'name': 'Done Add',
            'type': 'action',
        })
        pMod = param.addChild({
            'name': 'Modify',
            'type': 'action'})

        pArea = param.addChild({
            'name': 'Is area',
            'type': 'bool',
            'value': True})

        pAdd.sigActivated.connect(self._addOrStopFreehand)
        pAdd.sigActivated.connect(self._menu.hide)

        pMod.sigActivated.connect(self._modifyFreehand)
        pMod.sigActivated.connect(self._menu.hide)

        pArea.sigValueChanged.connect(self._setFreehandIsArea)

        self.pNew.hide()

        print('''Press the left mouse button to draw.
Change the view using the middle mouse button
Click on 'Done Add' to stop drawing
''')
        return path

    def _addGrid(self, param, state):
        w = self.display.widget

        if 'size' not in state:
            state['size'] = w.image.shape[1:3]
        if 'pos' not in state:
            state['pos'] = [0, 0]

        path = GridROI(**state)

        path.setViewBox(w.view.vb)
        # TODO:
#         pFit = param.addChild({
#             'name': 'Fit shape to image',
#             'type': 'action',
#             'tip': 'Not implemented at the moment'
#             })
        # pFit.sigActivated.connect(lambda: raise NotImplemented('shape fitting
        # is not implemented at the moment')

        pCells = param.addChild({
            'name': 'Cells',
            'type': 'empty',
            'highlight': True})

        pX = pCells.addChild({
            'name': 'x',
            'type': 'int',
            'value': 4,
            'limits': [1, 1000]})

        pY = pCells.addChild({
            'name': 'y',
            'type': 'int',
            'value': 5,
            'limits': [1, 1000]})

        pShape = pCells.addChild({
            'name': 'Shape',
            'type': 'list',
            'value': 'rect',
            'limits': ['Rect', 'Circle', 'Pseudosquare']})

        pAvgCellInt = param.addChild({
            'name': 'Return average cell intensity',
            'type': 'action'})
        pAvgCellInt.sigActivated.connect(lambda _p, pa=path:
                                         self._showCellAverage_grid(pa))

        pRatio = pShape.addChild({
            'name': 'Ratio Circle/Square',
            'type': 'float',
            'value': 1.2,
            'limits': [1, 1.41],
            'visible': False})

        pShape.sigValueChanged.connect(lambda _p, v:
                                       pRatio.show(v == 'Pseudosquare'))
        pX.sigValueChanged.connect(lambda _p, v, grid=path, py=pY:
                                   grid.setGrid(v, py.value()))
        pY.sigValueChanged.connect(lambda _p, v, grid=path, px=pX:
                                   grid.setGrid(px.value(), v))
        pShape.sigValueChanged.connect(lambda _p, v, grid=path:
                                       grid.setCellShape(v))
        pRatio.sigValueChanged.connect(lambda _p, v, grid=path:
                                       [c.setRatioEllispeRect(v)
                                        for c in grid.cells])
        return path

    def _showCellAverage_grid(self, path):
        for n, img in enumerate(self.display.widget.image):
            avg = path.getCellParameters(img)
            self.display.workspace.addTableDock(
                name='layer %s' % n, array=avg)

    def _showCellAverage_Pgrid(self, path, fnname):
        d = self.display
        fn = {'mean': np.mean, 'standard deviation': np.std}[fnname]
        for n, img in enumerate(d.widget.image):
            avg = path.cellAverages(img, fn)
            self.display.workspace.addTableDock(
                name='[%s].%s - Cell average(%s)' % (d.number, n, fnname),
                array=avg)
