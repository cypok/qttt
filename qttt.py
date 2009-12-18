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

class Remote:
    def __init__(self):
        if len(sys.argv) > 1:
            config_file = sys.argv[1]
        else:
            config_file = os.environ['HOME']+'/.tttrc'
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
    def messageBox(self, title, text):
        box = QtGui.QMessageBox()
        box.setWindowTitle(title)
        box.setText(text)
        return box.exec_()

    def __init__(self):
        QtGui.QMainWindow.__init__(self)

        self.remote = Remote()

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setupUi(self)

        self.gb_current.hide()

        self.move(400, 100)
        self.resize(350, 550)

        self.setWindowTitle("QTTT - %s" % self.remote.getConfig('base_url'))

        self.connect(self.action_Qt,    QtCore.SIGNAL("activated()"),       QtGui.qApp.aboutQt)
        self.connect(self.pb_update,    QtCore.SIGNAL("clicked()"),         self.sendUpdate)
        self.connect(self.le_update,    QtCore.SIGNAL("returnPressed()"),   self.sendUpdate)
        self.connect(self.pb_stop,      QtCore.SIGNAL("clicked()"),         self.finishLast)

        self.refresh_timer = QtCore.QTimer()
        self.refresh_timer.setInterval(5*60*1000) # 5 minutes
        self.connect(self.refresh_timer, QtCore.SIGNAL("timeout()"), self.getUpdates)
        self.refresh_timer.start()

        self.last_update_timer = QtCore.QTimer()
        self.last_update_timer.setInterval(1000) # 1 second
        self.connect(self.last_update_timer, QtCore.SIGNAL("timeout()"), self.refreshLastUpdateTime)

        self.getUpdates()

    def showUpdates(self, updates):
        arr = []
        for upd in updates:
            s = u"@%(nick)s: %(msg)s" % {
                        'nick': upd['user']['nickname'],
                        'msg': upd['human_message']}
            if upd['kind'] == 'update':
                s += u" (%s ч.)" % (upd['hours'] if upd.get('hours') else "...")
            arr.append(s)
        self.te_updates.setPlainText(u"\n\n".join(arr))

    def showLastUpdate(self, update):
        if update is None:
            self.last_update_timer.stop()
            self.gb_current.hide()
        else:
            self.lb_current.setText(update['human_message'])
            self.last_update_started_at = dateutil.parser.parse(update['started_at'])
            self.refreshLastUpdateTime()
            self.last_update_timer.start()
            self.gb_current.show()

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
            self.messageBox(u"Отправка апдейта", u"Апдейт успешно отправлен")
            self.le_update.clear()

        else:
            errors = res[1]['error']
            if len(res[1]['error']) > 1:
                text = u"Произошли ошибки:\n%s"
            else:
                text = u"Произошла ошибка:\n%s"
            self.messageBox(u"Отправка апдейта", text % "\n".join(errors))

        self.getUpdates()

    def getUpdates(self):
        res = self.remote.getUpdates()
        self.showUpdates(res)

        res = self.remote.getLastUpdate()
        self.showLastUpdate(res)

    def finishLast(self):
        self.remote.finishLast()
        self.getUpdates()


app = QtGui.QApplication(sys.argv)
main = MainWindow()
main.show()
sys.exit(app.exec_())
