# coding=utf-8
import numpy as np

from imgProcessor.transform.StitchImages import StitchImages

from dataArtist.widgets.Tool import Tool


class InPlaneImageStitching(Tool):
    '''
    Stitch two images at a given edge together.
    Find the right overlap through template matching

    ...works on unloaded images too

    '''
    icon = 'imgStitching.svg'

    def __init__(self, imageDisplay):
        Tool.__init__(self, imageDisplay)

#         self._refImg = None
        self._refTool = None

        pa = self.setParameterMenu()
        self.createResultInDisplayParam(pa)

        self.pSide = pa.addChild({
            'name': 'Side',
            'type': 'list',
            'value': 'bottom',
            'limits': ['bottom', 'top', 'left', 'right'],
            'tip': 'stitch-position of layer[1...n] relative to layer[0]'})

#         pImgChoose = pa.addChild({
#             'name': 'add to image',
#                     'value': 'from display',
#                     'type': 'menu'})
#
#         self.pImg = pImgChoose.addChild({
#             'name': 'chosen',
#                     'value': '-',
#                     'type': 'str',
#                     'readonly': True})
#         pImgChoose.aboutToShow.connect(self.buildImgMenu)

        self.pBgColor = pa.addChild({
            'name': 'Background colour',
            'type': 'list',
            'value': '0',
            'limits': ['-', '0', 'np.nan']})

        self.pOverlap = pa.addChild({
            'name': 'Overlap',
                    'type': 'int',
                    'value': 250,
                    'min': 0})

        self.pOverlapDev = self.pOverlap.addChild({
            'name': 'Deviation',
                    'type': 'int',
                    'value': 50,
                    'min': 0})

        self.pRot = pa.addChild({
            'name': 'Rotation [DEG]',
                    'type': 'float',
                    'value': 0,
                    'limits': [-45, 45]})
        self.pRotDev = self.pRot.addChild({
            'name': 'Deviation',
                    'type': 'float',
                    'value': 1,
                    'limits': [0, 20]})

        self.pSet = pa.addChild({
            'name': 'Set parameters to result',
                    'type': 'bool',
                    'value': False,
                    'tip': 'Activate, to set overlap and rotation to found result'})
        pRefDispl = pa.addChild({
            'name': 'Take values from Display',
                    'type': 'menu',
                    'value': '-',
                    'tip': '###################'})

        pRefDispl.aboutToShow.connect(lambda menu:
                                      self.buildOtherDisplaysMenu(
                                          menu, self._setRefDisplay))

    def _setRefDisplay(self, display):
        self._refTool = display.tools[self.__class__.__name__]

    # TODO: replace with buildOtherDisplayLayersMenu
#     def buildImgMenu(self, menu):
#         '''
#         fill the menu with all available images within other displays
#         '''
#         menu.clear()
#         for d in self.display.workspace.displays():
#             if d.widget.__class__ == self.display.widget.__class__:
#                 m = menu.addMenu(d.name())
#                 for n, l in enumerate(d.layerNames()):
#                     m.addAction(l).triggered.connect(
#                         lambda _checked, d=d, n=n, l=l:
#                             self.setRefImg(d, n, l))
#                     if d == self.display:
#                         # allow only to choose first layer from same display
#                         break
#
#     def setRefImg(self, display, layernumber, layername):
#         '''
#         extract the reference image and -name from a given display and layer number
#         '''
#         self._refDisplay = display
#         self._refLayer = layernumber if layernumber else None
#         im = display.widget.image
#         if im is None:
#             # TODO: reader callable instead of filenames
#             self._refImg = display.filenames[layernumber]
#         else:
#             self._refImg = im[layernumber]
#
#         self.pImg.setValue(layername)

    def activate(self):
        self.startThread(self._process, self._done)

    def _process(self):
        #         d = self.display
        im = self.getDataOrFilenames()
#
#         if self._refImg is None:
#             # try to take first layer of current display:
#             n = d.layerNames()
#             if len(n) > 1:
#                 self.setRefImg(d, 0, n[0])
#         if self._refImg is None:
#             raise Exception('Need to define reference image first')

        refImg = im[0]
        assert len(im) > 1, 'need at least 2 images'
        im = im[1:]

        st = StitchImages(refImg)

#         if self._refDisplay.number == d.number:

        bgcol = {'0': 0,
                 'np.nan': np.nan,
                 '-': None}
        out = None

        if self._refTool:
            try:
                params = self._refTool._lastParams
            except AttributeError:
                raise Exception('Tool from display [%] was not executed so far'
                                % self._refTool.display.number())

        c = 0
        self._lastParams = []
        for i in im:
            if i is not None:

                if self._refTool:
                    kwargs = dict(side=self._refTool.pSide.value(),
                                  backgroundColor=bgcol[
                                      self._refTool.pBgColor.value()],
                                  params=params[c])

                    c += 1
                    if c == len(params):
                        c = 0

                else:
                    kwargs = dict(side=self.pSide.value(),
                                  backgroundColor=bgcol[self.pBgColor.value()],
                                  overlap=self.pOverlap.value(),
                                  overlapDeviation=self.pOverlapDev.value(),
                                  rotation=self.pRot.value(),
                                  rotationDeviation=self.pRotDev.value())

                out = st.addImg(i, **kwargs)

                self._lastParams.append(st.lastParams)

                if self.pSet.value():
                    offs, rot = st.lastParams[1:]
                    self.pOverlap.setValue(offs)
                    self.pOverlapDev.setValue(0)
                    self.pRot.setValue(rot)
                    self.pRotDev.setValue(0)

        return out

    def _done(self, out):
        self.handleOutput([out], title='stiched',
                          changes='stitched', names=['stitched'])
