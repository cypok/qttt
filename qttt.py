#!/usr/bin/env python
# -*- coding: utf8 -*-

from PyQt4 import QtCore, QtGui

from main_ui import Ui_MainWindow
import os
import sys
import datetime
import dateutil.parser
import dateutil.tz
import dateutil.relativedelta

from update import Update
from update import UpdatesStorage
from remote import Remote
from config import Config

from edit_update import EditUpdate

class MainWindow(QtGui.QMainWindow, Ui_MainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)

        self.config = Config()
        self.config.read()
        self.config.set_defaults()

        self.remote = Remote(self.config)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setupUi(self)

        self.tray = QtGui.QSystemTrayIcon(self)
        
        icon = QtGui.QIcon('icon.png')
        self.tray.setIcon(icon)
        self.setWindowIcon(icon)
        
        self.tray.show()

        self.gb_current.hide()

        self.move(  self.config['qttt']['geometry']['left'],
                    self.config['qttt']['geometry']['top'] )
        self.resize(self.config['qttt']['geometry']['width'],
                    self.config['qttt']['geometry']['height'] )

        self.setWindowTitle('QTTT - %s' % self.config['site']['base_url'])

        self.lb_current.setWordWrap(True)

        self.updates_layout = QtGui.QVBoxLayout(self.scrollAreaWidgetContents)
        self.updates_layout.setMargin(1)

        self.storage = UpdatesStorage(os.path.expanduser(self.config['qttt']['db_path']),
                self.updates_layout, self.remote)

        self.connect(self.action_Qt,    QtCore.SIGNAL('activated()'),       QtGui.qApp.aboutQt)
        self.connect(self.pb_update,    QtCore.SIGNAL('clicked()'),         self.sendUpdate)
        self.connect(self.le_update,    QtCore.SIGNAL('returnPressed()'),   self.sendUpdate)
        self.connect(self.pb_stop,      QtCore.SIGNAL('clicked()'),         self.finishLast)
        self.connect(self.tray,         QtCore.SIGNAL('activated(QSystemTrayIcon::ActivationReason)'), self.trayActivated)
        self.connect(QtGui.qApp,        QtCore.SIGNAL('lastWindowClosed()'),self.writeConfig)

        self.refresh_timer = QtCore.QTimer()
        self.refresh_timer.setInterval(5*60*1000) # 5 minutes
        self.connect(self.refresh_timer, QtCore.SIGNAL('timeout()'), self.getUpdates)
        self.refresh_timer.start()

        self.last_update_timer = QtCore.QTimer()
        self.last_update_timer.setInterval(1000) # 1 second
        self.connect(self.last_update_timer, QtCore.SIGNAL('timeout()'), self.refreshLastUpdateTime)

        try:
            user = self.remote.getUser()
        except:
            QtGui.QMessageBox.warning(self, u"Ошибка", u"Не могу соединиться с сервером")
            # it's hard but it's WORKING! :)
            exit()
        if user.get('error') is not None:
            QtGui.QMessageBox.warning(self, u"Ошибка", u"Неверный api-key указан в .tttrc файле")
            # it's hard but it's WORKING! :)
            exit()
        self.storage.loadUpdatesFromDB()
        self.getUpdates()

    def writeConfig(self):
        self.config['qttt']['geometry']['width'] = self.size().width()
        self.config['qttt']['geometry']['height'] = self.size().height()
        self.config['qttt']['geometry']['left'] = self.pos().x()
        self.config['qttt']['geometry']['top'] = self.pos().y()

        self.config.write()

    def showMessage(self, title, message, status=None, only_status=False):
        self.statusBar().showMessage(status if status else message, 5000)
        if not only_status:
            self.tray.showMessage(title, message)

    def showLastUpdate(self, upd):
        self.lb_current.setText(upd.message)
        self.last_update_started_at = upd.started_at # it's easy to remember this time
        self.refreshLastUpdateTime()
        self.last_update_timer.start()
        self.gb_current.show()
    
    def hideLastUpdate(self):
        self.last_update_timer.stop()
        self.gb_current.hide()

    def refreshLastUpdateTime(self):
        now = datetime.datetime.now(dateutil.tz.tzlocal())
        delta = dateutil.relativedelta.relativedelta(now, self.last_update_started_at)
        self.lb_time.setText('%02i:%02i:%02i' % (delta.hours, delta.minutes, delta.seconds))

    def sendUpdate(self):
        text = self.le_update.text()
        if text.isEmpty():
            self.getUpdates()
            return

        res = self.remote.sendUpdate(text)
        if res[0]:
            self.showMessage(u'Отправка апдейта', u'Апдейт успешно отправлен', only_status = True)
            self.le_update.clear()

        else:
            errors = res[1]['error']
            if len(res[1]['error']) > 1:
                text = u'Произошли ошибки:\n%s'
            else:
                text = u'Произошла ошибка:\n%s'
            self.showMessage(u'Отправка апдейта', text % '\n'.join(errors), u'Произошли ошибки')

        self.getUpdates()
    
    def edit_update_dialog(self, upd):
        dlg = EditUpdate(upd, upd.widget)
        if dlg.exec_() == 0:
            return
        upd_data = dlg.changed_update()
        res = self.remote.editUpdate(upd.uuid, upd_data)
        if res[0]:
            self.showMessage(u'Редактирование апдейта', u'Апдейт успешно отредактирован', only_status = True)
        else:
            errors = res[1]['error']

            # cause we could receive one string or list of them
            if errors.__class__ is not list:
                errors = [errors]

            if len(errors) > 1:
                text = u'Произошли ошибки:\n%s'
            else:
                text = u'Произошла ошибка:\n%s'
            self.showMessage(u'Редактирование апдейта', text % '\n'.join(errors), u'Произошли ошибки')

        self.getUpdates()

    def delete_update_dialog(self, upd):
        self.showMessage(u'Извините', u'Этот функционал еще не реализован')

    def getUpdates(self):
        # get all updates
        last_update = self.remote.getLastUpdate()
        all_updates = self.remote.getUpdates(self.storage.last_refresh)

        all_updates.reverse() # cause we got reversed in time array
        for upd in all_updates:
            self.storage.addOrRefreshUpdate(upd)

        self.storage.refreshLayout()

        # check we can now render last_update
        if last_update is None:
            self.hideLastUpdate()
        else:
            self.showLastUpdate(self.storage.updates[last_update['uuid']])
            

    def finishLast(self):
        self.remote.finishLast()
        self.getUpdates()

    def closeEvent(self, event):
        # TODO: в трей, если нажат крестик
        # если Файл->Выход или Ctrl-Q то закрыть программу
        pass

    def trayActivated(self, reason):
        if reason in (  QtGui.QSystemTrayIcon.DoubleClick,
                        QtGui.QSystemTrayIcon.Trigger,
                        QtGui.QSystemTrayIcon.MiddleClick ):
            self.setVisible(not self.isVisible())

app = QtGui.QApplication(sys.argv)

main = MainWindow()
main.show()

sys.exit(app.exec_())

