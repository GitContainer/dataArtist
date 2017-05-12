# coding=utf-8
import cv2
import numpy as np

from fancywidgets.pyQtBased.Dialogs import Dialogs

from imgProcessor.transformations import toUIntArray, isColor
from imgProcessor.imgIO import imwrite
from imgProcessor.reader.qImageToArray import qImageToArray
from pyqtgraph_karl.functions import makeARGB, makeRGBA
from imgProcessor.interpolate.LinearInterpolateImageStack \
    import LinearInterpolateImageStack

from dataArtist.widgets.Tool import Tool


class SaveToFile(Tool):
    '''
    Save the display image to file
    '''
    icon = 'export.svg'

    def __init__(self, imageDisplay):
        Tool.__init__(self, imageDisplay)

        self._dialogs = Dialogs()

        ftypes = """Portable Network Graphics (*.png)
Windows bitmaps (*.bmp *.dib)
JPEG files (*.jpeg *.jpg *.jpe)
JPEG 2000 files (*.jp2)
Portable image format (*.pbm *.pgm *.ppm)
Sun rasters (*.sr *.ras)
TIFF files (*.tiff *.tif)"""

        self.engine = {'normal image':
                       (self.exportCV2,
                        ftypes),
                       '32bit floating-point TIFF file':
                       (self.exportFTiff,
                        'TIFF file (*.tiff)'),
                       'rendered':
                       (self.exportRendered,
                        ftypes),
                       'Numpy array':
                       (self.exportNumpy,
                        'Numpy array (*.npy)'),
                       'Txt file':
                       (lambda: self.exportNumpy(np.savetxt),
                        'Text file (*.txt)'),
                       'Video':
                       (self.exportVideo, 'Video file (*.avi *.png)'),
                       }
        pa = self.setParameterMenu()

        self.pExportAll = pa.addChild({
            'name': 'export all image layers',
            'type': 'bool',
            'value': False})

        self.pEngine = pa.addChild({
            'name': 'Type',
            'type': 'list',
            'value': 'normal image',
            'limits': list(self.engine.keys()),
            'tip': '''normal image: export the original image array
rendered: export the current display view'''})

        self.pRange = self.pEngine.addChild({
            'name': 'Range',
            'type': 'list',
            'value': 'current',
            'limits': ['0-max', 'min-max', 'current'],
            'visible': True})

        self.pDType = self.pEngine.addChild({
            'name': 'Bit depth',
            'type': 'list',
            'value': '16 bit',
            'limits': ['8 bit', '16 bit'],
            'visible': True})
        self.pDType.sigValueChanged.connect(self._pDTypeChanged)


