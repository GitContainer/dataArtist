from qtpy import QtWidgets


class ChooseFileReaderDialog(QtWidgets.QDialog):
    '''
    If mutliple file readers are available for a given file type
    this dialog lets the user decide which one to take.
    '''
    index = 0

    def __init__(self, readers):
        QtWidgets.QDialog.__init__(self)

        labTxt = QtWidgets.QLabel(
            '''Multiple file reader are available for the chosen ftype:
(Hover for details)''')
        g = QtWidgets.QButtonGroup()

        l = QtWidgets.QVBoxLayout()
        self.setLayout(l)

        l.addWidget(labTxt)

        gl = QtWidgets.QGroupBox('Readers')
        l.addWidget(gl)

        b = QtWidgets.QPushButton('Done')
        b.clicked.connect(self.accept)
        l.addWidget(b)

        l = QtWidgets.QVBoxLayout()
        gl.setLayout(l)

        for n, r in enumerate(readers):
            btn = QtWidgets.QRadioButton(r.__name__)
            btn.clicked.connect(
                lambda checked,
                n=n: self.__setattr__(
                    'index',
                    n))
            if r.__doc__ is not None:
                btn.setToolTip(r.__doc__)
            p = getattr(r, 'preferred', False)
            if p:
                btn.click()
            g.addButton(btn)
            l.addWidget(btn)

        g.setExclusive(True)
