# coding=utf-8
import numpy as np
import traceback
import platform
from qtpy import QtWidgets, QtCore, QtGui

from pyqtgraph_karl import console
from pyqtgraph_karl.parametertree import Parameter

from fancytools.os.PathStr import PathStr

from fancywidgets.pyQtBased.FwTabWidget import FwTabWidget
from fancywidgets.pyQtBased.CodeEditor import CodeEditor
from fancywidgets.pyQtBased.CircleWidget import CircleWidget

import dataArtist
from dataArtist.widgets.ParameterMenu import ParameterMenu
from dataArtist.widgets.Tool import Tool

# ---CONSTANTS------------------------------
# GET ALL PYTHON BUILD-INs:
import builtins
BUILTINS_DICT = {}
for b in dir(builtins):
    BUILTINS_DICT[b] = getattr(builtins, b)
del builtins
# SPRIPT_PATH = PathStr.getcwd('dataArtist').join("scripts")
SPRIPT_PATH = PathStr(dataArtist.__file__).dirname().join('scripts')
# ------------------------------------------


class Automation(QtWidgets.QWidget):
    '''
    Widget for easy automation within dataArtist, providing:

    * On/Of switch
    * 'Collect' button to grab the address of tool buttons and it's parameters
    * 'Import' list to load saved scripts
    * Multiple script editors listed as Tabs
    * 'Run on new input'
        - Activate active script as soon as the input has changed
    * 'Run' - run active script now
    '''

    def __init__(self, display, splitter):
        QtWidgets.QWidget.__init__(self)

        self.display = display
        display.sigLayerChanged.connect(self.toggleDataChanged)
        display.sigNewLayer.connect(self.toggleNewData)
        self.setMinimumHeight(30)

        self.splitter = splitter

        self._collect = False
        self._activeWidgets = []

        # LAYOUT
        layout = QtWidgets.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignTop)
        # setMargin removed. obsolete, doesn't do anything, not even in PyQt4
        self.setLayout(layout)
        self._hl = QtWidgets.QHBoxLayout()
        layout.addLayout(self._hl)

        # BUTTON: show/hide 'Scripts'
        self.btn_scripts = QtWidgets.QRadioButton('Scripts')
        f = self.btn_scripts.font()
        f.setBold(True)
        self.btn_scripts.setFont(f)
        self.btn_scripts.clicked.connect(self._uncheckConsole)
        self.btn_scripts.clicked.connect(self._toggleScriptsFirstTime)
        self.btn_scripts.clicked.connect(self.updateSize)
        self._hl.addWidget(self.btn_scripts)

        # BUTTON: show/hide 'Console'
        self.btn_console = QtWidgets.QRadioButton('Console')
        f = self.btn_console.font()
        f.setBold(True)
        self.btn_console.setFont(f)
        self.btn_console.clicked.connect(self._uncheckScripts)
        self.btn_console.clicked.connect(self._toggleConsoleFirstTime)
        self.btn_console.clicked.connect(self.updateSize)

        self._hl.addWidget(self.btn_console)

        g = QtWidgets.QButtonGroup(self)
        g.setExclusive(False)
        g.addButton(self.btn_scripts)
        g.addButton(self.btn_console)

        self.splitter.setStretchFactor(0, 0)

        self.cb_run_on = QtWidgets.QComboBox()
        self.cb_run_on.addItems(['-', 'New Data', 'Data Changed'])

        self.tabs = FwTabWidget()
        self.tabs.hide()
        self.tabs.setTabsAddable(True)
        self.tabs.setTabsClosable(True)
        self.tabs.setTabsRenamable(True)

    def _uncheckScripts(self, show):
        if show and self.btn_scripts.isChecked():
            self._toggleScripts(False)
            self.btn_scripts.setChecked(False)

    def _uncheckConsole(self, show):
        if show and self.btn_console.isChecked():
            self._toggleConsole(False)
            self.btn_console.setChecked(False)

    def _toggleConsoleFirstTime(self):

        txt = '''This is a Python {} console.
        it accepts ...
        * all built-in functions, like 'dir'
        * already imported modules, like 'np', for numpy
        * special dataArtist functions, like d', d.l, d.l0,...
        '''.format(platform.python_version())

        namespace = _ExecGlobalsDict(self.display)

        self.console = console.ConsoleWidget(namespace=namespace, text=txt)
        self.console.ui.exceptionBtn.hide()
        self.console.input.sigExecuteCmd.connect(
            self.display.widget.updateView)
        self.layout().addWidget(self.console)

        # update connections:
        self.btn_console.clicked.disconnect(self._toggleConsoleFirstTime)
        self.btn_console.clicked.connect(self._toggleConsole)

    def _toggleConsole(self, show):
        self.console.setVisible(show)

    def _toggleScriptsFirstTime(self):
        # build scripts layout
        refreshR = 20

        # COMBOBOX: IMPORT
        self.combo_import = QtWidgets.QComboBox()
        self.combo_import.addItems((
            '<import>',
            'from file'))
        self.combo_import.addItems(
            # don't show '.py' and hide __init__.py
            [x[:-3] for x in SPRIPT_PATH.listdir()
             if (x[0] != '_' and x.endswith('.py'))])
        self.combo_import.currentIndexChanged.connect(self._importScript)
        # BUTTON: COLLECT
        self.btn_collect = QtWidgets.QPushButton('Collect')
        self.btn_collect.setToolTip(
            'click on all tool parameters you want to change during the batch process')
        self.btn_collect.setCheckable(True)
        self.btn_collect.clicked.connect(self.collectTools)
        # TABWIDGET: SCRIPT
        self.tabs.defaultTabWidget = lambda: ScriptTab(self, refreshR)
        self.tabs.addEmptyTab('New')
        # BUTTON: RUN AT NEW INPUT
        self.label_run_on = QtWidgets.QLabel('Activate on')

        # SPINBOX REFRESHRATE
        self.label_refresh = QtWidgets.QLabel('Refresh rate:')
        self.sb_refreshrate = QtWidgets.QSpinBox()
        self.sb_refreshrate.setSuffix(" Hz")
        self.sb_refreshrate.setMinimum(0)
        self.sb_refreshrate.setMaximum(100)
        self.sb_refreshrate.setValue(refreshR)
        self.sb_refreshrate.valueChanged.connect(
            lambda hz: self.tabs.currentWidget().thread.setRefreshrate(hz))
        # BUTTON: RUN
        self.btn_run_now = QtWidgets.QPushButton('Run')
        self.btn_run_now.setCheckable(True)
        self.btn_run_now.clicked.connect(self.toggle)

        self._hl.addWidget(self.btn_collect)
        l = self.layout()
        l.addWidget(self.combo_import)
        l.addWidget(self.tabs)

        self.tabs.show()

        hl2 = QtWidgets.QHBoxLayout()
        hl2.addWidget(self.label_run_on)
        hl2.addWidget(self.cb_run_on)
        hl2.addWidget(self.label_refresh)
        hl2.addWidget(self.sb_refreshrate)
        hl2.insertStretch(1, 0)
        hl2.insertStretch(2, 0)
        l.addLayout(hl2)
        l.addWidget(self.btn_run_now)

        # update connections:
        self.btn_scripts.clicked.disconnect(self._toggleScriptsFirstTime)
        self.btn_scripts.clicked.connect(self._toggleScripts)

    def checkWidgetIsActive(self, widget):
        # bring widget into list of updated widgets
        # if not there already
        a = self._activeWidgets
        if widget not in a:
            a.append(widget)

    def saveState(self):
        state = {'scriptOn':    self.btn_scripts.isChecked(),
                 'consoleOn':   self.btn_console.isChecked(),
                 'runOn':     str(self.cb_run_on.currentText()),
                 'tabTitles': [str(self.tabs.tabText(tab))
                               for tab in self.tabs],
                 'curTab': self.tabs.currentIndex()}
        # BUTTONS
        # l['runOnNewInput'] = self.btn_run_new.isChecked()
        # SCRIPTS
        ss = state['scripts'] = []
        for tab in self.tabs:
            ss.append(tab.editor.toPlainText())
