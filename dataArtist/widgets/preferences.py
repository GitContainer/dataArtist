# coding=utf-8
'''
Widgets handling all dataArtist preferences
'''

from qtpy import QtWidgets, QtCore
import pyqtgraph_karl as pg

from dataArtist.communication.RabbitMQServer import RabbitMQServer
from dataArtist.communication.WatchFolder import WatchFolder


class PreferencesCommunication(QtWidgets.QWidget):
    '''
    Preferences for communication between dataArtist and other programs
     - this is at the moment done using a RabbitMQ server
    '''

    def __init__(self, gui):
        QtWidgets.QWidget.__init__(self)

        self.gui = gui

        rab = self.rabbitMQServer = RabbitMQServer(gui)
        self._wf = wf = WatchFolder(gui)

        s = gui.app.session
        # CONNECT SAVE/RESTORE:
        s.sigSave.connect(self._save)
        s.sigRestore.connect(self._restore)
        # CONNECT CLOSE
        gui.app.lastWindowClosed.connect(
            rab.stop)

        # LAYOUT:
        layout = QtWidgets.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignTop)
        self.setLayout(layout)

        # WATCH FOLDER
        #############
        self.cb_watchFolder = QtWidgets.QCheckBox('Watch folder')
        self.cb_watchFolder.toggled.connect(self._watchFolderChanged)
        layout.addWidget(self.cb_watchFolder)

        self._folder_opts = QtWidgets.QWidget()
        layout.addWidget(self._folder_opts)
        gl = QtWidgets.QGridLayout()
        self._folder_opts.setLayout(gl)
        self._folder_opts.hide()

        self._wf_folderEdit = QtWidgets.QLineEdit('-')
        self._wf_folderEdit.setReadOnly(True)
        gl.addWidget(self._wf_folderEdit, 0, 0)
        btn = QtWidgets.QPushButton('Change')
        btn.clicked.connect(self._wf_folderChanged)
        gl.addWidget(btn, 0, 1)

        self._cb_filesOnly = QtWidgets.QCheckBox('Files only')
        self._cb_filesOnly.setChecked(wf.opts['files only'])
        self.cb_watchFolder.toggled.connect(lambda val:
                                            wf.opts.__setitem__('files only', val))
        gl.addWidget(self._cb_filesOnly, 1, 0)

        gl.addWidget(QtWidgets.QLabel('refreshrate [msec]'), 2, 0)
        self._wf_refRate = QtWidgets.QSpinBox()
        self._wf_refRate.setRange(1, 100000)
        self._wf_refRate.setValue(wf.opts['refreshrate'])
        self._wf_refRate.valueChanged.connect(self._wf_refRateChanged)
        gl.addWidget(self._wf_refRate, 2, 1)

        # RABBIT MQ
        ##########
        hlayout = QtWidgets.QHBoxLayout()
        layout.addLayout(hlayout)

        self.cb_allowRabbit = QtWidgets.QCheckBox(
            'Allow inter-process communication\nusing the RabbitMQ server')
        self.cb_allowRabbit.toggled.connect(self._allowRabbitMQchanged)
        self.cb_allowRabbit.toggled.connect(self.updateGeometry)

        hlayout.addWidget(self.cb_allowRabbit)

        self.cb_confirm = QtWidgets.QCheckBox('Confirm received messages')
        self.cb_confirm.hide()
        self.cb_confirm.setChecked(rab.opts['corfirmPosts'])
        self.cb_confirm.toggled .connect(lambda val: rab.opts.__setitem__(
            'corfirmPosts', val))
        hlayout.addWidget(self.cb_confirm)

        self._rab_opts = QtWidgets.QWidget()
        layout.addWidget(self._rab_opts)
        gl = QtWidgets.QGridLayout()
        self._rab_opts.setLayout(gl)
        self._rab_opts.hide()

        gl.addWidget(QtWidgets.QLabel('refreshrate [msec]'), 0, 0)
        self._rab_refRate = QtWidgets.QSpinBox()
        self._rab_refRate.setRange(1, 1000)
        self._rab_refRate.setValue(rab.opts['refreshrate'])
        self._rab_refRate.valueChanged.connect(lambda val: rab.opts.__setitem__(
            'refreshrate', val))
        gl.addWidget(self._rab_refRate, 0, 1)

        gl.addWidget(QtWidgets.QLabel('host'), 1, 0)
        self.le_host = QtWidgets.QLineEdit()
        self.le_host.setText(rab.opts['host'])
        self.le_host.textChanged.connect(lambda val:
                                         rab.opts.__setitem__('host', val))
        gl.addWidget(self.le_host, 1, 1)

        gl.addWidget(QtWidgets.QLabel(
            '<b>....listen to queues named:</b>'), 3, 0)
        for n, (queue, action) in enumerate(rab.listenTo.items()):
            gl.addWidget(QtWidgets.QLabel(queue), 4 + n, 0)
            gl.addWidget(QtWidgets.QLabel(action.__doc__), 4 + n, 1)

    def _watchFolderChanged(self, checked):
        self._folder_opts.setVisible(checked)
        if checked:
            if self._wf_folderEdit.text() != '-':
                self._wf.start()
            # update size
            tt = self.gui.menuBar().file_preferences
            s = tt.minimumSize()
            h, w = s.height(), s.width()
            tt.setMinimumSize(w, h + 400)
        else:
            self._wf.stop()
            # update size
            tt = self.gui.menuBar().file_preferences
            s = tt.minimumSize()
            h, w = s.height(), s.width()
            tt.setMinimumSize(w, h - 400)

    def _wf_refRateChanged(self, rate):
        self._wf.opts['refreshrate'] = rate
        self._wf.stop()
        self._wf.start()

    def _wf_folderChanged(self):
        t = self._wf_folderEdit.text()
        kwargs = {}
        if t != '-':
            kwargs['directory'] = t
        f = self.gui.dialogs.getExistingDirectory(**kwargs)
        if f:
            self._wf.opts['folder'] = f
            self._wf_folderEdit.setText(f)
            self._wf.stop()
            self._wf.start()

    def _allowRabbitMQchanged(self, checked):
        PX_FACTOR = QtWidgets.QApplication.instance().PX_FACTOR

        if checked:
            try:
                self.rabbitMQServer.start()
            except Exception as ex:
                # maybe rabbitMQ is not installed
                # needs to assign to self, otherwise garbage collected
                self._errm = QtWidgets.QErrorMessage()
                self._errm.showMessage("""Could not load RabbitMQ

%s: %s

Have you installed it?

https://www.rabbitmq.com""" % (
                    type(ex).__name__, ex.args))
                self.cb_allowRabbit.setChecked(False)
                self.cb_allowRabbit.setEnabled(False)
                return

            # update size
            tt = self.gui.menuBar().file_preferences
            s = tt.minimumSize()
            h, w = s.height(), s.width()
            tt.setMinimumSize(w + 600 * PX_FACTOR, h + 600 * PX_FACTOR)

        else:
            self.rabbitMQServer.stop()
            # update size
            tt = self.gui.menuBar().file_preferences
            s = tt.minimumSize()
            h, w = s.height(), s.width()
            if h:
                tt.setMinimumSize(w - 600 * PX_FACTOR, h - 600 * PX_FACTOR)

        self._rab_opts.setVisible(checked)
        self.cb_confirm.setVisible(checked)

    def _save(self, state):
        # TODO: add server.opts.[activated]
        # TODO: only save server.opts
        # TODO. create def update to read from server.opts
        #         session.addContentToSave({
        state['pcommunication'] = {
            'WatchFolderOpts': self._wf.opts,

            'RMQ_refreshRate': self._rab_refRate.value(),
            'RMQ_host': str(self.le_host.text()),
            #             'RMQ_timeout': self.sb_timeout.value(),
            'RMQ_activated': self.cb_allowRabbit.isChecked(),
            'RMQ_confirmPosts': self.cb_confirm.isChecked(),
        }

    def _restore(self, state):
        l = state['pcommunication']

        wf = l['WatchFolderOpts']
        self._wf_refRate.setValue(wf['refreshrate'])
        self._cb_filesOnly.setChecked(wf['files only'])
        self._wf_folderEdit.setText(wf['folder'])

        self._rab_refRate.setValue(l['RMQ_refreshRate'])
        self.le_host.setText(l['RMQ_host'])
