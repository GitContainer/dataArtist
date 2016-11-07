# coding=utf-8

from pyqtgraph_karl.dockarea.DockArea import DockArea

from qtpy import QtWidgets
from dataArtist.input.getFileReader import SUPPORTED_FTYPES


class MiddleDockArea(DockArea):
    '''
    Main area of the gui which shows some text
    when there are no displays
    '''

    def __init__(self, max_docks_xy=(2, 2), *args, **kwargs):
        DockArea.__init__(self, max_docks_xy, *args, **kwargs)

        ftypes = sorted(SUPPORTED_FTYPES)
        # split in chunks of 4:
        ftypes = [ftypes[i:i + 4] for i in range(0, len(ftypes), 4)]
        # format ftypes:
        t = '<ul>'
        for f in ftypes:
            t += '<li>' + str(f)[1:-1]
        t += '</ul>'

        self.text = QtWidgets.QLabel('''<html>
            <p>Just <strong>drag and drop</strong> ...</p>
        <ul>
            <li>one or more <strong>files </strong>or <strong>folders</strong></li>
            <li><strong>number-fields</strong> from clipboard</li>
            <li><strong>images </strong>from clipboard</li>
        </ul><p>
            over this area to open it</p>
            <nl><nl> <p> <strong>Supported file types are:</strong> %s
            </html>''' % t)
        l = QtWidgets.QHBoxLayout()
        l.addStretch(1)
        l.addWidget(self.text, stretch=10)
        self.layout.addLayout(l)

    def addDock(self, dock, *args, **kwargs):
        self.text.hide()
        return DockArea.addDock(self, dock, *args, **kwargs)
