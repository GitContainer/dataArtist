#!/usr/bin/env python
# coding=utf-8
import sys
import os

from qtpy import QtGui, QtWidgets, QtCore

from appbase.MultiWorkspaceWindow import MultiWorkspaceWindow
from appbase.Application import Application
from fancytools.os.PathStr import PathStr
from imgProcessor.reader.qImageToArray import qImageToArray
# from interactiveTutorial.TutorialMenu import TutorialMenu

# OWN
import dataArtist
from dataArtist.input.html2data import html2data
from dataArtist.widgets.preferences \
    import PreferencesView, PreferencesImport, PreferencesCommunication
from dataArtist.widgets.Workspace import Workspace
from dataArtist.widgets.UndoRedo import UndoRedo
from dataArtist.widgets.ProgressBar import ProgressBar
from dataArtist.widgets.dialogs.FirstStartDialog import FirstStartDialog
from dataArtist.widgets.GlobalTools import GlobalTools
from dataArtist.widgets.StatusBar import StatusBar

# by default pyqtgraph is still col-major, so:
import pyqtgraph_karl
pyqtgraph_karl.setConfigOptions(imageAxisOrder='row-major')
del pyqtgraph_karl

##########
# to allow to execute py code from a frozen environment
# type e.g. gui.exe -exec print(4+4)
if '-exec' in sys.argv:
    try:
        exec(sys.argv[-1])
    except Exception as err:
        input('-exec failed! --> %s' % err)
    sys.exit()
##########


MEDIA_FOLDER = PathStr(dataArtist.__file__).dirname().join('media')
HELP_FILE = MEDIA_FOLDER.join('USER_MANUAL.pdf')


def _showActionToolTipInMenu(menu, action):
    # show tooltip on the right side of [menu]
    # QMenu normaly doesnt allow QActions to show tooltips...
    tip = action.toolTip()
    p = menu.pos()
    p.setX(p.x() + 105)
    p.setY(p.y() - 21)
    if tip != action.text():
        QtWidgets.QToolTip.showText(p, tip)


class Gui(MultiWorkspaceWindow):
    '''
    The main class to be called to create an instance of dataArtist
    '''

    def __init__(self, title='dataArtist', workspaceCls=Workspace):
        MultiWorkspaceWindow.__init__(self, workspaceCls, title)

        s = self.app.session

        # cannot resize to px size anymore since there
        # are high dpi screens around, therefore rescale relative:
        PX_FACTOR = QtWidgets.QApplication.instance().PX_FACTOR = QtGui.QPaintDevice.logicalDpiY(
            self) / 96
        self.resize(620 * PX_FACTOR, 550 * PX_FACTOR)

        # ALLOW DRAGnDROP
        self.setAcceptDrops(True)
        # INIT CHILD PARTS:
        self.dialogs = s.dialogs
        self.pref_import = PreferencesImport(self)

        self._appendMenubarAndPreferences()
        # CONNECT OWN SAVE/RESTORE FUNCTIONS TO THE SESSION:
        s.sigSave.connect(self._save)
        s.sigRestore.connect(self._restore)
        st = StatusBar()
        self.setStatusBar(st)
        # connect output to status bar:
        s.streamOut.message.connect(st.showMessage)
        s.streamErr.message.connect(st.showError)

        # dict that contains all displays that are unbounded
        # from the main window and showed frameless:
        self.framelessDisplays = {}

        self.addWorkspace()
        # PROGRESS BAR:
        self.progressBar = ProgressBar(st)
        st.setSizeGripEnabled(False)

    def isEmpty(self):
        return (self.centralWidget().count() == 1
                and not self.currentWorkspace().displays())

    def _save(self, state):
        state['gui'] = self.saveState()

    def _restore(self, state):
        return self.restoreState(state['gui'])

    def saveState(self):
        l = {}
        i = self.size()
        p = self.pos()
        l['geometry'] = (p.x(), p.y(), i.width(), i.height())
