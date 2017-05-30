# coding=utf-8
import cv2
import numpy as np

import pyqtgraph_karl as pg
from qtpy import QtCore
from pyqtgraph_karl import ImageView
from collections import OrderedDict

from fancytools.os.PathStr import PathStr
from fancytools.utils.incrementName import incrementName
from imgProcessor.transform.PerspectiveImageStitching import PerspectiveImageStitching as PerspectiveTransformation
from imgProcessor.transformations import isColor, toColor, toGray, isRot90, rot90

# OWN
from dataArtist.items.ColorLayerItem import ColorLayerItem
from dataArtist.figures._PyqtgraphgDisplayBase import PyqtgraphgDisplayBase
from dataArtist.figures.DisplayWidget import DisplayWidget
from dataArtist.widgets.dialogs.DifferentShapeDialog import DifferentShapeDialog
# from matplotlib.backends.qt_compat import QtWidgets
from imgProcessor.imgSignal import scaleSignalCutParams


class ImageWidget(DisplayWidget, ImageView, PyqtgraphgDisplayBase):
    '''
    A pyqtgraph.ImageView with methods to add/move/remove images
    as layer or colour-layer
    '''
    dimensions = (3, 4)
    icon = PathStr.getcwd('dataArtist').join('media', 'icons', 'image.svg')
    sigOverlayAdded = QtCore.Signal(object, object, object)  # item, name, tip
    sigOverlayRemoved = QtCore.Signal(object)  # item

    shows_one_layer_at_a_time = True

    def __init__(self, display, axes, data=None, names=None, **kwargs):
        for a in axes:
            a.setPen()  # update colour theme

        ImageView.__init__(
            self, view=pg.PlotItem(
                axisItems={
                    'bottom': axes[0],
                    'left': axes[1]})
        )
        PyqtgraphgDisplayBase.__init__(self)
        DisplayWidget.__init__(self, **kwargs)

        self.display = display
        self.moveLayerToNewImage = None
        self.cItems = OrderedDict()  # colorlayerItems

        self.sigTimeChanged.connect(self.display.highlightLayer)

        # for unified access within different widgets:
        self.item = self.imageItem
        self.setTitle = self.view.setTitle

        self._firstTime = True
        self._changed = False
        self._timeline_visible = True
        self._image_redefined = False
        self._moved_layer = None
        self._set_kwargs = {}

        self.opts['discreteTimeLine'] = True

        # TODO: better would be to init imageView with given histrogramAxis
        #      ... but this is easier:
        axes[2].sigLabelChanged.connect(self.setHistogramLabel)
        self.setHistogramLabel(axes[2].labelText)
        axes[2].sigRangeChanged.connect(self.ui.histogram.axis.setRange)
        axes[2].sigFontSizeChanged.connect(self._setHistogramFontSize)

        # hide buttons
        self.ui.roiBtn.hide()
        self.ui.menuBtn.hide()
        # fixed height for time axis:
        self.ui.splitter.setSizes([self.height() - 35, 35])
        self.ui.splitter.setStretchFactor(0, 1)
        # Remove ROI plot:
        self.ui.roiPlot.setMouseEnabled(False, False)
        self.ui.roiPlot.hide()

        # -------------------
        # Context menu over colorbar histogram:
        vb = self.ui.histogram.vb
        menu = vb.menu
        # remove 'Export...' menu:
        vb.raiseContextMenu = self._cbar_raiseContextMenu
        # remove mouse mode
        menu.removeAction(menu.leftMenu.menuAction())
        # remove redundsant menus:
        menu.removeAction(
            next(a for a in menu.actions() if a.text() == 'X Axis'))
