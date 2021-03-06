# coding=utf-8
import weakref

import pyqtgraph_karl as pg
from qtpy import QtGui, QtCore, QtWidgets

from fancywidgets.pyQtBased.Console import Console
from fancytools.fcollections.naturalSorting import naturalSorting
from fancytools.fcollections.WeakList import WeakList

# OWN
from dataArtist.widgets.DisplayPrefTabs import DisplayPrefTabs
from dataArtist.widgets.MiddleDockArea import MiddleDockArea
from dataArtist.widgets.docks import DockTable, DockTextEditor
from dataArtist.widgets.DisplayDock import DisplayDock
from dataArtist.widgets.dialogs.ImportDialog import ImportDialog


class Workspace(QtWidgets.QWidget):
    '''
    One workspace of dataArtist.gui containing:
    * multiple displays
    * toolbars
    * a side panel with display preferences
    '''

    def __init__(self, gui):

        QtWidgets.QWidget.__init__(self)

        self.gui = gui
        self._last_active_display = None
        self._n_displays = 0  # number of opened displays
        # BUILD MAIN DOCKAREAS:
        self.console = Console(self.gui.app.session.streamOut.message,
                               self.gui.app.session.streamErr.message)
        self.console.setMinimumHeight(25)

        self.displayPrefTabs = DisplayPrefTabs()
        self.displayPrefTabs.currentChanged.connect(self.tabChanged)

        self.area_middle = MiddleDockArea()

        # LAYOUT:
        layout = QtWidgets.QHBoxLayout()
        # remove space between statusbar and console:
        m = layout.contentsMargins()
        m.setBottom(0)
        layout.setContentsMargins(m)
        self.setLayout(layout)
        # middle - displays and message
        self.middle_splitter = QtWidgets.QSplitter(
            QtCore.Qt.Orientation(0))  # 0=horiz, 1=vert
        self.middle_splitter.addWidget(self.area_middle)
        self.middle_splitter.addWidget(self.console)
        # hide console by default
        self.middle_splitter.moveSplitter(0, 0)  # (410, 1)
        # add areas to centralWidget
        self.vert_splitter = QtWidgets.QSplitter(
            QtCore.Qt.Orientation(1))  # 0=horiz, 1=vert
        layout.addWidget(self.vert_splitter)
        self.vert_splitter.addWidget(self.displayPrefTabs)
        self.vert_splitter.addWidget(self.middle_splitter)
        # display pref tabs with fixed size:
        self.vert_splitter.setStretchFactor(1, 1)

        self.setActive()

    def number(self):
        '''
        return the number of this workspace
        '''
        return self.gui.centralWidget().indexOf(self) + 1

    def setPrintView(self, boolean):
        '''
        Hide dock labels and QSplitter handle if True
        for a nice and printable view
        '''
        containers, docks = self.area_middle.findAll()

        if boolean:
            col = 'black' if pg.getConfigOption(
                'background') == 'k' else 'white'
            for d in list(docks.values()):
                d.hideTitleBar()
            for c in containers:
                if isinstance(c, QtWidgets.QSplitter):
                    c.setStyleSheet(
                        "QSplitter::handle{background-color: %s;}" %
                        col)
        else:
            for d in list(docks.values()):
                d.showTitleBar()
            for c in containers:
                if isinstance(c, QtWidgets.QSplitter):
                    c.setStyleSheet("")

    def saveState(self):
        l = {'middleSplitter': self.middle_splitter.sizes(),
             'vertSplitter': self.vert_splitter.sizes()}
        # GENERAL
        # DISPLAYS
        d = self.displaydict()
        for number, display in d.items():
            d[number] = (display.name(), len(display.axes))
            l['display_%i' % number] = display.saveState()
        l['displays'] = d  # ={name:(name,nDim)}
        curD = self.getCurrentDisplay()
        if curD:
            l['currentDisplay'] = curD.number
            # TOOLBARS
            t = l['toolbars'] = {}
            if curD.widget:
                for bar in self._sortToolbars(curD.widget.toolbars):
                    br = False
                    if bar.isSelected():
                        br = self.gui.toolBarBreak(bar)
                    t[bar.name] = (bar.isSelected(), br)
        else:
            l['currentDisplay'] = None
        l['nDisplays'] = self._n_displays
        l['displayLayout'] = self.area_middle.saveState() if d else None
        # TABLES
        tables = self.tables()
        lt = l['tables'] = {}  # {n:t.name() for n,t in enumerate(tables)}
        for t in tables:
            lt[t.name()] = t.widgets[0].table()

        # NOTEPADS
        notepads = self.notepads()
        lt = l['notepads'] = {}
        for t in notepads:
            lt[t.name()] = t.widgets[0].text.toHtml()
        return l

    def restoreState(self, state):
        # GENERAL
        self.middle_splitter.setSizes(state['middleSplitter'])
        self.vert_splitter.setSizes(state['vertSplitter'])
        # DISPLAYS
        currentDisplay = None
        currN = state['currentDisplay']
        for d in self.displays():
            d.close()
        for number, (name, nDim) in state['displays'].items():
            d = self.addDisplay(number=number, axes=nDim, docktitle=name)
            # self.changeToolBars(d)
