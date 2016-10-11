# coding=utf-8
from dataArtist.widgets.Tool import Tool

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

        pa = self.setParameterMenu()

        pSync = pa.addChild({
            'name': 'Synchronize',
            'value': 'Display',
            'type': 'menu',
            'highlight': True
        })
        pSync.aboutToShow.connect(self._buildLinkView)

    def _buildLinkView(self, menu):
        '''
        Add an action for all other displays and connect it to
        self._linkView
        '''
        menu.clear()

        for d in self.display.workspace.displays():
            if d.name() != self.display.name():
                a = QtWidgets.QAction(d.name(), menu, checkable=True)
                menu.addAction(a)
                if d in self._connected:
                    a.setChecked(True)
                a.triggered.connect(lambda checked, d=d:
                                    self._linkView(d, checked))

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
