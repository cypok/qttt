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
        data = "update[human_message]=%s" % text
        res = json.loads(self.http.request(url, type, data)[1])
        return (res.get(u'error') is None), res

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

        self.connect(self.pb_update, QtCore.SIGNAL("clicked()"), self.sendUpdate)
        self.connect(self.le_update, QtCore.SIGNAL("returnPressed()"), self.sendUpdate)


    def sendUpdate(self):
        text = self.le_update.text()
        if text.isEmpty():
            return

        res = self.remote.sendUpdate(text)
        if res[0]:
            self.messageBox(u"Отправка апдейта", u"Апдейт успешно отправлен")
        else:
            errors = res[1][u'error']
            if len(res[1][u'error']) > 1:
                text = u"Произошли ошибки:\n%s"
            else:
                text = u"Произошла ошибка:\n%s"
            self.messageBox(u"Отправка апдейта", text % u"\n".join(errors))




app = QtGui.QApplication(sys.argv)
main = MainWindow()
main.show()
sys.exit(app.exec_())
