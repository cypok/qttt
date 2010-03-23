from PyQt4 import QtGui, QtCore
from edit_update_ui import Ui_Dialog
from time import mktime
from datetime import datetime

def datetime2QDateTime(dt):
    return QtCore.QDateTime.fromTime_t(int(mktime(dt.timetuple())))

def QDateTime2datetime(qdt):
    return datetime.fromtimestamp(qdt.toTime_t())

class EditUpdate(QtGui.QDialog, Ui_Dialog):
    def __init__(self, update, parent = None):
        QtGui.QDialog.__init__(self, parent)

        self.setupUi(self)
        self.hours.setSingleStep(0.25)

        self.message.setText(update.message)
        self.started_at.setDateTime(datetime2QDateTime(update.started_at))

        if update.finished_at is not None:
            self.finished_at.setDateTime(datetime2QDateTime(update.finished_at))
            self.hours.setValue(update.hours)
        else:
            self.finished_at.setEnabled(False)
            self.hours.setEnabled(False)

    def changed_update(self):
        return {"message" : self.message.text(),
                "started_at" : QDateTime2datetime(self.started_at.dateTime()),
                "finished_at" : QDateTime2datetime(self.finished_at.dateTime()) if self.finished_at.isEnabled() else None,
                "hours" : self.hours.value() if self.hours.isEnabled() else None}
