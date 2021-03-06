# -*- coding: utf8 -*-

from PyQt4 import Qt, QtCore, QtGui

import dateutil.parser
import dateutil.tz
import sqlite3
import os
import time
import re

class Update:
    @staticmethod
    def sqlTimeFormat(time):
        return time.isoformat() if time else None

    @staticmethod
    def set_current_user(user):
        Update.current_user = user

    @staticmethod
    def to_local_timezone(dt):
        ''' Convert datetime to local timezone (before showing and editing)'''
        if dt.tzinfo is None:
          return dt
        src_offset = dt.tzinfo.utcoffset(dt)
        local_offset = dateutil.tz.tzlocal().utcoffset(dt)
        return dt - src_offset + local_offset

    @staticmethod
    def from_local_timezone(dt, dst_tzinfo):
        ''' Convert datetime from local timezone to dst_tzinfo's timezone (before saving)'''
        if dst_tzinfo is None:
          return dt
        local_offset = dateutil.tz.tzlocal().utcoffset(dt)
        dst_offset = dst_tzinfo.utcoffset(dt)
        return dt - local_offset + dst_offset

    def __init__(self, remote):
        self.remote = remote

        self.widget = QtGui.QTextBrowser()
        self.widget.setOpenLinks(False)
        self.widget.connect(self.widget, QtCore.SIGNAL('anchorClicked(const QUrl&)'), lambda url: QtGui.QDesktopServices.openUrl(url))

    def add_actions(self):
        self.widget.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        if (self.user == self.current_user):
            action_continue = QtGui.QAction(u'Продолжить', self.widget)
            action_edit = QtGui.QAction(u'Редактировать', self.widget)
            action_delete = QtGui.QAction(u'Удалить', self.widget)
            self.widget.addAction(action_continue)
            self.widget.addAction(action_edit)
            self.widget.addAction(action_delete)

            self.widget.connect(action_continue, QtCore.SIGNAL('triggered(bool)'), lambda: QtGui.qApp.activeWindow().continueUpdate(self))
            self.widget.connect(action_edit, QtCore.SIGNAL('triggered(bool)'), lambda: QtGui.qApp.activeWindow().editUpdateDialog(self))
            self.widget.connect(action_delete, QtCore.SIGNAL('triggered(bool)'), lambda: QtGui.qApp.activeWindow().deleteUpdateDialog(self))

    def initializeFromJSON(self, json):
        self.uuid = json['uuid']
        self.user = json['user']['nickname']
        self.refreshFromJSON(json)

        self.add_actions()

    def sqlTuple(self):
        return (self.uuid, self.user, self.message, self.kind, self.hours,
                self.sqlTimeFormat(self.started_at), self.sqlTimeFormat(self.finished_at),
                self.sqlTimeFormat(self.updated_at))

    def initializeFromSQL(self, row):
        self.uuid = row[0]
        self.user = row[1]
        self.message = row[2]
        self.kind = row[3]
        self.hours = row[4]
        self.started_at = dateutil.parser.parse(row[5])
        self.finished_at = dateutil.parser.parse(row[6]) if row[6] else None
        self.updated_at = dateutil.parser.parse(row[7])

        self.resetHtml()

        self.add_actions()

    def refreshFromJSON(self, json):
        self.message = json['human_message']
        self.kind = json['kind']
        self.hours = float(json['hours']) if json.get('hours') else None
        self.started_at = dateutil.parser.parse(json['started_at'])
        self.finished_at = dateutil.parser.parse(json['finished_at']) if json['finished_at'] else None
        self.updated_at = dateutil.parser.parse(json['updated_at'])

        self.resetHtml()

    def resetHtml(self):
        s = u"<b><font color='#3f0afe'>@%s</font></b> " % self.user
        time = self.to_local_timezone( self.started_at ).strftime("%H:%M")
        if self.kind == 'update':
            s += u"<small>начал в </small>%s<small> и " % time
            if self.hours:
                s += u"потратил </small><b><font color='#3d8811'>%s ч.</font></b>" % self.hours
            else:
                s += u"до сих пор не закончил</small>"
        else:
            s += u"<small>написал в </small>%s" % time
        message = re.sub(u"#(\\w+)", lambda m: u"<a href='%(base)s/projects/%(proj)s' target='_blank'>#%(proj)s</a>" % {"base": self.remote.url, "proj": m.group(1)},self.message)
        s += u"</font><hr/>%s" % message
        
        self.widget.setHtml(s)

