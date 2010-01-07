# -*- coding: utf8 -*-

from PyQt4 import QtCore, QtGui

import dateutil.parser
import sqlite3
import os
import time

class Update:
    def __init__(self, json):
        self.uuid = json['uuid']
        self.user = json['user']['nickname']
    
        self.widget = QtGui.QTextBrowser()

        self.refresh(json)


    def refresh(self, json):
        self.message = json['human_message']
        self.started_at = dateutil.parser.parse(json['started_at'])
        if json['finished_at'] is not None:
            self.finished_at = dateutil.parser.parse(json['finished_at'])
        else:
            self.finished_at = None
        self.updated_at = dateutil.parser.parse(json['updated_at'])
        self.kind = json['kind']
        self.hours = float(json['hours']) if json.get('hours') else None

        s = u"<b><font color='#3f0afe'>@%(nick)s</font></b>: %(msg)s" % {
                'nick': self.user,
                'msg':self.message}
        if self.kind == 'update':
            s += u" <b><font color='#3d8811'>(%s ч.)</font></b>" % (self.hours if self.hours else "...")
        
        self.widget.setHtml(s)

class UpdatesStorage:
    def __init__(self, db_path, updates_layout):
        if not os.access(os.path.dirname(db_path), os.F_OK):
            # if directory not exists - create it!
            os.makedirs(os.path.dirname(db_path))
        self.connection = sqlite3.connect(db_path)
        self.cursor = self.connection.cursor()

        self.cursor.execute('CREATE TABLE IF NOT EXISTS updates (id INTEGER, uuid TEXT, message TEXT)')
        
        self.updates_layout = updates_layout

        self.last_timeline_date = None # date of last got status or update
        self.last_refresh = None # time of last refreshing (servers timestamp)

        self.updates = {}

    def __del__(self):
        self.cursor.close()
        self.connection.close()

    def showUpdate(self, upd):
        parent = self.updates_layout.parent()
        # show DATE label if new date started
        if self.last_timeline_date is None or upd.started_at.date() > self.last_timeline_date:
            label = QtGui.QLabel(parent)
            label.setAlignment(QtCore.Qt.AlignHCenter)
            label.setTextFormat(QtCore.Qt.RichText)
            label.setText('<h3>%s</h3>' % upd.started_at.date().strftime('%A, %d.%m.%y').decode('utf-8'))
            self.updates_layout.insertWidget(0, label)

            self.last_timeline_date = upd.started_at.date()

        upd.widget.setParent(parent) # parent = scroll area
        self.updates_layout.insertWidget(1, upd.widget)
        
        
    def addOrRefreshUpdate(self, upd):
        updated_at = dateutil.parser.parse(upd['updated_at'])
        refresh = time.mktime(updated_at.timetuple())
        if self.last_refresh is None or self.last_refresh < refresh:
            self.last_refresh = refresh

        if upd['uuid'] in self.updates:
            # refresh if it is needed
            old = self.updates[upd['uuid']]
            if old.updated_at < updated_at:
                old.refresh(upd)
        else:
            # create and show
            self.updates[upd['uuid']] = Update(upd)
            self.showUpdate( self.updates[upd['uuid']] )

