# coding=utf-8
from qtpy import QtWidgets


class ProgressBar(QtWidgets.QWidget):
    '''
    A general propose procress bar
    e.g. used when files are imported or tools are executed.
    '''

    def __init__(self, statusbar):
        QtWidgets.QWidget.__init__(self)

        self.statusbar = statusbar

        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.bar = QtWidgets.QProgressBar()
        self.cancel = QtWidgets.QPushButton('Cancel')
        self.label = QtWidgets.QLabel()
        layout.addWidget(self.label)
        layout.addWidget(self.bar)
        layout.addWidget(self.cancel)
        self.statusbar.addPermanentWidget(self, stretch=0.5)

        self.hide()

    def show(self):
        self.statusbar.clearMessage()
        QtWidgets.QWidget.show(self)
