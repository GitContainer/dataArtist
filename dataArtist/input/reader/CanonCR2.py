# coding=utf-8
from dataArtist.input.reader._ReaderBase import ReaderBase, ReaderPreferences

try:
    # package is optional, but needed to read cr2 files:
    import rawpy
except ImportError:
    rawpy = None


class CanonCR2(ReaderBase):
    '''
    Import CANON CR2 (raw) files
    '''
    ftypes = ('cr2',)
    axes = ['x', 'y', '']
    preferred = False

    def __init__(self, *args, **kwargs):
        ReaderBase.__init__(self, *args, **kwargs)
        self.preferences = ReaderPreferences(name='Canon CR2 file import')

    @staticmethod
    def check(ftype, fname):
        if rawpy is None:
            print('please install <<pip install rawpy> to enable *.cr2 import')
            return False
        return ftype in CanonCR2.ftypes

    def open(self, filename):
        with rawpy.imread(filename) as raw:
            arr = self.toFloat(raw.postprocess())
            labels = None
        return arr, labels