#         self.sb_timeout.setValue(l['RMQ_timeout'])
        self.cb_confirm.setChecked(l['RMQ_confirmPosts'])
        self.cb_allowRabbit.setChecked(l['RMQ_activated'])


class ChooseProfile(QtWidgets.QWidget):

    def __init__(self, session):
        QtWidgets.QWidget.__init__(self)

        lab = QtWidgets.QLabel('Profile:')
        tt = '''The chosen profile influences the visibility of tool bars.
Changes are only effective after restarting the program.'''
        lab.setToolTip(tt)

        cb = QtWidgets.QComboBox()
        cb.setToolTip(tt)
        items = ('simple', 'advanced')
        cb.addItems(items)
        try:
            cb.setCurrentIndex(items.index(session.opts['profile']))
        except KeyError:
            session.opts['profile'] = 'simple'
            pass
        cb.currentIndexChanged.connect(lambda _i:
                                       session.opts.__setitem__(
                                           'profile', str(cb.currentText())))

        l = QtWidgets.QHBoxLayout()
        self.setLayout(l)

        l.addWidget(lab)
        l.addWidget(cb)


class PreferencesView(QtWidgets.QWidget):
    '''
    General view preferences, like the colour theme
    '''

    def __init__(self, gui):
        # TODO: make pyqtgraph optics(colortheme...) directly changeable
        # not just at reload
        QtWidgets.QWidget.__init__(self)
        self.gui = gui
        session = gui.app.session
        # CONNECT SAVE/RESTORE:
        session.sigSave.connect(self._save)
        session.sigRestore.connect(self._restore)
        # LAYOUT:
        layout = QtWidgets.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignTop)
        self.setLayout(layout)

        hlayout = QtWidgets.QHBoxLayout()
        layout.addLayout(hlayout)
        self.label_colorTheme = QtWidgets.QLabel('Color theme')
        hlayout.addWidget(self.label_colorTheme)

        self.combo_colorTheme = QtWidgets.QComboBox()
        hlayout.addWidget(self.combo_colorTheme)
        self.combo_colorTheme.addItems(('dark', 'bright'))
        self.combo_colorTheme.currentIndexChanged.connect(
            self._colorThemeChanged)
        # by default pyqtgraph is dark ... make bright:
        self.combo_colorTheme.setCurrentIndex(1)

        self.check_antialiasting = QtWidgets.QCheckBox('Antialiasting')
        layout.addWidget(self.check_antialiasting)
        self.check_antialiasting.stateChanged.connect(
            self._antialiastingChanged)

        combo_profile = ChooseProfile(session)
        layout.addWidget(combo_profile)

        btn = QtWidgets.QPushButton('Make default')
        btn.clicked.connect(self._makeDefault)
        layout.addWidget(btn)

        p = session.opts.get('pview', None)
        if p is not None:
            self._restore(p)

    def _makeDefault(self):
        d = {}
        self._save(d)
        self.gui.app.session.opts['pview'] = d

    def _antialiastingChanged(self, val):
        pg.setConfigOption('antialias', bool(val))
        for ws in self.gui.workspaces():
            ws.reload()

    def _save(self, state):
        state['pview'] = {
            'colorTheme': self.combo_colorTheme.currentIndex(),
            'antialias': self.check_antialiasting.isChecked()}

    def _restore(self, state):
        p = state['pview']
        self.combo_colorTheme.setCurrentIndex(p['colorTheme'])
        self.check_antialiasting.setChecked(p['antialias'])

    def _colorThemeChanged(self, _index):
        theme = self.combo_colorTheme.currentText()
        if theme == 'dark':
            pg.setConfigOption('foreground', 'w')
            pg.setConfigOption('background', 'k')

        elif theme == "bright":
            pg.setConfigOption('foreground', 'k')
            pg.setConfigOption('background', 'w')
        else:
            raise AttributeError('theme %s unknown' % theme)

        for ws in self.gui.workspaces():
            ws.reload()