#         l['desktop'] = QtGui.QApplication.desktop().screenNumber(self)
        c = self.centralWidget()
        l['nWorkspaces'] = c.count()
        l['currentWorkspace'] = c.indexOf(self.currentWorkspace())
        l['maximized'] = self.isMaximized()
        l['fullscreen'] = self.menuBar().ckBox_fullscreen.isChecked()
        l['showTools'] = self.menu_toolbars.a_show.isChecked()
        # WORKSPACES
        sw = l['workspaces'] = {}
        for w in self.workspaces():
            sw[w.number()] = w.saveState()
        l['undoRedo'] = self.undoRedo.saveState()
        # GLOBAL TOOLS
        tt = []
        for t in self.gTools:
            tt.append(t.saveState())
        l['globalTools'] = tt
        return l

    def restoreState(self, l):
        self.setGeometry(*l['geometry'])
        self.menuBar().setFullscreen(l['fullscreen'])
        if l['maximized']:
            self.showMaximized()
        else:
            self.showNormal()
        # WORKSPACES
        c = self.centralWidget()
        n = l['nWorkspaces']
        # CLOSE OLD:
        for w in self.workspaces():
            self.closeWorkspace(w)
            # ADD NEW:
        for _ in range(n - c.count()):
            self.addWorkspace()
            # RESTORE:
        self.showWorkspace(l['currentWorkspace'])
        lw = l['workspaces']
        for number, w in zip(lw, self.workspaces()):
            w.restoreState(lw[number])

        self.menu_toolbars.a_show.setChecked(l['showTools'])
        self._toggleShowSelectedToolbars(l['showTools'])

        self.undoRedo.restoreState(l['undoRedo'])
        # GLOBAL TOOLS
        for t, tt in zip(self.gTools, l['globalTools']):
            t.restoreState(tt)

    def addFilePath(self, filepath):
        '''
        create a new display for one ore more given file paths
        INPUT: "Path/To/File.txt"
        '''
        if filepath:
            return self.currentWorkspace().addFiles([PathStr(filepath)])

    def openFile(self):
        '''
        create a new display for one ore more  files
        '''
        filepaths = self.dialogs.getOpenFileNames()
        if filepaths:
            return self.currentWorkspace().addFiles(filepaths)

    def changeActiveDisplay(self, arg):
        '''
        change the active display
        INPUT: "[displaynumber]"
            e.g.:
            "4" --> make display 4 active display
        '''
        number = int(arg)
        self.currentWorkspace().changeDisplayNumber(number)

    def showDisplay(self, arg):
        '''
        show display as frame-less window
        INPUT: "[displaynumber], [(x,y,width,height)]'
            e.g.:
            "4, (0,0,100,200)" --> show display 4 at position 0,0 with size 100,200
            "3, False" --> hide display 3
        '''
        displaynumber, pos = eval(arg)
        if not pos:
            return self.hideDisplay(displaynumber)
        else:
            (x, y, width, height) = pos
        d = self.framelessDisplays.get(displaynumber, None)
        if not d:
            try:
                d = self.currentWorkspace().displaydict()[displaynumber]
                d.release()
                d.hideTitleBar()
                d.setWindowFlags(QtCore.Qt.FramelessWindowHint |
                                 QtCore.Qt.WindowStaysOnTopHint)
                self.framelessDisplays[displaynumber] = d
            except KeyError:
                print('displaynumber [%s] not known' % displaynumber)
                return
        d.move(QtCore.QPoint(x, y))
        d.resize(width, height)
        d.show()

    def hideDisplay(self, displaynumber):
        '''
        close frame-less display
        [displaynumber]
        '''
        d = self.framelessDisplays.pop(displaynumber, None)
        if d:
            d.showTitleBar()
            d.embedd()
        else:
            print('displaynumber [%s] not known' % displaynumber)

    def runScriptFromName(self, name):
        '''
        run an open script, identified by name
        in the current display
        INPUT: "[scriptname]"
            e.g.:
            'New' --> run a script, called 'New' in the current active display
        '''
        d = self.currentWorkspace().getCurrentDisplay()
        w = d.tab.automation.tabs.widgetByName(name.decode("utf-8"))
        if not w:
            raise Exception(
                'couldnt find script [%s] in the current display' % name)
        w.thread.start()

    def _appendMenubarAndPreferences(self):
        m = self.menuBar()
        m.aboutWidget.setModule(dataArtist)
        m.aboutWidget.setInstitutionLogo((
            (MEDIA_FOLDER.join('institution_logo_crest.svg'),
                "http://www.lboro.ac.uk/research/crest/"),
            (MEDIA_FOLDER.join('institution_logo_seris.svg'),
                "http://www.seris.nus.edu.sg/"))
        )

        # hide the menu so toolbars can only be show/hidden via
        # gui->view->toolbars:
        m.setContextMenuPolicy(QtCore.Qt.PreventContextMenu)

        self.undoRedo = UndoRedo(MEDIA_FOLDER)

        self.gTools = GlobalTools()
        self.gTools.addWidget(self.undoRedo)

        m.setCornerWidget(self.gTools)

        # APPEND PREFERENCES
        pView = PreferencesView(self)
        # pView.setColorTheme('bright')

        t = m.file_preferences.tabs
        t.addTab(pView, 'View')
        t.addTab(self.pref_import, 'Import')
        t.addTab(PreferencesCommunication(self), 'Communication')
        # APPEND MENUBAR
        # MENU - FILE
        f = m.menu_file
        p = f.action_preferences
        action_file = QtWidgets.QAction('&Import', f)
        action_file.triggered.connect(self.openFile)
        action_file.setShortcut(
            QtGui.QKeySequence(
                QtCore.Qt.CTRL +
                QtCore.Qt.Key_I))
        f.insertAction(p, action_file)
        f.insertSeparator(p)
        # MENU VIEW
        v = m.menu_view
        # ACTION PRINT VIEW
        aPrintView = QtWidgets.QAction('Print view', v)
        aPrintView.setCheckable(True)
        aPrintView.triggered.connect(
            lambda checked: self.currentWorkspace().setPrintView(checked))
        v.addAction(aPrintView)

        # SHOW/HIDE history
        aHistory = QtWidgets.QAction('Program log', v)
        aHistory.setShortcut(QtCore.Qt.Key_F4)
        m.shortcutsWidget.addShortcut('F3', 'Show/Hide Program log')

        aHistory.setCheckable(True)

        def showhideHistory(checked):
            s = self.currentWorkspace().middle_splitter
            r = s.getRange(1)[1]
            if checked:
                r /= 1.5
            return s.moveSplitter(r, 1)

        def isHistoryVisible():
            s = self.currentWorkspace().middle_splitter
            aHistory.setChecked(s.sizes()[1] != 0)

        aHistory.triggered.connect(showhideHistory)
        v.aboutToShow.connect(isHistoryVisible)
        v.addAction(aHistory)

        # SHOW/HIDE preferences
        aPref = QtWidgets.QAction('Dock preferences', v)
        aPref.setShortcut(QtCore.Qt.Key_F3)
        aPref.setCheckable(True)
        m.shortcutsWidget.addShortcut('F3', 'Show/Hide Preferences')

        def isPrefVisible():
            w = self.currentWorkspace()
            s = w.vert_splitter
            return s.sizes()[0] != 0

        def showhidePref():
            s = self.currentWorkspace().vert_splitter
            if len(s) == 1:
                # preference tab is popped out
                return
            show = not isPrefVisible()
            if show:
                # restore last size:
                if hasattr(s, '_last_size'):
                    r = s._last_size
                else:
                    # initial width:
                    r = self.width() // 2.5
            else:
                # save current size:
                s._last_size = s.sizes()[0]
                r = 0
            return s.moveSplitter(r, 1)

        def setupPref():
            w = self.currentWorkspace()
            aPref.setChecked(isPrefVisible())
            aPref.setEnabled(w.displayPrefTabs.isVisible())

        aPref.triggered.connect(showhidePref)
        v.aboutToShow.connect(setupPref)
        v.addAction(aPref)

        mcopy = v.addMenu('Copy to clipboard')
        # ACTION VIEW2CLIPBOARD
        aClipboard = QtWidgets.QAction('All displays', v)
        aClipboard.triggered.connect(
            lambda checked: self.currentWorkspace().copyViewToClipboard())
        aClipboard.setShortcut(QtGui.QKeySequence('Ctrl+Shift+F12'))
        mcopy.addAction(aClipboard)
        # ACTION Display2CLIPBOARD
        aClipboard = QtWidgets.QAction('Active Display', v)
        aClipboard.triggered.connect(
            lambda checked: self.currentWorkspace().copyCurrentDisplayToClipboard())
        aClipboard.setShortcut(QtGui.QKeySequence('Ctrl+F12'))
        mcopy.addAction(aClipboard)

        # ACTION Display2CLIPBOARD
        aClipboard = QtWidgets.QAction('Active Display Item', v)
        aClipboard.triggered.connect(
            lambda checked: self.currentWorkspace().copyCurrentDisplayItemToClipboard())
        aClipboard.setShortcut(QtCore.Qt.Key_F12)
        mcopy.addAction(aClipboard)

        # MENU - TOOLS
        t = m.menu_tools = QtWidgets.QMenu('Dock')
        m.insertMenuBefore(m.menu_workspace, t)
        # ADD DISPLAY
        mDisplay = t.addMenu('Add Display')
        for i, name, key in (  # (1, 'Dot'),
                (2, 'Graph', QtCore.Qt.Key_F5),
                (3, 'Image/Video', QtCore.Qt.Key_F6),
                # TODO:
                # (4, 'Surface')
                # (5, 'TODO: Volume')
        ):
            a = mDisplay.addAction('%sD - %s' % (i - 1, name))
            a.setShortcut(key)
            a.triggered.connect(lambda checked, i=i:
                                self.currentWorkspace().addDisplay(axes=i))
        # ADD TABLE
        t.addAction('Add Table').triggered.connect(
            lambda: self.currentWorkspace().addTableDock())
        # ADD NOTEPAD
        t.addAction('Add Notepad').triggered.connect(
            lambda: self.currentWorkspace().addTextDock())
        t.addSeparator()
        # DUPLICATE CURRENT DOCK
        t.addAction('Duplicate current display').triggered.connect(
            self._duplicateCurrentDiplay)
        self._m_duplDisp = t.addMenu('Move current display to other workspace')
        self._m_duplDisp.aboutToShow.connect(self._fillMenuDuplicateToOtherWS)
        # MENU - TOOLBARS
        self.menu_toolbars = QtWidgets.QMenu('Toolbars', m)
        self.menu_toolbars.hovered[QtWidgets.QAction].connect(
            lambda action, m=self.menu_toolbars: _showActionToolTipInMenu(m, action))

        # SHOW ALL TOOLBARS - ACTION
        a = self.menu_toolbars.a_show = QtWidgets.QAction('show', m)
        f = a.font()
        f.setBold(True)
        a.setFont(f)
        a.setCheckable(True)
        a.setChecked(True)
        a.triggered.connect(self._toggleShowSelectedToolbars)

        self.menu_toolbars.aboutToShow.connect(self._listToolbarsInMenu)
        m.insertMenuBefore(m.menu_workspace, self.menu_toolbars)
        # MENU HELP
        m.menu_help.addAction('User manual').triggered.connect(
            lambda checked: os.startfile(HELP_FILE))
        # TUTORIALS
        # not used at the moment
        #         self.m_tutorials = TutorialMenu(
        #                         tutorialFolder=PathStr.getcwd('dataArtist').join('tutorials'),
        #                         openFunction=self._openFnForTutorial,
        #                         saveFunction=self.app.session.blockingSave)
        #         m.menu_help.addMenu(self.m_tutorials)

        m.menu_help.addAction('Online tutorials').triggered.connect(
            lambda checked: os.startfile(
                'http://www.youtube.com/channel/UCjjngrC3jPdx1HL8zJ8yqLQ'))
        m.menu_help.addAction('Support').triggered.connect(
            lambda checked: os.startfile(
                'https://github.com/radjkarl/dataArtist/issues'))

    def _duplicateCurrentDiplay(self):
        d = self.currentWorkspace().getCurrentDisplay()
        if not d:
            raise Exception('no display chosen')
        d.duplicate()

    def _moveCurrentDiplayToWorkspace(self, i):
        w = self.currentWorkspace()
        ws = self.workspaces(i)
        w.moveCurrentDisplayToOtherWorkspace(ws)

    def _fillMenuDuplicateToOtherWS(self):
        c = self.centralWidget()
        self._m_duplDisp.clear()
        for i in range(c.count()):
            if i != c.currentIndex():
                t = '[%s]' % str(i + 1)
                a = QtWidgets.QAction(t, self._m_duplDisp)
                a.triggered.connect(lambda clicked, i=i, self=self:
                                    self._moveCurrentDiplayToWorkspace(i))
                self._m_duplDisp.addAction(a)

    def _openFnForTutorial(self, path):
        self.app.session.setSessionPath(path)
        self.app.session.restoreCurrentState()

    def _listToolbarsInMenu(self):
        m = self.menu_toolbars
        # REMOVE OLD:
        m.clear()
        m.addAction(m.a_show)
        if m.a_show.isChecked():
            self.currentWorkspace().addShowToolBarAction(m)

    def _toggleShowSelectedToolbars(self, checked):
        self.currentWorkspace().toggleShowSelectedToolbars(checked)

    # DRAG AND GROP
    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    def keyPressEvent(self, event):
        if event.matches(QtGui.QKeySequence.Paste):
            self.dropEvent(QtWidgets.QApplication.clipboard())

    def dragEnterEvent(self, event):
        m = event.mimeData()
        if (m.hasUrls() or
                m.hasImage() or
                m.hasText()):
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()
        else:
            event.ignore()

    def _getFilePathsFromUrls(self, urls):
        '''
        return a list of all file paths in event.mimeData.urls()
        '''
        l = []

        def _appendRecursive(path):
            if path.isfile():
                # file
                l.append(path)
            else:
                for f in path:
                    # for all files in folder
                    _appendRecursive(path.join(f))

        # one or more files/folders are dropped
        for url in urls:
            if url.isLocalFile():
                path = PathStr(url.toLocalFile())
                if path.exists():
                    _appendRecursive(path)
        return l

    def dropEvent(self, event):
        m = event.mimeData()
        w = self.currentWorkspace()
        # HTML Images
        if m.hasHtml():
            paths = html2data(str(m.html()))
            w.addFiles(paths)
        # FILES
        elif m.hasUrls():
            paths = self._getFilePathsFromUrls(m.urls())
            # filter from session files and open those:
            i = 0
            while i < len(paths):
                p = paths[i]
                # DATAARTIST SESSION
                if p.endswith(self.app.session.FTYPE):
                    if self.isEmpty():
                        self.app.session.replace(p)
                    else:
                        self.app.session.new(p)
                    paths.pop(i)
                else:
                    i += 1
            w.addFiles(paths)
        # TEXT/TABLES
        elif m.hasText():
            txt = str(m.text())
            if self.txtIsTable(txt):
                w.addTableDock(text=txt)
            else:
                w.addTextDock(text=txt)

        elif m.hasImage():
            i = QtGui.QImage(m.imageData())
            w.addDisplay(data=[qImageToArray(i)])

    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    @staticmethod
    def txtIsTable(txt):
        # for now just a simple check whether there is at least
        # on tab sign in the first line
        return txt[:txt.find('\n')].count('\t') > 0


def main(name='dataArtist',
         ftype='da',
         first_start_dialog=FirstStartDialog,
         icon=None):
    '''
    General start routine
    Create a QApplication and Gui instance
    '''
    if icon is None:
        icon = MEDIA_FOLDER.join('logo.svg')

    app = Application(sys.argv,
                      name=name,
                      ftype=ftype,
                      icon=icon,
                      first_start_dialog=first_start_dialog)
    if os.name == 'posix':  # for linux-systems
        # native these under GTK looks bad - better replace
        app.setStyle("fusion")
    win = Gui(title=name)
    s = app.session
    s.registerMainWindow(win)

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
