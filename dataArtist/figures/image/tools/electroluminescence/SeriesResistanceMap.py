from dataArtist.widgets.Tool import Tool
from dataArtist.items.PerspectiveGridROI import PerspectiveGridROI

try:
    from PROimgProcessor.electroluminescence.paramFromFilename \
        import paramFromFilename
    from PROimgProcessor.electroluminescence.seriesResistanceMapping \
        import seriesResistanceMapping
except ImportError:
    seriesResistanceMapping = None


class SeriesResistanceMap(Tool):
    '''
    Calculate a series resistance map from
    two EL images taken at different currents

    This tool needs both images to be in the same display.
    Both images need to be fully corrected including ...
    * background removal
    * flat field
    * artifacts
    * lens
    * perspective
    '''
    icon = 'seriesResistance.svg'

    def __init__(self, imageDisplay):
        Tool.__init__(self, imageDisplay)

        self.display.showToolBar('Measurement')

        pa = self.setParameterMenu()

        self.createResultInDisplayParam(pa)

        self.pParamFromName = pa.addChild({
            'name': 'Get parameters from filename',
            'type': 'bool',
            'value': True,
            'tip': '''Read voltage, current, temperature from filename
            Filename has to have to following formating:
            ...
            _e[EXPOSURE TIME IN MS]
            _V[VOLTAGE in V]
            _I[CURRENT IN A]
            _T[TEMPERATURE in DEG C]...
            float point number are written like that:
            '0-015' for 0.015
            '''})
        self.pParamFromName.sigValueChanged.connect(lambda p, v:
                                                    [ch.show(not(v))
                                                     for ch in p.childs])

        for name in ('First image', 'Second image'):
            ch = self.pParamFromName.addChild({
                'name': name,
                'type': 'empty',
                'highlight': True,
                'visible': False})
            ch.addChild({
                'name': 'Exposure time',
                'type': 'float',
                'suffix': 's',
                'siPrefix': True,
                'value': 10})
            ch.addChild({
                'name': 'Voltage',
                'type': 'float',
                'suffix': 'V',
                'siPrefix': True,
                'value': 10})
            ch.addChild({
                'name': 'Current',
                'type': 'float',
                'suffix': 'A',
                'siPrefix': True,
                'value': 10})
            ch.addChild({
                'name': 'Temperature',
                'type': 'float',
                'suffix': 'DEG C',
                'siPrefix': True,
                'value': 20})

    def activate(self):
        if seriesResistanceMapping is None:
            raise Exception(
                'proprietary module [%s] not found' % 'PROimgProcessor')
        self.startThread(self._process, self._done)

    def _process(self):
        w = self.display.widget
        img = w.image

        # get grid:
        t = self.display.tools['Selection']
        gridROI = None
        for gridROI in t.paths:
            if isinstance(gridROI, PerspectiveGridROI):
                break
        if not isinstance(gridROI, PerspectiveGridROI):
            t.pType.setValue('PerspectiveGrid')
            t.pNew.sigActivated.emit(t.pNew)
            print('Need to define grid first')
            return

        # checks:
        assert len(img) in (
            2, 3), 'need 2EL  OR 2EL and 1BG images in the display'

        # TODO: remove as soon as no diff convention...
        # yx vs xy convention:
        img1 = img[0]
        img2 = img[1]

        # remove background:
        if len(img) == 3:
            bg = img[2]
            img1 = img1 - bg
            img2 = img2 - bg

        # get variables:
        p = self.pParamFromName
        if p.value():
            f = self.display.filenames
            try:
                expTime1, voltage1, current1, temperature1 = paramFromFilename(
                    f[0].basename())
                expTime2, voltage2, current2, temperature2 = paramFromFilename(
                    f[1].basename())
            except Exception as e:
                raise Exception(
                    'Cannot extract parameters frmo file name: %s' % e)
        else:
            expTime1 = p.childs[0].param('Exposure time').value()
            expTime2 = p.childs[1].param('Exposure time').value()
            voltage1 = p.childs[0].param('Voltage').value()
            voltage2 = p.childs[1].param('Voltage').value()
            current1 = p.childs[0].param('Current').value()
            current2 = p.childs[1].param('Current').value()
            temperature1 = p.childs[0].param('Temperature').value()
            temperature2 = p.childs[1].param('Temperature').value()

        Rs, j0i, Ubias2grid = seriesResistanceMapping(
            img1, img2,
            voltage1, voltage2,
            current1, current2,
            temperature1, temperature2,
            module_length=None,  # cm

            grid=gridROI.nCells,
            border=gridROI.edges(),

            expTime1=expTime1,
            expTime2=expTime2,
            correct_perspective=False)

        return Rs, j0i,  Ubias2grid

    def _done(self, out):
        if out is not None:

            for arr, name in zip(out, ('Series resistance map [Ohm]',
                                       'Local dark saturation current density [A]',
                                       'Cell operating voltage [V]')):
                print(arr.shape, name)
                axes = self.display.axes.copy()
                axes[2].p.setValue(name)

                self.display.workspace.addDisplay(
                    origin=self.display,
                    data=[arr],
                    title=name, axes=axes)


#                 self.handleOutput([arr], title=name, axes=axes)
