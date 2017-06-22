import numpy as np
from dataArtist.widgets.Tool import Tool


def _import():
    global maximum_filter, PerspectiveGridROI, labelCracks, evalCracks, detectLabelCrackParams
    from scipy.ndimage.filters import maximum_filter
    from dataArtist.items.PerspectiveGridROI import PerspectiveGridROI

    try:
        from PROimgProcessor.features.crackDetection import labelCracks, evalCracks,\
            detectLabelCrackParams
    except ImportError:
        labelCracks = None


class CrackDetection(Tool):
    '''
    '''
    icon = 'crackDetection.svg'

    def __init__(self, display):
        Tool.__init__(self, display)
        _import()

        pa = self.setParameterMenu()
        # TODO: [ALLWAYS NEW] is only because later self.handleOUtput
        # is called 2x - currently this fn only works with one output display..
        # --> implement n. output displays as disct by given title
        self.createResultInDisplayParam(pa, value='[ALLWAYS NEW]')

        self.pMask = pa.addChild({
            'name': 'Grid mask',
            'type': 'menu',
            'value': '-'})
        self.pMask.aboutToShow.connect(self._buildGridMaskMenu)

        self.pDark = pa.addChild({
            'name': 'Cracks are dark',
            'type': 'bool',
            'value': True})

        self.pWidth = pa.addChild({
            'name': 'Crack width',
            'type': 'int',
            'value': 3,
            'limits': (1, 100)})

        # TODO: find better name
        self.pDebug = pa.addChild({
            'name': 'Debug',
            'type': 'bool',
            'value': False})

        self.pDetect = pa.addChild({
            'name': 'Detect parameters',
            'type': 'bool',
            'value': True})

        pGrad = pa.addChild({
            'name': 'Gradient',
            'type': 'empty',
            'visible': False})

        self.pKSizeIntensity = pGrad.addChild({
            'name': 'Kernel size',
            'type': 'int',
            'value': 9,
            'limits': (1, 101)})

        self.pThreshIntensity = pGrad.addChild({
            'name': 'Threshold',
            'type': 'float',
            'value': 0.02,
            'min': 0,
            'tip': '...of the laplacian'})

        pProp = pa.addChild({
            'name': 'Propagation',
            'type': 'empty',
            'visible': False})

        self.pKSizeProp = pProp.addChild({
            'name': 'Kernel size',
            'type': 'int',
            'value': 21,
            'limits': (1, 101)})

        self.pThreshProp = pProp.addChild({
            'name': 'Like-likeness',
            'type': 'float',
            'value': 50,
            'limits': (0, 100),
            'suffix': '%',
            'tip': '...of the Laplacian'})

        self.pNorient = pProp.addChild({
            'name': 'N orientations',
            'type': 'int',
            'value': 8,
            'limits': (1, 30)})

        self.pDetect.sigValueChanged.connect(
            lambda _p, v: [pa.show(not v) for pa in (pGrad, pProp)])

    def _buildGridMaskMenu(self, menu):
        menu.clear()
        menu.addAction('-')
        # SUBMENU FOR ALL DISPLAYS
        for name in self.display.widget.cItems.keys():
            menu.addAction(name).triggered.connect(
                lambda _checked, n=name: menu.setTitle(n))

#                     lambda _checked, d=d, n=n, l=l:
#                         triggerFn(d, n, l))
#             # ACTION FOR ALL LAYERS
#             for n, l in enumerate(d.layerNames()):
#                 name = '%s - %s' % (n, l)
#                 a = m.addAction(name)
#                 a.triggered.connect(
#                     lambda _checked, d=d, n=n, l=l:
#                         triggerFn(d, n, l))
#                 if updateMenuValue:
#                     a.triggered.connect(
#                         lambda _checked, name=name: menu.setTitle(name))
#
#
#         self.display.widget.cItems.items:

    def activate(self):
        self.startThread(self._process, self._done)

    def _process(self):
        d = self.display
        img = d.widget.image
        out = np.empty(shape=img.shape[:3], dtype=bool)
        width = self.pWidth.value()
        debug = self.pDebug.value()
        laps, linelikellyness, params = [], [], []
        ki = self.pKSizeIntensity.value()
        ki += 1 - ki % 2  # enusre odd number

        t = d.tools['Selection']
        path = t.findPath(PerspectiveGridROI)
        shape = path.nCells if path is not None else (6, 10)
        border = path.vertices() if path is not None else None
        if border is None:
            print('No [Grid] found, assume image is corrected and there is \
no border around the image')

        v = self.pMask.value()
        if v != '-':
            grid = d.widget.cItems[v].image_full
        else:
            grid = None
            print('Please define [Grid Mask] to improve precision')

        for n, im in enumerate(img):

            if self.pDetect.value():
                kwargs = detectLabelCrackParams(img, shape)
                self.pKSizeProp.setValue(kwargs['ksize_length'])
                self.pThreshProp.setValue(kwargs['thresh_length'] * 100)
                self.pKSizeIntensity.setValue(kwargs['ksize_intensity'])
                self.pThreshIntensity.setValue(kwargs['thresh_intensity'])
            else:
                kwargs = dict(ksize_intensity=ki,
                              ksize_length=self.pKSizeProp.value(),
                              thresh_length=self.pThreshProp.value() / 100,
                              norientations=self.pNorient.value(),
                              thresh_intensity=self.pThreshIntensity.value())

            cracks, h, orient, lap,  mx = labelCracks(im, grid,
                                                      cracks_are_bright=not self.pDark.value(),
                                                      **kwargs)
            params.append(evalCracks(cracks, h, orient, shape, border))
            if width > 1:
                cracks = maximum_filter(cracks, width)
            out[n] = cracks

            if debug:
                laps.append(lap)
                linelikellyness.append(mx)

        return out, laps, linelikellyness, params

    def _done(self, ooo):
        out, laps, linelikellyness, params = ooo

        self.display.widget.addColorLayer(
            layer=out,
            name='Cracks')

        if len(laps):
            self.handleOutput([laps, linelikellyness],
                              title='Debugging//CrackDetection',
                              names=['Laplacian', 'Line-likeness'])

        # TODO: all tables tabbed:
        for n, (crackLength, crackFragment, crackMainDir) in enumerate(params):
            d0 = self.display.workspace.addTableDock(name='crack length[%i]' % n,
                                                     array=crackLength)
            d1 = self.display.workspace.addTableDock(name='crack fragmentation[%i]' % n,
                                                     array=crackFragment)
            d2 = self.display.workspace.addTableDock(name='main crack direction (DEG)[%i]' % n,
                                                     array=crackMainDir)
            # tab all output tables:
            self.display.area.moveDock(d1, 'below', d0)
            self.display.area.moveDock(d2, 'below', d0)