class UpdatesStorage:
    def __init__(self, db_path, updates_layout, remote):
        if not os.access(os.path.dirname(db_path), os.F_OK):
            # if directory not exists - create it!
            os.makedirs(os.path.dirname(db_path))
        self.connection = sqlite3.connect(db_path)
        self.cursor = self.connection.cursor()

        self.cursor.execute(
          'CREATE TABLE IF NOT EXISTS updates(uuid, user, message, kind, hours, started_at, finished_at, updated_at)'
        )
        # and delete very old updates
        self.cursor.execute(
          "DELETE FROM updates WHERE (started_at < date('now','-14 days'))"
        )
        
        self.updates_layout = updates_layout

        self.remote = remote

        self.last_timeline_date = None # date of last got status or update
        self.last_refresh = None # time of last refreshing (servers timestamp)

        self.updates = {}

    def loadUpdatesFromDB(self):
        self.cursor.execute('SELECT * FROM updates ORDER BY started_at')
        for row in self.cursor.fetchall():
            u = Update(self.remote)
            u.initializeFromSQL(row)
            self.updates[u.uuid] = u

        self.refreshLayout()


    def __del__(self):
        self.cursor.close()
        self.connection.close()

    def showUpdate(self, upd):
        parent = self.updates_layout.parent()
        local_start_date = Update.to_local_timezone(upd.started_at).date()
        # show DATE label if new date started
        if self.last_timeline_date is None or local_start_date > self.last_timeline_date:
            label = QtGui.QLabel()
            label.setAlignment(QtCore.Qt.AlignHCenter)
            label.setTextFormat(QtCore.Qt.RichText)
            label.setText('<h3>%s</h3>' % local_start_date.strftime('%A, %d.%m.%y').decode('utf-8'))
            self.updates_layout.insertWidget(0, label)

            self.last_timeline_date = local_start_date

        upd.widget.setParent(parent) # parent = scroll area
        self.updates_layout.insertWidget(1, upd.widget)
        
    def addOrRefreshUpdate(self, upd_json):
        updated_at = dateutil.parser.parse(upd_json['updated_at'])
        refresh = time.mktime(updated_at.timetuple())
        if self.last_refresh is None or self.last_refresh < refresh:
            self.last_refresh = refresh

        upd = self.updates.get(upd_json['uuid'])
        if upd is not None:
            # refresh if it is needed
            if upd.updated_at < updated_at:
                upd.refreshFromJSON(upd_json)

            self.cursor.execute(
              """UPDATE updates
                 SET user=?,message=?,kind=?,
                     hours=?,started_at=?,finished_at=?,updated_at=?
                 WHERE uuid = ?""",
              list(upd.sqlTuple())[1:] + [upd.uuid]
            )
            self.connection.commit()

        else:
            # create and show
            upd = Update(self.remote)
            upd.initializeFromJSON(upd_json)

            self.updates[upd_json['uuid']] = upd
        
            self.cursor.execute(
              """INSERT INTO updates
                 VALUES(?,?,?,?,?,?,?,?)""",
              upd.sqlTuple()
            )
            self.connection.commit()
    
    def refreshLayout(self):
        # clear layout
        while True:
            item = self.updates_layout.itemAt(0)
#            print str(item) if item is None else str(item.widget())

            if item is None:
                break
            self.updates_layout.removeItem(item)
            # and delete labels
            if isinstance(item.widget(), QtGui.QLabel):
                item.widget().close()

        upds = self.updates.values()
        upds.sort(lambda x,y : cmp(x.started_at, y.started_at))

        self.last_timeline_date = None
        for u in upds:
            self.showUpdate(u)
    
    def deleteUpdate(self, upd):
        del self.updates[upd.uuid]

        self.updates_layout.removeWidget(upd.widget)
        upd.widget.close()

        self.cursor.execute(
          """DELETE FROM updates
             WHERE uuid == ?""",
          [upd.uuid]
        )
        self.connection.commit()
