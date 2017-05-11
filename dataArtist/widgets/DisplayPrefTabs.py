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

        # pop-out button:
        s = QtWidgets.QApplication.style()
        btn = QtWidgets.QToolButton()
        btn.setIcon(s.standardIcon(QtWidgets.QStyle.SP_TitleBarNormalButton))
        btn.setToolTip('Pop-out Dock Preferences')
        btn.clicked.connect(self._togglePopOut)
        self.cornerWidget().layout().addWidget(btn)

    def _togglePopOut(self):
        if self.parent() is None:
            self._popIn()
        else:
            # pop out
            self._parent = self.parent()
            # create window at same position as widget is:
            # TODO: replace 50 with relative position of self in window
            p = self.window().pos()
            p.setY(p.y() + 50 * QtWidgets.QApplication.instance().PX_FACTOR
                   )
            self.setParent(None)
            self.setWindowTitle('Preferences')
            self.move(p)
            self.show()

    def _popIn(self):
        self._parent.insertWidget(0, self)
        self._parent = None

    def closeEvent(self, evt):
        if self.parent() is None:
            self._popIn()
            return evt.ignore()
        return evt.accept()

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
            # initialise with size 0:
            self.show()
            self.parent().moveSplitter(0, 1)
