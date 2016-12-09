# coding=utf-8
from dataArtist.widgets.Tool import Tool


class Legend(Tool):
    '''
    show/hide the legend or its frame
    '''
    icon = 'legend.svg'

    def __init__(self, plotDisplay):
        Tool.__init__(self, plotDisplay)

        pa = self.setParameterMenu()
        l = self.display.widget.view.legend
        pFrame = pa.addChild({
            'name': 'Show frame',
            'type': 'bool',
            'value': l.frame})
        pFrame.sigValueChanged.connect(self._drawFrame)

        pOrientation = pa.addChild({
            'name': 'N Columns',
            'type': 'int',
            'value': 1})
        pOrientation.sigValueChanged.connect(lambda param, value:
                                             l.setColumnCount(value))

        self.setChecked(True)

    def _drawFrame(self, param, show):
        l = self.display.widget.view.legend
        l.frame = show
        l.update()

    def activate(self):
        self.display.widget.view.legend.show()

    def deactivate(self):
        self.display.widget.view.legend.hide()
