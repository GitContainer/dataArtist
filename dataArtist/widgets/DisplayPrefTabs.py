# coding=utf-8
from fancywidgets.pyQtBased.FwTabWidget import FwTabWidget

from qtpy import QtWidgets


class DisplayPrefTabs(FwTabWidget):
    '''
    hide tabs-area if no tabs added
    '''

    def __init__(self):
        FwTabWidget.__init__(self)
        self.setMovable(True)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding)
        self.hide()

    def removeTab(self, tab):
        '''
        hide if there are no tabs
        '''
        FwTabWidget.removeTab(self, tab)
        if self.count() == 0:
            self.hide()

    def addTab(self, *args):
        '''
        show is a tab is added
        '''
        FwTabWidget.addTab(self, *args)
        if not self.isVisible():
            # initialize with size 0:
            self.show()
            self.parent().moveSplitter(0, 1)
