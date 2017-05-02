# coding=utf-8
from __future__ import division
from __future__ import print_function

import numpy as np
import pyqtgraph_karl as pg
import cv2
#from imgProcessor.QuadDetection import QuadDetection, ObjectNotFound
# from imgProcessor.features.QuadDetection import QuadDetection
from dataArtist.items.PerspectiveGridROI import PerspectiveGridROI

from imgProcessor.camera.PerspectiveCorrection \
    import PerspectiveCorrection as PC

# from fancytools.spatial.closestNonZeroIndex import closestNonZeroIndex

# OWN
from dataArtist.widgets.Tool import Tool
from dataArtist.figures.image.tools.globals.CalibrationFile import CalibrationFile


# PROPRIETARY
try:
    from PROimgProcessor.transform.subPixelAlignment import subPixelAlignment
    from PROimgProcessor.features.GridDetection import GridDetection

except ImportError:
    subPixelAlignment = None
    GridDetection = None


class PerspectiveCorrection(Tool):
    '''
    Correct the rotation and position of a quad distorted through perspective.
    The edge points of the quad can be chosen manually or automated
    '''

    icon = 'quadDetection.svg'

    def __init__(self, imageDisplay):
        Tool.__init__(self, imageDisplay)

        self.quadROI = None
        self.outDisplay = None
#         self.outDisplayViewFactor = None
        self._refPn = []

#         self._cLayerLines = None

        pa = self.setParameterMenu()

        self.calFileTool = self.showGlobalTool(CalibrationFile)

        self.pExecOn = pa.addChild({
            'name': 'Execute on',
            'type': 'list',
            'value': 'all images',
            'limits': ['current image', 'all images', 'last image']})

        self.pRef = pa.addChild({
            'name': 'Reference',
            'type': 'list',
            'value': 'Object profile',
            'limits': ['Object profile', 'Reference image', 'Reference points']})
        # HOMOGRAPHY THROUGH QUAD
        self.pBorder = self.pRef.addChild({
            'name': 'Border',
            'type': 'int',
            'value': 50,
            'limits': (0, 1000)})
        pro = GridDetection is not None
        self.pManual = self.pRef.addChild({
            'name': 'Manual object detection',
            'type': 'bool',
            'value': not pro,
            'readonly': not pro
        })
        self.pCells = self.pRef.addChild({
            'name': 'Rectify cells',
            'type': 'bool',
            'value': False,
            'readonly': not pro})
        self.pCellsX = self.pCells.addChild({
            'name': 'X',
            'type': 'int',
            'value': 6,
            'limits': (1, 100)})
        self.pCellsY = self.pCells.addChild({
            'name': 'Y',
            'type': 'int',
            'value': 10,
            'limits': (1, 100)})

        self.pCellsX.sigValueChanged.connect(self._updateROI)
        self.pCellsY.sigValueChanged.connect(self._updateROI)

        self.pMask = self.pRef.addChild({
            'name': 'Create Mask',
            'type': 'bool',
            'value': True})
        self.pSubcells = self.pMask.addChild({
            'name': 'N subcells',
            'type': 'int',
            'value': -1})
        self.pCellOrient = self.pMask.addChild({
            'name': 'Subcells orientation',
            'type': 'list',
            'value': 'horiz',
            'values': ['horiz', 'vert']})
        self.pCellShape = self.pMask.addChild({
            'name': 'Cell shape',
            'type': 'list',
            'value': 'square',
            'values': ['square', 'pseudo square']})
        self.pMask.sigValueChanged.connect(lambda param, val:
                                           [ch.show(val) for ch in param.childs])
        self.pMask.setValue(False)

        # HOMOGRAPHY THROUGH REF IMAGE
        self.pRefImgChoose = self.pRef.addChild({
            'name': 'Reference image',
                    'value': 'From display',
                    'type': 'menu',
                    'visible': False})
        self.pRefImg = self.pRefImgChoose.addChild({
            'name': 'Chosen',
                    'value': '-',
                    'type': 'str',
                    'readonly': True})
        self.pRefImgChoose.aboutToShow.connect(lambda menu:
                                               self.buildOtherDisplayLayersMenu(
                                                   menu, self._setRefImg,
                                                   includeThisDisplay=True))

        self.pSubPx = self.pRef.addChild({
            'name': 'Sub-pixel alignment',
                    'value': True,
                    'type': 'bool',
                    'visible': False,
                    'enabled': pro})
        self.pSubPx_x = self.pSubPx.addChild({
            'name': 'cells x',
                    'value': 12,
                    'type': 'int',
                    'limits': (1, 100)})
        self.pSubPx_y = self.pSubPx.addChild({
            'name': 'cells y',
                    'value': 9,
                    'type': 'int',
                    'limits': (1, 100)})
        self.pSubPx_neigh = self.pSubPx.addChild({
            'name': 'n neighbors',
                    'value': 2,
                    'type': 'int',
                    'limits': (1, 100)})
        self.pSubPx_maxDev = self.pSubPx.addChild({
            'name': 'max dev',
                    'value': 30,
                    'type': 'int',
                    'limits': (1, 1000)})

        self.pSubPx.sigValueChanged.connect(lambda param, val:
                                            [ch.show(not val) for ch in param.childs])

        self.pRef.sigValueChanged.connect(self._pRefChanged)
