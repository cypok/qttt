# -*- coding: utf8 -*-

from PyQt4 import QtCore, QtGui

import dateutil.parser

class Update:
    def __init__(self, json):
        self.id = int(json['id'])
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
