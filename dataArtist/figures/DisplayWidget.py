# coding=utf-8
from builtins import zip
from builtins import object
import weakref

from dataArtist.widgets import Toolbars


class DisplayWidget(object):
    '''
    Base class for all display.widget
    '''
    selectedToolbars = {}
    shows_one_layer_at_a_time = False

    def __init__(self, toolbars=None):
        self.tools = {}
        if toolbars is not None:
            self.toolbars = toolbars
        else:
            # wekref causes win10 exec. to not have empty d.widget.tools
            self.toolbars = Toolbars.build(self)  # weakref.proxy(self))

    def saveState(self):
        state = {'toolbars': [t.isSelected() for t in self.toolbars]}
        # tools
        state['tools'] = t = {}
        for name, tool in self.tools.items():
            t[name] = tool.saveState()
        return state

    def restoreState(self, state):
        # toolbars
        for t, sel in zip(self.toolbars, state['toolbars']):
            t.setSelected(sel)
        # tools
        t = state['tools']
        for name, tool in self.tools.items():
            try:
                tool.restoreState(t[name])
            except KeyError:
                pass
