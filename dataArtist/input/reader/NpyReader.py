# coding=utf-8
import numpy as np

# OWN
from pyqtgraph_karl.parametertree.parameterTypes import GroupParameter
from dataArtist.input.reader._ReaderBase import ReaderBase


class NpyReader(ReaderBase):
    '''
    Reader for numpy arrays saved to file as *.npy
    '''
    ftypes = ('npy',)

    def __init__(self, *args, **kwargs):
        ReaderBase.__init__(self, *args, **kwargs)
        self.preferences = _Preferences()

    @staticmethod
    def check(ftype, fname):
        b = ftype in NpyReader.ftypes
        if b:
            # get the array shape
            arr = np.load(fname, mmap_mode='r')
            NpyReader.axes = arr.ndim + 1
            # delete memory mapped array to close it
            del arr
        return b

    def open(self, filename):
        arr = np.load(filename)
        if self.preferences.pMulti.value():
            labels = [str(i) for i in range(len(arr))]
        else:
            labels = None
        return arr, labels


class _Preferences(GroupParameter):

    def __init__(self, name=' Numpy array import'):

        GroupParameter.__init__(self, name=name)

        self.pMulti = self.addChild({
            'name': 'Contains multiple layers',
            'type': 'bool',
            'value': True if NpyReader.axes == 4 else False})