#         menu.removeAction(
#             next(a for a in menu.actions() if 'Export' in a.text()))
        # y-Axis menu
        yAxisAction = next(a for a in menu.actions() if a.text() == 'Y Axis')
        yAxisAction.setText('Scale')
        # connect min-max edit with cbar intensity range change:
        menu.ctrl[-1].minText.editingFinished.connect(self._cbar_updateRange)
        menu.ctrl[-1].maxText.editingFinished.connect(self._cbar_updateRange)
        # add cbar fit:
        menu.addAction('Fit').triggered.connect(self._cbar_fit)
        # -------------------

    def _cbar_updateRange(self):
        c = self.ui.histogram.vb.menu.ctrl[-1]
        mn = float(c.minText.text())
        mx = float(c.maxText.text())
        self.ui.histogram.item.setLevels(mn, mx)

    def _cbar_fit(self):
        img = self.image[self.currentIndex]
        r = scaleSignalCutParams(img, 0.01)
        self.ui.histogram.setLevels(*r)

    def _cbar_raiseContextMenu(self, ev):
        vb = self.ui.histogram.vb
        menu = vb.getMenu(ev)
        menu.popup(ev.screenPos().toPoint())

    def setOpts(self, **opts):
        self.opts.update(opts)

    @staticmethod
    def getNLayers(data):
        if data is None:
            return 0
        s = data.shape
        l = data.ndim
        if l == 2:
            return 1
        if l == 3:
            if s[-1] in (3, 4):
                return 1
            return s[0]
        if l == 4:
            if s[-1] in (3, 4):
                return s[0]
        return 0

    def close(self):
        self.sigTimeChanged.disconnect(self.display.highlightLayer)

        self.clear()  # free memory
        try:
            ImageView.close(self)
        except TypeError:
            pass

    def roiClicked(self):
        '''not used'''
        pass

    def roiChanged(self):
        '''not used'''
        pass

    def saveState(self):
        state = DisplayWidget.saveState(self)
        state['view'] = self.view.vb.getState()
        state['histogram'] = self.ui.histogram.vb.getState()
        state['histoRegion'] = self.ui.histogram.getLevels()
        state['colorbar'] = self.ui.histogram.gradient.saveState()
        state['currentIndex'] = self.currentIndex
        state['image'] = self.image
        return state

    def restoreState(self, state):
        self.view.vb.setState(state['view'])
        self.ui.histogram.vb.setState(state['histogram'])
        self.ui.histogram.setLevels(*state['histoRegion'])
        self.ui.histogram.gradient.restoreState(state['colorbar'])
        img = state['image']
        if img is not None:
            self.setImage(img, autoRange=False, autoLevels=False,
                          autoHistogramRange=False)
        try:
            self.setCurrentIndex(state['currentIndex'])
        except AttributeError:
            # cannot set index, because has no layers
            pass
        DisplayWidget.restoreState(self, state)

    def showTimeline(self, show=True):
        self._timeline_visible = show
        if show and len(self.image) > 1:
            self.ui.roiPlot.show()
        else:
            self.ui.roiPlot.hide()

    def setColorLayer(self, layer, **kwargs):
        '''
        same as addColorLayer, but replaces citem, if existent
        '''
        name = kwargs.get('name', None)
        if name:
            item = self.cItems.get(name, None)
            if item:
                return item.setLayer(layer)
        return self.addColorLayer(layer, **kwargs)

    def addColorLayer(self, layer=None, name='Unnamed', tip='',
                      color=None, alpha=0.5):
        '''
        add a [layer], a np.array (2d or 3d), as colour overlay to the image
        '''
        if layer is None:
            s = self.image.shape
            if len(s) == 4:  # multi layer color image
                s = s[1:-1]
            elif len(s) == 3:
                if s[-1] == 3:  # single layer color image
                    s = s[:-1]
                else:  # multi layer grey image
                    s = s[1:]
            layer = np.zeros(shape=s)

        if isColor(layer):
            layer = toGray(layer)

        if color is None:
            # set colour as function of the number of colorItems:
            color = pg.intColor(len(self.cItems)).rgb()

        cItem = ColorLayerItem(layer,
                               imageWidget=self,
                               color=color,
                               alpha=alpha
                               )
        name = incrementName(list(self.cItems.keys()), name)
        self.cItems[name] = cItem
        self.view.addItem(cItem)
        self.sigOverlayAdded.emit(cItem, name, tip)
        return cItem

    def removeColorLayer(self, nameOrItem):
        if isinstance(nameOrItem, ColorLayerItem):
            for name, item in self.cItems.items():
                if item == nameOrItem:
                    break
        else:
            name = nameOrItem
        item = self.cItems.pop(name)
        self.view.removeItem(item)
        self.sigOverlayRemoved.emit(item)
        del item

    def _setHistogramFontSize(self, ptSize):
        '''
        set font size of the histogram and change the size of the
        viewBox that contain the image and the histogram accordingly
        '''
        vb = self.ui.histogram.vb
        if not hasattr(self, '_initHistWidth'):
            w = self._initHistWidth = vb.width()
        else:
            w = self._initHistWidth
        vb.setFixedWidth(w * (9.0 / ptSize))
        self.ui.histogram.axis.setFontSize(ptSize)
        self.ui.histogram.axis.update()

    def insertLayer(self, index, name=None, data=None):
        '''
        insert a new image as layer
        ...add new / override existing layer
        ...show dialog when data.shape != self.image.shape
        '''
        if data is not None:
            try:
                self.image = np.insert(self.image, index, data, axis=0)

            except IndexError:
                index = -1
                self.image = np.insert(self.image, index, data, axis=0)

            except (ValueError, MemoryError):
                if index == 0 and len(self.image) == 1:
                    # replace, if only has one layer
                    self.image = np.expand_dims(data, axis=0)
                else:
                    if isinstance(data, list):
                        data = data[0]

                    s1 = self.image[0].shape
                    s2 = data.shape
                    # LAYER COLOR IS DIFFERENT:
                    c1 = isColor(self.image[0])
                    c2 = isColor(data)
                    if c1 and not c2:
                        data = toColor(data)
                        s2 = data.shape
                    elif not c1 and c2:
                        self.image = toColor(self.image)
                        s1 = self.image[0].shape
                    if s1 != s2:
                        if isRot90(s1, s2):
                            print('Image is rotated 90DEG.')
                            data = rot90(data)
                        else:
                            # NEW LAYER SHAPE DOESNT FIT EXISTING:
                            ###show DIALOG#####
                            d = DifferentShapeDialog(name, s1, s2)
                            d.exec_()

                            r = d.opt
                            if r == d.optNewDisplay:
                                self.moveLayerToNewImage = index
                                return
                            elif r == d.optCut:
                                data = data[0:s1[0], 0:s1[1]]
                                if data.shape != s1:
                                    d = np.zeros(s1)
                                    d[0:s2[0], 0:s2[1]] = data
                                    data = d
                            elif r == d.optResize:
                                data = cv2.resize(data, (s1[1], s1[0]))

                            elif r == d.optWarp:
                                data = PerspectiveTransformation(
                                    self.image[-1]).fitImg(data)

                    self.image = np.insert(self.image, index, data, axis=0)

            self.currentIndex = index
            self.setImage(self.image)
            return self.image[index]

    def insertMovedLayer(self, index):
        self.insertLayer(index, data=self._moved_layer)

    def addLayer(self, name=None, data=None, index=None):
        '''
        add a new image as layer the the and of the image stack
        '''
        if self.image is not None:
            if index is None:
                index = len(self.image)
            self.insertLayer(index, data=data)
        else:
            self.update(data)
        self.updateView()
        if self.image is not None:
            self.setCurrentIndex(len(self.image))

    def removeLayer(self, index, toMove=False):
        if self.moveLayerToNewImage is None or self.moveLayerToNewImage != index:
            if toMove:
                if self.image is not None:
                    self._moved_layer = self.image[index]
                else:
                    self._moved_layer = None
            self.image = np.delete(self.image, index, axis=0)
            s = self.image.shape[0]
            if s == 0:
                self.image = None
                self.imageDisp = None
                self.item.clear()
            else:
                # TODO: has last index, if addWidget was called before
                    # therefore index cannot be preserved when layers are
                    # limited
                i = self.currentIndex
                if index != 0 and i == index:
                    i -= 1
                self.setImage(self.image)
                self.setCurrentIndex(i)
        # reset:
        self.moveLayerToNewImage = None

    def clear(self):
        self.setImage(np.zeros((1, 3, 3)))
        self.image = None
        for name in self.cItems:
            self.removeColorLayer(name)

    def getData(self, index=None):
        '''
        return all image layers or one specified by index
        '''
        if self.image is None:
            return None
        if index is not None:
            return self.image[index]
        return self.image

    def update(self, data=None, index=None, label=None, **kwargs):
        '''
        update either the full image or an image layer
        '''
        if data is not None:
            data = np.asarray(data)
            if index is not None and self.image is not None:
                try:
                    self.image[index] = data
                except (ValueError, IndexError):
                    self.insertLayer(index, name=label, data=data)
            else:
                # set all layers
                if (data.ndim == 2  # single grayscale
                        or data.ndim == 3
                        and data.shape[2] in (3, 4)):  # single color
                    data = np.expand_dims(data, axis=0)
                if self.image is None or self.image.shape != data.shape:
                    self._image_redefined = True
                self.image = data
        self._set_kwargs = kwargs
        self._set_index = index
        self._changed = True

    def updateView(self, force=False):
        '''
        update the visual representation
        '''
        if self.image is not None and (force or self._changed):
            if self._image_redefined or self._firstTime:
                self.setImage(self.image, **self._set_kwargs)
                self._firstTime = False
                self._image_redefined = False

            elif (force or self._set_index is None or
                  self._set_index == self.currentIndex):
                # needed by ImageView to set histogram levels
                self.imageDisp = None
                self.updateImage(**self._set_kwargs)
                if self.opts['autoLevels']:
                    self.autoLevels()
            self._changed = False

    def updateImage(self, autoHistogramRange=None, levels=None):
        '''
        overwrite original method to hide timeline when
        3d image has only one layer
        '''
        # Redraw image on screen
        if self.image is None:
            return

        if autoHistogramRange is None:
            autoHistogramRange = self.opts['autoHistogramRange']

        if levels is not None:
            self.setLevels(*levels)

        image = self.getProcessedImage()

        if autoHistogramRange:
            if np.isinf(self.levelMax):
                # otherwise crashes when loading images containing inf
                self.levelMax = self.quickMinMax(image[np.isfinite(image)])[1]
            self.ui.histogram.setHistogramRange(self.levelMin, self.levelMax)

        if self.axes['t'] is not None:
            # show/hide timeline:
            self.ui.roiPlot.setVisible(
                self.image.shape[0] > 1 and self._timeline_visible)
            image = image[self.currentIndex]

        # ensure initial right scaling (not done when image is [0...1]
        # TODO: fix the origin bug
        if image.dtype == bool:
            return self.imageItem.updateImage(image, levels=(0., 1.))

        # else: #TODO: dA crashes with self.levelMin == self.levelMax
        elif self.levelMin != self.levelMax:
            self.imageItem.updateImage(image)
