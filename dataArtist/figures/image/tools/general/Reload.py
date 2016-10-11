from __future__ import print_function
from dataArtist.widgets.Tool import Tool


class Reload(Tool):
    '''
    Load or reload the displays data
    '''
    icon = 'reload.svg'

    def activate(self):
        if not self.display.reader:
            print('no input data to reload, updating view...')
            self.display.widget.updateView()
        else:
            self.display.updateInput()
