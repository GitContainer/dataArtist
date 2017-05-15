# coding=utf-8
import numpy as np
import pyqtgraph_karl as pg
import cv2

from dataArtist.items.PerspectiveGridROI import PerspectiveGridROI

from imgProcessor.camera.PerspectiveCorrection \
    import PerspectiveCorrection as PC

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
        self._refPn = []
        pa = self.setParameterMenu()

        self.calFileTool = self.showGlobalTool(CalibrationFile)

        self.pExecOn = pa.addChild({
            'name': 'Execute on',
            'type': 'list',
            'value': 'all images',
            'limits': ['current image', 'all images', 'last image']})

        self.createResultInDisplayParam(pa)

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
            'value': 0,
            'limits': (0, 100)})
        self.pCellsY = self.pCells.addChild({
            'name': 'Y',
            'type': 'int',
            'value': 0,
            'limits': (0, 100)})

        def fn(_p, _v):
            return self._updateROI()
        self.pCellsX.sigValueChanged.connect(fn)
        self.pCellsY.sigValueChanged.connect(fn)

        self.pMask = self.pRef.addChild({
            'name': 'Create Mask',
            'type': 'bool',
            'value': True})
        self.pMaskOffset = self.pMask.addChild({
            'name': 'Offset',
            'type': 'int',
            'value': 0,
            'limits': (0, 1000),
            'suffix': 'px'})
        self.pMaskDetect = self.pMask.addChild({
            'name': 'Detect parameters',
            'type': 'bool',
            'value': False})
        self.pSubcells = self.pMaskDetect.addChild({
            'name': 'Number busbars',
            'type': 'int',
            'value': 3,
            'limits': (0, 109)})
        self.pCellOrient = self.pMaskDetect.addChild({
            'name': 'Busbar Orientation',
            'type': 'list',
            'value': 'horiz',
            'values': ['horiz', 'vert']})
        self.pCellShape = self.pMaskDetect.addChild({
            'name': 'Cell shape',
            'type': 'list',
            'value': 'square',
            'values': ['square', 'pseudo square']})
        self.pMask.sigValueChanged.connect(lambda param, val:
                                           [ch.show(val) for ch in param.childs])
        self.pMask.setValue(False)
        self.pMaskDetect.sigValueChanged.connect(lambda param, val:
                                                 [ch.show(not val) for ch in param.childs])
        self.pMaskDetect.setValue(True)

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
                                            [ch.show(val) for ch in param.childs])
        self.pSubPx.setValue(False)
        self.pRef.sigValueChanged.connect(self._pRefChanged)
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
        if value:
            if not self.quadROI:
                self.quadROI = self._createROI()
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

        vv = val == 'Reference points'
        if vv:
            if not len(self._refPn):
                self._refPn = self._createRefPn()
            [r.show() for r in self._refPn]
        else:
            [r.hide() for r in self._refPn]
        self.pCorrViewFactor.show(not vv)

    def _updateROI(self, roi=None):
        if roi is None:
            roi = self.quadROI
        if roi is not None:
            roi.p.param('X').setValue(self.pCellsX.value())
            roi.p.param('Y').setValue(self.pCellsY.value())

    def _createROI(self, display=None):
        if display is None:
            display = self.display

        t = display.tools['Selection']
        # check whether already a grid ROI exists:
        quadROI = t.findPath(PerspectiveGridROI)
        if quadROI is None:
            # no grid ROI there -> create one!
            t.pType.setValue('PerspectiveGrid')
            quadROI = t.new()  # pNew.sigActivated.emit(t.pNew)
        quadROI.sigRegionChanged.connect(lambda: self.pManual.setValue(True))
        self._updateROI(quadROI)
        return quadROI

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
            vertices = None
            if self.pManual.value():
                if not self.quadROI:
                    self.quadROI = self._createROI()
                    raise Exception('need to fit quad first.')
                vertices = self.quadROI.vertices()

            if GridDetection is None:
                self.pc = PC(img.shape, **self._pc_args)
                self.pc.setReference(self._refImg)
            else:
                if self.pMaskDetect.value():
                    nSublines = None
                    cellshape = None
                else:
                    ns = self.pSubcells.value()
                    if self.pCellOrient.value() == 'horiz':
                        nSublines = ([ns], [0])
                    else:
                        nSublines = ([0], [ns])
                    cellshape = self.pCellShape.value()

                gy = self.pCellsY.value()
                gx = self.pCellsX.value()
                if 0 in (gx, gy):
                    grid = None
                else:
                    grid = gy, gx
                self.pc = GridDetection(img=img,
                                        border=self.pBorder.value(),
                                        vertices=vertices,
                                        shape=cellshape,
                                        grid=grid,
                                        nSublines=nSublines,
                                        refine_cells=self.pCells.value(),
                                        refine_sublines=self.pMask.value())

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
                            corr = subPixelAlignment(
                                corr, self._refImg,
                                niter=20,
                                grid=(self.pSubPx_y.value(),
                                      self.pSubPx_x.value()),
                                method='smooth',
                                # maxGrad=2,
                                concentrateNNeighbours=self.pSubPx_neigh.value(),
                                maxDev=self.pSubPx_maxDev.value())[0]

                        out.append(corr)
        return out

    def _done(self, out):
        change = 'PerspectiveFit'
        self.outDisplay = self.handleOutput(out, title=change)
#         if not self.outDisplay or self.outDisplay.isClosed():
#             self.outDisplay = self.display.workspace.addDisplay(
#                 origin=self.display,
#                 changes=change,
#                 data=out,
#                 title=change)
#         else:
#             self.outDisplay.widget.update(out)
#             self.outDisplay.widget.updateView()
        if self.pRef.value() == 'Object profile':
            # show grid in display:
            if not self.pManual.value():
                if self.quadROI is None:
                    self.quadROI = self._createROI()
                # TODO: unclean having perspectiveCorrection in GridDetection
                pc = self.pc
                if isinstance(pc, GridDetection):
                    # if GridDetection is not None:
                    gx, gy = pc.opts['grid']
                    self.pCellsX.setValue(gx)
                    self.pCellsY.setValue(gy)
                    pc = self.pc._pc
                self.quadROI.setVertices(pc.quad)
                self.quadROI.show()

            # inherit corrected grid to output display:
                # TODO: unclean
            self.outDisplay.clicked.emit(self.outDisplay)  # init tools
            quadROI = self._createROI(self.outDisplay)
            b = self.pBorder.value()
            sy, sx = out[0].shape[:2]
            v = np.array([(b, sy - b),
                          (sx - b, sy - b),
                          (sx - b, b),
                          (b, b)])
            quadROI.setVertices(v)
        # synchronize handle movemend in both this and output display:
#         quadROI.sigRegionChanged.connect(self.___a)


#         if self.pCorrViewFactor.value() and self.pDrawViewFactor.value():
#             if not self.outDisplayViewFactor:

        # TODO: mask generation in extra tool
        if self.pMask.value() and self.pMask.isVisible():
            self.outDisplay.widget.addColorLayer(
                layer=self.pc.mask(offs=self.pMaskOffset.value()),
                name='Grid mask')

        if not self.pOverrideOutput.value():
            self.outDisplay = None
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