#         self.pSnap.sigValueChanged.connect(self._pSnapChanged)
        self.pManual.sigValueChanged.connect(self._setupQuadManually)

        pShowPlane = self.pManual.addChild({
            'name': 'Show Plane',
            'type': 'bool',
            'value': True})
        pShowPlane.sigValueChanged.connect(self._showROI)

        self.pCalcOutSize = pa.addChild({
            'name': 'Output size',
            'type': 'list',
            'value': 'Calculate',
            'limits': ['Calculate', 'Current Size', 'Manual']})
        self.pOutWidth = self.pCalcOutSize.addChild({
            'name': 'Image width [px]',
            'type': 'int',
            'value': 1000,
            'visible': False})

        self.pOutHeight = self.pCalcOutSize.addChild({
            'name': 'Image height [px]',
            'type': 'int',
            'value': 600,
            'visible': False
        })
        self.pCalcOutSize.sigValueChanged.connect(self._pCalcOutSizeChanged)

        self.pCalcAR = pa.addChild({
            'name': 'Calculate aspect ratio',
            'type': 'bool',
            'value': True,
            'tip': ''})

        self.pObjWidth = self.pCalcAR.addChild({
            'name': 'Object width [mm]',
            'type': 'float',
            'value': 0,
            'visible': False})

        self.pObjHeight = self.pCalcAR.addChild({
            'name': 'Object height [mm]',
            'type': 'float',
            'value': 0,
            'visible': False
        })
        self.pCalcAR.sigValueChanged.connect(lambda param, val:
                                             [ch.show(not val) for ch in param.childs])

        self.pCorrViewFactor = pa.addChild({
            'name': 'Correct Intensity',
            'type': 'bool',
            'value': False,
            'tip': 'For realistic results choose a camera calibration'})
#         self.pDrawViewFactor = self.pCorrViewFactor.addChild({
#             'name': 'Show tilt factor',
#             'type': 'bool',
#             'value': False})
#         self.pCorrViewFactor.sigValueChanged.connect(lambda param, val:
#                                                      self.pDrawViewFactor.show(val))

        self.pLive = pa.addChild({
            'name': 'Live',
            'tip': 'Update result whenever one of the parameter was changed',
            'type': 'bool',
            'value': False})

        self.pOverrideOutput = pa.addChild({
            'name': 'Override output',
            'type': 'bool',
            'value': True})

    def _pCalcOutSizeChanged(self, _p, v):
        self.pCalcAR.show(v == 'Calculate')
        self.pOutWidth.show(v == 'Manual')
        self.pOutHeight.show(v == 'Manual')

    def _setRefImg(self, display, layernumber, layername):
        '''
        extract the reference image and -name from a given display and layer number
        '''
        im = display.widget.image
        self._refImg_from_own_display = -1
        self._refImg = im[layernumber]
        if display == self.display:
            self._refImg_from_own_display = layernumber
        self.pRefImg.setValue(layername)

    def _showROI(self, _p, value):
        if self.quadROI is not None:
            self.quadROI.show() if value else self.quadROI.hide()

    def _setupQuadManually(self, _p, value):
        #         self.pSnap.show(value)
        if value:
            if not self.quadROI:
                self._createROI()
            else:
                self.quadROI.show()
        elif self.quadROI:
            self.quadROI.hide()

    def _createRefPn(self):
        w = self.display.widget

        r = w.view.vb.viewRange()
        p = ((r[0][0] + r[0][1]) / 2,
             (r[1][0] + r[1][1]) / 2)
        s = [(r[0][1] - r[0][0]) * 0.1, (r[1][1] - r[1][0]) * 0.1]

        pos = np.array([[p[0] - s[0], p[1] + s[1]],
                        [p[0] - s[0], p[1] - s[1]],
                        [p[0] + s[0], p[1] - s[1]]])

        rFrom = pg.PolyLineROI(pos, pen=(255, 0, 0), movable=False)
        rTo = pg.PolyLineROI(pos + (5, 5), pen=(0, 255, 0), movable=False)
        w.view.vb.addItem(rFrom)
        w.view.vb.addItem(rTo)
        return (rFrom, rTo)

    def _pRefChanged(self, _p, val):
        x = val == 'Reference image'
        self.pRefImgChoose.show(x)
        self.pSubPx.show(x)

        x = val == 'Object profile'
        self.pManual.show(x)
        self.pCells.show(x)
        self.pBorder.show(x)
        self.pMask.show(x)

        #self.pCalcAR.show(val != 'Reference points')
        vv = val == 'Reference points'
        if vv:
            if not len(self._refPn):
                self._refPn = self._createRefPn()
            [r.show() for r in self._refPn]
        else:
            [r.hide() for r in self._refPn]
        self.pCorrViewFactor.show(not vv)