#         self.pCutNegativeValues = self.pEngine.addChild({
#             'name': 'Cut negative values',
#             'type': 'bool',
#             'value':False,
#             'visible':True})
        self.pStretchValues = self.pEngine.addChild({
            'name': 'Stretch values',
            'type': 'bool',
            'value': True,
            'visible': True,
            'tip': '''If True, rather stretch intensities than
cut values higher than maximum image intensity'''})

        self.pOnlyImage = self.pEngine.addChild({
            'name': 'Only image',
            'type': 'bool',
            'value': False,
            'tip': '''True - export only the shown image
- excluding background and axes''',
            'visible': False})

        self.pEngine.sigValueChanged.connect(self._pEngineChanged)

        self.pResize = pa.addChild({
            'name': 'Resize',
            'type': 'bool',
            'value': False})

        self.pAspectRatio = self.pResize.addChild({
            'name': 'Keep Aspect Ratio',
            'type': 'bool',
            'value': True,
            'visible': False})

        self.pWidth = self.pResize.addChild({
            'name': 'Width',
            'type': 'int',
            'value': 0,
            'visible': False})
        self.pWidth.sigValueChanged.connect(self._pWidthChanged)

        self.pHeight = self.pResize.addChild({
            'name': 'Height',
            'type': 'int',
            'value': 0,
            'visible': False})
        self.pHeight.sigValueChanged.connect(self._pHeightChanged)

        self.pResize.addChild({
            'name': 'Reset',
            'type': 'action',
            'visible': False}).sigActivated.connect(self._pResetChanged)

        self.pResize.sigValueChanged.connect(lambda param, value:
                                             [ch.show(value)
                                              for ch in param.children()])

        self.pFrames = self.pEngine.addChild({
            'name': 'Frames per time step',
            'type': 'float',
            'value': 15,
            'limits': (1, 100),
            'visible': False})

        self.pPath = pa.addChild({
            'name': 'path',
            'type': 'str',
            'value': ''})

        pChoosePath = self.pPath.addChild({
            'name': 'choose',
            'type': 'action'})
        pChoosePath.sigActivated.connect(self._pChoosePathChanged)

        self._menu.aboutToShow.connect(self._updateOutputSize)
        self._menu.aboutToShow.connect(self._updateDType)

    def _pChoosePathChanged(self, _param):
        self._choosePath()
        self.activate()

    def _pResetChanged(self):
        try:
            self._menu.aboutToShow.disconnect(self._updateOutputSize)
        except:
            pass
        self._menu.aboutToShow.connect(self._updateOutputSize)
        self._updateOutputSize()

    def _pEngineChanged(self, _param, val):
        #         self.pCutNegativeValues.show(val == 'normal image')
        self.pStretchValues.show(val == 'normal image')
        self.pOnlyImage.show(val == 'rendered')
        self.pRange.show(val == 'normal image')
        self.pDType.show(val == 'normal image')
        self.pFrames.show(val == 'Video')

    def _updateOutputSize(self):
        if self.pEngine.value() == 'rendered':
            size = self.display.size()
            w = size.width()
            h = size.height()
        else:
            h, w = self.display.widget.image.shape[1:3]
        self.aspectRatio = h / w
        self.pWidth.setValue(w, blockSignal=self._pWidthChanged)
        self.pHeight.setValue(h, blockSignal=self._pHeightChanged)

    def _updateDType(self):
        w = self.display.widget
        if (w.levelMax - w.levelMin) > 255:
            self.pDType.setValue('16 bit', blockSignal=self._pDTypeChanged)
        else:
            self.pDType.setValue('8 bit', blockSignal=self._pDTypeChanged)

    def _pDTypeChanged(self):
        # dont change dtype automatically anymore as soon as user changed param
        try:
            self._menu.aboutToShow.disconnect(self._updateDType)
        except:
            pass

    def _pHeightChanged(self, _param, value):
        try:
            self._menu.aboutToShow.disconnect(self._updateOutputSize)
        except:
            pass
        if self.pAspectRatio.value():
            self.pWidth.setValue(int(round(value / self.aspectRatio)),
                                 blockSignal=self._pWidthChanged)

    def _pWidthChanged(self, _param, value):
        try:
            self._menu.aboutToShow.disconnect(self._updateOutputSize)
        except:
            pass
        if self.pAspectRatio.value():
            self.pHeight.setValue(int(round(value * self.aspectRatio)),
                                  blockSignal=self._pHeightChanged)

    def _choosePath(self):
        filt = self.engine[self.pEngine.value()][1]
        kwargs = dict(filter=filt,
                      # selectedFilter='png' #this option is not supported in
                      # PyQt5 any more
                      )
        f = self.display.filenames[0]
        if f is not None:
            kwargs['directory'] = f.dirname()

        path = self._dialogs.getSaveFileName(**kwargs)
        if path:
            self.pPath.setValue(path)

    def activate(self):
        # CHECK PATH
        if not self.pPath.value():
            self._choosePath()
            if not self.pPath.value():
                raise Exception('define a file path first!')

        self.engine[self.pEngine.value()][0]()

    def exportRendered(self):
        '''
        Use QPixmap.grabWidget(display) to save the image
        '''
        d = self.display
        try:
            # get instance back from weakref
            d = d.__repr__.__self__
        except:
            pass
        # PREPARE LAYOUT:
        d.release()
        d.hideTitleBar()

        if self.pResize.value():
            d.resize(self.pWidth.value(), self.pHeight.value())
        # SAVE:
        path = self.pPath.value()

        def grabAndSave(path2):
            if self.pOnlyImage.value():
                item = d.widget.imageItem
                b = item.sceneBoundingRect().toRect()
                w = d.widget.grab(b)  # QtGui.QPixmap.grabWidget(d.widget, b)
            else:
                w = d.grab()  # QtGui.QPixmap.grabWidget(d)
            w.save(path2)
            print('Saved image under %s' % path2)

        if self.pExportAll.value():
            # EACH LAYER SEPARATE
            old_i = d.widget.currentIndex
            for i in range(len(d.widget.image)):
                path2 = path.replace('.', '__%s.' % i)
                d.widget.setCurrentIndex(i)
                grabAndSave(path2)
            d.widget.setCurrentIndex(old_i)
        else:
            grabAndSave(path)
        # RESET LAYOUT:
        d.showTitleBar()
        d.embedd()

    def exportNumpy(self, method=np.save):
        '''
        Export as a numpy array *.npy
        '''
        path = self.pPath.value()
        w = self.display.widget
        image = w.image

        if not self.pExportAll.value():
            image = image[w.currentIndex]
        method(path, image)
        print('Saved image under %s' % path)

    def _export(self, fn):
        def export(img, path):
            if self.pResize.value():
                img = cv2.resize(
                    img, (self.pWidth.value(), self.pHeight.value()))
            fn(path, img)
            print('Saved image under %s' % path)
        w = self.display.widget
        image = w.image
        path = self.pPath.value()

        if self.pExportAll.value():
            for n, img in enumerate(image):
                path2 = path.replace('.', '__%s.' % n)
                export(img, path2)
        else:
            image = image[w.currentIndex]
            export(image, path)

    def exportFTiff(self):
        '''
        Use pil.Image.fromarray(data).save() to save the image array
        '''
        def fn(path, img):
            # float tiff only works if img is tiff:
            path = path.setFiletype('tiff')
            imwrite(path, img, dtype=float)
