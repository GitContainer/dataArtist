import numpy as np
from dataArtist.widgets.Tool import Tool
from PROimgProcessor.features.crackDetection import labelCracks, evalCracks,\
    detectLabelCrackParams
from scipy.ndimage.filters import maximum_filter


try:
    pass
except ImportError:
    seriesResistanceMapping = None


class CrackDetection(Tool):
    '''
    '''
    icon = 'crackDetection.svg'

    def __init__(self, display):
        Tool.__init__(self, display)

        pa = self.setParameterMenu()
        # TODO: [ALLWAYS NEW] is only because later self.handleOUtput
        # is called 2x - currently this fn only works with one output display..
        # --> implement n. output displays as disct by given title
        self.createResultInDisplayParam(pa, value='[ALLWAYS NEW]')

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
            'limits': (0, 1e5),
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
            'name': 'Threshold',
            'type': 'float',
            'value': 0.01,
            'limits': (0, 1e5),
            'tip': '...of the Laplacian'})

        self.pNorient = pProp.addChild({
            'name': 'N orientations',
            'type': 'int',
            'value': 8,
            'limits': (1, 30)})

        self.pDetect.sigValueChanged.connect(
            lambda _p, v: [pa.show(not v) for pa in (pGrad, pProp)])

        # mask frmo clayer
        # ncells from selection
        # opt lap, linelikellyness auszugeben

    def activate(self):
        img = self.display.widget.image
        out = np.empty_like(img, dtype=bool)
        width = self.pWidth.value()
        debug = self.pDebug.value()
        laps, linelikellyness, params = [], [], []
        ki = self.pKSizeIntensity.value()
        ki += 1 - ki % 2  # enusre odd number

        for n, im in enumerate(img):
            shape = (6, 10)

            if self.pDetect.value():
                kwargs = detectLabelCrackParams(img, shape)
            else:
                kwargs = dict(ksize_intensity=ki,
                              ksize_len=self.pKSizeProp.value(),
                              thresh_length=self.pThreshProp.value(),
                              norientations=self.pNorient.value())

            grid = im == 0
            border = None

    #######
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

        self.display.widget.addColorLayer(
            layer=out,
            name='Cracks')

        if debug:
            self.handleOutput(laps, title='Laplacian')
            self.handleOutput(linelikellyness, title='Line-likeness')

        for n, (crackLength, crackFragment, crackMainDir) in enumerate(params):
            self.display.workspace.addTableDock(name='crack length[%i]' % n,
                                                array=crackLength)
            self.display.workspace.addTableDock(name='crack fragmentation[%i]' % n,
                                                array=crackFragment)
            self.display.workspace.addTableDock(name='main crack direction (DEG)[%i]' % n,
                                                array=crackMainDir)
