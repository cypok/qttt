#!/usr/bin/env python
# -*- coding: utf8 -*-

import sys
from PyQt4 import QtCore, QtGui

from main_ui import Ui_MainWindow
import os
import yaml
import json
import httplib2
import urllib
import datetime
import dateutil.parser
import dateutil.tz
import dateutil.relativedelta

from update import Update

class Remote:
    def __init__(self):
        if len(sys.argv) > 1:
            config_file = sys.argv[1]
        else:
            config_file = os.path.expanduser("~")+'/.tttrc'
        with open(config_file) as f:
            self.config = yaml.load(f.read())
        self.http = httplib2.Http()

    def getConfig(self, name):
        return self.config[name]

    def sendUpdate(self, text):
        url = "%s/updates.json?%s" % (self.getConfig("base_url"), urllib.urlencode({'api_key':self.getConfig('api_key')}))
        type = "POST"
        data = "update[human_message]=%s" % unicode(text).encode('utf-8')
        res = json.loads(self.http.request(url, type, data)[1])
        return (res.get('error') is None), res

    def getUpdates(self):
        url = "%s/updates.json?%s" % (self.getConfig("base_url"), urllib.urlencode({'api_key':self.getConfig('api_key'),'limit':15}))
        type = "GET"
        res = json.loads(self.http.request(url, type)[1])
        return res

    def getLastUpdate(self):
        url = "%s/updates/last.json?%s" % (self.getConfig("base_url"), urllib.urlencode({'api_key':self.getConfig('api_key'),'limit':15}))
        type = "GET"
        res = json.loads(self.http.request(url, type)[1])
        return (res if res.get('error') is None else None)

    def finishLast(self):
        url = "%s/updates/finish_last.json?%s" % (self.getConfig("base_url"), urllib.urlencode({'api_key':self.getConfig('api_key')}))
        type = "POST"
        json.loads(self.http.request(url, type)[1])

class MainWindow(QtGui.QMainWindow, Ui_MainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)

        self.remote = Remote()

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setupUi(self)

        self.tray = QtGui.QSystemTrayIcon(self)
        
        icon = QtGui.QIcon('icon.png')
        self.tray.setIcon(icon)
        self.setWindowIcon(icon)
        
        self.tray.show()

        self.gb_current.hide()

        self.move(400, 50)
        self.resize(350, 550)

        self.setWindowTitle("QTTT - %s" % self.remote.getConfig('base_url'))

        self.updates_layout = QtGui.QVBoxLayout(self.scrollAreaWidgetContents)
        self.updates_layout.setMargin(1)

        self.connect(self.action_Qt,    QtCore.SIGNAL("activated()"),       QtGui.qApp.aboutQt)
        self.connect(self.pb_update,    QtCore.SIGNAL("clicked()"),         self.sendUpdate)
        self.connect(self.le_update,    QtCore.SIGNAL("returnPressed()"),   self.sendUpdate)
        self.connect(self.pb_stop,      QtCore.SIGNAL("clicked()"),         self.finishLast)
        self.connect(self.tray,         QtCore.SIGNAL("activated(QSystemTrayIcon::ActivationReason)"), self.trayActivated)

        self.refresh_timer = QtCore.QTimer()
        self.refresh_timer.setInterval(5*60*1000) # 5 minutes
        self.connect(self.refresh_timer, QtCore.SIGNAL("timeout()"), self.getUpdates)
        self.refresh_timer.start()

        self.last_update_timer = QtCore.QTimer()
        self.last_update_timer.setInterval(1000) # 1 second
        self.connect(self.last_update_timer, QtCore.SIGNAL("timeout()"), self.refreshLastUpdateTime)

        self.updates = {}
        self.last_update = None
        self.getUpdates()

    def showMessage(self, title, message, status=None, only_status=False):
        self.statusBar().showMessage(status if status else message, 5000)
        if not only_status:
            self.tray.showMessage(title, message)

    def showUpdate(self, upd):
        upd.widget.setParent(self.sa_updates)
        self.updates_layout.insertWidget(0, upd.widget)

    def showLastUpdate(self, u):
        self.lb_current.setText(u.message)
        self.last_update_started_at = dateutil.parser.parse(u.started_at) # it's easy to remember this time
        self.refreshLastUpdateTime()
        self.last_update_timer.start()
        self.gb_current.show()
    
    def hideLastUpdate(self):
        self.last_update_timer.stop()
        self.gb_current.hide()

    def refreshLastUpdateTime(self):
        now = datetime.datetime.now(dateutil.tz.tzlocal())
        delta = dateutil.relativedelta.relativedelta(now, self.last_update_started_at)
        self.lb_time.setText("%02i:%02i:%02i" % (delta.hours, delta.minutes, delta.seconds))

    def sendUpdate(self):
        text = self.le_update.text()
        if text.isEmpty():
            self.getUpdates()
            return

        res = self.remote.sendUpdate(text)
        if res[0]:
            self.showMessage(u"Отправка апдейта", u"Апдейт успешно отправлен", only_status = True)
            self.le_update.clear()

        else:
            errors = res[1]['error']
            if len(res[1]['error']) > 1:
                text = u"Произошли ошибки:\n%s"
            else:
                text = u"Произошла ошибка:\n%s"
            self.showMessage(u"Отправка апдейта", text % "\n".join(errors), u"Произошли ошибки")

        self.getUpdates()

    def getUpdates(self):
        # get all updates
        all_updates = self.remote.getUpdates()
        last_update = self.remote.getLastUpdate()

        all_updates.reverse() # cause we got reversed in time array
        for upd in all_updates:
            if upd['id'] in self.updates:
                # refresh if it is needed
                old = self.updates[upd['id']]
                if old.updated_at < upd['updated_at']:
                    old.refresh(upd)
            else:
                # create and show
                self.updates[upd['id']] = Update(upd)
                self.showUpdate( self.updates[upd['id']] )

        # check we can now render last_update
        if last_update is None:
            self.hideLastUpdate()
        else:
            if last_update['id'] in self.updates:
                self.showLastUpdate(self.updates[last_update['id']])
            

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