#             session.addContentToSave(tab.editor.toPlainText(),
#                             *path+('scripts', '%s.txt' %n))
        #-->
#         session.addContentToSave(l, *path+('automation.txt',))
        return state

    def restoreState(self, state):
        # BUTTONS
        self.btn_scripts.setChecked(state['scriptOn'])
#         self._toggleScripts(state['active'])
        self.btn_console.setChecked(state['consoleOn'])
        # self.btn_run_new.setChecked(l['runOnNewInput'])
        self.cb_run_on.setCurrentIndex([self.cb_run_on.itemText(i)
                                        for i in range(self.cb_run_on.count())].index(
            state['runOn']))
        # SCRIPTS
        ss = state['scripts']
        if ss and not hasattr(self, 'combo_import'):
            self._toggleScriptsFirstTime()
        self.tabs.clear()
        for n, title in enumerate(state['tabTitles']):
            tab = self.tabs.addEmptyTab(title)
            tab.editor.setPlainText(ss[n])
        self.tabs.setCurrentIndex(state['curTab'])

    def collectTools(self):
        '''
        Get a Tool button or a parameter within the tools menu
        and add it to the active script
        '''
        # TOGGLE BETWEEN NORMAL- AND PointingHandCursor
        self._collect = not self._collect
        if self._collect:
            QtWidgets.QApplication.setOverrideCursor(QtGui.QCursor(
                QtCore.Qt.PointingHandCursor))
        else:
            QtWidgets.QApplication.restoreOverrideCursor()
        # TOGGLE BUTTON
        self.btn_collect.setChecked(self._collect)
        # add chosen widget to active script:

        def fn(tool):
            return self.tabs.currentWidget().addTool(tool)

        for tool in self.display.widget.tools.values():
            # TOOLS:
            tool.returnToolOnClick(self._collect, fn)
            # TOOL-PARAMETERS:
            if isinstance(tool.menu(), ParameterMenu):
                tool.menu().pTree.returnParameterOnKlick(self._collect, fn)

    def _importScript(self, index):
        '''
        Open a file, read it's content and add it to the active script tab
        '''
        self.combo_import.setCurrentIndex(0)
        if index == 0:  # '<import>' placeholder within the comboBox
            return
        if index == 1:  # import from file
            f = self.display.workspace.gui.dialogs.getOpenFileName()
            if f is not None and f.isfile():
                tab = self.tabs.addEmptyTab('file')
                with open(f, 'r') as r:
                    tab.editor.appendPlainText(r.read())
        else:
            # import one of the examples scripts
            tab = self.tabs.addEmptyTab('ex%s' % str(index - 1))
            tab.editor.appendPlainText(
                open(SPRIPT_PATH.join(
                    str(self.combo_import.itemText(index))) + '.py', 'r').read())

    def _updateWidget(self):
        '''
        update all active display widgets
        '''
        for widget in self._activeWidgets:
            try:
                widget.updateView(force=True)
            except Exception:
                traceback.print_exc()

    def minimumHeight(self):
        return QtWidgets.QWidget.minimumHeight(self) + 10

    def updateSize(self):
        s = self.splitter
        l = s.sizes()
        if self.btn_scripts.isChecked() or self.btn_console.isChecked():
            # resize to 50%
            s.setSizes(np.ones(len(l)) * np.mean(l))
            self.splitter.setStretchFactor(0, 1)
        else:
            minSize = self.minimumHeight()
            l[1] = max(0, np.sum(l) - minSize)
            l[0] = minSize

            s.setSizes(l)
            self.splitter.setStretchFactor(0, 0)

    def _toggleScripts(self, show):
        '''
        Show/hide all widgets within Automation except of the on/off switch
        And move the horizontal splitter according to the space needed
        '''
        if show:
            self.tabs.show()
            self.btn_run_now.show()
            self.btn_collect.show()
            self.label_run_on.show()
            self.cb_run_on.show()
            self.combo_import.show()
            self.label_refresh.show()
            self.sb_refreshrate.show()
        else:
            self.tabs.hide()
            self.btn_run_now.hide()
            self.btn_collect.hide()
            self.label_run_on.hide()
            self.cb_run_on.hide()
            self.combo_import.hide()
            self.label_refresh.hide()
            self.sb_refreshrate.hide()

    def _setRunning(self):
        '''update button'''
        self.btn_run_now.setChecked(True)
        self.btn_run_now.setText('Stop')
        self.display.workspace.gui.undoRedo.is_active = False
        # TODO: remove try... if .display if not a weakref.proxy any more
        try:
            d = self.display.__repr__.__self__
        except:
            d = self.display
        # SHOW RUN INDICATOR
        self._runIndicator = CircleWidget(d)
        self._runIndicator.move(2, 2)
        self._runIndicator.show()

    def _setDone(self):
        '''update button'''
        self.btn_run_now.setChecked(False)
        self.btn_run_now.setText('Start')
        self.display.workspace.gui.undoRedo.is_active = True
        if hasattr(self, '_runIndicator'):
            self._runIndicator.close()
            del self._runIndicator

    def toggle(self):
        '''
        Start/Stop the active script
        '''
        tab = self.tabs.currentWidget()
        # STOP
        if self.btn_run_now.text() == 'Stop':
            tab.thread.kill()
            return
        # START
        self.display.backupChangedLayer(
            changes='Script <%s>' %
            self.tabs.tabText(tab))
        self._activeWidgets = [self.display.widget]

        tab.thread.start()

    def toggleNewData(self):
        '''
        toggle run settings allow running for new data
        '''
        if self.btn_scripts.isChecked() and self.cb_run_on.currentIndex() == 1:  # =new data
            self.toggle()

    def toggleDataChanged(self):
        '''
        toggle run settings allow running for data changed
        '''
        if self.btn_scripts.isChecked() and self.cb_run_on.currentIndex() == 2:  # =data changed
            self.toggle()


