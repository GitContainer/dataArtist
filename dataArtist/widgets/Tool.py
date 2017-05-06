# coding=utf-8
import os
import cv2
import sys

from qtpy import QtWidgets, QtCore, QtGui

from fancytools.os.PathStr import PathStr

from dataArtist.widgets.ParameterMenu import ParameterMenu


import dataArtist
ICONFOLDER = PathStr(dataArtist.__file__).dirname().join('media', 'icons')
del dataArtist


class _ProcessThread(QtCore.QThread):
    '''
    Thread to be used in tool.activate in order not to block
    the gui
    '''
    sigDone = QtCore.Signal(object)

    def __init__(self, tool, runfn, donefn=None):
        QtCore.QThread.__init__(self)
        self.tool = tool
        self.progressBar = tool.display.workspace.gui.progressBar
        self.runfn = runfn
        self._exc_info = None

        self.sigDone.connect(self.done)
        if donefn is not None:
            self.sigDone.connect(donefn)

    def kill(self):
        self.progressBar.hide()
        self.progressBar.cancel.clicked.disconnect(self.kill)
        self.tool.setChecked(False)
        self.terminate()
        if self._exc_info is not None:
            _, ei, tb = self._exc_info
            raise ei.with_traceback(tb)

    def start(self):
        self.progressBar.show()
        self.progressBar.cancel.clicked.connect(self.kill)
        self.progressBar.bar.setValue(50)
        self.progressBar.label.setText(
            "Processing %s" %
            self.tool.__class__.__name__)
        QtCore.QThread.start(self)

    def done(self):
        self.progressBar.hide()
        self.progressBar.cancel.clicked.disconnect(self.kill)

    def run(self):
        try:
            out = self.runfn()
        except (cv2.error, Exception, AssertionError) as e:
            if type(e) is cv2.error:
                print(e)
            self.progressBar.cancel.click()
            self._exc_info = sys.exc_info()
            return

        self.sigDone.emit(out)


