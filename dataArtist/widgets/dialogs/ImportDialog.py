# coding=utf-8
from qtpy import QtWidgets, QtCore


class ImportDialog(QtWidgets.QDialog):
    '''
    Dialog that shares some of the preferences of
    dataArtist.widgets.preferences.PreferencesImport
    '''

    def __init__(self, import_pref, fnames):
        QtWidgets.QDialog.__init__(self)

        l = QtWidgets.QVBoxLayout()
        self.setLayout(l)

        p = self.pref = import_pref
        self.dial_pref = p.__class__(p.gui)
        p.updateSettings(self.dial_pref)

        l.addWidget(self.dial_pref)
        if len(fnames) > 1:
            self.setWindowTitle('Import %s File(s)' % len(fnames))
        else:
            self.setWindowTitle('Import File')

        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)

        self.btn_done = QtWidgets.QPushButton('Done')
        self.btn_done.clicked.connect(self.accept)
        l.addWidget(self.btn_done)

    def accept(self, _evt):
        '''
        write setting to the preferences
        '''
        self.dial_pref.updateSettings(self.pref)
        QtWidgets.QDialog.accept(self)