#             imwrite(path, transpose(img), dtype=float)
        return self._export(fn)

    def exportVideo(self):
        self.startThread(self._exportVideoThread)

    def _exportVideoThread(self):
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        ww = self.display.widget
        im = ww.image
        if self.pResize.value():
            w, h = (self.pWidth.value(), self.pHeight.value())
            im = [cv2.resize(i, (w, h)) for i in im]
        else:
            h, w = im.shape[1:3]
        fr = self.pFrames.value()
        pa = self.pPath.value()
        assert pa[-3:] in ('avi',
                           'png'), 'video export only supports *.avi or *.png'
        isVideo = pa[-3:] == 'avi'
        if isVideo:
            cap = cv2.VideoCapture(0)
            # im.ndim==4)
            out = cv2.VideoWriter(pa, fourcc, fr, (w, h), isColor=1)

        times = np.linspace(0, len(im), len(im) * fr)
        interpolator = LinearInterpolateImageStack(im)

        lut = ww.item.lut
        if lut is not None:
            lut = lut(im[0])

        for n, time in enumerate(times):
            # update progress:
            self._thread.sigUpdate.emit(100 * n / len(times))
            image = interpolator(time)

            argb = makeRGBA(image, lut=lut,
                            levels=ww.item.levels)[0]
            cimg = cv2.cvtColor(argb, cv2.COLOR_RGBA2BGR)

            if isVideo:
                out.write(cimg)
            else:
                cv2.imwrite('%s_%i_%.3f.png' % (pa[:-4], n, time), cimg)

        if isVideo:
            cap.release()
            out.release()

    def exportCV2(self):
        '''
        Use cv2.imwrite() to save the image array
        '''
        w = self.display.widget

        def fn(path, img):
            r = self.pRange.value()
            if r == '0-max':
                r = (0, w.levelMax)
            elif r == 'min-max':
                r = (w.levelMin, w.levelMax)
            else:  # 'current'
                r = w.ui.histogram.getLevels()
            int_img = toUIntArray(img,
                                  # cutNegative=self.pCutNegativeValues.value(),
                                  cutHigh=~self.pStretchValues.value(),
                                  range=r,
                                  dtype={'8 bit': np.uint8,
                                         '16 bit': np.uint16}[
                                      self.pDType.value()])
            if isColor(int_img):
                int_img = cv2.cvtColor(int_img, cv2.COLOR_RGB2BGR)

            cv2.imwrite(path, int_img)

        return self._export(fn)
