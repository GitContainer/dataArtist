# coding=utf-8
from __future__ import print_function

from collections import OrderedDict
# OWN
from dataArtist.figures.image.ImageWidget import ImageWidget
from dataArtist.figures.image.tools.globals.CalibrationFile import CalibrationFile
from dataArtist.widgets.ImageTool import ImageTool

# TODO: all fn fits are slow because there is no down-scaling a.t.m.
# TODO: post proc. methods shuold be limited for some methods:
#    MultiSpots only allows replace ones and no med, gauss


class FlatField(ImageTool):
    '''
    Create a flat field calibration map from multiple
    input images.

    The methods are detailed in 
    ---
    K.Bedrich, M.Bokalic et al.:
    ELECTROLUMINESCENCE IMAGING OF PV DEVICES:
    ADVANCED FLAT FIELD CALIBRATION,2017
    ---
    '''
    icon = 'flatField.svg'

    def __init__(self, imageDisplay):
        ImageTool.__init__(self, imageDisplay)

        # <<<<< save startup time
        from imgProcessor.camera.flatField.vignettingFromSpotAverage \
            import vignettingFromSpotAverage
        from imgProcessor.camera.flatField.vignettingFromDifferentObjects \
            import vignettingFromDifferentObjects
        from imgProcessor.camera.flatField.vignettingFromRandomSteps \
            import vignettingFromRandomSteps
        from imgProcessor.camera.flatField.flatFieldFromCloseDistance \
            import flatFieldFromCloseDistance
        from imgProcessor.camera.flatField.postProcessing \
            import ppMETHODS, postProcessing
        FlatField._postProcessing = postProcessing
        # >>>>>>
        self.outDisplay = None
        self.calFileTool = self.showGlobalTool(CalibrationFile)

        self._bg = None

        pa = self.setParameterMenu()

        pMeasure = pa.addChild({
            'name': 'Calculate calibration array ...',
            'type': 'empty'})

        self.createResultInDisplayParam(pMeasure)

        self._m = OrderedDict([('Direct measurement in short distance',
                                flatFieldFromCloseDistance),
                               ('Discrete spot average',
                                vignettingFromSpotAverage),
                               ('Local maximum of multiple DUTs',
                                vignettingFromDifferentObjects),
                               # TODO: implement
                               #('Vignetting-Object separation from discrete steps (Method D)',
                               # vignettingFromDiscreteSteps)
                               ('Vignetting-object separation using pattern recognition',
                                vignettingFromRandomSteps)
                               ])
        tip = '\n\n'.join(['%s:\n %s' % (k, fn.__doc__)
                           for k, fn in self._m.items()])
        kk = list(self._m.keys())
        self.pMethod = pMeasure.addChild({
            'name': 'Method',
            'type': 'list',
            'value': kk[0],
            'limits': kk,
            'tip': tip})

        lim = ['-']
        lim.extend(ppMETHODS)
        self.pFitMethod = pMeasure.addChild({
            'name': 'Post processing',
                    'type': 'list',
                    'value': lim[0],
                    'limits': lim,
                    'tip': postProcessing.__doc__
                    #'visible': False
        })

#         self.pMethod.sigValueChanged.connect(lambda p, v:
# self.pFitMethod.show(p.value() == 'from normal images'))

        self.pBg = pMeasure.addChild({
            'name': 'Background image(s)',
                    'value': '-',
                    'type': 'menu',
                    'tip': '''either one averaged or multiple RAW
                    background images of the same exposure time'''})
        self.pBg.aboutToShow.connect(self._buildRefImgMenu)

        self.pEsimateTresh = pMeasure.addChild({
            'name': 'Estimate Threshold',
                    'value': True,
                    'type': 'bool',
                    'tip': '''If True: signal-background threshold will be 
                    estimated using OTSUS method'''})
        self.pThresh = self.pEsimateTresh.addChild({
            'name': 'Threshold',
                    'value': 100,
                    'type': 'float',
                    'visible': False})
        self.pEsimateTresh.sigValueChanged.connect(
            lambda _, v: self.pThresh.show(not v))

        pa.addChild({
            'name': 'Load calibration array ...',
            'type': 'menu',
            'value': 'from display'}).aboutToShow.connect(
                lambda m, fn=self._fromDisplay:
            self.buildOtherDisplayLayersMenu(m, fn, includeThisDisplay=True))

        self.pUpdate = pa.addChild({
            'name': 'Update calibration',
                    'type': 'action',
                    'visible': False})
        self.pUpdate.sigActivated.connect(self.updateCalibration)

    def _fromDisplay(self, display, n, layername):
        self.calFileTool.udpateFlatField(display.widget.image[n])

    def _buildRefImgMenu(self, menu):
        '''
        fill the menu with all available images within other displays
        '''
        menu.clear()

        def setRefImg(display):
            self._bg = display
            menu.setTitle(display.name()[:20])

        for d in self.display.workspace.displays():
            if isinstance(d.widget, ImageWidget) and d != self.display:
                menu.addAction(d.name()).triggered.connect(
                    lambda checked, d=d: setRefImg(d))

    def updateCalibration(self):
        if self.outDisplay is None:
            raise Exception('need to create flat field map first')
        self.calFileTool.udpateFlatField(self.outDisplay.widget.image[0])

#     def _fnImgAvg(self, imgs):
#         ff = FlatFieldFromImgFit(imgs)
#         if self.pFitMethod.value() == 'fit vignetting function':
#             try:
#                 out, bglevel = ff.flatFieldFromFunction()[:2]
#             except RuntimeError:
#                 print(
#                     "couldn't fit vignetting function - fit polynomial instead")
#                 out, bglevel = ff.flatFieldFromFit()[:2]
#         else:
#             out, bglevel = ff.flatFieldFromFit()[:2]
#         print('background level = %s' % bglevel)
#         return out

    def activate(self):
        self.startThread(self._calc, self._done)

    def _calc(self):
        # TODO: add standard deviation map
        img = self.getImageOrFilenames()

        # if self.pMethod.value() == 'from calibration images':
        if self._bg is None:
            print('assume images are already background corrected')
            bgimg = 0
        else:
            bgimg = self._bg.widget.image
            if img is None:
                img = self._bg.filenames
        th = None
        if not self.pEsimateTresh.value():
            th = self.pThresh.value()

        fn = self._m[self.pMethod.value()]
        try:
            out = fn(img, bgimg, thresh=th)
        except TypeError:
            out = fn(img, bgimg)

        if type(out) is tuple:
            ff, mask = out
#             print(mask)
#             mask = mask.astype(bool)
        else:
            ff, mask = out, None
        v = self.pFitMethod.value()
        if v == '-':
            return ff
        return FlatField._postProcessing(ff, v, mask)

    def _done(self, out):
        self.outDisplay = self.handleOutput([out], title='flat field')
        self.pUpdate.show()
