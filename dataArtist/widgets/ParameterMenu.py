# coding=utf-8
from qtpy import QtWidgets, QtCore

from pyqtgraph_karl.parametertree import Parameter
# from dataArtist.widgets.ParameterTree import ParameterTree
from pyqtgraph_karl.parametertree import ParameterTree


class ParameterMenu(QtWidgets.QMenu):
    '''
    A QMenu embedding a ParameterTree
    '''

    def __init__(self, tool):
        QtWidgets.QMenu.__init__(self, tool)
        self.content = _MenuContent(tool)
        self.pTree = self.content.pTree

        self.maxSize = [350, 800]  # px

        # embed parameterTree as a QWidgetAction:
        a = QtWidgets.QWidgetAction(self)
        a.setDefaultWidget(self.content)
        self.addAction(a)
        self.setActiveAction(a)

        self.p = self.pTree.p
        self.p.tool = tool
        tool.param = self.p.param

        self.aboutToShow.connect(self.aboutToShowFn)
        self.aboutToHide.connect(self.aboutToHideFn)

        self._topWidgets = []

        #<<<<<
        # due to Qt5 bug:
        # uncomment following
        # and QActions inside QMenu inside this tool will not
        # fire trigger
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.FramelessWindowHint)
        self.installEventFilter(self)

    def eventFilter(self, op, event):
        if event.type() == QtCore.QEvent.WindowDeactivate:
            QtCore.QTimer.singleShot(10, self.close)
        return False
        #>>>>>

    def addTopWidget(self, w):
        self._topWidgets.append(w)
        self.content.layout().insertWidget(1, w)

    def aboutToShowFn(self):
        self.p.sigTreeStateChanged.connect(self.delayedResize)
        self.pTree.expanded.connect(self.delayedResize)
        self.resizeToContent()

    def aboutToHideFn(self):
        self.p.sigTreeStateChanged.disconnect(self.delayedResize)

    def delayedResize(self):
        # allow pTree to fully add/remove parameters
        # before size is updated
        QtCore.QTimer.singleShot(10, self.resizeToContent)

    def resizeToContent(self):
        '''
        set a fixed minimum width and calculate the height from
        the height of all rows
        '''
        PX_FACTOR = QtWidgets.QApplication.instance().PX_FACTOR
        width = self.maxSize[0] * PX_FACTOR
        heightMax = self.maxSize[1] * PX_FACTOR
        height = 6 * PX_FACTOR  # self.content.header.contentsRect().height()
        hh = [w.height() for w in self._topWidgets]
        if hh:
            height += max(hh)
        _iter = QtWidgets.QTreeWidgetItemIterator(self.pTree)
        while _iter.value():
            item = _iter.value()
            height += self.pTree.visualItemRect(item).height()
            _iter += 1

        # limit height
        if height >= heightMax:
            height = heightMax
        self.pTree.setFixedSize(width - 5 * PX_FACTOR, height)
        # prevent scroll bar(+22):
        self.setFixedSize(width, height + 22 * PX_FACTOR)


class _MenuContent(QtWidgets.QWidget):
    '''
    Show:
    Tool name - info sign  and activate button
    on top of the parameterTree
    '''

    def __init__(self, tool):
        QtWidgets.QWidget.__init__(self)

        PX_FACTOR = QtWidgets.QApplication.instance().PX_FACTOR

        l = QtWidgets.QVBoxLayout()
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(0)

        self.setLayout(l)

        self.header = header = QtWidgets.QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)

        label = QtWidgets.QLabel('<b> %s</b>' % tool.__class__.__name__)

        self.pTree = _Parameters()

        header.addWidget(label)
        doc = getattr(tool, '__doc__', None)
        if doc:
            doclabel = QtWidgets.QLabel('<i>   (?)</i>')
            doclabel.setToolTip(doc)
            header.addWidget(doclabel, stretch=1)

        if hasattr(tool, 'activate'):
            btn = QtWidgets.QPushButton('activate')
            btn.clicked.connect(tool.click)
            btn.setFixedHeight(17 * PX_FACTOR)
            btn.setFixedWidth(50 * PX_FACTOR)
            header.addWidget(btn)

        l.addLayout(header)
        l.addWidget(self.pTree)


class _Parameters(ParameterTree):

    def __init__(self):
        self.p = Parameter.create(
            name='',
            type='empty')
        ParameterTree.__init__(self, self.p, showHeader=False)
