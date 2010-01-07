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
from update import UpdatesStorage

class Config:
    @staticmethod
    def set_if_empty(d, key, value):
        if key not in d:
            d[key] = value

    def __init__(self):
        if len(sys.argv) > 1:
            self.config_file = sys.argv[1]
        else:
            self.config_file = os.path.expanduser('~/.tttrc')
        self.data = {}

    def read(self):
        with open(self.config_file) as f:
            self.data = yaml.load(f.read())

    def write(self):
        with open(self.config_file, 'w') as f:
            f.write( yaml.dump(self.data, default_flow_style = False, explicit_start = True) )

    def __getitem__(self, item):
        return self.data.get(item)
    
    def __setitem__(self, item, value):
        self.date[item] = value

    def set_defaults(self):
        self.set_if_empty(self.data, 'qttt', {})

        self.set_if_empty(self.data['qttt'], 'db_path', '~/.ttt/updates.db')
        
        self.set_if_empty(self.data['qttt'], 'geometry', {})

        self.set_if_empty(self.data['qttt']['geometry'], 'left', 400)
        self.set_if_empty(self.data['qttt']['geometry'], 'top', 50)
        self.set_if_empty(self.data['qttt']['geometry'], 'width', 350)
        self.set_if_empty(self.data['qttt']['geometry'], 'height', 550)


class Remote:
    def __init__(self, config):
        self.api_key = config['site']['api_key']
        self.url = config['site']['base_url']

        self.http = httplib2.Http()

    def sendUpdate(self, text):
        url = '%s/updates.json?%s' % (self.url, urllib.urlencode({'api_key':self.api_key}))
        type = 'POST'
        data = 'update[human_message]=%s' % unicode(text).encode('utf-8')
        res = json.loads(self.http.request(url, type, data)[1])
        return (res.get('error') is None), res

    def getUpdates(self, since=None):
        params = {'api_key':self.api_key,'limit':15}
        if since:
            params['since'] = since
        url = '%s/updates.json?%s' % (self.url, urllib.urlencode(params))
        type = 'GET'
        res = json.loads(self.http.request(url, type)[1])
        return res

    def getLastUpdate(self):
        url = '%s/updates/last.json?%s' % (self.url, urllib.urlencode({'api_key':self.api_key,'limit':15}))
        type = 'GET'
        res = json.loads(self.http.request(url, type)[1])
        return (res if res.get('error') is None else None)

    def finishLast(self):
        url = '%s/updates/finish_last.json?%s' % (self.url, urllib.urlencode({'api_key':self.api_key}))
        type = 'POST'
        json.loads(self.http.request(url, type)[1])


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

        self.storage = UpdatesStorage(os.path.expanduser(self.config['qttt']['db_path']), self.updates_layout)

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

    def getUpdates(self):
        # get all updates
        last_update = self.remote.getLastUpdate()
        all_updates = self.remote.getUpdates(self.storage.last_refresh)

        all_updates.reverse() # cause we got reversed in time array
        for upd in all_updates:
            self.storage.addOrRefreshUpdate(upd)

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

