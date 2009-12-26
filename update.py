# -*- coding: utf8 -*-

from PyQt4 import QtCore, QtGui

class Update:
    def __init__(self, json):
        self.id = int(json['id'])
        self.user = json['user']['nickname']
    
        self.widget = QtGui.QTextBrowser()

        self.refresh(json)


    def refresh(self, json):
        self.message = json['human_message']
        self.started_at = json['started_at']
        self.finished_at = json['finished_at']
        self.updated_at = json['updated_at']
        self.kind = json['kind']
        self.hours = float(json['hours']) if json.get('hours') else None

        s = u"<b><font color='#3f0afe'>@%(nick)s</font></b>: %(msg)s" % {
                'nick': self.user,
                'msg':self.message}
        if self.kind == 'update':
            s += u" <b><font color='#3d8811'>(%s ч.)</font></b>" % (self.hours if self.hours else "...")
        
        self.widget.setHtml(s)
