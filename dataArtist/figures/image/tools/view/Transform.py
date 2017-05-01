# coding=utf-8
from imgProcessor.transformations import transpose, rot90
import numpy as np

# OWN
from dataArtist.widgets.Tool import Tool
from pyqtgraph.widgets.JoystickButton import JoystickButton

# TODO: SCALE/ROTATE DEG

class Transform(Tool):
    '''
    General image transformations
    '''
    icon = 'rotate.svg'

    def __init__(self, display):
        Tool.__init__(self, display)

        self._lastMoveVal = [0, 0]

        pa = self.setParameterMenu()

        joy = JoystickButton()
        joy.sigStateChanged.connect(self._move_joystickChanged)
        self._menu.addTopWidget(joy)

        self.pX = pa.addChild({
            'name': 'X',
            'type': 'int',
            'value': 0, })
        self._pxChanged = lambda param, val, axis=1: self._move_pXYChanged(val, axis)
        self.pX.sigValueChanged.connect(self._pxChanged)

        self.pY = pa.addChild({
            'name': 'Y',
            'type': 'int',
            'value': 0, })
        self._pyChanged = lambda param, val, axis=0: self._move_pXYChanged(val, axis)
        self.pY.sigValueChanged.connect(self._pyChanged)

        pAccept = pa.addChild({
            'name': 'Accept',
            'type': 'action'})
        pAccept.sigActivated.connect(self._move_acceptChanges)

        pReset = pa.addChild({
            'name': 'Reset',
            'type': 'action'})
        pReset.sigActivated.connect(self._move_resetChanges)


        pa.addChild({
            'name': '---',
            'type': 'empty'})

        pTranspose = pa.addChild({
            'name': 'Rotate 90 DEG',
            'type': 'action'})
        pTranspose.sigActivated.connect(self._rot90)

        pTranspose = pa.addChild({
            'name': 'Transpose',
            'type': 'action'})
        pTranspose.sigActivated.connect(self._transpose)

        pMirrorX = pa.addChild({
            'name': 'Flip Horizontally',
            'type': 'action'})
        pMirrorX.sigActivated.connect(self._mirrorX)

        pMirrorY = pa.addChild({
            'name': 'Flip Vertically',
            'type': 'action'})
        pMirrorY.sigActivated.connect(self._mirrorY)


    def _move_joystickChanged(self, joystick, xy):
        self.pX.setValue(self.pX.value() + int(xy[0] * 10))
        self.pY.setValue(self.pY.value() + int(xy[1] * 10))


    def _move_pXYChanged(self, value, axis):
        w = self.display.widget
        c = w.currentIndex
        im = w.image
        stack = False
        if im.ndim == 3:
            stack = True
            im = im[c]
        # MOve:
        im = np.roll(im, value - self._lastMoveVal[axis], axis)
        if stack:
            w.image[c] = im
        else:
            w.image = im
        w.imageItem.updateImage(im)
        self._lastMoveVal[axis] = value


    def _move_acceptChanges(self):
        self.pX.setValue(0, blockSignal=self._pxChanged)
        self.pY.setValue(0, blockSignal=self._pyChanged)
        self._lastMoveVal = [0, 0]


    def _move_resetChanges(self):
        self.pX.setValue(0)
        self.pY.setValue(0)


    def _transpose(self):
        w = self.display.widget
        i = w.image
        w.setImage(transpose(i))

    def _mirrorX(self):
        w = self.display.widget
        i = w.image
        w.setImage(i[:, ::-1])

    def _mirrorY(self):
        w = self.display.widget
        i = w.image
        w.setImage(i[:, :, ::-1])

    def _rot90(self):
        w = self.display.widget
        i = w.image
        w.setImage(rot90(i))

        # rotate axes:
        v = w.view
        a1 = v.axes['bottom']['item']
        a2 = v.axes['left']['item']
        v.setAxes({'bottom': a2, 'left': a1})
