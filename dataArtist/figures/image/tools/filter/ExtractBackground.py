# coding=utf-8
from dataArtist.widgets.Tool import Tool


def _import():
    global fastFilter
    from imgProcessor.filters.fastFilter import fastFilter


class ExtractBackground(Tool):
    '''
    extract background (as low gradient variation obtained through
    a fast spatial median)
    '''
    icon = 'extractBackground.svg'

    def __init__(self, imageDisplay):
        Tool.__init__(self, imageDisplay)
        _import()

        pa = self.setParameterMenu()
        self.createResultInDisplayParam(pa)

        self.pSize = pa.addChild({
            'name': 'Size',
            'type': 'int',
            'value': 30,
            'min': 5})
        self.pFilter = pa.addChild({
            'name': 'Filter Type',
            'type': 'list',
            'value': 'median',
            'limits': ['median', 'mean']})
        self.pSetEvery = pa.addChild({
            'name': 'Set every',
            'type': 'bool',
            'value': False,
            'tip': 'Otherwise value calculated as size/3.5'})
        self.pEvery = self.pSetEvery.addChild({
            'name': 'value',
            'type': 'int',
            'value': 10,
            'limits': [5, 1000],
            'visible': False})
        self.pSetEvery.sigValueChanged.connect(
            lambda p, v: self.pEvery.show(v))

    def activate(self):
        out = []
        size = self.pSize.value()
        if self.pSetEvery.value():
            every = self.pEvery.value()
        else:
            every = int(size / 3.5)
        for img in self.display.widget.image:
            out.append(fastFilter(img, ksize=size, every=every,
                                  fn=self.pFilter.value()))

        self.handleOutput(out, title='Background')
