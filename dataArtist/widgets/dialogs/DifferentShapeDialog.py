from qtpy import QtWidgets


class DifferentShapeDialog(QtWidgets.QDialog):
    '''
    If an image is to be imported into an ImageWidget
    filled already with other images of a different size
    This dialog lets the user decide what to do this the new image:
    * Resize
    * Cut
    * Warp
    * Add to new display
    '''

    opt = 0

    optResize = 0
    optWarp = 1
    optCut = 2
    optNewDisplay = 3

    def __init__(self, layerlabel, shape1, shape2):
        QtWidgets.QDialog.__init__(self)

        labTxt = QtWidgets.QLabel(
            '''the latest layer %s has a different shape than the other layers:
        %s != %s
        How would you like to proceed?''' % (layerlabel, shape1, shape2))
        btnR = QtWidgets.QPushButton("Resize")
        btnR.clicked.connect(lambda: [self.__setattr__('opt', self.optResize),
                                      self.close()])
        btnR.setToolTip(
            'Resize the new image to fit the shape of the existent ones.')
        btnC = QtWidgets.QPushButton("Cut")
        btnC.clicked.connect(lambda: [self.__setattr__('opt', self.optCut),
                                      self.close()])
        btnC.setToolTip(
            'Cut the new image to fit the shape of the existent ones.')

        btnW = QtWidgets.QPushButton("Warp")
        btnW.clicked.connect(lambda: [self.__setattr__('opt', self.optWarp),
                                      self.close()])
        btnW.setToolTip('''To a perspective transformation fo fit the last image
        with the new one using pattern recognition''')

        btnN = QtWidgets.QPushButton("New display")
        btnN.clicked.connect(lambda: [self.__setattr__('opt', self.optNewDisplay),
                                      self.close()])
        btnN.setToolTip('Put the new image in a new display.')

        lv = QtWidgets.QVBoxLayout()
        lh = QtWidgets.QHBoxLayout()

        lv.addWidget(labTxt)
        lv.addLayout(lh)

        lh.addWidget(btnR)
        lh.addWidget(btnC)
        lh.addWidget(btnW)
        lh.addWidget(btnN)

        self.setLayout(lv)