class _QComboBox(QtWidgets.QComboBox):

    def __init__(self, pref, *args, **kwargs):
        self.pref = pref
        QtWidgets.QComboBox.__init__(self, *args, **kwargs)
        self.activated.connect(self._updateDisplayNumber)

    def showPopup(self):
        self.buildMenu()
        QtWidgets.QComboBox.showPopup(self)

    def buildMenu(self):
        old = [self.itemText(i) for i in range(self.count())]
        new = ['CURRENT']
        self._numbers = list(
            self.pref.gui.currentWorkspace().displaydict().keys())
        new.extend(['[%i]' % n for n in self._numbers])
        if old != new:
            self.clear()
            self.addItems(new)
            if len(old) == 0:
                self.pref.importFilesPolicy = self.pref.inCurrentDisplay

    def _updateDisplayNumber(self, index):
        if index == 0:
            self.pref.importFilesPolicy = self.pref.inCurrentDisplay
        else:
            self.pref.importFilesPolicy = self.pref.inDisplay
            self.pref.displayNumber = self._numbers[index - 1]


class PreferencesImport(QtWidgets.QWidget):
    '''
    Preferences for importing files
    '''
    separated = 0
    together = 1
    inDisplay = 2
    inCurrentDisplay = 3
    displayNumber = None

    importFilesPolicy = together
    showImportDialog = True
    loadImportedFiles = True

    def __init__(self, gui):
        QtWidgets.QWidget.__init__(self)
        self.gui = gui
        # CONNECT SAVE/RESTORE:
        gui.app.session.sigSave.connect(self._save)
        gui.app.session.sigRestore.connect(self._restore)
        # LAYOUT:
        layout = QtWidgets.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignTop)
        self.setLayout(layout)

        # <<<
        hlayout = QtWidgets.QHBoxLayout()
        layout.addLayout(hlayout)
        label_multifiles = QtWidgets.QLabel('Import files')
        hlayout.addWidget(label_multifiles)

        self.combo_import = QtWidgets.QComboBox()
        hlayout.addWidget(self.combo_import)

        self.combo_import.addItems(('SPLIT into MULTIPLE displays',
                                    'ALL in NEW display',
                                    'ADD to display',
                                    ))

        self.combo_import.setCurrentIndex(self.importFilesPolicy)
        self.combo_import.currentIndexChanged.connect(self._importChanged)
        # >>>

        # <<< LABEL(Display) - COMBO(CURRENT, 1,2,3...)
        hlayout = QtWidgets.QHBoxLayout()
        layout.addLayout(hlayout)
        self.label_displays = QtWidgets.QLabel('Display')
        hlayout.addWidget(self.label_displays)
        self.combo_display = _QComboBox(self)
        hlayout.addWidget(self.combo_display)
        self.combo_display.hide()
        self.label_displays.hide()
        # >>>

        self.btn_loadFiles = QtWidgets.QCheckBox('load files')
        self.btn_loadFiles.setChecked(True)
        self.btn_loadFiles.toggled.connect(
            lambda checked, self=self: self.__setattr__(
                'loadImportedFiles', checked))
        layout.addWidget(self.btn_loadFiles)

        self.btn_ask = QtWidgets.QCheckBox('Show import dialog')
        self.btn_ask.setChecked(self.showImportDialog)
        self.btn_ask.toggled.connect(
            lambda checked, self=self: self.__setattr__(
                'showImportDialog', checked))
        layout.addWidget(self.btn_ask)

    def _importChanged(self, index):
        self.importFilesPolicy = index
        v = index == self.inDisplay
        if v:
            self.combo_display.buildMenu()
            self.combo_display.show()
            self.label_displays.show()
        else:
            self.combo_display.hide()
            self.label_displays.hide()

    def _save(self, state):
        state['pimport'] = {
            'importOption': self.combo_import.currentIndex(),
            'loadFiles': self.btn_loadFiles.isChecked(),
            'showDialog': self.btn_ask.isChecked()}

    def _restore(self, state):
        l = state['pimport']
        self.combo_import.setCurrentIndex(l['importOption'])
        self.btn_loadFiles.setChecked(l['loadFiles'])
        self.btn_ask.setChecked(l['showDialog'])

    def updateSettings(self, pref):
        '''
        update all setting to the given instance
        '''
        pref.combo_import.setCurrentIndex(
            self.combo_import.currentIndex())
        pref.btn_ask.setChecked(self.showImportDialog)
        pref.btn_loadFiles.setChecked(self.loadImportedFiles)
        pref.combo_display.setCurrentIndex(
            self.combo_display.currentIndex())
        pref.displayNumber = self.displayNumber
        pref.importFilesPolicy = self.importFilesPolicy