class ScriptTab(CodeEditor):
    '''
    A Tab containing:
    * a code editor
    * a QThread to run the script
    * method addTool() to add tools or toolParameters to the code editor
    '''

    def __init__(self, automation, refreshrate):
        CodeEditor.__init__(self, automation.display.workspace.gui.dialogs)
        # THREAD to run the script within:
        self.thread = _Thread(self, automation, refreshrate)
        self.editor.setToolTip('''This is a Python {} script.
it accepts ...
* all built-in functions, like 'dir'
* already imported modules, like 'np', for numpy
* special dataArtist functions, like 'new', 'd', d.l, d.l0, d1,l0, new, timed ...

Click on 'Globals' in the right click menu for more information.
'''.format(platform.python_version()))

        self.addGlobals({'d': 'Access the current display',
                         'd0': 'Access display 0',
                         'd.l': 'Access all layers of [d]',
                         'd.l0': 'Access only the first layer of [d]',
                         'd.tools[<NAME>].click()': 'Execute a tool, given by name',
                         '''d.tools[<NAME>].param(
<NAME1>,...).setValue(<VALUE>)''': 'Modify a parameter of a tool',
                         'new': '''Create A new display
Options are...
    new(axes=3)
    new(axes=['x','y'])
    new(names=['LIST OF FILENAMES TO LOAD FROM'])
    new(data=np.ones(shape=100,100), axes=3) # to create on image layer
    new(data=np.ones(shape=10,10), axes=2) # to create 10 layers of 2d plots ''',
                         'timed': '''Creates, registers and return a QtCore.QTimer instance
Options are...
    timed(func_to_call, timeout=20) #executes func_to_call every 20 ms
    timed(func_to_call, timeout=20, stopAfter=10000) #... ends the execution after 10 sec
    timed(func_to_call, timeout=20, stopAfter=10000, stopFunc=done) #... execute 'done' when done
    timed(func_to_call, 20, 10000, done)#... same, but shorter''',
                         'np': 'The [numpy] package, containing e.g. np.array.'}
                        )

    def addTool(self, widget):
        '''
        append a tool or tool-parameter to the end of the editor text
        '''
        # TOOL
        if isinstance(widget, Tool):
            self.editor.appendPlainText("d.tools['%s'].click()" % (
                widget.__class__.__name__))
        # TOOL-PARAMETER
        elif isinstance(widget, Parameter):
            topParam, path = widget.path()
            tool = topParam.tool
            p = str(path)[1:-1]
            if len(path) == 1:
                p = p[:-1]
            self.editor.appendPlainText("d.tools['%s'].param(%s).setValue('XXX')" % (
                tool.__class__.__name__, p))