#             d.setName(name)
            d.restoreState(state['display_%i' % number])
            if number == currN:
                currentDisplay = d
        # TABLES
        for t in self.tables():
            t.close()
        for name, content in state['tables'].items():
            dt = self.addTableDock(name=name)
            dt.widgets[0].importTable(content)
        # NOTEPADS
        for t in self.notepads():
            t.close()
        for name, content in state['notepads'].items():
            dt = self.addTextDock(name=name)
            dt.widgets[0].text.setHtml(content)
        # LAYOUT
        if state['displayLayout']:
            self.area_middle.restoreState(state['displayLayout'])
        self._n_displays = state['nDisplays']
        if currentDisplay:
            # TOOLBARS
            for bar in currentDisplay.widget.toolbars:
                issel, hasbreak = state['toolbars'][bar.name]
                bar.setSelected(issel)
                bar.hasBreak = hasbreak
            # remove old:
#             for bar in d.widget.toolbars:
#                 self.gui.removeToolBar(bar)
            self.changeDisplay(currentDisplay)

    def integrateDisplay(self, display):
        '''
        integrate a new display into the workspace
        '''
        display.clicked.connect(self.changeDisplay)
        display.label.sigClicked.connect(lambda: self.changeDisplay(
            weakref.proxy(display)))
        # close this tab too if the display is closed:
        display.closed.connect(self._displayClosed)
        self.displayPrefTabs.addTab(display.tab, "[%s]" % display.number)
        self.area_middle.addDock(display)

    def _displayClosed(self, display):
        self.displayPrefTabs.removeTab(display.tab)
        l = self.displays()
        if l:
            # select an other display
            self.changeDisplay(l[0])
        else:
            # remove remaining toolbars
            for bar in self._last_active_display.widget.toolbars:
                self.gui.removeToolBar(bar)
            self._last_active_display = None

    def displays(self):
        '''
        return a list of displays within this workspace
        '''
        return WeakList([d for d in list(self.area_middle.docks.values())
                         if isinstance(d, DisplayDock)])

    def tables(self):
        '''
        return a list of tables within this workspace
        '''
        return [d for d in list(self.area_middle.docks.values())
                if isinstance(d, DockTable)]

    def notepads(self):
        '''
        return a list of notepads within this workspace
        '''
        return [d for d in list(self.area_middle.docks.values())
                if isinstance(d, DockTextEditor)]

    def changeDisplayNumber(self, number):
        '''
        change to display of given [number]
        '''
        d = self.displaydict()[number]
        self.changeDisplay(d)

    def displaydict(self):
        '''
        returns dict{number:displayInstance}
        '''
        d = {}
        for x in self.displays():
            d[x.number] = x
        return d

    def setActive(self):
        '''
        activate this workspace
        '''
        if self._last_active_display:
            self.changeToolBars(self._last_active_display)
        self.console.setActive()

    def setInactive(self):
        '''
        deactivate this workspace
        '''
        self._removeCurrentToolBars()
        self.console.setInactive()

    def _removeCurrentToolBars(self):
        toolbars = self.gui.findChildren(QtWidgets.QToolBar)
        for bar in toolbars:
            self.gui.removeToolBar(bar)

    def close(self):
        self.setInactive()
        for widget in list(self.area_middle.docks.values()):
            widget.close()
        QtWidgets.QWidget.close(self)

    def tabChanged(self, index):
        '''
        also change the display combined to the changed tab
        '''
        tab = self.displayPrefTabs.widget(index)
        if tab and hasattr(tab, 'display'):
            self.changeDisplay(tab.display)

    def changeDisplay(self, display):
        '''
        show tab, symbolActive and the toolbars of the changed display
        '''
        if (self._last_active_display and
                self._last_active_display.name == display.name):
            return
        if self._last_active_display != display:
            if self._last_active_display:
                self._last_active_display.label.setSelected(False)
            # add a symbol to the active display:
            display.label.setSelected(True)
            # set global toolbar to the toolbars of the active display:
            self.changeToolBars(display)
            self._last_active_display = display
            # activate this tab if its display is clicked:
            self.displayPrefTabs.setCurrentWidget(display.tab)

    def reload(self):
        '''
        reload all display and current toolbars
        '''
        cur = self.getCurrentDisplay()
        if cur:
            for bar in cur.widget.toolbars:
                self.gui.removeToolBar(bar)
        for d in self.displays():
            d.reloadWidget()
        self.changeToolBars(cur)

    def getCurrentDisplay(self):
        try:
            return self.displayPrefTabs.currentWidget().display
        except AttributeError:  # there is no display so far
            return None

    def moveCurrentDisplayToOtherWorkspace(self, workspsace):
        d = self.getCurrentDisplay()
        if not d:
            raise Exception('no display chosen')
        # at the moment display is a weakproxy
        # executing this returns the original class:
            # TODO: find better solution
        d = d.__repr__.__self__
        workspsace.integrateDisplay(d)
        self._removeCurrentToolBars()
        self._last_active_display = None
        d = self.getCurrentDisplay()
        if d:
            self.changeDisplay(d)

    def _2dToolbars(self):
        '''return list of lists of all toolbars in the current workspace
        e.g. [ [bar1, bar2], #row1
               [bar3] ]      #row2
        '''
        toolbars = sorted(self.gui.findChildren(QtWidgets.QToolBar),
                          key=lambda bar: (bar.pos().y(), bar.pos().x()))
        rows = [[]]
        for bar in toolbars:
            if self.gui.toolBarBreak(bar):
                rows.append([])
            if bar.isVisible():
                rows[-1].append(bar)
        rows = [r for r in rows if len(r)]  # remove empty rows
        return rows

    # TODO: only works for TopToolBarArea - make work for others as well
    # ignore all other positions - only positioning in top bar

    def addNewToolbar(self, newbar):
        # find position [right end one toolbar row]
        # for new toolbars depending on where
        # space is available
        w = self.gui.size().width()
        needed_space = newbar.width
        p = QtCore.Qt.TopToolBarArea

        toolbars = self._2dToolbars()

        # there are now toolbars at the moment
        if not len(toolbars):
            return self.gui.addToolBar(p, newbar)

        avail_space = []
        for row in toolbars:
            avail_space.append(
                w - sum([bar.width for bar in row if bar != newbar]))

        # assign position for new toolbar:
        for row, space in enumerate(avail_space):
            if space >= needed_space:
                try:
                    # add at end of current row
                    before = toolbars[row + 1][0]
                    self.gui.insertToolBar(before, newbar)
                    self.gui.removeToolBarBreak(newbar)
                    self.gui.insertToolBarBreak(before)
                except IndexError:
                    # there is no following row
                    self.gui.addToolBar(p, newbar)
                return
        # need to create new row to add toolbar
        self.gui.addToolBarBreak(p)
        self.gui.addToolBar(p, newbar)

    def _sortToolbars(self, bars):
        return sorted(bars, key=lambda bar:
                      (bar.pos().y(), bar.pos().x()))

    def changeToolBars(self, display):
        '''
        remove old and show new toolbars - if there are selected
        apply position of last display.widget.toolbars
        '''
        # will remove and add toolbars,
        # if there's a 2nd row, prevent resize:
        self.gui.setUpdatesEnabled(False)

        # only show/change toolbars is that button is checked:
        if not self.gui.menu_toolbars.a_show.isChecked():
            return

        d = self._last_active_display
        if d:
            # save old layout
            for bar in d.widget.toolbars:
                if bar.isSelected():
                    # bar.position = self.gui.toolBarArea(bar)
                    bar.hasBreak = self.gui.toolBarBreak(bar)
            # save order:
            d.widget.toolbars = self._sortToolbars(d.widget.toolbars)
            # remove old:
            for bar in d.widget.toolbars:
                self.gui.removeToolBar(bar)
            # is displays are of same kind:
            if d.widget.__class__ == display.widget.__class__:
                # apply sequence of old display to new one:
                t = display.widget.toolbars

                def findBar(bar):
                    for n, b in enumerate(d.widget.toolbars):
                        if b.name == bar.name:
                            return n
                display.widget.toolbars = sorted(t, key=findBar)

        # add new toolbars:
        if display is not None:
            for bar in display.widget.toolbars:
                if bar.isSelected():
                    #                 p = bar.position
                    self.gui.addToolBar(QtCore.Qt.TopToolBarArea, bar)
                    if bar.hasBreak:
                        self.gui.insertToolBarBreak(bar)
                    bar.show()

        self.gui.setUpdatesEnabled(True)

    def addShowToolBarAction(self, menu):
        d = self._last_active_display
        if d is not None:
            for t in d.widget.toolbars:
                menu.addAction(t.toggleViewAction())

    def toggleShowSelectedToolbars(self, show):
        if show:
            self.changeToolBars(self.getCurrentDisplay())
        else:
            if self._last_active_display is not None:
                for t in self._last_active_display.widget.toolbars:
                    t.hide()

    def addTableDock(self, name=None, text=None, array=None):
        '''
        add a new table to the dock area
        '''
        if name is None:
            name = 'table %s' % (len(self.tables()) + 1)
        d = DockTable(name=name, text=text, array=array)
        self.area_middle.addDock(d)
        return d

    def addTextDock(self, name=None, text=None):
        '''
        add a new notepad to the dock area
        '''
        if name is None:
            name = 'notepad %s' % (len(self.notepads()) + 1)
        d = DockTextEditor(name=name, text=text)
        self.area_middle.addDock(d)
        return d

    def addDisplay(self, **kwargs):
        '''
        create and integrate a new display
        '''
        number = kwargs.pop('number', None)
        if number is not None:
            if number > self._n_displays:
                self._n_displays = number
        else:
            number = self._n_displays
            self._n_displays += 1
        display = DisplayDock(number, weakref.proxy(self), **kwargs)
        self.integrateDisplay(display)
        return display

    def copyViewToClipboard(self):
        p = self.area_middle.grab()
        QtWidgets.QApplication.clipboard().setPixmap(p)
        print('Copied view to clipboard.')

    def copyCurrentDisplayToClipboard(self):
        d = self.getCurrentDisplay()
        if d is not None:
            p = d.widget.grab()
            QtWidgets.QApplication.clipboard().setPixmap(p)
            print('Copied current display to clipboard.')

    def copyCurrentDisplayItemToClipboard(self):
        d = self.getCurrentDisplay()
        if d is not None:
            b = d.widget.item.sceneBoundingRect().toRect()
            try:
                # in case multiple items are in grid order:
                for i in d.widget.subitems:
                    b = b.united(i.sceneBoundingRect().toRect())
            except AttributeError:
                pass
            p = d.widget.grab(b)
            QtWidgets.QApplication.clipboard().setPixmap(p)
            print('Copied current display item to clipboard.')

    def addFiles(self, names):
        '''
        check the importPolicy: if = ask: show import dialog to ask user
        if import together: import all files together in one display
        else: import separated
        '''
        if not names:
            return
        # sort by names:
        names = naturalSorting(names)
        # show import dialog, if wished, choose there to take import settings from
        # a)import dialog b)preferences->import
        pref = self.gui.pref_import
        if pref.showImportDialog:
            dial = ImportDialog(pref, names)
            dial.exec_()
            if not dial.result():
                return
        # add files in current display:
        i = pref.importFilesPolicy
        l = pref.loadImportedFiles
        if i in (pref.inCurrentDisplay, pref.inDisplay):
            if i == pref.inCurrentDisplay:
                display = self.getCurrentDisplay()
            else:
                display = self.displaydict()[pref.displayNumber]
            if display is not None:
                display.addFiles(names, openfiles=l)
            else:
                # if there is no display yet: create a new one:
                display = self.addDisplay(names=names, openfiles=l)
        # import all files in one new display:
        elif i == pref.together:
            self.addDisplay(names=names, openfiles=l)
        # import files in separate displays:
        else:
            for p in names:
                # import each file separate
                # also give a list when there is only one file
                self.addDisplay(names=[p], openfiles=l)
