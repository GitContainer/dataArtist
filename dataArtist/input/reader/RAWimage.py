# coding=utf-8

import numpy as np
from collections import OrderedDict

from pyqtgraph_karl.parametertree.parameterTypes import GroupParameter

# OWN
from dataArtist.input.reader._ReaderBase import ReaderBase


from imgProcessor.reader.RAW import RAW, STR_TO_DTYPE


class RAWimage(ReaderBase):
    '''
    Read RAW images
    '''
    ftypes = ('raw', 'bin')
    axes = ['x', 'y', '']
    #preferred = True
    forceSetup = True

    def __init__(self, *args, **kwargs):
        self.preferences = _Preferences()

        ReaderBase.__init__(self, *args, **kwargs)

    def open(self, filename):
        p = self.preferences

        arr = RAW(filename, p.pWidth.value(), p.pHeight.value(), 
                  p.pDType.value(), p.pLittleEndian.value())

        arr = self.toFloat(arr)

        labels = None
        return arr, labels


class _Preferences(GroupParameter):

    def __init__(self, name=' RAW image import'):

        GroupParameter.__init__(self, name=name)

        self.pDType = self.addChild({
            'name': 'Image type',
            'type': 'list',
            'value': '16-bit Unsigned',
            'limits': list(STR_TO_DTYPE.keys())})
        self.pLittleEndian = self.addChild({
            'name': 'Little-endian byte order',
            'type': 'bool',
            'value': False})
        self.pWidth = self.addChild({
            'name': 'Width',
            'type': 'int',
            'value': 640,
            'unit': 'pixels'})
        self.pHeight = self.addChild({
            'name': 'Height',
            'type': 'int',
            'value': 480,
            'unit': 'pixels'})
        self.pToFloat = self.addChild({
            'name': 'transform to float',
            'type': 'bool',
            'value': True})
        self.pForceFloat64 = self.pToFloat.addChild({
            'name': 'Force double precision (64bit)',
            'type': 'bool',
            'value': False})
        self.pToFloat.sigValueChanged.connect(lambda p, v:
                                              self.pForceFloat64.show(v))