class _ExecGlobalsDict(dict):
    '''
    a dict containing the globals for the script execution
    containing all normal build-ins and some special arguments
    '''

    def __init__(self, display):
        dict.__init__(self)
        self.display = display
        knownArgs = {'np': np,
                     'd': display,
                     #'QtGui': QtGui,
                     #'QtCore': QtCore
                     }
        self.update(knownArgs)
        self.update(BUILTINS_DICT)

    def __getitem__(self, key):
        '''
        try to find item, elsewise:
        translate 'd1'-'d[n]' into the corresponding display of the same number
        '''
        try:
            return dict.__getitem__(self, key)
        except KeyError as e:
            if key[0] == 'd' and key[1:].isdigit():
                n = int(key[1:])
                try:
                    return self.displaydict[n]
                except KeyError:
                    raise Exception("display %s doesn't exist" % n)
            raise e

    @property
    def displaydict(self):
        return self.display.workspace.displaydict()

#     def setup(self):
#         '''
#         get all current displays
#         '''
#         self.displaydict = self.display.workspace.displaydict()


class _Thread(QtCore.QThread):
    '''
    The thread for executing the script within ScriptTab
    '''

    def __init__(self, scriptTab, automation, refreshrate):
        QtCore.QThread.__init__(self)

        self.scriptTab = scriptTab
        self.automation = automation
        # CREATE AND EXTEND THE GLOBALS USED FOR EXECUTING THE SCRIPT:
        self._globals = _ExecGlobalsDict(automation.display)
        self._globals.update({  # 'wait':self.wait,
            'timed': self._getAndRegisterTimer,
            'new': self._addActiveWidget})
        k = list(self._globals.keys())
        for b in list(BUILTINS_DICT.keys()):
            k.remove(b)

        self._widgetUpdateTimer = QtCore.QTimer()
        self._widgetUpdateTimer.timeout.connect(self.automation._updateWidget)
        self.setRefreshrate(refreshrate)

    def _addActiveWidget(self, *args, **kwargs):
        a = self.automation
        d = a.display.workspace.addDisplay(*args, **kwargs)
        a.checkWidgetIsActive(d.widget)
        return d

    def _getAndRegisterTimer(self, timeoutFunc=None, timeout=None, stopAfter=None,
                             stopFunc=None):
        '''
        A convenience function for creating processes connected through a QTimer

        ============  ======================================================
        Argument      Description
        ============  ======================================================
        timeoutFunc   A function to be called after every [timeout]
        timeout       Execute [timeoutFunc] every [timeout] in milliseconds
        stopAfter     Stop the timed process after [stopAfter] milliseconds
        stopFunc      A function to be called when the timer stopped
        ============  ======================================================
        '''
        t = _Timer()

        self._timers.append(t)
        t.sigStarted.connect(self.automation._setRunning)
        t.sigStopped.connect(self._checkStopped)

        if timeoutFunc:
            t.timeout.connect(timeoutFunc)
        if timeout:
            t.start(timeout)
        if stopAfter:
            QtCore.QTimer.singleShot(stopAfter, t.stop)
        if stopFunc:
            t.sigStopped.connect(stopFunc)
        return t

    def setRefreshrate(self, hz):
        self._widgetUpdateTimer.setInterval(1000 / hz)

    def _checkStopped(self):
        '''
        Set the script execution to 'done' if all timers are inactive
        '''
        for t in self._timers:
            if t.isActive():
                return
        if self._done:
            self._widgetUpdateTimer.stop()
            self.automation._updateWidget()
            self.automation._setDone()

    def start(self):
        '''
        Start the script execution
        and check whether the execution is done at the end
        '''
        self._done = False

        self._timers = []
        # self._globals.setup()

        self._widgetUpdateTimer.start()
        try:
            c = compile(str(self.scriptTab.editor.toPlainText()),
                        '<string>', 'exec')
            exec(c, self._globals)
        except Exception:
            traceback.print_exc()
        self._done = True
        self._checkStopped()

    def kill(self):
        '''
        Stop all timers and kill this script execution thread
        '''
        for t in self._timers:
            t.stop()
        if self.isRunning():
            self.terminate()


class _Timer(QtCore.QTimer):
    '''
    A QTimer with 2 new signals. emitted, when the timer...
    * started, and
    * stopped
    '''
    sigStarted = QtCore.Signal(object)  # self
    sigStopped = QtCore.Signal(object)  # self

    def start(self, msec=None):
        self.sigStarted.emit(self)
        if msec:
            QtCore.QTimer.start(self, msec)
        else:
            QtCore.QTimer.start(self)

    def stop(self):
        QtCore.QTimer.stop(self)
        self.sigStopped.emit(self)
