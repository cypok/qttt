from PyQt4 import QtGui, QtCore
from edit_update_ui import Ui_Dialog
from time import mktime
from datetime import datetime
from update import Update

class EditUpdate(QtGui.QDialog, Ui_Dialog):
    def __init__(self, update, parent = None):
        QtGui.QDialog.__init__(self, parent)

        self.setupUi(self)
        self.hours.setSingleStep(0.25)

        self.message.setText(update.message)
        self.started_at.setDateTime(Update.to_local_timezone(update.started_at))
        self.tzinfo = update.started_at.tzinfo # store initial tzinfo to be able to convert back

        if update.finished_at is not None:
            self.finished_at.setDateTime(Update.to_local_timezone(update.finished_at))
            self.hours.setValue(update.hours)
        else:
            self.finished_at.setEnabled(False)
            self.hours.setEnabled(False)

    def changed_update(self):
        return {"message" : self.message.text(),
                "started_at" : Update.from_local_timezone(self.started_at.dateTime().toPyDateTime(), self.tzinfo),
                "finished_at" : Update.from_local_timezone(self.finished_at.dateTime().toPyDateTime(), self.tzinfo) if self.finished_at.isEnabled() else None,
                "hours" : self.hours.value() if self.hours.isEnabled() else None}