class Tool(QtWidgets.QToolButton):
    '''
    Base class for all display.widget.tools
    '''
    reinit = False  # whether to execute activate()/deactivate() at restoreState()

    def __init__(self, display):
        super().__init__()
        self.display = display
        self.view = display.widget.view.vb
        # SET ICON
        icon = getattr(self, 'icon', None)
        if icon:
            if not os.path.exists(icon):
                icon = ICONFOLDER.join(icon)
            self.setIcon(QtGui.QIcon(icon))
        # SET TOOLTIP
        if self.__doc__:
            # USING THE CLASS DOC
            t = '%s\n\t%s' % (self.__class__.__name__, self.__doc__)
        else:
            # USING THE CLASS NAME
            t = self.__class__.__name__
        self.setToolTip(t)
        # SETUP CHECKABILITY:
        if hasattr(self, 'activate'):
            try:
                # if a tool has a method deactivate it should be checkable
                self.deactivate
                self.setCheckable(True)
            except AttributeError:
                self.deactivate = self._deactivate
                self.setCheckable(False)
            self.clicked.connect(self.toggle)
        else:
            self.setPopupMode(QtWidgets.QToolButton.InstantPopup)

    def showGlobalTool(self, toolCls):
        g = self.display.workspace.gui.gTools
        for t in g:
            if t.__class__ == toolCls:
                t.show()
                return t
        t = toolCls(self.display)
        g.addWidget(t)
        return t

    def createResultInDisplayParam(self, parent, value='[NEW, OVERRIDE]'):
        self.pOutDisplay = parent.addChild({'name': 'Result in display',
                                            'value': value,
                                            'type': 'menu'})
        self.pOutDisplay.display = None
        self.pOutDisplay.aboutToShow.connect(self._buildResInDisplayMenu)
        return self.pOutDisplay

    def _buildResInDisplayMenu(self, menu):

        def addToParam(name, display=None, layer=None):
            menu.setTitle(name)
            self.pOutDisplay.display = display
            self.pOutDisplay.layer = layer

        menu.clear()

        a = menu.addAction('[NEW, OVERRIDE]')
        a.triggered.connect(lambda: addToParam('[NEW, OVERRIDE]'))
        # a.setToolTip('Create once a new display, than replace values in there.')

        a = menu.addAction('[NEW, ADD]')
        a.triggered.connect(lambda: addToParam('[NEW, ADD]'))

        a = menu.addAction('[ALLWAYS NEW]')
        a.triggered.connect(lambda: addToParam('[ALLWAYS NEW]'))
        # a.setToolTip('Create every time a new')

        a = menu.addAction('[ADD]')
        a.triggered.connect(lambda: addToParam('[ADD]'))
        # a.setToolTip('Add a new layer to the current display.')

        a = menu.addAction('[REPLACE]')
        a.triggered.connect(lambda: addToParam('[REPLACE]'))
        # a.setToolTip('Add the current layer to the current display.')

        for d in self.display.workspace.displays():
            if d != self.display and d.widget.__class__ == self.display.widget.__class__:
                m = menu.addMenu(d.name())
                m.addAction('[ADD]').triggered.connect(
                    lambda checked, d=d: addToParam('[ADD to %s]' % d.name(), d))
                for n, l in enumerate(d.layerNames()):
                    m.addAction(l).triggered.connect(
                        lambda checked, d=d, n=n, l=l:
                        addToParam('[REPLACE %s]' % l, d, n))

    def handleOutput(self, out, **kwargs):
        try:
            v = self.pOutDisplay.value()
        except AttributeError:
            v = '[ALLWAYS NEW]'

        if v == '[ALLWAYS NEW]':
            self.setChecked(False)
            d = self.display.workspace.addDisplay(
                origin=self.display,
                data=out,
                **kwargs)

        elif v == '[NEW, OVERRIDE]' or v == '[NEW, ADD]':
            d = self.pOutDisplay.display
            if d is None or d.isClosed():
                # NEW
                d = self.display.workspace.addDisplay(
                    origin=self.display,
                    data=out,
                    **kwargs)
                self.pOutDisplay.display = d
            else:
                t = kwargs.pop('title', None)
                n = kwargs.pop('names', None)
                if v == '[NEW, OVERRIDE]':
                    # OVERRIDE
                    d.changeAllLayers(data=out, **kwargs)
                else:
                    if n is None:
                        n = t
                    # ADD
                    d.addLayer(filename=n, data=out, **kwargs)
        else:
            t = kwargs.pop('title', None)
            n = kwargs.pop('names', None)
            out = out[0]
            # TODO: changes filename in name or names ... in displaydock - make
            # it consistent
            if n:
                n = n[0]
            elif t is not None:
                n = t
            d = self.display
            if v == '[REPLACE]':
                d.changeLayer(data=out, **kwargs)
            elif v == '[ADD]':
                d.addLayer(filename=n, data=out, **kwargs)
            else:
                # CHANGE OTHER DISPLAY
                l = self.pOutDisplay.layer
                d = self.pOutDisplay.display
                if l is None:
                    d.addLayer(
                        filename=n,
                        data=out,
                        origin=self.display,
                        **kwargs)
                else:
                    d.changeLayer(data=out, index=l, **kwargs)
        return d

    def buildOtherDisplayLayersMenu(self, menu, triggerFn,
                                    includeThisDisplay=False,
                                    updateMenuValue=True):
        '''
        fill the menu with all available layers within other displays
        this function of often connected with the menu.aboutToShow signal
        '''
        menu.clear()
        # SUBMENU FOR ALL DISPLAYS
        for d in self.display.otherDisplaysOfSameType(includeThisDisplay):
            m = menu.addMenu(d.name())
            # ACTION FOR ALL LAYERS
            for n, l in enumerate(d.layerNames()):
                name = '%s - %s' % (n, l)
                a = m.addAction(name)
                a.triggered.connect(
                    lambda _checked, d=d, n=n, l=l:
                        triggerFn(d, n, l))
                if updateMenuValue:
                    a.triggered.connect(
                        lambda _checked, name=name: menu.setTitle(name))

    def buildOtherDisplaysMenu(self, menu, triggerFn, lenMenuName=25):
        '''
        fill the menu with all available displays
        this function of often connected with the menu.aboutToShow signal
        '''
        menu.clear()
        # SUBMENU FOR ALL DISPLAYS
        for d in self.display.otherDisplaysOfSameType():
            a = menu.addAction(d.name())
            a.triggered.connect(lambda _checked, d=d:
                                triggerFn(d))
            a.triggered.connect(lambda _checked, d=d:
                                menu.setTitle(d.name()[:lenMenuName]))

    def _checkShowBtnMenu(self):
        if self.popupMode() != QtWidgets.QToolButton.InstantPopup:
            self.setPopupMode(QtWidgets.QToolButton.MenuButtonPopup)

    def setMenu(self, *args):
        '''
        only show drop-down menu option if menu is filled with entries
        '''
        self._checkShowBtnMenu()
        QtWidgets.QToolButton.setMenu(self, *args)

    def setParameterMenu(self):
        self._menu = ParameterMenu(self)
        self.setMenu(self._menu)
        self._menu.aboutToShow.connect(self._highlightCurrentTool)
        return self._menu.p

    def _highlightCurrentTool(self):
        '''
        often you'll setup a tool within its menu
        then return to your image and then execute that tool.
        but which tool was it?
        with this method the last tool whose menu was called will be
        drawn slightly darker to help you remember.
        '''
        bar = self.parent()
        # reset last highlighted tool:
        for tool in bar.findChildren(QtWidgets.QToolButton):
            if tool.property('modified') == 'True':
                tool.setProperty('modified', 'False')
                tool.style().unpolish(tool)
                tool.style().polish(tool)
                tool.update()

        # highlight current tool
        self.setProperty('modified', 'True')
        tbar = self.parent()
        color = tbar.palette().color(tbar.backgroundRole())
        color = color.darker(120)

        self.setStyleSheet(self.styleSheet() + """QToolButton[modified = "True"] {  
        background-color: %s;}""" % color.name())

    def addAction(self, *args):
        '''
        only show drop-down menu option if menu is filled with entries
        '''
        self._checkShowBtnMenu()
        QtWidgets.QToolButton.addAction(self, *args)

    def startThread(self, runfn, donefn=None):
        self._thread = _ProcessThread(self, runfn, donefn)
        self._thread.start()

    def toggle(self):
        if not self.isCheckable() or self.isChecked():
            self.display.closed.connect(self.deactivate)
            self.activate()
        else:
            try:
                self.display.closed.disconnect(self.deactivate)
            except TypeError:
                pass  # 'instancemethod' object is not connected
            self.deactivate()

    def _deactivate(self): pass

    def saveState(self):
        state = {'activated': self.isChecked()}
        # self.saveToDict(l)
        try:
            state['menu'] = self.menu().p.saveState()
        except AttributeError:
            pass
        return state

    def restoreState(self, state):
        try:
            self.menu().p.restoreState(state['menu'])
        except AttributeError:
            pass
        cnew = state['activated']
        self.setChecked(cnew)
        if self.reinit:
            if cnew:
                self.activate()
            else:
                try:
                    self.deactivate()
                except AttributeError:
                    pass

    def returnToolOnClick(self, activate, returnMethod):
        '''
        if activate=True:
            run [returnMethod(self)] when this tool is clicked
        '''
        self._returnMethod = returnMethod
        if activate:
            try:
                self.clicked.disconnect(self.toggle)
            except TypeError:
                pass  # module not connected
            self.clicked.connect(self._doReturnToolOnClick)
        else:
            self.clicked.connect(self.toggle)
            try:
                self.clicked.disconnect(self._doReturnToolOnClick)
            except TypeError:
                pass  # module not connected

    def _doReturnToolOnClick(self):
        self.setChecked(False)
        return self._returnMethod(self)

    def mouseCoord(self, evt):
        '''
        return the mouse coordinates
        '''
        # case clicked:
        if not isinstance(evt, QtCore.QPointF):
            evt = evt.scenePos()
        mousePoint = self.view.mapSceneToView(evt)
        return mousePoint.x(), mousePoint.y()