#
#     def _pSnapChanged(self, param, val):
#         w = self.display.widget
#
#         if val:
#             img = w.image
#             img = img[w.currentIndex]
#
#             q = QuadDetection(img)
#             s = img.shape[0]
#             threshold=40
#             minLineLength=int(s/10)
#             maxLineGap = int(s/10)
#
#             q.findLines( threshold=threshold,
#                          minLineLength=minLineLength,
#                          maxLineGap=maxLineGap )
#             i = np.zeros_like(img, dtype=np.uint8)
#             q.drawLines(i, thickness=1, color=255)
#             if self._cLayerLines is None:
#                 self._cLayerLines = w.addColorLayer(layer=i, name='Detected edges',
#                                                     tip='houghLines')
#             else:
#                 self._cLayerLines.setLayer(i)
#         elif self._cLayerLines is not None:
#             w.removeColorLayer(self._cLayerLines)
#             self._cLayerLines = None
#
#     def _roiMoved(self):
#         if self._cLayerLines is not None:
#             i = self._cLayerLines.image
#             for h in self.quadROI.handles:
#                 # snap to closest line
#                 pos = h['item'].pos()
#                 pt = (pos.x(), pos.y())
#                 closest = closestNonZeroIndex(pt, i, kSize=101)
#                 if closest is not None:
#                     h['item'].setPos(closest[0], closest[1])
#             self.quadROI.update()

    def _updateROI(self):
        if self.quadROI:
            self.quadROI.nCells = self.pCellsX.value(), self.pCellsY.value()
            self.quadROI.update()

    def _createROI(self):
        w = self.display.widget
        s = w.image[w.currentIndex].shape[:2]
        if not self.quadROI:

            r = w.view.vb.viewRange()
            p = ((r[0][0] + r[0][1]) / 2,
                 (r[1][0] + r[1][1]) / 2)
            s = [(r[0][1] - r[0][0]) * 0.1, (r[1][1] - r[1][0]) * 0.1]

            self.quadROI = PerspectiveGridROI(nCells=(self.pCellsX.value(),
                                                      self.pCellsY.value()),
                                              pos=p, size=s)

            w.view.vb.addItem(self.quadROI)

    def activate(self):
        if self.pLive.value():
            self._prepare()
            self.display.widget.item.sigImageChanged.connect(
                self._processAndDone)
        else:
            self.startThread(self._prepareAndProcess, self._done)

    def _prepare(self):
        w = self.display.widget
        img = w.image[w.currentIndex]
        v = self.pRef.value()
        if v == 'Reference points':
            self.pc = None
            return  # do in self.process

        try:
            c = self.calFileTool.currentCameraMatrix()
        except AttributeError:
            c = None
        # height/width:
        if self.pCalcAR.value():
            w, h = None, None
        else:
            if self.pCalcOutSize.value() == 'Current Size':
                w, h = img.shape[:2]
            else:
                w = self.pObjWidth.value()
                if w == 0:
                    w = None
                h = self.pObjHeight.value()
                if h == 0:
                    h = None
        # output size:
        size = (None, None)
        if not self.pCalcOutSize.value():
            size = (self.pOutHeight.value(), self.pOutWidth.value())

        self._pc_args = dict(obj_width_mm=h,
                             obj_height_mm=w,
                             cameraMatrix=c,
                             do_correctIntensity=self.pCorrViewFactor.value(),
                             new_size=size)

        # HOMOGRAPHY THROUGH REFERENCE IMAGE
        if v == 'Reference image':
            # INIT:
            self.pc = PC(img.shape, **self._pc_args)
            self.pc.setReference(self._refImg)

        else:
            # HOMOGRAPHY THROUGH QUAD
            vertices = None  # QuadDetection(img).vertices
            if self.pManual.value():
                vertices = np.array([(h['pos'].x(), h['pos'].y())
                                     for h in self.quadROI.handles])
                vertices += self.quadROI.pos()
            if GridDetection is None:
                self.pc = PC(img.shape, **self._pc_args)
                self.pc.setReference(self._refImg)
            ns = self.pSubcells.value()
            if ns == -1:
                nSublines = None
            elif self.pCellOrient.value() == 'horiz':
                nSublines = ([ns], [0])
            else:
                nSublines = ([0], [ns])

            self.pc = GridDetection(img=img,
                                    border=self.pBorder.value(),
                                    vertices=vertices,
                                    shape=self.pCellShape.value(),
                                    grid=(
                                        self.pCellsY.value(),
                                        self.pCellsX.value()),
                                    nSublines=nSublines,
                                    refine=self.pCells.value(),
                                    refine_sublines=self.pMask.value())

            if not self.pManual.value():
                if not self.quadROI:
                    self._createROI()
                # show found ROI:
                for h, c in zip(self.quadROI.handles, self.pc.opts['vertices']):
                    pos = c[::-1] - self.quadROI.pos()
                    h['item'].setPos(pos[1], pos[0])
                self.quadROI.show()

    def _process(self):
        w = self.display.widget
        img = w.image
        out = []
        v = self.pRef.value()

        if v == 'Reference points':
            # 2x3 point warp:
            r0, r1 = self._refPn
            pts0 = np.array([(h['pos'].y(), h['pos'].x())
                             for h in r0.handles]) + r0.pos()
            pts1 = np.array([(h['pos'].y(), h['pos'].x())
                             for h in r1.handles]) + r1.pos()
            # TODO: embed in PyerspectiveCorrection
            M = cv2.getAffineTransform(
                pts0.astype(
                    np.float32), pts1.astype(
                    np.float32))
            for n, i in enumerate(img):
                out.append(
                    # TODO: allow different image shapes
                    cv2.warpAffine(i, M, w.image.shape[1:3],
                                   borderValue=0))
                print(out[-1].shape)
        else:
            r = v == 'Reference image'
            e = self.pExecOn.value()
            for n, i in enumerate(img):
                if (e == 'all images' or
                        (e == 'current image' and n == w.currentIndex) or
                        (e == 'last image' and n == len(img) - 1)):

                    if not (r and n == self._refImg_from_own_display):
                        corr = self.pc.correct(i)

                        if r and self.pSubPx.value():

                            corr = subPixelAlignment(corr, self._refImg,
                                                     niter=20,
                                                     grid=(self.pSubPx_y.value(),
                                                           self.pSubPx_x.value()),
                                                     method='smooth',
                                                     # maxGrad=2,
                                                     concentrateNNeighbours=self.pSubPx_neigh.value(
                                                     ),
                                                     maxDev=self.pSubPx_maxDev.value())[0]

                        out.append(corr)
        return out

    def _done(self, out):
        change = 'PerspectiveFit'
        if not self.outDisplay or self.outDisplay.isClosed():
            self.outDisplay = self.display.workspace.addDisplay(
                origin=self.display,
                changes=change,
                data=out,
                title=change)
        else:
            self.outDisplay.widget.update(out)
            self.outDisplay.widget.updateView()

#         if self.pCorrViewFactor.value() and self.pDrawViewFactor.value():
#             if not self.outDisplayViewFactor:
        if self.pMask.value() and self.pMask.isVisible():
            self.display.workspace.addDisplay(
                origin=self.display,
                data=[self.pc.mask()],
                title='Grid mask')
#             else:
#                 self.outDisplayViewFactor.widget.setImage(
#                     self.pc.maps['tilt_factor'])

        if not self.pOverrideOutput.value():
            self.outDisplay = None
#             self.outDisplayViewFactor = None
        if not self.pLive.value():
            self.setChecked(False)
            del self.pc

    def _prepareAndProcess(self):
        self._prepare()
        return self._process()

    def _processAndDone(self):
        out = self._process()
        self._done(out)

    def deactivate(self):
        try:
            w = self.display.widget
            w.item.sigImageChanged.disconnect(self._processAndDone)
        except:
            pass
