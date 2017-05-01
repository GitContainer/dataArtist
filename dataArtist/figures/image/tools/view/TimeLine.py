# coding=utf-8
from dataArtist.widgets.Tool import Tool

from imgProcessor.interpolate.LinearInterpolateImageStack import LinearInterpolateImageStack

from qtpy import QtWidgets


class TimeLine(Tool):
    '''
    Show/Hide the time line
    '''
    icon = 'timeLine.svg'

    def __init__(self, imageDisplay):
        Tool.__init__(self, imageDisplay)
        self.setChecked(True)

        self._connected = []
        self.interpolator = None

        pa = self.setParameterMenu()

        pSync = pa.addChild({
            'name': 'Synchronize',
            'value': 'Display',
            'type': 'menu',
            'highlight': True})
        pSync.aboutToShow.connect(self._buildLinkView)

        pCont = pa.addChild({
            'name': 'Continous',
            'value': False,
            'type': 'bool',
            'tip':'Fade between different images'})
        
        pCont.sigValueChanged.connect(self.setContinous)


    def _buildLinkView(self, menu):
        '''
        Add an action for all other displays and connect it to
        self._linkView
        '''
        menu.clear()

        for d in self.display.workspace.displays():
            if d.name() != self.display.name():
                
                cb = QtWidgets.QCheckBox(d.name(), menu)
                a =  QtWidgets.QWidgetAction(menu)
                a.setDefaultWidget(cb)
                menu.addAction(a)
                
                if d in self._connected:
                    cb.setChecked(True)
                cb.clicked.connect(lambda checked, d=d:
                                    self._linkView(d, checked))

    
    #ONLY A TEMPORARY TEST FUNCTION
    def setContinous(self, p,v):
        w = self.display.widget
        w.setOpts(discreteTimeLine=not v)        
        if v:
            self.interpolator = LinearInterpolateImageStack(lambda :w.image, dynamic=True)
            w.timeLine.sigPositionChanged.connect(self._showInterpolatedImage)

        elif self.interpolator is not None:
            w.timeLine.sigPositionChanged.disconnect(self._showInterpolatedImage)
            self.interpolator = None
          
                
    def _showInterpolatedImage(self):
        w = self.display.widget
        w.timeLine.sigPositionChanged.disconnect(self._showInterpolatedImage)

        time = w.timeLine.value()
        #wait till image is shown till next interpolation is started:
        w.item.sigImageChanged.connect(self._reconnectToShowInterpolatedImage)
        w.imageItem.updateImage(self.interpolator(time))    
            

    def _reconnectToShowInterpolatedImage(self):
        w = self.display.widget
        w.timeLine.sigPositionChanged.connect(self._showInterpolatedImage)
        w.item.sigImageChanged.disconnect(self._reconnectToShowInterpolatedImage)


    def _changeSlaveTime(self):
        ind = self.display.widget.currentIndex

        for i in range(len(self._connected) - 1, -1, -1):
            slave = self._connected[i]
            if slave.isClosed():
                self._connected.pop(i)
            else:
                slave.widget.setCurrentIndex(ind)


    def _linkView(self, display, linked):
        w = self.display.widget

        if linked:
            # only connect one time at fist usage:
            try:
                w.sigTimeChanged.disconnect(self._changeSlaveTime)
            except:
                pass
            w.sigTimeChanged.connect(self._changeSlaveTime)

            self._connected.append(display)
        else:
            self._connected.remove(display)


    def activate(self):
        self.display.widget.showTimeline(True)


    def deactivate(self):
        self.display.widget.showTimeline(False)
