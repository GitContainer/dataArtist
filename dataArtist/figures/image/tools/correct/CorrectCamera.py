# coding=utf-8
from dataArtist.widgets.Tool import Tool
from dataArtist.figures.image.tools.globals.CalibrationFile import CalibrationFile


class CorrectCamera(Tool):
    '''
    Correct for the following camera related distortions:

    1. Single time effects (only if multiple images are in display)
    2. Dark current (either calculated or given in other display)
    3. Vignetting/Sensitivity
    4. Image artifacts
    5. Blur (not at the moment)
    6. Lens distortion

    using a camera calibration file
    '''
    icon = 'correctCamera.svg'

    def __init__(self, display):
        Tool.__init__(self, display)

        self.calFileTool = self.showGlobalTool(CalibrationFile)
        self._bgDisplay = None

        pa = self.setParameterMenu()

        self.pCalName = pa.addChild({
            'name': 'Camera calibration',
            'type': 'str',
            'value': '',
            'readonly': True,
            'tip': "The current calibration file. To change, use 'CalibrationFile' tool button"})
        self._menu.aboutToShow.connect(self._updatepCal)

        self.createResultInDisplayParam(pa)

        self.pAllLayers = pa.addChild({
            'name': 'Execute on',
            'type': 'list',
            'value': 'all layers average',
            'tip': '''
all layers:
        average: all images are averaged and single time effects (STE) are removed
        indiviual: all images are corrected, no averaging, no ste removal
pair of two layers: every next 2 image are averaged and STE removed
current layer: only the current image is taken - no average, no STE removal
                    ''',
            'limits': ['CURRENT layer',
                       'ALL layers average',
                       'ALL layers individual',
                       'ALL as pair of two layers',
                       'LAST two layers']})

        self.pDeblur = pa.addChild({
            'name': 'Deblur',
            'type': 'bool',
            'value': False,
            'tip': 'Whether to deconvolute the image - this might take some minutes'})

        self.pDenoise = pa.addChild({
            'name': 'Denoise',
            'type': 'bool',
            'value': False,
            'tip': 'Remove noise using Non-Local Means Denoising - this takes some time'})

        self.pKeepSize = pa.addChild({
            'name': 'Keep size',
            'type': 'bool',
            'value': True})

        self.pBgMethod = pa.addChild({
            'name': 'Background',
            'type': 'list',
            'value': 'from display',
            'limits': ['calculate', 'from display']})
        self.pBgMethod.sigValueChanged.connect(self._pBgMethodChanged)

        self.pBgExpTime = self.pBgMethod.addChild({
            'name': 'Exposure time',
            'type': 'float',
            'value': 10,
            'suffix': 's',
            'siPrefix': True,
            'visible': False,
            'min': 0})

        self.pBgFromDisplay = self.pBgMethod.addChild({
            'name': 'From display',
            'type': 'menu',
            'value': '-'})
        self.pBgFromDisplay.aboutToShow.connect(
            lambda m, fn=self._setBGDisplay:
            self.buildOtherDisplaysMenu(
                m, fn))

        self.pThreshold = pa.addChild({
            'name': 'Artifact removal threshold',
            'type': 'slider',
            'value': 1,
            'limits': [0., 1.],
            'tip': '''0--> replace everything with median, 
0.9 --> replace with median if rel. difference [img]-[median] > 0.9
1 --> do nothing'''})

        self.pThreshold.sigValueChanged.connect(
            self._updateSlider)

    def _updateSlider(self, p, v):
        w = list(p.items.keys())[0].widget
        if v > 0.9:
            w.slider.setStyleSheet('')
        elif v > 0.7:
            w.slider.setStyleSheet("QSlider {background-color: orange;}")
        else:
            w.slider.setStyleSheet("QSlider {background-color: red;}")

    def _updatepCal(self):
        v = self.calFileTool.pCal.value()
        self.pCalName.setValue(v)
        hasCal = v != '-'
        self.pDeblur.show(hasCal)
        self.pDenoise.show(hasCal)
        self.pKeepSize.show(hasCal)
        if hasCal:
            self.pBgMethod.setOpts(readonly=False)
        else:
            self.pBgMethod.setOpts(value='from display', readonly=True)

    def _pBgMethodChanged(self, _param, value):
        '''
        show/hide right parameters for chosen option
        '''
        if value == 'calculate':
            self.pBgExpTime.show()
            self.pBgFromDisplay.hide()
        else:
            self.pBgFromDisplay.show()
            self.pBgExpTime.hide()

    def _setBGDisplay(self, display):
        self._bgDisplay = display

    def activate(self):
        '''
        open camera calibration and undistort image(s)
        '''
        self.startThread(self._process, self._done)

    def _process(self):
        w = self.display.widget
        im = w.image

        out = []

        # GET VARIABLES:
        bgImages = None
        exposureTime = None
        if self.pBgMethod.value() == 'calculate':
            exposureTime = self.pBgExpTime.value()
        elif self.pBgFromDisplay.value() != '-':
            bgImages = self._bgDisplay.widget.image

        l = len(im)
        wc = w.currentIndex
        #                      list of slices
        c = {'CURRENT layer': (wc,),
             'ALL layers average': (slice(None),),
             'ALL layers individual': range(l),
             'ALL as pair of two layers': [slice(i, i + 1) for i in range(l)[::2]],
             'LAST two layers': (slice(-2, None),)
             }[
            self.pAllLayers.value()]

        for i in c:
            out.append(self.calFileTool.correct(
                images=im[i],
                exposure_time=exposureTime,
                bgImages=bgImages,
                threshold=self.pThreshold.value(),
                keep_size=self.pKeepSize.value(),
                deblur=self.pDeblur.value(),
                denoise=self.pDenoise.value())
            )
        return out

    def _done(self, out):
        self.handleOutput(out, title='corrected camera distortion',
                          changes='corrected camera distortion')
